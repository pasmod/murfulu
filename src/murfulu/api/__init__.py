"""FastAPI routes.

Owns: the HTTP surface — request and response models, authentication, roles —
and nothing else. Routes call the other packages and return their results.

Deliberately thin: if a route contains a rule, a score or a query, that logic
belongs in ``murfulu.engine``, ``murfulu.scoring`` or ``murfulu.search``.
"""
