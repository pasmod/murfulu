"""The measurement behind ``tools/flag_homograph_claims.py``.

Split out because the runner and the statistics are two things, and the file
was over this project's 400-line limit with both in it. Nothing here knows
about corpus versions, files or arguments: it takes words and vectors and
returns the two rank statistics and the cut read off them.
"""

from __future__ import annotations

import os
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

GANJOOR_VARIABLE = "MURFULU_GANJOOR_PATH"

LINES_PER_WORD = 6
MIN_LINES = 2
#: A verse line, not a prose paragraph. One 20,000-character row asks the
#: model for a 158 GiB attention buffer — found the hard way.
MAX_LINE_CHARS = 200
#: Resolution of the histogram the cut is read off.
BINS = 50

_WORD = re.compile(r"[ء-يٱ-ۓ‌]+")
_MARKS = re.compile(r"[ً-ْٰـ]")
_FOLD = str.maketrans({"ي": "ی", "ك": "ک", "ة": "ه", "أ": "ا", "إ": "ا", "ؤ": "و"})


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return _MARKS.sub("", text).translate(_FOLD)


def gather_lines(wanted: set[str], limit: int = LINES_PER_WORD) -> dict[str, list[str]]:
    """Verse lines per wanted word, in one pass over the Ganjoor source.

    Not through Elasticsearch: this has to work on a corpus version whose index
    has not been built yet, and matching whole tokens against the source is
    what the counting does.
    """
    source = os.environ.get(GANJOOR_VARIABLE)
    if not source:
        raise SystemExit(f"set {GANJOOR_VARIABLE}")
    connection = sqlite3.connect(f"file:{Path(source).expanduser()}?mode=ro", uri=True)
    found: dict[str, list[str]] = defaultdict(list)
    open_slots = set(wanted)
    for (text,) in connection.execute("SELECT text FROM verse WHERE text IS NOT NULL"):
        line = _normalise(text.strip())
        if not line or len(line) > MAX_LINE_CHARS:
            continue
        for raw in set(_WORD.findall(line)):
            token = raw.strip("‌")
            if token in open_slots:
                found[token].append(line)
                if len(found[token]) >= limit:
                    open_slots.discard(token)
        if not open_slots:
            break
    connection.close()
    return found


def embed(words: list[str], lines: dict[str, list[str]], model: Any, np: Any) -> Any:
    """One vector per word: the mean of the lines it was written in."""
    flat = [line for word in words for line in lines[word]]
    print(f"embedding {len(flat):,} lines…")
    encoded = model.encode(flat, batch_size=64, normalize_embeddings=True)
    pooled = []
    at = 0
    for word in words:
        count = len(lines[word])
        centre = encoded[at : at + count].mean(axis=0)
        at += count
        pooled.append(centre / np.linalg.norm(centre))
    return np.vstack(pooled)


def cut_from(shares: Any, np: Any) -> float:
    """Where the claims stop outnumbering what an unrelated pairing would give.

    The statistic is a rank among candidates the claim has nothing to do with,
    so under the null it is uniform on [0, 1] — a density of exactly 1. The cut
    is the first bin, walking up, whose claim density falls below that: past it
    a claim is no denser than chance. Nothing is tuned.
    """
    edges = np.linspace(0.0, 1.0, BINS + 1)
    density, _ = np.histogram(shares, bins=edges, density=True)
    for index in range(BINS):
        if density[index] < 1.0:
            return float(edges[index])
    return 1.0


def constructed_null(sims: Any, claimed: Any, np: Any) -> Any:
    """The rule-fit statistic for pairings that are wrong by construction.

    Every word against every rule that never claimed it. The uniform null the
    cut assumes is a claim about the statistic, and this is the check on it.
    """
    shares: list[Any] = []
    for row in range(sims.shape[0]):
        rivals = ~claimed[row]
        if rivals.sum() < 2:
            continue
        against = sims[row][rivals]
        beaten = (against[None, :] > against[:, None]).sum(axis=1)
        shares.append(beaten / (rivals.sum() - 1))
    return np.concatenate(shares)


def rule_fit(
    order_of_rules: list[str],
    measured: dict[str, list[str]],
    rows_of: dict[str, Any],
    stacks: dict[str, Any],
    against_rules: Any,
    claimed: Any,
    np: Any,
) -> tuple[dict[tuple[str, str], float], Any, Any]:
    """Per claim: the share of non-claiming rules that fit the word better."""
    totals = {rule: stack.sum(axis=0) for rule, stack in stacks.items()}
    shares: dict[tuple[str, str], float] = {}
    collected: list[Any] = []
    cosines: list[Any] = []
    for rule in order_of_rules:
        words = measured[rule]
        stack = stacks[rule]
        rows = rows_of[rule]
        # Leave-one-out in one step: subtract each word from its own rule's
        # sum before normalising, so no word can vouch for itself.
        left_out = totals[rule] - stack
        left_out = left_out / np.linalg.norm(left_out, axis=1, keepdims=True)
        scores = (stack * left_out).sum(axis=1)
        cosines.append(scores)

        rivals = ~claimed[rows]
        sims = against_rules[rows]
        beaten = ((sims > scores[:, None]) & rivals).sum(axis=1)
        share = beaten / np.maximum(rivals.sum(axis=1), 1)
        collected.append(share)
        for word, value in zip(words, share, strict=True):
            shares[rule, word] = float(value)
    return shares, np.concatenate(collected), np.concatenate(cosines)


def base_fit(
    pairs: list[tuple[str, str, str]],
    row_of: dict[str, int],
    base_row: dict[str, int],
    against_bases: Any,
) -> dict[tuple[str, str], float]:
    """Per claim: the share of other bases that fit the word better than its own.

    The check that does not care how contaminated the rule is. A derived word
    should resemble the word it was derived from more than it resembles a base
    it has nothing to do with.
    """
    shares: dict[tuple[str, str], float] = {}
    total = against_bases.shape[1]
    for rule, word, base in pairs:
        row = against_bases[row_of[word]]
        score = row[base_row[base]]
        shares[rule, word] = float((row > score).sum()) / max(total - 1, 1)
    return shares


def _describe(sample: Any, np: Any) -> dict[str, float]:
    """Enough of a distribution to reproduce the judgement without the file."""
    described: dict[str, float] = {
        "n": int(sample.size),
        "mean": round(float(sample.mean()), 4),
        "sd": round(float(sample.std()), 4),
        "min": round(float(sample.min()), 4),
        "max": round(float(sample.max()), 4),
    }
    for point in (1, 5, 25, 50, 75, 95, 99):
        described[f"p{point}"] = round(float(np.percentile(sample, point)), 4)
    return described
