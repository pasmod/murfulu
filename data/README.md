# data/

Large files here are gitignored.

## lexicon-20261111.sqlite — karbon 1.3.2, the final word bank (from corpus v15)

**karbon release 1.3.2** (2026-11-11), the lexicon inside its wheel, taken out
with `python tools/fetch_lexicon.py v1.3.2` (needs read access to karbon's
repository; `--wheel` takes a downloaded wheel instead). 58,983 rows, **none
soft-deleted**, 56,366 reviewed by the linguist (`needs_review` on 2,617, was
14,467). `karbon_meta`: build_date 2026-11-11, ruleset `V.7+V.9e-adj`, source
`dehkhoda-workshop`. Snapshot id `lexicon-20261111:e300dbc27083`. Journal mode
`delete`, so it opens `immutable=1` like the others.

New in the schema, all read only when present (tests in
`tests/test_karbon_1_3_2.py`), so the older snapshots open unchanged:

- **`bank_group`** — the linguist's twelve word-bank groups, one row per word
  and group: نام 23,306 · برنام 15,957 · کارنام 10,866 · وام‌واژه 6,454 ·
  نابسودکارواژه 1,772 · چون‌واژه 1,691 · کاربهر 1,106 · صوت 542 · پسوند 206 ·
  پیوند‌واژه 127 · پیش‌واژه 119 · جانام 114 (62,260 rows; 2,986 words sit in
  more than one group). A `Reading` carries every group of every row it
  collapses, as `bank_groups`, in karbon's order.
- **`bank_labels`** — the groups' Persian names and the two stems' new names,
  پیشین‌کاربن (past) and کنون‌کاربن (present).
- **`merge_map`** — karbon keeps one entry per word since 1.3.0: 3,569 old ids
  went into 2,987, no chains. `Lexicon.current_id` and `Lexicon.by_id` follow
  it, so an old id still finds its word.
- **`definition_truncated`** — the preview was cut at 200 characters.

`pos` still holds one dictionary label per row, now with seven more values
(چون‌واژه، کاربهر، صوت، پسوند، پیوند‌واژه، پیش‌واژه، جانام). The bank group is
derived from it plus the linguist's extra groups; karbon's own README in the
release ZIP gives the derivation.

**887 spelling + reading pairs are still on more than one row** (778 on two, 109 on three to seven). They are homonyms with
different senses (آب the water and آب the month), and collapse into one
reading as before; آرش is one of them, filed نام on one row and کارنام on the
other, and carries both groups.

Against `lexicon-20261012`, row by row on `id`:

| | rows |
|---|---:|
| 1.2.0's active rows | 45,577 |
| still there under the same id | 44,642 |
| merged into another row (`merge_map`) | 509 |
| gone, neither present nor merged | 426 (اسم ذات 207, وام‌واژه 85, اسم مرکب 66, صفت مرکب 32, اسم معنی 30, صفت 6) |
| Latin reading changed, same id | 9,980 (صفت مرکب 4,423, اسم مرکب 2,825, اسم ذات 2,155, وام‌واژه 355, اسم معنی 156, صفت 54, مصدر 6, صفت-اسم 2, no category 4), 134 of them in case only |
| verbs with a changed Latin stem | 13 (17 counting the Persian stem columns too) |
| category changed, same id | 12 (11 from none to مصدر) |
| new ids | 14,341 (اسم معنی 8,113, وام‌واژه 1,190, چون‌واژه 1,142, صفت 1,070, صفت مرکب 1,026, کاربهر 788, صوت 478, پسوند 152, پیوند‌واژه 119, پیش‌واژه 103, جانام 102, اسم مرکب 55, مصدر 3) |

3,060 of the merged ids never were 1.2.0 rows: they were added and merged
between the two releases.

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
