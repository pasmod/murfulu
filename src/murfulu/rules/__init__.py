"""Load and validate the rule pack.

Owns: reading the YAML rule files (``verb_stems``, ``nominals``,
``verbalisers``, ``glides``, ``semantic_tags``), validating each rule against
its schema, and exposing the pack as typed objects. Rule ids follow the
permanent ``FAMILY-NNN`` scheme in ``docs/RULE_PACK.md``.

Does not own: applying rules to a word. That is ``murfulu.engine``. No I/O
beyond reading the packaged YAML files.
"""
