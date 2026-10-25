"""What a precompute run produces, and how it is stored.

Three records. A :class:`Path` is one way of reaching a word, and it names the
lexicon entry it started from — a word merged from several entries can
otherwise no longer say where each of its derivations came from. A
:class:`Derivation` is one word with every path to it and the corpus evidence
for it. A :class:`Report` is what the run cost.

The identity of a word is **the Latin form plus the output word class**, per
docs/ARCHITECTURE.md. Behnevis is phonemic, so two Persian spellings can share
one reading and land on the same record; both are kept, and which of them the
app should show is a question for the linguist, not a dedup key.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from murfulu.rules.pack import RulePack
from murfulu.scoring.attestation import Attestation, Level

#: Steps 1–2, per docs/ARCHITECTURE.md. Deeper is generated on request.
DEFAULT_DEPTH = 2

#: The bucket a function-word homograph is counted in, apart from ``spelling``.
FUNCTION_WORD = "function_word"


def evidence_bucket(attestation: Attestation) -> str:
    """Which count a report puts one form's evidence in."""
    return FUNCTION_WORD if attestation.function_word else attestation.level.value


def _union(groups: Iterable[Iterable[str]]) -> list[str]:
    """Everything in the groups, once each, in first-seen order.

    First-seen rather than sorted so the field is stable between two runs over
    the same data — a set would reorder on every build and make two versions
    look different when nothing had changed.
    """
    seen: dict[str, None] = {}
    for group in groups:
        for item in group:
            seen.setdefault(item, None)
    return list(seen)


@dataclass(frozen=True)
class Path:
    """One way of reaching a form, and what it was built from."""

    base_latin: str
    base_fa: str
    base_type: str
    rule_ids: tuple[str, ...]
    affixes: tuple[str, ...] = ()
    glide_ids: tuple[str, ...] = ()
    #: The lexicon entry this chain started at. A merged record can hold paths
    #: from several entries, and the reader should be able to tell them apart.
    source_spelling_fa: str = ""
    source_latin: str = ""

    @property
    def depth(self) -> int:
        """How many rules were applied."""
        return len(self.rule_ids)

    def as_document(self) -> dict[str, Any]:
        """The stored shape. Not indexed — read back whole."""
        return {
            "base_form": self.base_latin,
            "base_fa": self.base_fa,
            "base_type": self.base_type,
            "rule_ids": list(self.rule_ids),
            "affixes": list(self.affixes),
            "glide_ids": list(self.glide_ids),
            "source_spelling_fa": self.source_spelling_fa,
            "source_latin": self.source_latin,
        }


