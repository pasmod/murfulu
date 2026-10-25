"""The Elasticsearch mappings, exactly as ``docs/ARCHITECTURE.md`` sets them out.

Three indices:

``documents``    one poem, page or chapter — never a line
``word_types``   one document per **reading**, not per spelling
``derivations``  one document per generated form

Field types are chosen for the searches the app actually does. Two are worth
naming: ``latin_reversed`` turns a suffix search (*-nā*) into a prefix query,
which is cheap; ``latin_wild`` is a ``wildcard`` field, which is the one type
built for leading wildcards.

Every mapping sets ``dynamic: strict``. A typo in a field name must fail the
write, not quietly create a new field that nothing ever queries.

Persian text is analysed by :data:`ANALYZER`, not by Lucene's stock ``persian``
analyzer. The reason is in that constant's own comment and it is the whole of
corpus version ``v2``.
"""

from __future__ import annotations

from typing import Any

#: The Persian analyser this project uses, and the two things it leaves out.
#:
#: **No stopword filter.** Lucene's stock ``persian`` analyzer removes a
#: stopword list holding رفت، گفت، شد، بود — the commonest verb forms in
#: classical poetry, and precisely the words a project about word formation is
#: made of. Measured on the live cluster: a phrase query for رفت returned zero
#: hits from a corpus that writes it hundreds of thousands of times, so
#: ``/word`` showed a count with no line under it to check the count against.
#: A stopword list is for relevance ranking in a search engine. Here every
#: word is evidence.
#:
#: **No zero-width-non-joiner character filter.** The stock analyzer maps the
#: ZWNJ to a space, which turns می‌رود into two tokens and گفت‌وگو into three.
#: ``corpus/wordtypes.py`` counts each of those as **one** word, so an
#: analyser that split them could not find the line a count came from. Without
#: the filter the tokeniser keeps the ZWNJ inside the token, which is what the
#: counting does.
#:
#: What is kept is the rest of the stock chain: lower-casing, Arabic-Indic
#: digits folded to ASCII, and the Arabic and Persian normalisations, which
#: fold ي ك ة and strip harakat — the same folding ``wordtypes.normalise``
#: does, in the opposite direction. Direction does not matter, because the
#: query and the text go through the same analyser.
ANALYZER = "persian_every_word"

#: Index settings carrying the analyser. Every index gets them, so a field can
#: be moved to Persian text later without a settings migration.
ANALYSIS: dict[str, Any] = {
    "analyzer": {
        ANALYZER: {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
                "lowercase",
                "decimal_digit",
                "arabic_normalization",
                "persian_normalization",
            ],
        }
    }
}

_KEYWORD = {"type": "keyword"}
_INTEGER = {"type": "integer"}
_TEXT_FA = {"type": "text", "analyzer": ANALYZER}

DOCUMENTS: dict[str, Any] = {
    "dynamic": "strict",
    "properties": {
        "source_id": _KEYWORD,
        "document_id": _KEYWORD,
        "author": _KEYWORD,
        "title": {"type": "text", "analyzer": ANALYZER, "fields": {"raw": _KEYWORD}},
        "century": _INTEGER,
        "text_fa": _TEXT_FA,
        "licence": _KEYWORD,
        "corpus_version": _KEYWORD,
        "extra": {"type": "object", "enabled": False},
    },
}

WORD_TYPES: dict[str, Any] = {
    "dynamic": "strict",
    "properties": {
        # identity
        "id": _KEYWORD,
        "spelling_fa": _KEYWORD,
        "latin": _KEYWORD,
        # Every other pronunciation the lexicon lists for this reading. برنا
        # is barnā and the same row also says bornā; 16.0% of readings carry
        # one, and until v6 there was no field for them, so the search screen
        # and the word page showed the first as if it were the only one.
        "latin_variants": _KEYWORD,
        "latin_reversed": _KEYWORD,
        "latin_wild": {"type": "wildcard"},
        "reading_id": _KEYWORD,
        "source_entry_ids": _KEYWORD,
        "sense_count": _INTEGER,
        # grammar — three different notions, deliberately not merged
        # The dictionary's own definition, as karbon holds it. Analysed like
        # any Persian text, so a reader can search inside meanings. It is a
        # **preview**: karbon cuts it at 200 characters, 27.6% of them
        # mid-word, and no مصدر has one at all.
        "definition_fa": _TEXT_FA,
        "lexicon_category": _KEYWORD,
        "word_class": _KEYWORD,
        "pos_observed": {"type": "object", "dynamic": True},
        # stems and structure
        "stem_1_fa": _KEYWORD,
        "stem_1_latin": _KEYWORD,
        "stem_2_fa": _KEYWORD,
        "stem_2_latin": _KEYWORD,
        "karbon_stem_rule": _INTEGER,
        "is_exception": {"type": "boolean"},
        "transitivity": _KEYWORD,
        "affixes": _KEYWORD,
        "semantic_tags": _KEYWORD,
        "rule_ids": _KEYWORD,
        # evidence, all per corpus version
        "total_count": _INTEGER,
        "doc_count": _INTEGER,
        "author_count": _INTEGER,
        "first_century": _INTEGER,
        "last_century": _INTEGER,
        "counts_by_century": {"type": "object", "dynamic": True},
        # The class of the function word these letters almost always are
        # (rules/function_words.yaml). On a reading's document the counts are
        # then empty — unknown, not zero — and the spelling's own document
        # (latin null) carries them.
        "function_word": _KEYWORD,
        "authors": _KEYWORD,
        "sources": _KEYWORD,
        # quality and meta
        "phonemic_confidence": {"type": "float"},
        "needs_review": {"type": "boolean"},
        "population": _KEYWORD,
        "corpus_version": _KEYWORD,
        "lexicon_snapshot_id": _KEYWORD,
    },
}

