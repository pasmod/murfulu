# Architecture — draft v0

**Status: draft.** Open decisions are marked ❓ and listed at the bottom.
Started 2026-08-11.

## Constraints that drive the design

1. **Latin is the working level.** Rules key on vowels; Arabic script does not
   write them. Everything internal is Latin (Behnevis, `š ž č j ˈ` convention).
2. **Latin comes from the lexicon, not from the corpus.** Corpus text has no
   vowels. A corpus word gets its Latin form by matching a lexicon entry.
3. **One spelling can be several words.** *مرد* = *mard* / *mord*. The unit of
   record is a **reading**, not a spelling.
4. **Corpus-agnostic.** Ganjoor is source #1. Books, prose and journalism follow.
   Nothing may assume poetry.
5. **Rules must be editable by a linguist without programming.** They are data,
   not code.
6. **Every generated word carries its derivation.** No unexplained output.

## Containers

| Container | Contents |
|---|---|
| `api` | FastAPI. Rule engine, generation, scoring, search API. Imports `karbon-nlp`. |
| `web` | React SPA, built in Node and served by nginx. Proxies `/api` to `api`, so the app names no host. |
| `elasticsearch` | Corpus documents + word-type statistics |
| `db` | Postgres — rules, curated data, expert feedback, generation cache |
| `ingest` | Same image as `api`, run as batch commands |

Plus a mounted volume for review screenshots.

The karbon lexicon (`lexicon.sqlite`) is mounted read-only into `api` and
`ingest`. We never write to it.

## Data stores, and what belongs where

**Elasticsearch** — anything we search or aggregate over, all rebuildable.

**Postgres** — anything authored or edited: rules, the linguist's decisions,
generation cache. Not rebuildable, so it gets backed up.

**karbon lexicon (sqlite, read-only)** — Latin forms, stems, categories.

Rule of thumb: if losing it means re-running a batch job, it goes in ES. If
losing it means losing human work, it goes in Postgres.

## Elasticsearch indices

### `documents`

One document per poem / page / chapter. Never per line — line splitting differs
per source.

```
source_id      ganjoor
document_id    ganjoor:ferdowsi:shahnameh:1234
author         فردوسی
title          ...
century        10
text_fa        raw text
tokens_fa      analyzed
license        ...
```

Used for citation retrieval and concordance. Search here is by spelling, since
corpus text has no Latin.

### `word_types`

The unique word set. One document **per reading**, not per spelling.

**Identity**

| Field | Type | Note |
|---|---|---|
| `id` | keyword | `{spelling}:{latin}` |
| `spelling_fa` | keyword | مرد |
| `latin` | keyword | mard |
| `latin_reversed` | keyword | dram — suffix search as a prefix query |
| `latin_wild` | wildcard | infix search |
| `reading_id` | keyword | primary karbon lexicon row, or null if unlinked |
| `source_entry_ids` | keyword[] | **all** lexicon rows with this spelling and reading |
| `sense_count` | integer | how many separate entries the dictionary lists |

**Grammar** — three different notions of word class, kept separate

| Field | Source | Reliability |
|---|---|---|
| `lexicon_category` | karbon lexicon (اسم ذات، صفت مرکب، مصدر…) | reviewed, trustworthy |
| `word_class` | mapped from the above (nām, barnām, kārnām…) | **the one the rules use** |
| `pos_observed` | hazm tagger over occurrences | noisy, a distribution not a value |

These are not the same thing and must not be merged. Dehkhoda's categories are
lexicographic. The linguist's types are what the rule pack matches on. The corpus
tagger gives a per-occurrence guess, so a word type carries a *distribution*
(`{"N": 0.82, "ADJ": 0.18}`), not a single tag. **Mapping Dehkhoda categories
to the linguist's types is an open task** — the two systems do not line up one to one.

**Stems and structure**

| Field | Note |
|---|---|
| `stem_1_fa`, `stem_1_latin` | verbs only |
| `stem_2_fa`, `stem_2_latin` | verbs only |
| `stem_rule` | which of rules 1–9 applied |
| `is_exception` | true if the verb is on an exception list |
| `transitivity` | from karbon, where known |
| `affixes` | keyword[] — once decomposition exists |
| `semantic_tags` | keyword[] — search by meaning |
| `rule_ids` | keyword[] — generated words only |

