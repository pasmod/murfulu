"""Elasticsearch index mappings and queries.

Owns: the ``documents``, ``word_types`` and ``derivations`` mappings, versioned
index names behind aliases, the query language described in ``docs/SEARCH.md``,
and batched attestation lookups.

Does not own: deciding what a result means. Scores are computed in
``murfulu.scoring``.
"""
