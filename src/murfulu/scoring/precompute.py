"""Apply every rule to every applicable lexicon entry, then ask the corpus.

This is the *simulate and check* pass. It builds the words the grammar allows
whether or not anyone ever wrote them, and then looks each one up in the
corpus. What comes out is the `derivations` index, and with it the two things
that cannot be read off corpus text alone: **which rule produced each attested
word**, and **how many words a rule produced that nobody ever used**.

Three things this module is careful about.

**One document per word, not per derivation.** The identity is the Latin form
plus the output word class, exactly as ``engine/dedupe.py`` groups within a
single entry — but here the grouping runs across the whole lexicon, so a form
two different entries reach keeps both derivations instead of one silently
overwriting the other.

**No path is dropped.** Each derivation records the base it started from, so a
merged record still says where every chain came from.

**The first run uses only fully-reviewed input.** Verbs, adjectives and
abstract nouns are 100% reviewed in the lexicon snapshot; concrete nouns,
compounds and loanwords are around 60%. Widening the pool is a later decision
and wants the numbers this run produces — see docs/LEXICON_ANALYSIS.md §6.
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from murfulu import generation
from murfulu.engine.affix import Step
from murfulu.engine.dedupe import GroupedForm
from murfulu.engine.meaning import Meaning
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import Rule, RulePack
from murfulu.scoring.attestation import Attestation, Index, Level
from murfulu.scoring.grounding import stored_grounded
from murfulu.scoring.records import (
    DEFAULT_DEPTH,
    Derivation,
    Path,
    Report,
    evidence_bucket,
)
from murfulu.scoring.semantics import Semantics
from murfulu.scoring.sisters import SisterForms, SuspectClaims, collect

#: The first run's input pool: the three lexicon categories that are **100%
#: reviewed**. Measured in docs/LEXICON_ANALYSIS.md §5.
REVIEWED_CATEGORIES = ("مصدر", "صفت", "اسم معنی")

#: What counts as written ground. Both levels of evidence do: the letters
#: having been written is enough to say a chain does not pass over nothing.
_WRITTEN = (Level.READING, Level.SPELLING)

__all__ = [
    "DEFAULT_DEPTH",
    "REVIEWED_CATEGORIES",
    "Derivation",
    "Path",
    "Precompute",
    "Report",
    "input_readings",
    "run",
]


@dataclass
class _Merged:
    """A form under construction, before it becomes a :class:`Derivation`."""

    form_latin: str
    form_fa: str
    output_type: str
    paths: list[Path]
    semantic_tags: list[str]
    meaning_fa: str | None
    stem_1: str | None
    stem_2: str | None
    attestation: Attestation | None = None
    base_attested: bool | None = None
    semantic_typicality: float | None = None
    semantic_bases: int | None = None
    #: The rule and base of the **first** step of the shortest chain, kept
    #: because a stored path records only the base of its last step and the
    #: semantic question is asked of the first. Two strings, not a path.
    first_step: tuple[str, str] | None = None
    first_step_depth: int = 0
    #: Other Persian spellings that arrived under the same reading.
    form_fa_variants: list[str] = field(default_factory=list)
    #: Filled by a second pass; see :meth:`Precompute.sisters`.
    sister_forms: tuple[str, ...] = ()
    #: Whole paths already recorded. Keyed on the path, **not on the rule
    #: chain**: 95,021 forms in the first run are reached by the same rule from
    #: two different lexicon entries, and keying on the chain alone threw the
    #: second entry away while the record still claimed one source.
    seen: set[Path] = field(default_factory=set)


def input_readings(
    lexicon: Lexicon, categories: Iterable[str] = REVIEWED_CATEGORIES
) -> Iterator[Reading]:
    """Every lexicon reading in the run's input pool, in snapshot order."""
    wanted = set(categories)
    for reading in lexicon.all_readings():
        if reading.lexicon_category in wanted:
            yield reading


def _base_type(
    pack: RulePack, path: tuple[Step, ...], entry_types: dict[str, str]
) -> str:
    """The word class the last rule was applied to.

    Recoverable without storing it, in two cases. A later step starts at what
    the previous rule declares it produces. A first step starts at one of the
    entry's own starting points — and a verb has **two**, so which one is
    settled by the form the rule was applied to, not by taking the first.
    *Raftār* is built on *raft* and *Raveš* on *row*, and calling both
    kārbon-e yek would be wrong for half the verb's family.
    """
    if not path:
        return ""
    if len(path) >= 2:
        previous = pack.by_id(path[-2].rule_id)
        return previous.output_types[0] if isinstance(previous, Rule) else ""
    named = entry_types.get(path[0].base_latin)
    if named:
        return named
    # Nothing else identifies it, so the rule's own input side has to answer,
    # and only when it names exactly one class. Two would be a guess.
    rule = pack.by_id(path[0].rule_id)
    if not isinstance(rule, Rule) or len(rule.input_types) != 1:
        return ""
    return rule.input_types[0]


