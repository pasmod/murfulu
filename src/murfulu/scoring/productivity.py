"""How productive each rule actually is, measured rather than asserted.

Two numbers, and they answer different questions.

**Baayen's P** — hapaxes divided by tokens, over the words this rule produced
that the corpus actually has. A rule whose attested output is mostly words used
once is still coining; one whose output is a handful of very frequent words has
stopped. It says nothing about the words the rule could form and nobody wrote,
because those have no tokens at all.

**The realisation rate** — attested outputs divided by outputs built. This is
Monakhov's simulate-and-check measure, and it is the one our pipeline is shaped
for: the precompute already built every form the rule allows, so the share of
them anyone ever wrote is directly countable. It weights a neologism and a
common word equally, which P does not.

Both are **tied to a corpus version** and neither is meaningful without it.
Every record carries the version, the lexicon snapshot and the rule-pack
version that produced it.

A rule that built nothing has no productivity — not a productivity of zero.
The difference matters: 29 rules cannot be measured by this pass at all, each
for a stated reason, and reporting them as unproductive would be a finding
where there is only an absence.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from murfulu.rules.pack import Rule, RulePack
from murfulu.scoring.attestation import Level
from murfulu.scoring.records import Derivation

#: Rule kinds this pass cannot exercise, and why. A stem rule is a different
#: operation and always will be. **Compounding is two different situations
#: wearing one word**, and saying so takes both lines:
#:
#: A **template** is built. :func:`murfulu.engine.compound.fill` produces
#: *Budonabud*, *Goftogu* and *Kešākeš* exactly as the source has them. What
#: is missing is that **nothing calls it** — not this pass, not ``/generate``
#: — so no compound has ever reached a reader.
#:
#: A **slot** is not built at all: ``fill`` refuses anything that is not a
#: template, and the six slot rules pair a word with a class rather than with
#: another pattern. That half is PLAN task 2.3.
#:
#: **This text has now been wrong in three directions**, which is why it is
#: this long. It first said compounding was "generated on demand", the
#: intention stated as fact; a language model given the API believed it and
#: coined words on rules that produce nothing. It then said compounding was
#: "not built yet", which libelled a module that works. It then said "nothing
#: calls it yet" — true until `/compound` was written on 2026-08-14 and false
#: from that morning on.
#:
#: What is true now: compounding **is** built and **is** served, and *this*
#: pass still cannot measure it, because this pass counts what the precompute
#: produced and the precompute does affixation. A slot rule's output is a
#: product — 20,879 nouns against 1,696 verbs — and holding it to count it is
#: not something the precompute should start doing.
#: `tools/measure_compounding.py` measures them separately and writes its rows
#: into the same file, so a reader never sees this text for a rule it reached.
UNMEASURABLE_KINDS = {
    "stem": "a stem rule: infinitive to stem, not affixation",
    "template": "compounding: measured by tools/measure_compounding.py, not here",
    "slot": "compounding: measured by tools/measure_compounding.py, not here",
    # An infix sits *between two words* — delnāčasb is دل + نا + چسب — so it
    # needs a second word exactly as a slot does. It used to fall through to
    # the suffix branch and build časbnā instead, 27,361 types of it.
    "infix": "compounding by infix: not built (PLAN 2.3)",
}

NO_ELIGIBLE_BASE = "no entry in the input pool has a word class this rule takes"

#: Which measured band each authored strength is expected to land in. The bands
#: are **terciles of the measured distribution**, so they move with the data
#: rather than being fixed thresholds — but naming which tercile a `typical`
#: rule belongs in is still a judgement, and it is the linguist's.
#: See docs/OPEN_QUESTIONS item R.
EXPECTED_BAND = {"obligatory": "high", "typical": "middle", "occasional": "low"}

BANDS = ("low", "middle", "high")


@dataclass(frozen=True)
class Productivity:
    """What one rule produced, and how much of it the corpus has."""

    rule_id: str
    authored_strength: str | None = None
    types_built: int = 0
    #: Outputs the corpus has at either level of evidence.
    types_attested: int = 0
    #: Outputs the corpus has **and** the lexicon confirms the reading of. The
    #: stricter count, and the only one free of homograph doubt.
    types_confirmed: int = 0
    #: Corpus occurrences of the attested outputs, and how many of those
    #: outputs occur exactly once. Both at the looser level of evidence.
    tokens: int = 0
    hapaxes: int = 0
    #: The same two counts over confirmed readings only.
    tokens_confirmed: int = 0
    hapaxes_confirmed: int = 0
    #: Outputs that are the same string as what they were built from, or as
    #: the lexicon entry the chain started at. A rule that returns its own
    #: input is attested by construction — the word was already in the
    #: dictionary — and counting that as productivity flatters it.
    types_echoing_source: int = 0
    #: Empty when the rule was measured. Set when it could not be.
    unmeasurable_reason: str = ""
    corpus_version: str = ""
    rule_pack_version: str = ""
    lexicon_snapshot_id: str = ""

    @property
    def measured(self) -> bool:
        """True when this pass could say anything about the rule at all."""
        return not self.unmeasurable_reason

    @property
    def potential_p(self) -> float | None:
        """Baayen's P: hapaxes over tokens. None when there are no tokens."""
        return self.hapaxes / self.tokens if self.tokens else None

    @property
    def potential_p_confirmed(self) -> float | None:
        """Baayen's P over confirmed readings only. The defensible one."""
        if not self.tokens_confirmed:
            return None
        return self.hapaxes_confirmed / self.tokens_confirmed

    @property
    def realisation_rate(self) -> float | None:
        """Attested outputs over outputs built. None when nothing was built."""
        return self.types_attested / self.types_built if self.types_built else None

    @property
    def echo_share(self) -> float | None:
        """Share of the output that is the same string as its own input.

        Read the realisation rate next to this. A rule at 0.77 whose echo
        share is 1.0 has not coined anything: it renamed words the dictionary
        already had.
        """
        if not self.types_built:
            return None
        return self.types_echoing_source / self.types_built

    def as_document(self) -> dict[str, Any]:
        """The stored shape, one object per rule per corpus version."""
        return {
            "rule_id": self.rule_id,
            "authored_strength": self.authored_strength,
            "types_built": self.types_built,
            "types_attested": self.types_attested,
            "types_confirmed": self.types_confirmed,
            "tokens": self.tokens,
            "hapaxes": self.hapaxes,
            "tokens_confirmed": self.tokens_confirmed,
            "hapaxes_confirmed": self.hapaxes_confirmed,
            "types_echoing_source": self.types_echoing_source,
            "echo_share": self.echo_share,
            "potential_p": self.potential_p,
            "potential_p_confirmed": self.potential_p_confirmed,
            "realisation_rate": self.realisation_rate,
            "measured": self.measured,
            "unmeasurable_reason": self.unmeasurable_reason,
            "corpus_version": self.corpus_version,
            "rule_pack_version": self.rule_pack_version,
            "lexicon_snapshot_id": self.lexicon_snapshot_id,
        }


