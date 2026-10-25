"""Say which corpus words a rule actually formed.

A suffix search finds *Pahnā* and *Fanā* together. The first was built with
*-nā*; the second is an Arabic loan that happens to end in those letters. Only
a derivation knows the difference, so this pass carries what the precompute
learned back onto the corpus word types — the affixes, the rules and the
semantic tags — and the search can then split its results.

**Which derivations are allowed to make the claim** is the whole question here,
and the answer follows the levels of attestation:

``reading``   the corpus has this spelling *and* the lexicon reads it the way
              we built it. **Claimed.**
``spelling``, no reading anywhere
              the letters are there and nothing contradicts us — but nothing
              confirms us either. **Proposed, not claimed.**
``spelling``, read as something else
              the corpus reads those letters as a different word. **Refused.**
``none``      the word was never written. Nothing to attach it to.

The middle case was claimed in the first version of this pass, on the argument
that گفتار is obviously what *-ār* builds and the dictionary merely lacks the
entry. **Measured against the real corpus, that was wrong.** Claiming every
unlinked spelling attached *-nā* to مولانا، نخلنا، لقینا and eighty more —
Arabic phrases ending in the possessive نا, which is not the Persian suffix at
all. An unlinked spelling means the lexicon knows *nothing* about the word,
including that it might not be Persian.

So they are kept as proposals instead: a list of words the corpus writes, that
our rules can build, and that no dictionary entry can confirm. That list is
worth more as a request to karbon than as an assertion in the index.

**A fourth answer, added once the semantic artefact existed.** A reading can be
confirmed and the claim still be wrong, because two different derivations spell
the same word: شاهدان is the plural of شاهد, not شاه + *-dān*. Those claims are
now *contested* — measured against the rule's own output centroid by
``tools/flag_homograph_claims.py``, held out of the index, and counted. Held
out rather than written, because ``word_types.rule_ids`` is an assertion: it is
what puts a word in the search screen's *formed with this affix* group. A word
we doubt belongs in the other group, which says only that the letters match.

**A fifth, needing no measurement: the letters are a function word's.** از,
در, به are prepositions in all but a handful of their hundreds of thousands of
occurrences, so a rule "forming" *Az* or *Dar* from a present stem has formed
nothing the corpus can show (``rules/function_words.yaml``). Contested in the
same way and for the same reason, and counted.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from murfulu.corpus.wordtypes import normalise
from murfulu.scoring.attestation import Attestation, Level
from murfulu.scoring.records import Derivation
from murfulu.scoring.sisters import SuspectClaims

#: The three fields a derivation contributes to a word type.
FIELDS = ("affixes", "rule_ids", "semantic_tags")

#: Why a claim on a function word's letters is held out.
FUNCTION_WORD_REASON = "the letters are a function word"


@dataclass
class AffixMap:
    """Word-type id → what the derivations say formed it."""

    by_word_type: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    corpus_version: str = ""
    #: Derivations whose spelling the corpus reads as a different word.
    #: Counted, never attached: how often our form collides with another.
    refused_homographs: int = 0
    #: Word-type id → the same three lists, for spellings the corpus has and
    #: **no dictionary entry confirms**. Never written to the index. This is
    #: the review list, and the strongest form of the request in UPSTREAM B2:
    #: words in real use, derivable by a rule, missing from the lexicon.
    proposed: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    #: Word-type id → ``{rule id: reason}`` for claims the homograph detector
    #: doubts. Held out of the index and reported, so a doubted claim is
    #: countable rather than either asserted or lost.
    contested: dict[str, dict[str, str]] = field(default_factory=dict)

    def __len__(self) -> int:
        """How many corpus word types a rule can be shown to have formed."""
        return len(self.by_word_type)

    def fields_for(self, word_type_id: str) -> dict[str, list[str]]:
        """The three lists to write onto one word type, or empty ones."""
        found = self.by_word_type.get(word_type_id)
        return found if found is not None else {name: [] for name in FIELDS}

    @property
    def contested_claims(self) -> int:
        """How many ``(word, rule)`` claims the detector doubted."""
        return sum(len(rules) for rules in self.contested.values())

    def as_document(self) -> dict[str, Any]:
        """The stored shape, for handing between pipeline runs."""
        return {
            "corpus_version": self.corpus_version,
            "refused_homographs": self.refused_homographs,
            "word_types": self.by_word_type,
            "proposed": self.proposed,
            "contested": self.contested,
        }

    @classmethod
    def from_document(cls, raw: dict[str, Any]) -> AffixMap:
        """Read one back."""
        return cls(
            by_word_type=raw.get("word_types") or {},
            corpus_version=raw.get("corpus_version", ""),
            refused_homographs=int(raw.get("refused_homographs", 0)),
            proposed=raw.get("proposed") or {},
            contested=raw.get("contested") or {},
        )


def _word_type_id(
    derivation: Derivation, evidence: Attestation
) -> tuple[str, bool] | None:
    """Which word type this derivation may claim, and whether it is confirmed.

    Returns ``(id, confirmed)``, or ``None`` when the corpus reads those
    letters as a different word and the derivation may say nothing at all.
    """
    spelling = normalise(derivation.form_fa)
    if evidence.level is Level.READING:
        return f"{spelling}:{derivation.form_latin}", True
    if evidence.level is Level.SPELLING and evidence.spelling_unlinked:
        # The unlinked record carries an empty Latin side. Proposed only: no
        # entry confirms this is even a Persian word.
        return f"{spelling}:", False
    return None


def _forming_rules(derivation: Derivation) -> list[tuple[str, str]]:
    """The (rule id, affix) pairs that made this word, one per path."""
    found: list[tuple[str, str]] = []
    for path in derivation.paths:
        if not path.rule_ids:
            continue
        pair = (path.rule_ids[-1], path.affixes[-1] if path.affixes else "")
        if pair not in found:
            found.append(pair)
    return found


def build(
    derivations: Iterable[Derivation],
    corpus_version: str = "",
    suspect: SuspectClaims | None = None,
) -> AffixMap:
    """Collect what each attested corpus word type was formed by.

    ``suspect`` holds ``(rule, Latin form)`` claims the homograph detector
    doubts. Those rules are held out of the word type's claim and recorded in
    ``contested``; a word every one of whose rules is doubted makes no claim
    at all, rather than a quiet one.
    """
    doubted = suspect or frozenset()
    affix_map = AffixMap(corpus_version=corpus_version)
    for derivation in derivations:
        evidence = derivation.attestation
        if evidence is None or evidence.level is Level.NONE:
            continue
        affix_map.corpus_version = affix_map.corpus_version or (
            derivation.corpus_version
        )
        if evidence.function_word:
            # Written, but as another word: nothing to claim, and every rule
            # that would have claimed it is recorded as contested.
            identifier = f"{normalise(derivation.form_fa)}:{derivation.form_latin}"
            for rule_id, _ in _forming_rules(derivation):
                affix_map.contested.setdefault(identifier, {})[rule_id] = (
                    FUNCTION_WORD_REASON
                )
            continue
        found = _word_type_id(derivation, evidence)
        if found is None:
            affix_map.refused_homographs += 1
            continue

        identifier, confirmed = found
        into = affix_map.by_word_type if confirmed else affix_map.proposed
        entry: dict[str, list[str]] = {name: [] for name in FIELDS}
        for rule_id, affix in _forming_rules(derivation):
            if (rule_id, derivation.form_latin) in doubted:
                affix_map.contested.setdefault(identifier, {})[rule_id] = (
                    "far from the words this rule usually makes"
                )
                continue
            if rule_id not in entry["rule_ids"]:
                entry["rule_ids"].append(rule_id)
            if affix and affix not in entry["affixes"]:
                entry["affixes"].append(affix)
        if not entry["rule_ids"]:
            # Every rule that could have made this word is doubted. Recorded
            # above; nothing is claimed here.
            continue
        for tag in derivation.semantic_tags:
            if tag not in entry["semantic_tags"]:
                entry["semantic_tags"].append(tag)
        stored = into.setdefault(identifier, {name: [] for name in FIELDS})
        for name in FIELDS:
            for value in entry[name]:
                if value not in stored[name]:
                    stored[name].append(value)
    return affix_map
