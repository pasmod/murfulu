"""Characters the Behnevis alphabet does not have, repaired as they are read.

**This is not an override and must not become one.**
:mod:`murfulu.lexicon.overrides` holds values this project *believes
differently* — a stem the grammar document and the lexicon disagree on — and
every one of them is unconfirmed until the linguist rules. Nothing here is a
belief. The Behnevis alphabet is a closed set, so a character outside it is
always a fault and never a judgement: nobody meant a Greek omicron.

Measured 2026-08-13 against snapshot ``lexicon-20260808``, over all 45,579
active rows: **eleven Latin fields on eleven rows** hold a character that
looks like a Behnevis letter and is not one. The expensive one is سپردن,
whose present stem is written ``sepοr`` — a stem is copied into everything
built on it, so **2,592 forms in the v4 index carried the omicron**. None of
them could be typed, searched or matched against the corpus, and on screen
they were indistinguishable from a correct form.

Reported upstream as ``docs/UPSTREAM.md`` A5. This repairs them here until it
lands there, and goes away when it does.

**Only look-alikes are repaired.** تباهیدن is written ``tabāhهdan``, with an
Arabic ه in a Latin field. An ه does not look like anything in particular, so
what was meant is a guess — and guessing is what this module exists not to do.
That reading is left as the snapshot has it and flagged instead, so nothing
downstream can mistake it for a checked one.
"""

from __future__ import annotations

#: Each character and the Behnevis letter it is a look-alike of. Every entry
#: is a pair that renders near-identically in the fonts the app ships, which
#: is why the fault survived review in the first place.
LOOKALIKES = {
    "ο": "o",  # GREEK SMALL LETTER OMICRON
    "Α": "A",  # GREEK CAPITAL LETTER ALPHA
    "α": "a",  # GREEK SMALL LETTER ALPHA
    "Ι": "I",  # GREEK CAPITAL LETTER IOTA
    "Ε": "E",  # GREEK CAPITAL LETTER EPSILON
    "О": "O",  # CYRILLIC CAPITAL LETTER O
    "о": "o",  # CYRILLIC SMALL LETTER O
    "а": "a",  # CYRILLIC SMALL LETTER A
    "е": "e",  # CYRILLIC SMALL LETTER IE
    "р": "p",  # CYRILLIC SMALL LETTER ER
    "с": "c",  # CYRILLIC SMALL LETTER ES
    "ú": "u",  # LATIN SMALL LETTER U WITH ACUTE
}

#: Every letter a Behnevis form may be written with. Anything alphabetic and
#: outside this set, after the repair above, is something nobody here can
#: read — so the reading is flagged rather than guessed at.
ALPHABET = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZāĀšŠžŽčČéÉíÍ")


def repair(latin: str | None) -> str | None:
    """Replace look-alike characters with the Behnevis letters they stand for.

    ``None`` and the empty string pass through, so a caller never has to know
    which fields the snapshot fills in.
    """
    if not latin:
        return latin
    return "".join(LOOKALIKES.get(character, character) for character in latin)


def is_readable(latin: str | None) -> bool:
    """Whether every letter in a repaired form is one Behnevis has.

    False means a character survived :func:`repair` that this project cannot
    read — the Arabic ه in تباهیدن is the one case in the snapshot — and the
    reading carrying it is flagged for review rather than corrected.
    """
    if not latin:
        return True
    return all(character in ALPHABET for character in latin if character.isalpha())