DERIVATIONS: dict[str, Any] = {
    "dynamic": "strict",
    "properties": {
        "id": _KEYWORD,
        "form_latin": _KEYWORD,
        "form_fa": _KEYWORD,
        # Two Persian spellings can share one Behnevis reading, and the id is
        # the reading. The second spelling is kept beside the first rather
        # than overwriting it — see docs/OPEN_QUESTIONS item Q.
        "form_fa_variants": _KEYWORD,
        "output_type": _KEYWORD,
        "base_form": _KEYWORD,
        "base_type": _KEYWORD,
        "stem_1": _KEYWORD,
        "stem_2": _KEYWORD,
        # every chain producing this form, shortest first
        "paths": {"type": "object", "enabled": False},
        # Every rule that builds this word, by any route. **Not a chain** — it
        # was called `rule_chain` until 2026-08-17 and its contents stopped
        # being a chain when it became the union of every path; a name that
        # says otherwise is a trap of the same kind as the value it replaced.
        # `paths` carries the ordered derivations. See S19.
        "built_by": _KEYWORD,
        "affixes": _KEYWORD,
        "glide_rules": _KEYWORD,
        "semantic_tags": _KEYWORD,
        "depth": _INTEGER,
        "meaning_fa": {"type": "text", "analyzer": ANALYZER},
        "attestation": _KEYWORD,
        "attested_count": _INTEGER,
        "attested_docs": _INTEGER,
        "attested_authors": _INTEGER,
        # When the word was used, and whether it survived. Without these a
        # stored derivation cannot draw its own dispersion chart.
        "attested_first_century": _INTEGER,
        "attested_last_century": _INTEGER,
        # True when the corpus has the spelling but the lexicon has no reading
        # for it — a gap in the dictionary, not a doubt about the word. The
        # two must never look the same to a reader.
        "attestation_unlinked": {"type": "boolean"},
        # What the letters are usually read as instead, when they are.
        "attested_other_readings": _KEYWORD,
        # The class of the function word these letters almost always are
        # (rules/function_words.yaml). Set only then, and then no count above
        # is credited: *homograph of a function word, attestation unknown*.
        "attestation_function_word": _KEYWORD,
        # Whether some route to this word rests on written ground throughout.
        # A missing field is *not established*, never "no" — see
        # murfulu/scoring/grounding.py.
        "base_attested": {"type": "boolean"},
        # How much the first step's base resembles the bases its rule usually
        # takes, and how many bases the centroid was built from. Absent where
        # the rule has no centroid, which is most of them.
        "semantic_typicality": {"type": "float"},
        "semantic_bases": _INTEGER,
        "sister_forms": _KEYWORD,
        "scores": {"type": "object", "dynamic": True},
        "corpus_version": _KEYWORD,
        "rule_pack_version": _KEYWORD,
        "lexicon_snapshot_id": _KEYWORD,
        "generated_at": {"type": "date"},
    },
}

#: Alias name → mapping. The alias is what everything queries; the concrete
#: index behind it carries a version suffix.
MAPPINGS: dict[str, dict[str, Any]] = {
    "documents": DOCUMENTS,
    "word_types": WORD_TYPES,
    "derivations": DERIVATIONS,
}

#: Single node, local. Replicas would stay unassigned and turn the cluster
#: yellow, which makes a real problem harder to notice.
SETTINGS: dict[str, Any] = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": ANALYSIS,
}
