"""The model learned without some poets, so it can be measured on them.

``tools/evaluate_behnevis.py`` reads the held-out poets' marked words with
their signs hidden; ``tools/evaluate_behnevis_metre.py`` reads the same
poets' lines with and without the metre. Both learn the same fold from here.
"""

from __future__ import annotations

import zlib
from typing import Any

from murfulu.behnevis.choice import Answered, ChoiceModel
from murfulu.behnevis.inflect import Inflector
from murfulu.behnevis.transcribe import Transcriber
from murfulu.corpus.inflection import Analyser
from murfulu.search import harakat

#: A line where more than this share of the words carry signs is taken as a
#: quotation — in Ganjoor mostly Arabic, which editions vowel throughout — and
#: not learned from: its «مِن» is not the Persian *man*, and counting it made a
#: single bank reading look wrong two times in three (the first build,
#: 2026-11-14). Persian lines carry a sign on a word here and there.
MAX_SIGNED_SHARE = 0.3


def held_out(name: str, every: int) -> bool:
    """One in ``every`` by a stable hash, so a rerun holds out the same."""
    return zlib.crc32(name.encode()) % every == 0


def fold_model(
    model: Transcriber,
    bank: dict[str, tuple[str, ...]],
    inflection: Analyser,
    inflector: Inflector,
    marked: list[dict[str, Any]],
    answered: list[Answered],
) -> Transcriber:
    """The model learned without one poet in five.

    Its choices, coverage and pattern families come from the other poets
    only; its letters are the built model's, learned from the bank.
    """
    # People's picks on the reading screen are already among the answers the
    # build saved (by_person), split by poet like the rest; counted once.
    people = [a for a in answered if a.by_person]
    train_answered = [a for a in answered if not held_out(a.author, 5)]
    covered: dict[str, list[int]] = {}
    for m in marked:
        if held_out(m["author"], 5):
            continue
        candidates = list(
            dict.fromkeys(
                (*model.functions.get(m["spelling"], ()), *bank.get(m["spelling"], ()))
            )
        )
        if not candidates:
            continue
        verdicts = [harakat.fits(m["written"], c) for c in candidates]
        if not any(verdicts) and not all(v is False for v in verdicts):
            continue  # the signs cannot judge these readings
        fits = any(verdicts)
        covered.setdefault(m["spelling"], [0, 0])[0 if fits else 1] += 1
    for a in people:
        if not held_out(a.author, 5):
            covered.setdefault(a.spelling, [0, 0])[0] += 1
    return Transcriber(
        bank=bank,
        letters=model.letters,
        choice=ChoiceModel.train(train_answered),
        covered={k: (v[0], v[1]) for k, v in covered.items()},
        inflection=inflection,
        inflector=inflector,
        # Measured on the training poets only, as the build measures it on all.
        inflected_fit=inflector.measure(
            (m for m in marked if not held_out(m["author"], 5)),
            lambda spelling: bool(bank.get(spelling) or model.functions.get(spelling)),
        ),
    )
