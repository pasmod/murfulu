"""murfulu: Persian word generation from stems and word-formation rules.

The package is split by responsibility, one sub-package per concern. See
``docs/ENGINEERING.md`` for the module contract and ``docs/ARCHITECTURE.md``
for how the pieces fit together.

Sub-packages
------------
``rules``    load and validate the rule pack
``engine``   apply rules to stems
``scoring``  productivity, attestation, semantics, composite score
``lexicon``  read-only wrapper over the karbon lexicon
``search``   Elasticsearch queries and index mappings
``corpus``   source adapters and ingest pipelines
``api``      FastAPI routes
"""

__version__ = "0.0.0"
