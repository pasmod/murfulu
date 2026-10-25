"""The semantic part of a word's score: base-to-rule typicality.

The measure the pilot validated (93% against 33% chance,
`tools/semantic_pilot.py`): a rule's attested bases have a centre in meaning
space, and **typicality** is how close a base sits to the centre of the bases
its rule usually takes. *bāgh* sits among things a keeper can keep; *raft*
does not, which is the semantic difference between *bāghbān* and the never
written *Raftbān*.

The vectors are built by a batch job (`tools/build_semantic_vectors.py`) in an
environment with torch, and **read** here — the app never embeds anything. No
artefact means no scores, which is a legitimate state, and the answer is then
``None``: *not measured*, never a low score.

**This is one part of the score, not the score** (docs/FRONTEND.md: show the
parts, never one number), and it is unvalidated against expert judgement —
the feedback set (task 8.3) is what it will be fitted against. It ranks today
on the project lead's decision, recorded in RESEARCH_SCORING.md, and it never
hides a word.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

#: Where the artefact lives. Configuration, never a literal.
PATH_VARIABLE = "MURFULU_SEMANTIC_PATH"


@dataclass(frozen=True)
class Typicality:
    """One base measured against one rule's usual bases."""

    #: Cosine of the base's vector with the rule's base centroid, in [-1, 1].
    #: In practice ≈ 0.6–0.9: poetry shares a register, so the spread is
    #: narrow and comparisons are within a result, not against an absolute bar.
    score: float
    rule_id: str
    base_latin: str
    #: How many attested bases the centroid was computed from.
    bases: int


@dataclass(frozen=True)
class Centre:
    """What one rule's centroid is, for a screen rather than for a score.

    A number on its own says nothing a reader can check. *This rule's centre
    was built from 402 bases, and the ones nearest it are these* can be read
    against the rule and disagreed with.
    """

    rule_id: str
    #: How many attested bases the centroid was computed from.
    bases: int
    #: The nearest of them, best first, as the batch job ranked them.
    typical: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class Semantics:
    """The artefact, loaded: base vectors and per-rule centroids."""

    corpus_version: str = ""
    model: str = ""
    rules: dict[str, tuple[tuple[float, ...], int]] = field(default_factory=dict)
    bases: dict[str, tuple[float, ...]] = field(default_factory=dict)
    #: Rule id → its most typical bases, as the batch job ranked them. Kept
    #: apart from ``rules`` because it is for reading, not for arithmetic.
    typical_bases: dict[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)

    def __len__(self) -> int:
        """How many rules have a centroid."""
        return len(self.rules)

    def centre(self, rule_id: str) -> Centre | None:
        """What this rule's centroid is made of, or None if it has none.

        ``None`` means the rule had fewer than the artefact's minimum attested
        pairs — most rules do. The screen says so; it never shows a zero,
        which would read as *this rule makes nothing typical*.
        """
        found = self.rules.get(rule_id)
        if found is None:
            return None
        return Centre(
            rule_id=rule_id,
            bases=found[1],
            typical=self.typical_bases.get(rule_id, ()),
        )

    def typicality(self, rule_id: str, base_latin: str) -> Typicality | None:
        """How typical this base is of this rule's bases, or None.

        ``None`` covers every way the question cannot be answered — no
        artefact, a rule with no centroid, a base with no vector — because
        *not measured* must never look like *scored low*.
        """
        centroid = self.rules.get(rule_id)
        vector = self.bases.get(base_latin)
        if centroid is None or vector is None:
            return None
        return Typicality(
            score=round(_cosine(vector, centroid[0]), 4),
            rule_id=rule_id,
            base_latin=base_latin,
            bases=centroid[1],
        )


def _cosine(one: tuple[float, ...], other: tuple[float, ...]) -> float:
    """Plain-Python cosine. 1024 multiplications; no numpy in the app."""
    dot = sum(a * b for a, b in zip(one, other, strict=True))
    norm = math.sqrt(sum(a * a for a in one)) * math.sqrt(sum(b * b for b in other))
    return dot / norm if norm else 0.0


def path() -> Path | None:
    """The configured artefact, if there is one and it exists."""
    configured = os.environ.get(PATH_VARIABLE)
    if not configured:
        return None
    found = Path(configured).expanduser()
    return found if found.is_file() else None


def load(source: Path) -> Semantics:
    """Read one artefact."""
    document = json.loads(source.read_text(encoding="utf-8"))
    return Semantics(
        corpus_version=document.get("corpus_version", ""),
        model=document.get("model", ""),
        rules={
            rule: (tuple(entry["vector"]), int(entry.get("bases", 0)))
            for rule, entry in document.get("rules", {}).items()
        },
        bases={
            latin: tuple(vector) for latin, vector in document.get("bases", {}).items()
        },
        typical_bases={
            rule: tuple(entry.get("typical_bases") or ())
            for rule, entry in document.get("rules", {}).items()
        },
    )


@lru_cache(maxsize=1)
def loaded() -> Semantics:
    """The artefact, read once. Empty when none is configured."""
    found = path()
    return load(found) if found else Semantics()