@dataclass(frozen=True)
class Disagreement:
    """A rule whose measured productivity is not where its strength says."""

    rule_id: str
    authored_strength: str
    expected_band: str
    measured_band: str
    realisation_rate: float


@dataclass
class RuleStatistics:
    """Every rule's productivity for one corpus version."""

    by_rule: dict[str, Productivity] = field(default_factory=dict)
    corpus_version: str = ""

    def __len__(self) -> int:
        """How many rules were looked at. Every rule in the pack is."""
        return len(self.by_rule)

    @property
    def measured(self) -> list[Productivity]:
        """Rules this pass could put a number on."""
        return [p for p in self.by_rule.values() if p.measured]

    @property
    def unmeasured(self) -> list[Productivity]:
        """Rules it could not, each carrying the reason."""
        return [p for p in self.by_rule.values() if not p.measured]

    def bands(self) -> dict[str, str]:
        """Which tercile of the measured distribution each rule falls in.

        Terciles rather than fixed cut-offs: a threshold picked by hand would
        decide the answer, and the point is to let the data decide.
        """
        rates = sorted(
            p.realisation_rate
            for p in self.by_rule.values()
            if p.realisation_rate is not None
        )
        if not rates:
            return {}
        low = rates[len(rates) // 3]
        high = rates[2 * len(rates) // 3]
        placed = {}
        for productivity in self.by_rule.values():
            rate = productivity.realisation_rate
            if rate is None:
                continue
            placed[productivity.rule_id] = (
                "low" if rate < low else "high" if rate >= high else "middle"
            )
        return placed

    def disagreements(self) -> list[Disagreement]:
        """Rules whose authored strength and measured band do not match.

        Only rules that carry an authored strength can disagree with one, and
        the source grammar states a strength for very few of them — which is
        itself the finding, not a shortcoming of this method.
        """
        placed = self.bands()
        found = []
        for productivity in self.by_rule.values():
            strength = productivity.authored_strength
            rate = productivity.realisation_rate
            if not strength or rate is None:
                continue
            expected = EXPECTED_BAND.get(strength)
            measured = placed.get(productivity.rule_id)
            if expected and measured and expected != measured:
                found.append(
                    Disagreement(
                        rule_id=productivity.rule_id,
                        authored_strength=strength,
                        expected_band=expected,
                        measured_band=measured,
                        realisation_rate=rate,
                    )
                )
        return sorted(found, key=lambda d: d.rule_id)

    def most_productive(self, limit: int = 20) -> list[Productivity]:
        """The rules whose output the corpus most often has."""
        rated = [p for p in self.measured if p.realisation_rate is not None]
        return sorted(rated, key=lambda p: -(p.realisation_rate or 0.0))[:limit]

    def summary(self) -> str:
        """The lines the batch job prints."""
        rated = [p for p in self.measured if p.potential_p is not None]
        return "\n".join(
            [
                f"rules          {len(self)} in the pack",
                f"measured       {len(self.measured)} built at least one form",
                f"with a P       {len(rated)} have an attested output to count",
                f"unmeasured     {len(self.unmeasured)}",
                f"disagreements  {len(self.disagreements())} "
                f"against an authored strength",
                f"corpus         {self.corpus_version or 'unstated'}",
            ]
        )


def _reason(rule: Rule) -> str:
    """Why a rule that built nothing built nothing."""
    return UNMEASURABLE_KINDS.get(rule.kind, NO_ELIGIBLE_BASE)


def _last_rules(derivation: Derivation) -> dict[str, bool]:
    """The rules that formed this word, and whether each merely echoed it.

    The **last** step of a path is what made the word; the earlier steps made
    its base, and that base is a word in its own right elsewhere in the index.
    Counting mid-chain rules here would credit a rule twice.

    A path *echoes* when the form is the same string as what it was built from
    or as the lexicon entry the chain started at. That happens two ways: a
    zero-affix rule turning a stem into a noun, and *-an* rebuilding the very
    infinitive the generation started from. Both are attested by construction.
    """
    found: dict[str, bool] = {}
    form = derivation.form_latin.lower()
    for path in derivation.paths:
        if not path.rule_ids:
            continue
        echo = form in {path.base_latin.lower(), path.source_latin.lower()}
        rule_id = path.rule_ids[-1]
        found[rule_id] = found.get(rule_id, True) and echo
    return found


def measure(
    pack: RulePack,
    derivations: Iterable[Derivation],
    corpus_version: str = "",
    lexicon_snapshot_id: str = "",
) -> RuleStatistics:
    """Roll a finished precompute up into per-rule productivity."""
    built: Counter[str] = Counter()
    attested: Counter[str] = Counter()
    confirmed: Counter[str] = Counter()
    tokens: Counter[str] = Counter()
    hapaxes: Counter[str] = Counter()
    tokens_confirmed: Counter[str] = Counter()
    hapaxes_confirmed: Counter[str] = Counter()
    echoes: Counter[str] = Counter()
    snapshot = lexicon_snapshot_id

    for derivation in derivations:
        snapshot = snapshot or derivation.lexicon_snapshot_id
        corpus_version = corpus_version or derivation.corpus_version
        evidence = derivation.attestation
        count = evidence.total_count if evidence else 0
        for rule_id, echoed in _last_rules(derivation).items():
            built[rule_id] += 1
            if echoed:
                echoes[rule_id] += 1
            # A function word's letters are written, but not as this word, and
            # nothing about it is known — not an attested output of the rule.
            if (
                evidence is None
                or evidence.level is Level.NONE
                or evidence.function_word
            ):
                continue
            attested[rule_id] += 1
            tokens[rule_id] += count
            if count == 1:
                hapaxes[rule_id] += 1
            if evidence.level is Level.READING:
                confirmed[rule_id] += 1
                tokens_confirmed[rule_id] += count
                if count == 1:
                    hapaxes_confirmed[rule_id] += 1

    statistics = RuleStatistics(corpus_version=corpus_version)
    for rule in pack.rules:
        made = built[rule.id]
        # A rule that built forms but has none attested **was** measured: its
        # realisation rate is zero, which is a result. Only a rule that never
        # fired has nothing to say.
        reason = "" if made else _reason(rule)
        statistics.by_rule[rule.id] = Productivity(
            rule_id=rule.id,
            authored_strength=rule.strength,
            types_built=made,
            types_attested=attested[rule.id],
            types_confirmed=confirmed[rule.id],
            tokens=tokens[rule.id],
            hapaxes=hapaxes[rule.id],
            tokens_confirmed=tokens_confirmed[rule.id],
            hapaxes_confirmed=hapaxes_confirmed[rule.id],
            types_echoing_source=echoes[rule.id],
            unmeasurable_reason=reason,
            corpus_version=corpus_version,
            rule_pack_version=pack.version,
            lexicon_snapshot_id=snapshot,
        )
    return statistics
