"""The other words a rule actually made.

When someone is shown *Rowšannā* — a word nobody has written — the useful thing
to put beside it is not a score. It is the list of words the **same rule** did
make and that the corpus has: *Goftār*, *Raftār*, *Didār*. Those say what the
rule produces far better than a number does, and they are what a reader uses to
judge whether the new word belongs.

Only attested outputs are sisters. A rule's unattested output is the thing being
judged, not evidence for it.

Ordering is by strength of evidence, not by frequency alone:

1. a claim nothing **doubts** before one the homograph detector flagged, or
   one written with a function word's letters (از is the preposition, not
   *Az*) — a sister we are not sure the rule made is weaker evidence than one
   we are
2. a **confirmed reading** before a bare spelling — the lexicon agreeing on how
   the word is read is stronger than the letters occurring
3. then by **how many documents** it appears in — thirty hits in one poem is a
   rhyme, not a word
4. then by total occurrences, then alphabetically, so the same corpus always
   gives the same list

**A doubted sister is ranked last, never dropped.** شاهدان is the plural of
شاهد and not شاه + *-dān*, and a measurement said so — but the measurement is
a cosine against a centroid, not a ruling. Removing the row would hide a claim
the pipeline really is making; sinking it says what we think of it and leaves
it checkable.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from murfulu.scoring.attestation import Level
from murfulu.scoring.records import Derivation

#: ``(rule id, Latin form)`` pairs the detector doubts.
SuspectClaims = frozenset[tuple[str, str]]

#: How many sisters to keep per rule. The full list runs to a thousand for the
#: broadest rules, and the interface shows a handful.
DEFAULT_LIMIT = 20


@dataclass(frozen=True)
class Sister:
    """One attested output of a rule, with the evidence for it."""

    form_latin: str
    form_fa: str
    level: Level
    #: The word this rule was applied to, from the shortest path that ends in
    #: this rule. The homograph detector needs it: a derived word should
    #: resemble the word it was built from, and شاهدان does not resemble شاه.
    base_fa: str = ""
    doc_count: int = 0
    total_count: int = 0
    author_count: int = 0
    #: The word sits far from the words this rule usually makes. Measured, not
    #: judged — see ``tools/flag_homograph_claims.py``.
    suspect: bool = False
    #: The letters are a function word's (``rules/function_words.yaml``), so
    #: the corpus count is not this word's. Doubted like ``suspect``, for a
    #: reason that needs no measuring: از is the preposition, not *Az*.
    function_word: bool = False

    @property
    def doubted(self) -> bool:
        """True when something says this may not be the rule's word at all."""
        return self.suspect or self.function_word

    @property
    def confirmed(self) -> bool:
        """True when the lexicon confirms how the word is read."""
        return self.level is Level.READING

    @property
    def rank(self) -> tuple[int, int, int, int, str]:
        """The sort key. Doubt first, then evidence, frequency, name."""
        return (
            1 if self.doubted else 0,
            0 if self.confirmed else 1,
            -self.doc_count,
            -self.total_count,
            self.form_latin,
        )


@dataclass
class SisterForms:
    """Every rule's attested output, for one corpus version."""

    by_rule: dict[str, list[Sister]] = field(default_factory=dict)
    corpus_version: str = ""

    def for_rule(self, rule_id: str, limit: int | None = DEFAULT_LIMIT) -> list[Sister]:
        """The best-attested outputs of one rule. ``limit=None`` for all."""
        found = self.by_rule.get(rule_id, [])
        return found if limit is None else found[:limit]

    def for_derivation(
        self, derivation: Derivation, limit: int = DEFAULT_LIMIT
    ) -> tuple[str, ...]:
        """The sisters to store on one word, excluding the word itself.

        A word is not its own sister, and a word reachable by two rules gets
        the sisters of both — it belongs to two families and the reader should
        see both.
        """
        seen: list[str] = []
        for rule_id in _forming_rules(derivation):
            for sister in self.by_rule.get(rule_id, []):
                if sister.form_latin == derivation.form_latin:
                    continue
                if sister.form_latin not in seen:
                    seen.append(sister.form_latin)
                if len(seen) >= limit:
                    return tuple(seen)
        return tuple(seen)

    def counts(self) -> dict[str, int]:
        """How many attested outputs each rule has, before any limit."""
        return {rule_id: len(found) for rule_id, found in self.by_rule.items()}

    def suspect_counts(self) -> dict[str, int]:
        """How many of each rule's outputs the detector doubts."""
        return {
            rule_id: sum(1 for sister in found if sister.suspect)
            for rule_id, found in self.by_rule.items()
        }

    def function_word_counts(self) -> dict[str, int]:
        """How many of each rule's outputs are written as a function word."""
        return {
            rule_id: sum(1 for sister in found if sister.function_word)
            for rule_id, found in self.by_rule.items()
        }


def _forming_rules(derivation: Derivation) -> list[str]:
    """The rules that made this word — the last step of each of its paths."""
    return [rule_id for rule_id, _ in _forming(derivation)]


def _forming(derivation: Derivation) -> list[tuple[str, str]]:
    """``(rule, base)`` for the last step of each path, shortest path first."""
    found: dict[str, str] = {}
    for path in derivation.paths:
        if path.rule_ids:
            found.setdefault(path.rule_ids[-1], path.base_fa)
    return list(found.items())


def collect(
    derivations: Iterable[Derivation],
    corpus_version: str = "",
    suspect: SuspectClaims | None = None,
) -> SisterForms:
    """Gather every rule's attested output from a finished precompute.

    ``suspect`` holds the ``(rule, form)`` claims the homograph detector
    doubts. They are kept and ranked last; nothing is removed.
    """
    doubted = suspect or frozenset()
    forms = SisterForms(corpus_version=corpus_version)
    for derivation in derivations:
        evidence = derivation.attestation
        if evidence is None or evidence.level is Level.NONE:
            continue
        forms.corpus_version = forms.corpus_version or derivation.corpus_version
        for rule_id, base_fa in _forming(derivation):
            forms.by_rule.setdefault(rule_id, []).append(
                Sister(
                    form_latin=derivation.form_latin,
                    form_fa=derivation.form_fa,
                    level=evidence.level,
                    base_fa=base_fa,
                    doc_count=evidence.doc_count,
                    total_count=evidence.total_count,
                    author_count=evidence.author_count,
                    # Doubt is about *this rule* making *this word*: a word can
                    # be a fine output of one rule and a homograph under
                    # another, which is the whole shape of the fault.
                    suspect=(rule_id, derivation.form_latin) in doubted,
                    function_word=bool(evidence.function_word),
                )
            )

    for found in forms.by_rule.values():
        found.sort(key=lambda s: s.rank)
    return forms
