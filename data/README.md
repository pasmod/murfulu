# data/

Large files here are gitignored.

## lexicon-20261012.sqlite — served since corpus v13 (2026-10-18)

**karbon release 1.2.0**: the lexicon inside karbon's v1.2.0 wheel, 45,577
active rows, table `infinitives` plus `karbon_meta` (build_date 2026-10-12,
ruleset `V.7+V.9e-adj`, 31,110 reviewed). Snapshot id
`lexicon-20261012:af0310b6446c`.

Against `lexicon-20260808`, row by row on `id` (active rows only): 8 rows gone,
6 new, 122 Latin readings changed (73 صفت, 47 مصدر, 1 اسم معنی, 1 صفت مرکب),
154 verbs with a changed stem, 162 changed `phonemic_variants`, 106 changed
`needs_review`. No headword and no category changed.

What murfulu had to handle, and how (tests in `tests/test_karbon_1_2_0.py`):

- **`notes` and `file_path` are no longer shipped.** Nothing here ever read
  either, so no output changes; `Lexicon` now refuses, by name, a snapshot that
  lacks a column it *does* read, and `tools/audit_lexicon_use.py` lists the two
  as gone. The `[v7:badbracket]` signal in `notes` (UPSTREAM A2c) is lost to
  every consumer with this release.
- **`phonemic_variants` repeats the main reading** (`[main] + alternatives`,
  now for adjectives too). The reader already skipped the main reading, so the
  variants a reading carries are unchanged; a test pins it.
- **No `phonemic_ruleset` column in 1.2.0.** It exists only in karbon's live
  database; nothing here reads it.
- **`rules/lexicon_overrides.yaml` was keyed to one snapshot** and would have
  dropped silently. It now lists every snapshot its rows were re-read on;
  all three (آزردن, گسیختن, رُفتن) still apply to 1.2.0 unchanged. A snapshot
  not listed is logged, printed by the build tools (`overrides  NOT APPLIED`)
  and refused by a test against the configured one.

Greek look-alikes (اسور, افسور) are still in 1.2.0; `behnevis.py` repairs them
on read, as before.

## lexicon-20260808.sqlite — served until corpus v12

The karbon lexicon: 45,579 active rows (51,817 including soft-deleted), all
with a phonemic Latin form; 1,760 verbs with both stems.

Recovered from karbon's own git history — the live database was committed to
the `wip/kpsrv` branch by a daily sweep before it was gitignored. Rebuild with:

```bash
git -C ~/code/karbon show 6660ddc:data/infinitives.sqlite > data/lexicon-20260808.sqlite
```

## How stale is it?

Three days old at the time of recovery, and it is the state at karbon's 1.1.0
release, not a random old copy.

Measured against the 31 July snapshot, 8 days earlier:

| | 31 Jul | 8 Aug | change |
|---|---|---|---|
| active rows | 45,579 | 45,579 | 0 |
| needs_review | 14,361 | 14,361 | 0 |
| transitivity filled | 1,732 | 1,763 | +31 |
| subgroup filled | 5,989 | 5,989 | 0 |

31 changed values in 8 days, all in `transitivity` — the one review track still
running upstream. Every field the engine uses (headword, phonemic, both stems,
category) was unchanged.

Safe to build on. Ask the karbon maintainer for a fresh copy before the real
linguistic evaluation, not before writing code.

## Two safeguards

1. **The lexicon path is configuration, never hardcoded.** Swapping in a newer
   snapshot must not require a code change.
2. **Every stored result records which snapshot produced it**, alongside the
   corpus version. When a newer lexicon lands we know exactly what needs
   recomputing.

Categories present: اسم ذات 14,391 · صفت مرکب 12,131 · اسم مرکب 8,132 ·
وام‌واژه 5,347 · اسم معنی 1,991 · مصدر 1,752 · صفت 1,528 · صفت-اسم 296.
14,361 rows are flagged `needs_review`.

## compare-<old>-<new>.md

What a new corpus version changed against the one it replaces, measured before
the release (ENGINEERING "Building a corpus version", step 4).
`compare-v12-v13.md` is the karbon 1.2.0 lexicon; `compare-v13-v14.md` is the
function-word rule (`rules/function_words.yaml`): same inputs, 38 records whose
spelling is a listed function word credited nothing, and nothing moved that did
not follow from them.

## corpus_report-<version>.json and unlinked-<version>.tsv

Written by `tools/run_ingest.py --report-out` / `--unlinked-out`, gitignored
like the productivity file. The report is what the corpus screen shows: sizes,
coverage, the dating gaps and the head of the unmatched pile. `--report-only`
produces it without creating an index or moving an alias.

The figures are counted there rather than asked of Elasticsearch, because the
index answers both questions wrongly and neither error announces itself —
`cardinality` is an estimate, and one document per *reading* double-counts a
spelling the lexicon reads two ways. See `murfulu/corpus/report.py`.