def _paths_of(
    pack: RulePack, form: GroupedForm, reading: Reading, entry_types: dict[str, str]
) -> list[Path]:
    """Turn a grouped form's chains into stored paths."""
    built = []
    for chain in form.paths:
        built.append(
            Path(
                base_latin=chain[-1].base_latin if chain else form.base_latin,
                base_fa=form.base_fa,
                base_type=_base_type(pack, chain, entry_types),
                rule_ids=tuple(step.rule_id for step in chain),
                affixes=tuple(step.affix for step in chain if step.affix),
                glide_ids=tuple(step.glide_id for step in chain if step.glide_id),
                source_spelling_fa=reading.spelling_fa,
                source_latin=reading.latin,
            )
        )
    return built


class Precompute:
    """One precompute run: generate, merge, check attestation, hand out records.

    Merging happens in memory, because a form's derivations arrive from
    scattered lexicon entries and a streaming write keyed on the form would
    overwrite them. Measured on the reviewed pool: 1.7 million words, about
    1.5 GB, under half a minute.
    """

    def __init__(
        self,
        pack: RulePack,
        *,
        attestation: Index | None = None,
        semantics: Semantics | None = None,
        depth: int = DEFAULT_DEPTH,
        corpus_version: str = "",
        generated_at: str = "",
    ) -> None:
        self.pack = pack
        self.attestation = attestation
        # Passed in rather than read from the environment here: this module is
        # the batch job, and a job that silently picks up an artefact would
        # write a score into the index without anyone asking for one.
        self.semantics = semantics
        self.depth = depth
        self.corpus_version = corpus_version or (
            attestation.corpus_version if attestation else ""
        )
        self.generated_at = generated_at
        self.report = Report(depth=depth)
        self._merged: dict[tuple[str, str], _Merged] = {}
        self._snapshot_id = ""
        self._starting_bases: set[str] = set()
        self._typicality_cache: dict[
            tuple[str, str], tuple[float | None, int | None]
        ] = {}

    def add(self, reading: Reading) -> None:
        """Generate everything one lexicon reading produces and merge it in."""
        self._snapshot_id = self._snapshot_id or reading.snapshot_id
        result = generation.from_reading(self.pack, reading, depth=self.depth)
        self.report.entries += 1
        if result.truncated:
            self.report.entries_truncated += 1
        if result.forms:
            self.report.entries_with_forms += 1

        # A verb enters through two stems, so a form's starting class depends
        # on which one it was built from.
        entry_types = {base.latin: base.word_class for base in result.bases}
        self._starting_bases.update(entry_types)
        meanings = result.meanings
        for form in result.forms:
            self.report.forms_built += 1
            self._merge(form, reading, entry_types, meanings.get(form.latin))

    def _merge(
        self,
        form: GroupedForm,
        reading: Reading,
        entry_types: dict[str, str],
        meaning: Meaning | None,
    ) -> None:
        key = (form.latin, form.word_class)
        record = self._merged.get(key)
        if record is None:
            record = _Merged(
                form_latin=form.latin,
                form_fa=form.fa,
                output_type=form.word_class,
                paths=[],
                semantic_tags=list(form.semantic_tags),
                meaning_fa=meaning.text_fa if meaning else None,
                stem_1=reading.past_stem_latin,
                stem_2=reading.present_stem_latin,
            )
            self._merged[key] = record
        elif form.fa != record.form_fa and form.fa not in record.form_fa_variants:
            # Two Persian spellings that read the same way in Behnevis. The
            # second is kept, never overwritten — see OPEN_QUESTIONS item Q.
            record.form_fa_variants.append(form.fa)
            self.report.forms_with_two_spellings += 1

        for chain in form.paths:
            if chain and (
                record.first_step is None or len(chain) < record.first_step_depth
            ):
                record.first_step = (chain[0].rule_id, chain[0].base_latin)
                record.first_step_depth = len(chain)

        for path in _paths_of(self.pack, form, reading, entry_types):
            if path in record.seen:
                continue
            record.seen.add(path)
            record.paths.append(path)
            for rule_id in path.rule_ids:
                self.report.rule_uses[rule_id] += 1
        for tag in form.semantic_tags:
            if tag not in record.semantic_tags:
                record.semantic_tags.append(tag)

    def finish(self, seconds: float = 0.0) -> Report:
        """Sort the paths, ask the corpus, and fill in the report."""
        for record in self._merged.values():
            record.paths.sort(key=lambda p: p.depth)
            if len(record.paths) > 1:
                self.report.forms_with_two_paths += 1
            if self.attestation is not None:
                record.attestation = self.attestation.look_up(
                    record.form_fa, record.form_latin
                )
                self.report.by_attestation[evidence_bucket(record.attestation)] += 1
            self.report.by_depth[record.paths[0].depth] += 1
            record.semantic_typicality, record.semantic_bases = self._typicality(
                record.first_step
            )
            if record.semantic_typicality is not None:
                self.report.with_typicality += 1
        self._ground()
        self.report.forms_unique = len(self._merged)
        self.report.seconds = seconds
        return self.report

    def _typicality(
        self, first: tuple[str, str] | None
    ) -> tuple[float | None, int | None]:
        """How typical the first step's base is of its rule's bases.

        Memoised on ``(rule, base)``. The cosine is 1,024 multiplications in
        plain Python and there are 1.7 million records, but only a few tens of
        thousands of distinct pairs — the same stem enters the same rule again
        and again.
        """
        if first is None or self.semantics is None:
            return None, None
        cached = self._typicality_cache.get(first)
        if cached is None:
            found = self.semantics.typicality(*first)
            cached = (found.score, found.bases) if found else (None, None)
            self._typicality_cache[first] = cached
        return cached

    def _ground(self) -> None:
        """Say, for every record, whether some route to it stands on ground.

        A second pass over everything, and it has to be: written ground is
        *the whole run's* attested forms, so no record can be judged until the
        last one has been looked up. What counts is the same as in a live
        request — a form the corpus has, or one of the bases the generation
        started from, which is the dictionary's own and never counts against a
        word.
        """
        if self.attestation is None:
            return
        solid = set(self._starting_bases)
        for record in self._merged.values():
            evidence = record.attestation
            # A function word's letters are not this word's ground: the count
            # is another word's, so nothing is known about this one.
            if (
                evidence is not None
                and evidence.level in _WRITTEN
                and not evidence.function_word
            ):
                solid.add(record.form_latin)
        for record in self._merged.values():
            record.base_attested = stored_grounded(record.paths, solid.__contains__)
            if record.base_attested is None:
                self.report.grounding_unknown += 1
            elif record.base_attested:
                self.report.grounded += 1
            else:
                self.report.ungrounded += 1

    def sisters(
        self, limit: int = 0, suspect: SuspectClaims | None = None
    ) -> SisterForms:
        """Collect each rule's attested output, and optionally attach it.

        A second pass, because a word's sisters are other words of the same
        run: nothing can be attached until every one of them exists.

        The per-rule list is the artefact. Copying it onto each of 1.7 million
        words as well is the denormalisation docs/ARCHITECTURE.md asks for, and
        it costs real space — so ``limit`` is how many go on each word, and
        zero attaches none.

        ``suspect`` sinks the claims the homograph detector doubts, so the few
        that are copied onto each word are the ones least likely to be a
        homograph. None is removed.
        """
        found = collect(self.derivations(), self.corpus_version, suspect)
        if limit:
            for derivation in self.derivations():
                key = (derivation.form_latin, derivation.output_type)
                self._merged[key].sister_forms = found.for_derivation(derivation, limit)
        return found

    def derivations(self) -> Iterator[Derivation]:
        """Every merged word, ready to be written. Safe to iterate twice."""
        for record in self._merged.values():
            yield Derivation(
                form_latin=record.form_latin,
                form_fa=record.form_fa,
                output_type=record.output_type,
                paths=tuple(record.paths),
                form_fa_variants=tuple(record.form_fa_variants),
                semantic_tags=tuple(record.semantic_tags),
                sister_forms=record.sister_forms,
                meaning_fa=record.meaning_fa,
                attestation=record.attestation,
                base_attested=record.base_attested,
                semantic_typicality=record.semantic_typicality,
                semantic_bases=record.semantic_bases,
                stem_1=record.stem_1,
                stem_2=record.stem_2,
                corpus_version=self.corpus_version,
                rule_pack_version=self.pack.version,
                lexicon_snapshot_id=self._snapshot_id,
                generated_at=self.generated_at,
            )


def run(
    pack: RulePack,
    readings: Iterable[Reading],
    *,
    attestation: Index | None = None,
    semantics: Semantics | None = None,
    depth: int = DEFAULT_DEPTH,
    corpus_version: str = "",
    generated_at: str = "",
) -> Precompute:
    """Run the whole pass over one pool of readings and time it."""
    started = time.monotonic()
    job = Precompute(
        pack,
        attestation=attestation,
        semantics=semantics,
        depth=depth,
        corpus_version=corpus_version,
        generated_at=generated_at,
    )
    for reading in readings:
        job.add(reading)
    job.finish(time.monotonic() - started)
    return job
