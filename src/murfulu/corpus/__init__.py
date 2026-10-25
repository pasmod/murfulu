"""Corpus source adapters and the ingest pipelines.

Owns: one adapter per corpus behind a shared interface, and the batch jobs that
turn raw sources into documents, word types and links to the lexicon. Adding a
new collection must not touch anything outside this package.

Nothing here may assume poetry: Ganjoor is the first source, not the only one.

Does not own: the index mappings the pipelines write into. Those live in
``murfulu.search``.
"""