**Evidence** — all per corpus version

| Field | Note |
|---|---|
| `total_count` | occurrences |
| `doc_count` | distinct documents |
| `author_count` | distinct authors |
| `first_century`, `last_century` | integers |
| `counts_by_century` | small object — powers the dispersion chart without a second query |
| `authors` | keyword[], top N |
| `sources` | keyword[] |

**Quality and meta**

| Field | Note |
|---|---|
| `phonemic_confidence` | from karbon |
| `needs_review` | from karbon |
| `population` | keyword[] — corpus / lexicon / generated |
| `corpus_version` | keyword |

Unlinked spellings get a document with `latin: null`. That pile is the review
list and the lexicon-coverage measure.

**Repeated identical readings are kept, not collapsed.** 1,805 spellings appear
more than once in the lexicon; some are real homographs (کله = *Kale* / *kole*
/ *Kole*, three readings, three documents) and some are the same reading listed
several times because the dictionary separates senses (پی appears four times as
*Pey*). The second case becomes **one** document, but `source_entry_ids` keeps
every row and `sense_count` records how many — so a word can show "the
dictionary lists this in 4 senses" and link to each. Cheap to keep now,
unrecoverable later.

### `derivations`

The precomputed derivation space. One document per generated form.

| Field | Note |
|---|---|
| `id` | `{form_latin}:{output_type}` — the dedup key |
| `form_latin` | Raveš |
| `form_fa` | روش |
| `output_type` | karnam — the linguist's type |
| `base_form`, `base_type` | what it was built from |
| `stem_1`, `stem_2` | of the source verb |
| `paths` | all rule chains producing this form, shortest first |
| `rule_chain` | best path, for filtering |
| `affixes` | keyword[] |
| `glide_rules` | integer[] |
| `semantic_tags` | keyword[] |
| `depth` | steps taken |
| `meaning_fa` | composed from the semantic tags |
| `attestation` | reading / spelling / none |
| `attested_count`, `attested_docs`, `attested_authors` | if attested |
| `sister_forms` | other attested outputs of the same rule |
| `scores` | rule, productivity, semantic, composite |
| `corpus_version` | the counts are only true for this version |
| `generated_at` | live results are cached; this shows when |

Makes `in:generated` searchable and makes sister-form lookup a single query.

### Changes made when the mappings were written (2026-08-11)

The mappings in `murfulu/search/mappings.py` follow the tables above, with four
differences, all recorded here rather than left as a silent drift:

- **`stem_rule` is `karbon_stem_rule`.** The field holds karbon's number, which
  is not the source grammar's. Naming it plainly stops it being used as if it
  were ours.
- **`license` is `licence`** on `documents`, matching the spelling used
  everywhere else in these docs.
- **`lexicon_snapshot_id` added** to `word_types` and `derivations`. A result
  that depends on a lexicon snapshot must say which one, the same way it says
  which corpus version.
