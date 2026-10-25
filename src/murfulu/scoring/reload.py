"""Read precompute records back from what was written.

The precompute holds 1.7 million words in memory while it merges them, and
then hands them over. Everything downstream — rule productivity, sister forms,
the composite score — reads them again, and must not have to re-run the whole
pass to do it.

So a record round-trips: :meth:`Derivation.as_document` writes it,
:func:`from_document` reads it back. The two are pinned together by a test, or
they drift and every later pass silently measures something else.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path as FilePath
from typing import Any

from murfulu.scoring.attestation import Attestation, Level
from murfulu.scoring.records import Derivation, Path


def _path(raw: dict[str, Any]) -> Path:
    return Path(
        base_latin=raw.get("base_form", ""),
        base_fa=raw.get("base_fa", ""),
        base_type=raw.get("base_type", ""),
        rule_ids=tuple(raw.get("rule_ids") or ()),
        affixes=tuple(raw.get("affixes") or ()),
        glide_ids=tuple(raw.get("glide_ids") or ()),
        source_spelling_fa=raw.get("source_spelling_fa", ""),
        source_latin=raw.get("source_latin", ""),
    )


def _attestation(raw: dict[str, Any]) -> Attestation | None:
    """The corpus evidence, or None when the run was made without a corpus.

    A missing field means **unchecked**, never *not attested*: the two look the
    same in a JSON object and mean opposite things to a reader.
    """
    level = raw.get("attestation")
    if level is None:
        return None
    return Attestation(
        level=Level(level),
        corpus_version=raw.get("corpus_version", ""),
        total_count=raw.get("attested_count", 0),
        doc_count=raw.get("attested_docs", 0),
        author_count=raw.get("attested_authors", 0),
        first_century=raw.get("attested_first_century"),
        last_century=raw.get("attested_last_century"),
        other_readings=tuple(raw.get("attested_other_readings") or ()),
        spelling_unlinked=bool(raw.get("attestation_unlinked", False)),
        function_word=raw.get("attestation_function_word") or "",
    )


def from_document(raw: dict[str, Any]) -> Derivation:
    """Rebuild one derivation from the object that was stored."""
    return Derivation(
        form_latin=raw["form_latin"],
        form_fa=raw["form_fa"],
        output_type=raw["output_type"],
        paths=tuple(_path(item) for item in raw.get("paths") or ()),
        form_fa_variants=tuple(raw.get("form_fa_variants") or ()),
        semantic_tags=tuple(raw.get("semantic_tags") or ()),
        sister_forms=tuple(raw.get("sister_forms") or ()),
        meaning_fa=raw.get("meaning_fa"),
        attestation=_attestation(raw),
        base_attested=raw.get("base_attested"),
        semantic_typicality=raw.get("semantic_typicality"),
        semantic_bases=raw.get("semantic_bases"),
        stem_1=raw.get("stem_1"),
        stem_2=raw.get("stem_2"),
        corpus_version=raw.get("corpus_version", ""),
        rule_pack_version=raw.get("rule_pack_version", ""),
        lexicon_snapshot_id=raw.get("lexicon_snapshot_id", ""),
        generated_at=raw.get("generated_at", ""),
    )


def read_jsonl(path: FilePath) -> Iterator[Derivation]:
    """Stream a precompute file back, one record at a time.

    Streamed, not loaded: the file is 1.6 GB and nothing downstream needs more
    than one record at once.
    """
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield from_document(json.loads(line))