@dataclass(frozen=True)
class Derivation:
    """One generated word, with every derivation of it and the corpus evidence."""

    form_latin: str
    form_fa: str
    output_type: str
    paths: tuple[Path, ...]
    #: Other Persian spellings that read the same way in Behnevis. Two Persian
    #: words can share one reading, and the record's key is the reading — so
    #: the second spelling is kept here rather than dropped. Whether they are
    #: one word is the linguist's to say; see OPEN_QUESTIONS item Q.
    form_fa_variants: tuple[str, ...] = ()
    semantic_tags: tuple[str, ...] = ()
    #: Other attested words the same rule made. Filled after the run, because
    #: it needs every other word the run produced — see ``scoring/sisters.py``.
    sister_forms: tuple[str, ...] = ()
    meaning_fa: str | None = None
    attestation: Attestation | None = None
    #: Whether some route to this form rests on written ground throughout —
    #: see :mod:`murfulu.scoring.grounding`. **``None`` is "not established"**,
    #: never "no": a run made without a corpus, or a path too deep to read
    #: back, leaves the question open and a stored ``False`` would claim it
    #: was asked and answered.
    base_attested: bool | None = None
    #: How much the first step's base resembles the bases its rule usually
    #: takes, and how many bases that centroid was built from. ``None`` is
    #: *not measured* — most rules have no centroid — and never a low score.
    semantic_typicality: float | None = None
    semantic_bases: int | None = None
    stem_1: str | None = None
    stem_2: str | None = None
    corpus_version: str = ""
    rule_pack_version: str = ""
    lexicon_snapshot_id: str = ""
    generated_at: str = ""

    @property
    def id(self) -> str:
        """``{form_latin}:{output_type}`` — the dedup key, per ARCHITECTURE."""
        return f"{self.form_latin}:{self.output_type}"

    @property
    def best(self) -> Path:
        """The shortest derivation, which is the one shown first."""
        return self.paths[0]

    @property
    def every_rule(self) -> list[str]:
        """Every rule that builds this word, by any route, in first-seen order.

        **Not the shortest chain.** The field used to be `best.rule_ids`,
        which names one derivation of however many there are — measured on
        derivations-v7, **342,511 of 1,704,021 records, 20.1%**, carried a
        chain smaller than the union of their own paths. دندانایی is reached
        five ways and the field named the first pair, so a filter on it missed
        four rules that genuinely built the word.

        The field is a `keyword` and its use is *which rules built this*, so
        it is the union. **The order is no longer a chain** and nothing should
        read it as one: `paths` carries the ordered derivations and always
        has. Settled here rather than left open because the field had no
        reader at all — `/search` queries `word_types` — so nothing could
        break, and a filter written against it later would have been quietly
        20% short.

        **And the field is now called `built_by`** (2026-08-17, closing S19).
        A field named `rule_chain` whose contents are deliberately not a chain
        is the same trap in the name that the old value was in the data, and
        the rename was free because nothing read it. It takes effect at the
        next corpus version: derivations-v10 was built before the rename and
        still carries the old key.
        """
        return _union(path.rule_ids for path in self.paths)

    @property
    def every_affix(self) -> list[str]:
        """Every affix any derivation of this word uses.

        The same defect `rule_chain` had, and fixed with it: taken from the
        shortest path alone, a word reached two ways named one route's affixes
        and not the other's.
        """
        return _union(path.affixes for path in self.paths)

    @property
    def every_glide(self) -> list[str]:
        """Every glide rule any derivation of this word applies.

        Most words use none, and a word reached two ways can need a glide on
        one route and not the other — so the shortest path was the wrong place
        to read this from too.
        """
        return _union(path.glide_ids for path in self.paths)

    @property
    def depth(self) -> int:
        """Steps taken by the shortest derivation."""
        return self.best.depth

    def as_document(self) -> dict[str, Any]:
        """The Elasticsearch document, matching ``search/mappings.py``."""
        attested = self.attestation
        document: dict[str, Any] = {
            "id": self.id,
            "form_latin": self.form_latin,
            "form_fa": self.form_fa,
            "form_fa_variants": list(self.form_fa_variants),
            "output_type": self.output_type,
            "base_form": self.best.base_latin,
            "base_type": self.best.base_type,
            "stem_1": self.stem_1,
            "stem_2": self.stem_2,
            "paths": [path.as_document() for path in self.paths],
            # Every rule that builds this word, not the shortest chain. The
            # name says so as of 2026-08-17; see `every_rule`.
            "built_by": self.every_rule,
            "affixes": self.every_affix,
            "glide_rules": self.every_glide,
            "semantic_tags": list(self.semantic_tags),
            "sister_forms": list(self.sister_forms),
            "depth": self.depth,
            "meaning_fa": self.meaning_fa,
            "corpus_version": self.corpus_version,
            "rule_pack_version": self.rule_pack_version,
            "lexicon_snapshot_id": self.lexicon_snapshot_id,
        }
        # An empty string is not a date. Elasticsearch refuses it, and it
        # should: a record with no timestamp must carry none, not a blank one.
        if self.generated_at:
            document["generated_at"] = self.generated_at
        # Written only when there is an answer. A stored null and an absent
        # field both read as *not established*, and writing one where nothing
        # was measured would make the index look better informed than it is.
        if self.base_attested is not None:
            document["base_attested"] = self.base_attested
        if self.semantic_typicality is not None:
            document["semantic_typicality"] = self.semantic_typicality
            document["semantic_bases"] = self.semantic_bases
        if attested is not None:
            document["attestation"] = attested.level.value
            document["attested_count"] = attested.total_count
            document["attested_docs"] = attested.doc_count
            document["attested_authors"] = attested.author_count
            document["attested_first_century"] = attested.first_century
            document["attested_last_century"] = attested.last_century
            document["attestation_unlinked"] = attested.spelling_unlinked
            document["attested_other_readings"] = list(attested.other_readings)
            # Only where it is set: the letters are a function word's and no
            # count above is credited. See ``rules/function_words.yaml``.
            if attested.function_word:
                document["attestation_function_word"] = attested.function_word
        return document


