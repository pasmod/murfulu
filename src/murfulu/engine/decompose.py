"""Propose what a word might have been built from. Never decide.

The *sāzāyi* check runs the engine backwards: given *Raftār*, which rules
could have produced it and from what? It is the one place in the system that
guesses, so everything about it is arranged to make the guesses **checkable**
and to stop any of them being mistaken for an answer.

Two rules this module holds to.

**It proposes, it does not verify.** Stripping *-ār* off *Raftār* leaves
*raft*, which may be a stem, a word, or nothing at all. Whether the proposal
survives is decided by looking the remainder up and **building it forward
again** — in :mod:`murfulu.analysis`, which has the lexicon. A decomposition
that was never rebuilt is a spelling coincidence with a rule id attached.

**It reverses only what the data says.** A stem written *row* behaves as *rav*
the moment anything follows it, so stripping an affix off *Raveš* leaves
*rav*, and the entry to find is *row*. The *y* of *guyande* is the same kind
of thing from the other table: it is not part of *gu* and not part of *-ande*,
it is what the grammar puts between two vowels, so it comes back out and the
base proposed is *gu*. Both reversals come from the pack's own tables —
``stem_forms`` and ``glides``, the same ones the forward direction uses — and
not from a list of Persian sound changes written here.
"""

from __future__ import annotations

from dataclasses import dataclass

from murfulu.engine import glides
from murfulu.rules.pack import Rule, RulePack


@dataclass(frozen=True)
class Proposal:
    """One way the word *might* have been built. Unverified.

    ``base`` is what would be left after removing the affix, already put back
    into the form a lexicon entry would be written in.
    """

    rule: Rule
    base: str
    #: Set when the base was rewritten by a stem-form rule — *rav* → *row*.
    #: Shown, so nothing about the proposal is silent.
    stem_form: str | None = None
    #: Set when a glide was taken back out — the *y* of *guyande*, so the base
    #: is *gu* and not *guy*. Shown for the same reason.
    glide_id: str | None = None


def _cases(form: str) -> list[str]:
    """The word with its first letter both ways.

    **Capitalisation belongs to the result, not to the base.** The engine
    computes it from the output word class — a kārnām is written with a
    capital, a participle without — so *Raftār* is built from *raft*, not from
    *Raft*, and stripping the affix leaves the capital behind on the wrong
    word. Both are proposed and the lexicon decides.
    """
    if not form:
        return []
    lowered = form[0].lower() + form[1:]
    raised = form[0].upper() + form[1:]
    return [form] if lowered == raised else [lowered, raised]


def _bases_for(pack: RulePack, stripped: str) -> list[tuple[str, str | None]]:
    """The written forms a stripped remainder could correspond to.

    The remainder as it stands, whatever the stem-form table says is written
    differently from how it behaves — *rav* is how *row* behaves, so a
    remainder of *rav* also proposes *row* — and each of those with either
    capitalisation.
    """
    shapes: list[tuple[str, str | None]] = [(stripped, None)]
    for form in pack.stem_forms:
        if stripped.endswith(form.working):
            rewritten = stripped[: -len(form.working)] + form.written
            shapes.append((rewritten, f"{form.written}->{form.working}"))

    found: list[tuple[str, str | None]] = []
    for shape, stem_form in shapes:
        for cased in _cases(shape):
            found.append((cased, stem_form))
    return found


def _strip_suffix(affix: str, form: str) -> str | None:
    tail = affix.lstrip("-")
    if not tail or len(form) <= len(tail):
        return None
    return form[: -len(tail)] if form.lower().endswith(tail.lower()) else None


def _strip_prefix(affix: str, form: str) -> str | None:
    head = affix.rstrip("-")
    if not head or len(form) <= len(head):
        return None
    return form[len(head) :] if form.lower().startswith(head.lower()) else None


def _suffix_remainders(
    pack: RulePack, affix: str, form: str
) -> list[tuple[str, str | None]]:
    """What removing this suffix could leave, with and without a glide undone.

    Both are offered because both happen. *Raftār* is the plain case: take
    *-ār* off and *raft* is there. *Guyande* is not — the *y* is not part of
    anything, it is what the grammar puts between two vowels, and removing
    *-ande* as a string leaves *guy*, which is not a word. The glide table
    says which vowels met, so it can say what was there before they did.
    """
    found: list[tuple[str, str | None]] = []
    plain = _strip_suffix(affix, form)
    if plain:
        found.append((plain, None))
    found.extend(glides.undo(pack, affix.lstrip("-"), form))
    return found


def propose(pack: RulePack, form: str) -> list[Proposal]:
    """Every affix rule whose shape fits this word, with what it would leave.

    Purely a string question. Several proposals for one word is the normal
    case and is the point: *-ār* is four different rules, and which of them
    applies is a question about meaning, not about letters.
    """
    proposals: list[Proposal] = []
    for rule in pack.rules:
        if not rule.active or not rule.affix:
            continue
        if rule.kind == "suffix":
            remainders = _suffix_remainders(pack, rule.affix, form)
        elif rule.kind == "prefix":
            # A prefix goes in front, and the forward engine joins it by
            # plain concatenation — so no glide fired there and none is
            # undone here. **Whether one should** is FOR_THE_LINGUIST L25:
            # *be-* + *Emšipāš* puts two vowels together, which the glide
            # chapter opens by saying Persian does not do. Unconfirmed either
            # way; the two directions stay identical until it is settled.
            head = _strip_prefix(rule.affix, form)
            remainders = [(head, None)] if head else []
        else:
            continue
        for stripped, glide_id in remainders:
            for base, stem_form in _bases_for(pack, stripped):
                proposals.append(
                    Proposal(
                        rule=rule, base=base, stem_form=stem_form, glide_id=glide_id
                    )
                )
    return proposals
