"""The word classes a rule can take in or produce.

The project's grammar terms, transliterated, used as machine identifiers. This
is a **closed set**: a rule whose input or output is not in it is a mistake, not
a new class, and the loader must reject it.

The list is taken from the type vocabulary in ``docs/RULE_PACK.md``, which in
turn comes from the terminology table in the source grammar.
"""

from __future__ import annotations

from typing import Final

#: What each term replaces in traditional Persian grammar, straight from the
#: source document's own terminology table. Kept next to the identifiers
#: because a reader who has not met the grammar cannot guess them.
WORD_CLASSES: Final[dict[str, str]] = {
    "karbon_yek": "بن ماضی — the past stem of a verb",
    "karbon_do": "بن مضارع — the present stem of a verb",
    "nabesudkarvaze": "مصدر — the infinitive, uninflected",
    "karnam": "اسم مصدر / اسم معنی — the doing itself, named as a noun",
    "nam": "اسم — noun",
    "barnam": "صفت — adjective",
    "karandekarbahr": "صفت فاعلی — the doer participle",
    "karidekarbahr": "صفت مفعولی — the done-to participle",
    "jonvaze": "قید — adverb",
    "janam": "ضمیر — pronoun",
    "pisvaze": "حرف اضافه — preposition",
    "nedayi": "the vocative",
}


def traditional_term(name: str) -> str | None:
    """What traditional Persian grammar calls this class, where it has a name.

    The table above stores the traditional term and an English gloss in one
    string, separated by an em dash, exactly as the source grammar's own
    terminology table lays them out. This splits them without moving the
    authority: nothing here writes Persian, it only reads what was
    transcribed.

    ``None`` for a class the traditional system has no name for.
    """
    described = WORD_CLASSES.get(name)
    if not described:
        return None
    term, dash, _ = described.partition("—")
    return term.strip() or None if dash else None


def is_word_class(name: str) -> bool:
    """True when ``name`` is one of the closed set."""
    return name in WORD_CLASSES


def describe(name: str) -> str:
    """What a word class means, for an error message or a tooltip."""
    try:
        return WORD_CLASSES[name]
    except KeyError:
        raise KeyError(
            f"{name!r} is not a word class. Known: {', '.join(sorted(WORD_CLASSES))}"
        ) from None