@dataclass
class Report:
    """What one run did. Printed at the end of the batch job."""

    entries: int = 0
    entries_with_forms: int = 0
    entries_truncated: int = 0
    forms_built: int = 0
    forms_unique: int = 0
    #: Forms reachable by more than one derivation. Filled at the end.
    forms_with_two_paths: int = 0
    #: Forms where two Persian spellings share one Behnevis reading. Kept
    #: apart in the record, and a question for the linguist.
    forms_with_two_spellings: int = 0
    depth: int = DEFAULT_DEPTH
    seconds: float = 0.0
    #: Set by whatever wrote the run out. Zero means nothing was written.
    output_bytes: int = 0
    by_attestation: Counter[str] = field(default_factory=Counter)
    by_depth: Counter[int] = field(default_factory=Counter)
    #: Whether each form's chain stands on written ground. Three counts, not
    #: two: *not established* is its own answer — see ``scoring/grounding.py``.
    grounded: int = 0
    ungrounded: int = 0
    grounding_unknown: int = 0
    #: Forms carrying a semantic part. The rest have no centroid for their
    #: rule, or no vector for their base, and carry null rather than a low
    #: score.
    with_typicality: int = 0
    #: How many forms each rule appears in. A rule with zero never fired, and
    #: no productivity figure can be measured for it — see PLAN task 5.3.
    rule_uses: Counter[str] = field(default_factory=Counter)

    @property
    def function_word_homographs(self) -> int:
        """Forms whose letters are a function word's: written, credited nothing."""
        return self.by_attestation[FUNCTION_WORD]

    @property
    def attested(self) -> int:
        """Forms the corpus has at either level of evidence.

        Not the function-word homographs: the letters are written, but as
        another word, and nothing about this one is known.
        """
        return (
            self.by_attestation[Level.READING.value]
            + (self.by_attestation[Level.SPELLING.value])
        )

    def rules_that_never_fired(self, pack: RulePack) -> list[str]:
        """Active rules this run never produced a single form with."""
        return [r.id for r in pack.rules if r.active and not self.rule_uses[r.id]]

    def summary(self) -> str:
        """The lines the batch job prints. Run time and size are required."""
        size = f"{self.output_bytes / 1_000_000:,.1f} MB" if self.output_bytes else "—"
        return "\n".join(
            [
                f"entries        {self.entries:,} "
                f"({self.entries_with_forms:,} produced something)",
                f"forms built    {self.forms_built:,}",
                f"words written  {self.forms_unique:,} "
                f"({self.forms_with_two_paths:,} built more than one way, "
                f"{self.forms_with_two_spellings:,} with a second spelling)",
                f"attested       {self.attested:,} "
                f"(reading {self.by_attestation[Level.READING.value]:,}, "
                f"spelling {self.by_attestation[Level.SPELLING.value]:,}; "
                f"{self.function_word_homographs:,} function-word homographs "
                f"credited nothing)",
                f"run time       {self.seconds:,.1f}s",
                f"output size    {size}",
            ]
        )
