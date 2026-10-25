"""Score a derived form: productivity, attestation, semantics, composite.

Owns: measured rule productivity (Baayen P) per corpus version, attestation
levels (reading / spelling / none), semantic plausibility, and the weighted
combination of those parts. Weights come from configuration, not from code, and
every score is stored with its parts kept separate so a number can be explained.

Does not own: fetching the corpus counts. It is handed them by
``murfulu.search``.
"""
