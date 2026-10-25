"""Apply rules to stems: affixation, glides, compounding, recursion.

Owns: turning a base form plus a rule pack into derived forms, in Latin and
Persian together, each carrying the rule chain that produced it. Deduplication
of forms reachable by several chains lives here too.

Does not own: any infrastructure. This package must not import Elasticsearch,
Postgres or karbon — it takes data in and returns data out, which is what makes
it testable without a running system.

Glossary
--------
kārbon-e yek / do  the past and present verb stems
kārnām             deverbal noun (a "doing" word)
nām / barnām       noun / adjective
"""

from murfulu.engine.affix import (
    CannotApplyError,
    DerivedForm,
    Step,
    Word,
    apply,
    apply_all,
    can_apply,
    cased,
    working_form,
)
from murfulu.engine.compound import Filler, Verb, fill
from murfulu.engine.dedupe import GroupedForm, deduplicate
from murfulu.engine.generate import MAX_DEPTH, Generation, generate
from murfulu.engine.glides import Join, ambiguous_pairs, join, unapply, undo
from murfulu.engine.meaning import Meaning, compose

__all__ = [
    "CannotApplyError",
    "DerivedForm",
    "Join",
    "Step",
    "Word",
    "ambiguous_pairs",
    "apply",
    "apply_all",
    "MAX_DEPTH",
    "Filler",
    "Generation",
    "GroupedForm",
    "Meaning",
    "Verb",
    "can_apply",
    "compose",
    "deduplicate",
    "cased",
    "fill",
    "generate",
    "join",
    "unapply",
    "undo",
    "working_form",
]