- **`rule_pack_version` added** to `derivations`, which RULE_PACK.md already
  requires ("every stored derivation records the rule-pack version that
  produced it") but the field table omitted.

All three mappings are `dynamic: strict`.

### Changes made when the precompute was written (2026-08-11)

- **`glide_rules` is `keyword`, not `integer`.** Glide rules have ids like
  `G-04`, the same shape as every other rule id.
- **`form_fa_variants` added** to `derivations`. The id is the Latin form and
  Behnevis is phonemic, so two Persian spellings can land on one record —
  10,270 of them in the first run. The second is kept beside the first instead
  of overwriting it. See OPEN_QUESTIONS item Q2.
- **`paths` carries the source entry.** Merging runs across the whole lexicon,
  so each stored path records the base *and* the lexicon entry it started
  from; a merged record could otherwise no longer say where a chain came from.
- **`scores` is not written yet.** That is PLAN task 5.5. The field stays in
  the mapping; the precompute omits it, and a missing field is legal under
  `dynamic: strict` — only an undeclared one is not.
- **Four attestation fields added** to `derivations`:
  `attested_first_century`, `attested_last_century`, `attestation_unlinked`
  and `attested_other_readings`. All four were being computed and then thrown
  away at the storage layer. Without the centuries a stored word cannot draw
  its dispersion chart; without the unlinked flag a gap in the dictionary
  looks the same as a homograph collision.
- **`sister_forms` is a denormalisation with a measured price.** The per-rule
  list is the artefact; copying eight onto each of 1.7 million words costs
  380 MB, so how many go on each word is a parameter and zero is allowed.

### Search mechanics

- suffix search (*-nā*) → prefix query on `latin_reversed`
- prefix search (*bar-*) → prefix query on `latin`
- middle search → ES `wildcard` field type, which is built for leading wildcards
- everything filterable by source, century, author, category

## Postgres tables

```
rules            id, kind, input_type, input_category, affix, position,
                 output_type, semantic_tag, example, notes, active, version
glide_rules      left_vowel, right_vowel, result, example
derivations      cached generated form + path + scores + corpus version
expert_feedback  target, context JSON, verdict, note, author, screenshot ref;
                 append-only. Doubles as the evaluation set — see REVIEW.md
users            one row, no roles. Kept so a judgement keeps its author
sources          corpus source registry, licence, ingest date
corpus_versions  version id, sources included, doc count, build date
```

The rule tables mirror the source grammar tables one row per row, so a rule can be
traced back to its source line.

### Changes made when the schema was written (2026-08-12)

`murfulu/db/` and `migrations/versions/0001_authored_schema` follow the sketch
above with five differences, recorded here rather than left as silent drift.

- **There is no `derivations` table.** The sketch lists one, and the section
  *Live generation and caching* below says every live result is cached in the
  `derivations` **index**. Only one of those can be true. By the rule of thumb
  two paragraphs up — if losing it means re-running a batch job, it goes in
  Elasticsearch — a cache is not authored data. The index exists, is written
  by the precompute, and is where task 6.2 writes.
- **`rules` mirrors the loaded rule, not the shorter column list.** A rule
  takes several input types (`input_types`), carries several tags
  (`semantic_tags`) and gives several examples (`examples`); the singular
  `input_type`, `semantic_tag` and `example` above predate the rule pack.
  Templates additionally carry `pattern`, `pattern_fa` and `slots`. The row is
  `murfulu.rules.pack.Rule` field for field.
- **`sources included` is a table, not a list.** `corpus_version_sources`
  joins a version to the registered sources, so a version cannot claim a
  source that was never registered.
- **`expert_feedback` is append-only in the database.** The migration installs
  a trigger that refuses every UPDATE and DELETE. Two of its rules are check
  constraints rather than application code: a graded verdict and the
  `linguistic` category imply each other, and `owner` is one of `murfulu` or
  `karbon`.
- **`users` holds no credentials, and since 2026-08-17 holds one row.**
  Migration `0002` added `api_tokens` so an account could prove who it was;
  migration `0008` drops that table and the `role` column with it. A reader
  needed the site password to see anything and an expert token to answer
  anything, and that is one credential too many for a research app with one
  reviewer — the password wall in front of the whole site is the
  authentication now.

  **The table stays because the authorship does.** Feedback, rulings and
  proposals are append-only precisely so a judgement keeps whoever made it,
  and dropping the column would have discarded that on records already
  stored. An account is still disabled rather than deleted, for the same
  reason. What it costs — inter-rater agreement — is in
  [REVIEW.md](REVIEW.md) and in the dataset manifest.

Lists and captured context are stored as `JSONB`. The URL comes from
`MURFULU_DATABASE_URL` and is rewritten to name the driver, so no component
has to know which one is installed.

## Batch pipelines

Run through the `ingest` container. Each writes a new corpus version; nothing
is edited in place.

1. **Ingest** — source adapter → `documents`. One adapter per source; Ganjoor
   first (SQLite dump or `api.ganjoor.net`).
2. **Word types** — aggregate spellings with counts and dispersion.
3. **Link** — join word types against the karbon lexicon → attach Latin
   readings. Unmatched go to the review pile.
4. **Derivation space** — apply every rule to every applicable lexicon entry,
   then check attestation (Monakhov simulate-and-check). Writes the
   `derivations` index. Yields Baayen P per rule and precomputed sister forms
   in one pass. See [WALKTHROUGH_RAFTAN.md](WALKTHROUGH_RAFTAN.md).
5. **Rule statistics** — roll up step 4 into per-rule productivity, stored per
   corpus version.

## Evidence shown for every generated word

The same for precomputed and live results.

**Attested** — `attestation: reading`:

| Field | |
|---|---|
| total occurrences | |
| distinct documents | 30 hits in one poem is a rhyme, not a word |
| distinct authors | one author means one author's coinage |
| first / last century | survived, or died out |
| citations | the actual lines, with author and title |

**Not attested** — `attestation: none`:

| Field | |
|---|---|
| wording | "not found in corpus v3", never "does not exist" |
| score parts | rule strength, measured productivity, semantic plausibility — shown separately |
| **sister forms** | other words the same rule produced **that do exist** |

Sister forms are the strongest signal for a human. If rule 10 produced
*Goftār*, *Raftār* and *Didār*, and all three are attested, a new form from
rule 10 is probably sound. That tells a translator more than a composite score
does.

## Compounding

A second generation path alongside affixation, **limited to the combinations
the source grammar license** — nām + kārbon-e do (*soxanguy*), nām + nām, stem + o
+ stem (*Zadoxord*), čonvāže + kārbon-e do (*xošnevis*), and the rest of the
documented patterns. Free compounding of any two words is not attempted.

Modelled as `kind: template` rules with typed slots, so it needs no separate
engine — the slot filler queries the lexicon for candidates of the required
type. The candidate space is large, so compounding is generated on demand with
one slot pinned to the user's input, never precomputed exhaustively.

## Taking a word apart

The reverse of generation, added with PLAN 7.6. `engine/decompose.py`
proposes what a word might have been built from — purely string work, no
lexicon — and `analysis.py` looks each remainder up and **builds it forward
again**. Only an account that reproduces the word exactly survives.

The verification is not a nicety. Stripping a Persian suffix off an Arabic
loan leaves something a dictionary often knows, so a decomposer that stopped
at the remainder would claim derivations nobody built. It is the same failure
the affix backfill made, and it is refused the same way.

Nothing chooses between survivors. One word commonly has several accounts,
and which is meant is a question about meaning.

## Rule round-trip

YAML is the source of truth and an expert edits in the app, so the two must be
reconciled explicitly.

```
the linguist edits in app
   → written to Postgres as a *proposed change* (never applied silently)
   → exported to YAML by a command
   → reviewed as a git diff, committed
   → loader re-syncs Postgres from YAML
```

The app therefore holds two layers: the loaded rule pack (read-only, from YAML)
and pending proposals on top. What the engine uses is configurable — proposals
off by default, on for the linguist's own preview.

Changes belonging to karbon (stem exceptions, phonemic rules) follow the same
proposal path but export as a karbon pull request. See
[OWNERSHIP.md](OWNERSHIP.md).

## Reindex and corpus versions

Every pipeline run builds a new corpus version and writes to a fresh index
suffixed with it. An **alias** points at the current one, and swapping the alias
is the release step. So:

- rebuilds never mutate a live index
- the previous version stays queryable until deliberately dropped
- attestation figures are always tied to the version that produced them
- expert feedback records the corpus version it was given under, and stays
  valid across rebuilds — it judged the form, not the count

## Generation algorithm

Input: a word (Persian or Latin), or a stem.

```
1. resolve      → karbon: Latin form, category, stem 1 / stem 2
2. match rules  → all rules whose input side fits this category
3. apply        → affix + stem, with the 17 glide rules
4. recurse      → feed each output back in (guyā → Guyāyi), depth-limited,
                  cycle-detected
5. attest       → look each output up in word_types
6. score        → rule productivity, attestation, semantics, acceptability
7. return       → form, derivation path, composed meaning, scores, citations
```

Every output carries the full path: which rules, in which order, on which stem.

### Depth

Depth is **not** a quality limit. A three-step form is not worse for being
three steps — *Guyāyi* is two steps and entirely normal. Generating new words is
the point of the project, so we do not cut the chain short to be safe.

Generation runs until no rule matches. Two hard limits remain, and both are
mechanical rather than linguistic:

- **Loops.** Several rules return the type they consume (`nā-` + barnām →
  barnām), so a chain can extend forever. Hard stop at **5 steps**, plus cycle
  detection on (form, rule) pairs.
- **Size.** Each step multiplies. Step 2 is roughly 60 forms per verb; step 4
  could be thousands, times 45,000 lexicon entries.

So: **precompute steps 1–2, generate deeper on demand.**

### Live generation and caching

Live generation is cheap. Rule matching and affix application are in-memory
string work. The only real cost is the attestation lookup, which is a single
batched Elasticsearch request for all candidates at once — tens of milliseconds
for a few hundred forms. Semantic scoring uses precomputed affix matrices, so it
is a matrix multiply, not a model call.

Every live result is **cached** in the `derivations` index, tagged with the
corpus version. The first request for a word pays the cost; every later request
is a lookup. The cache grows into the precompute.

### Deduplication

Different rule chains can produce the same form. One row per word.

**Grouping key: `form_latin` + `output_type`.**

- not the Persian spelling — it collapses distinctions the Latin keeps
- not case-folded — `Gofte` (noun) and `gofte` (adjective) are different words
- type is part of the key because the same string in two categories is two
  words

Alternative paths are **kept, not discarded**. They are shown nested under the
form:

```
Ravāni  روانی
  ├ row + ān (rule 29) + i (rule 30)
  └ …
```

Two derivations for one form is useful information — it often means the word
carries two senses. Sort paths shortest first.

Scoring a grouped form: take the best-scoring path, and show the others.

## API sketch

```
POST /generate     {word|stem, category?, depth?}  → derivations + scores
POST /search       {pattern, position, filters}    → word types + counts
GET  /word/{id}    → readings, stats, citations
POST /explain      {word}                          → structural decomposition
GET  /rules        → the rule pack
GET  /corpus       → versions, sources, sizes
```

## Deployment

Runs **locally on the project lead's own machine**, not on the karbon
maintainer's server where karbon lives. Plain `docker compose up`; no Traefik,
no public hostname.

**And on a server as of 2026-08-17**, at `murfulu.mosaic-hub.de`, behind Caddy
with automatic HTTPS and a password on every route — see
[DEPLOY.md](DEPLOY.md), and published through a Cloudflare Tunnel rather than
a public IP. The password is at the edge rather than in the app because a
browser loading a page carries no credential for a proxy to check — and since
2026-08-17 it is the **only** credential: the app behind it has one account and
no roles. It is also what makes
deploying defensible: behind it are 19.5 million lines of poetry that Ganjoor
declines to warrant — their FAQ answers *are these data copyright-free* with
«لزوماً خیر!» — so the corpus cannot be republished on somebody else's
permission. Murfulu's own licence is settled (Apache-2.0, PLAN 8.4) and does
not reach the corpus; see NOTICE.

Repository is **private** on GitHub.

## Settled (2026-08-11)

- **Frontend: React SPA**, separate container. Backend is API-only.
- **karbon: imported as a library** (`pip install karbon-nlp`). Murfulu pins a
  karbon version; the lexicon file is mounted locally.
- **Rule pack: YAML in git, loaded into Postgres.** YAML is the source of
  truth. See [RULE_PACK.md](RULE_PACK.md).
- **Postgres** for authored data.
- **Persian spellings are composed, not converted.** Latin and Persian are
  built in parallel through the derivation; there is no Latin → Persian
  transliterator. Affixes carry `affix_fa`.
- **Corpus search happens in Latin**, against linked `word_types`. Unlinked
  corpus words have no Latin and are the coverage gap.
- **Own review mechanism**, with roles. See [REVIEW.md](REVIEW.md).
- **Verb inventory is not a blocker.** karbon's stem rules are validated on
  1,752 infinitives; we assume they generalise to the wider set. Recorded as an
  assumption, to be checked, not a gate.
- **Deployment: local, and one password-gated server.** Private repo.
  See [DEPLOY.md](DEPLOY.md).

## Open decisions

✅ **Recursion depth.** Settled in use rather than up front. **Two** by
default, because two steps reach *Ravandegi* and that is what a reader asking
about a word wants. **Three** is offered on the build screen (PLAN 9.13) and
has to be ranked and paged to be usable: one verb builds 660 forms at two steps
and 17,717 at three, of which fifty are words the corpus has. **Five** is the
engine's hard stop, mechanical rather than a judgement — a long word is not a
worse word. Depth never enters into how a result is ranked.

❓ **Rule strength** — how to represent the linguist's "mostly with…" conditions.
See RULE_PACK.md.
