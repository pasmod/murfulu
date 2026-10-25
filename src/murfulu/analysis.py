"""Take a word apart, and rebuild it to prove the analysis.

This is the *sāzāyi* check. :mod:`murfulu.engine.decompose` proposes what a
word might have been built from; here each proposal is looked up in the
lexicon and then **built forward again**. Only a proposal that reproduces the
word exactly survives.

That round trip is the whole design. Stripping *-nā* off *Mowlānā* leaves
*mowlā*, which is a real lexicon entry, and a decomposer that stopped there
would announce that a famous Arabic name is a Persian derivation. Building it
forward is what refuses.

**Nothing here chooses between survivors.** *Raftār* is *raft* + *-ār* under
four different rules, and *Raveš* can be built from two different verbs. Which
one is meant is a question about meaning, and the answer is the linguist's.
The analysis returns all of them, ordered by how much of the word each one
accounts for, and says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from murfulu.engine.decompose import propose
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import RulePack

#: How many affixes deep to look. *Ravandegi* is two — *ravande* then *-i* —
#: and the space grows with every step, so this is the same bounded recursion
#: the forward direction uses.
DEFAULT_DEPTH = 2


@dataclass(frozen=True)
class Step:
    """One affix removed, and the rule that would have added it."""

    rule_id: str
    affix: str
    affix_fa: str | None
    label_fa: str | None
    explanation_fa: str | None
    #: The form this step was applied to, on the way forward.
    applied_to: str
    stem_form: str | None = None
    #: Which glide rule joined the two vowels here — the *y* of *guyande*.
    #: Carried for the same reason as ``stem_form``: an account that shows
    #: *gu + -ande* and not where the *y* came from is asking the reader to
    #: take a letter on trust.
    glide_id: str | None = None


@dataclass(frozen=True)
class Analysis:
    """One complete account of a word, verified by rebuilding it."""

    form: str
    #: The lexicon entry the whole chain starts from.
    base: Reading
    #: The rules that would build the word from that entry, in order.
    steps: tuple[Step, ...] = ()

    @property
    def depth(self) -> int:
        """How many affixes the account uses."""
        return len(self.steps)


@dataclass
class Result:
    """Everything that survived, and everything that did not."""

    form: str
    analyses: list[Analysis] = field(default_factory=list)
    #: Proposals whose remainder is in no dictionary. Kept because "we cannot
    #: take this word apart" is a useful answer, and because the list says
    #: which affixes were tried rather than leaving the reader to wonder.
    unmatched_affixes: list[str] = field(default_factory=list)
    #: Forms the engine did build that differ from the asked-for word **only
    #: in case**. Case is meaning in Behnevis, so *budmān* and *Budmān* are
    #: not the same word and one must never be answered with the other — but
    #: an empty answer that is really a casing mistake looks exactly like
    #: *this word cannot be built*. Reported so the caller can tell them
    #: apart, and never merged into the accounts.
    built_in_another_case: list[str] = field(default_factory=list)
    #: Bases whose forward build stopped at the engine's form cap rather than
    #: because no rule applied. **This is what turns "no" into "not
    #: established".**
    #:
    #: Found 2026-08-17 while asking why درافکندگی does not rebuild — the case
    #: the coining experiment reported as the engine's largest gap. It is not a
    #: missing rule: building forward from افکندن reaches 20,050 forms at three
    #: steps, the cap is 20,000, and the run stops before *Darafkandegi*. Every
    #: rule the chain needs exists and fires; the search simply never arrives.
    #:
    #: The engine has always reported this on the forward side
    #: (``Generation.truncated``) and the analysis threw it away, so a
    #: truncated search and an exhausted one gave a reader the identical
    #: answer. A confident *this word cannot be built* over an unfinished
    #: search is the same fault as a bare 500 behind a healthy ``/health``.
    searched_partially: list[str] = field(default_factory=list)

    @property
    def explained(self) -> bool:
        """True when at least one account rebuilt the word."""
        return bool(self.analyses)

    @property
    def settled(self) -> bool:
        """Whether *no account* really means there is none.

        True when every base was searched to exhaustion. False means the
        question is open, not answered — the caller must not print *this word
        cannot be built*.
        """
        return bool(self.analyses) or not self.searched_partially


def _steps_for(
    pack: RulePack,
    reading: Reading,
    target: str,
    depth: int,
    other_casings: set[str] | None = None,
    truncated: list[str] | None = None,
) -> list[tuple[Step, ...]]:
    """Turn every verified chain into the steps a reader can follow.

    Anything that matches the target but for its case is recorded in
    ``other_casings`` rather than accepted: the two are different words.

    A base whose forward build **hit the form cap** is recorded in
    ``truncated``. The engine stops at 20,000 forms per call, and افکندن
    reaches that at three steps — so *Darafkandegi* was reported as impossible
    when the truth is that the search never got to it. See :class:`Result`.
    """
    from murfulu import generation

    built = generation.from_reading(pack, reading, depth=depth)
    if built.truncated and truncated is not None:
        truncated.append(reading.latin)
    accounts: list[tuple[Step, ...]] = []
    for form in built.forms:
        if form.latin != target:
            if other_casings is not None and form.latin.lower() == target.lower():
                other_casings.add(form.latin)
            continue
        for path in form.paths:
            steps = []
            for step in path:
                rule = pack.by_id(step.rule_id)
                steps.append(
                    Step(
                        rule_id=step.rule_id,
                        affix=step.affix or "",
                        affix_fa=getattr(rule, "affix_fa", None),
                        label_fa=getattr(rule, "label_fa", None),
                        explanation_fa=rule.explanation_fa,
                        applied_to=step.base_latin,
                        # The step's own, never the proposal's. The proposal
                        # knows one rewriting, of the base; copying it onto
                        # every step claimed *ow → av* on joins that have no
                        # stem change in them at all.
                        stem_form=step.stem_form,
                        glide_id=step.glide_id,
                    )
                )
            accounts.append(tuple(steps))
    return accounts


def _candidates(pack: RulePack, form: str, depth: int) -> set[str]:
    """Every remainder reachable by stripping up to ``depth`` affixes.

    One level is not enough and the reason is *Ravandegi*: stripping *-gi*
    leaves *ravande*, which is not in any dictionary because it is itself
    built — *row* + *-ande*. A decomposer that stopped at the first remainder
    it could not find would report that the word cannot be taken apart, which
    is the opposite of true.

    Only the remainders are collected here. Which of them is really the base,
    and by which rules, is settled by building forward.
    """
    found: set[str] = set()
    frontier = {form}
    for _ in range(max(1, depth)):
        further: set[str] = set()
        for word in frontier:
            for proposal in propose(pack, word):
                found.add(proposal.base)
                further.add(proposal.base)
        frontier = further
    return found


def explain(
    lexicon: Lexicon, pack: RulePack, form: str, depth: int = DEFAULT_DEPTH
) -> Result:
    """Take one word apart, keeping only what rebuilds it.

    A word that **is** a lexicon entry is still analysed: *Raftār* may be in
    the dictionary and still be built from *raft*, and a reader asking how it
    is made deserves the answer either way.
    """
    result = Result(form=form)
    seen: set[tuple[str, tuple[str, ...]]] = set()
    other_casings: set[str] = set()
    partial: list[str] = []

    for base in _candidates(pack, form, depth):
        readings = lexicon.by_latin(base) + lexicon.by_stem(base)
        if not readings:
            continue
        for reading in readings:
            for steps in _steps_for(pack, reading, form, depth, other_casings, partial):
                key = (reading.latin, tuple(step.rule_id for step in steps))
                if key in seen:
                    continue
                seen.add(key)
                result.analyses.append(Analysis(form=form, base=reading, steps=steps))

    # Fewest steps first: an account that explains the word in one move is a
    # better account than one that needs two, all else being equal.
    result.analyses.sort(key=lambda one: (one.depth, one.base.latin))
    # Only worth saying when nothing rebuilt the word as it was written.
    if not result.analyses:
        result.built_in_another_case = sorted(other_casings)
        # Likewise: a search that found the word ran far enough by definition,
        # so the caveat belongs only on an empty answer.
        result.searched_partially = sorted(set(partial))
    accounted = {step.rule_id for one in result.analyses for step in one.steps}
    result.unmatched_affixes = sorted(
        {
            p.rule.affix
            for p in propose(pack, form)
            if p.rule.affix and p.rule.id not in accounted
        }
    )
    return result
