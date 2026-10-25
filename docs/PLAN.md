                    # Build plan

Ordered task list. Each task states what "done" means, so it can be checked
without asking anyone.

**Rules for whoever works through this:**

- Do the next task that is not `[x]` and not `BLOCKED`.
- A task is finished only when its *done test* passes.
- Run the tests. Commit. Tick the box in this file.
- Update `docs/` when a task changes the design.
- If a task needs a decision, mark it `BLOCKED` with the question and move on.
  Never guess a design decision.
- Follow [ENGINEERING.md](ENGINEERING.md): Docker, modules, no file over 400
  lines, tests, no personal names.

---

## Phase 0 — Foundations

- [x] **0.1 Project skeleton.** Module folders per ENGINEERING.md (`rules/`,
      `engine/`, `scoring/`, `lexicon/`, `search/`, `corpus/`, `api/`), each
      with a docstring saying what it owns.
      *Done when:* `pip install -e .` works and every module imports.

- [x] **0.2 Tooling.** `ruff`, `mypy`, `pytest` configured. One command runs
      all three.
      *Done when:* `make check` passes on an empty project.

- [x] **0.3 Docker.** `docker-compose.yml` with `api`, `db` (Postgres),
      `elasticsearch`. Pinned versions. `.env.example` committed.
      *Done when:* `docker compose up` starts all three and healthchecks pass.

- [x] **0.4 CI.** GitHub Actions running lint, types and tests on push.
      *Done when:* the workflow is green.
      `.github/workflows/check.yml`, two jobs: `make check` on a Python runner,
      and the test suite inside the built image. Green on `main`.

## Phase 1 — Rule pack

The source is `Dasturhāye Vāžesāzi az Kārbonhā.docx` in the Google Drive
archive (see [SOURCES.md](SOURCES.md)). Schema in [RULE_PACK.md](RULE_PACK.md).

- [x] **1.0 Assign permanent rule ids.** Apply the `FAMILY-NNN` scheme from
      [RULE_PACK.md](RULE_PACK.md): S, V, N, D, G. Ids are permanent, appended
      never inserted, never reused.
      *Done when:* every source row has exactly one id and no id is used twice.

      **Done for V, N and G.** `tools/assign_rule_ids.py` →
      `rules/rule_ids.json`, 82 + 105 + 17 ids, no duplicates, tested. V and N
      mirror the document's own row numbers, which is what the worked examples
      in RULE_PACK.md require (V-010, V-017 and V-053 are verb rows 10, 17 and
      53). Two mechanical consequences, both recorded in RULE_PACK.md: verb row
      77 is empty in the source, so **V-077 is reserved and never used**; and
      the one unnumbered row in each rule table is appended (V-082 after row 8,
      N-105 after row 84) rather than inserted.

      **Both open questions answered, 2026-08-11.**

      1. **The `D` family is dropped.** It never existed. The whole Drive
         archive and the earlier prototype were searched; the concept document
         names exactly **two** rules that make a verb from a noun — `-idan`
         (intransitive) and `-āndan` (transitive) — and those are verb-table
         rows 3 and 4. They are **V-003 and V-004**, tagged
         `makes_verb_from_nominal`. No `D` id was ever issued. The reason is
         recorded in `rules/rule_ids.json` under `retired_families`.

      2. **The `S` family is extracted and assigned.**
         `tools/extract_stem_rules.py` → `rules/stem_source_rows.json`: 9 rules,
         2 sub-rules and 39 exception verbs. `S-01` … `S-09` mirror the
         document's rule numbers. Sub-rules 4-1 and 4-2 are parts of `S-04`,
         because the text says stem 2 divides into "eight groups" (rules 2–9).
         Three exception rows could not be read and are flagged rather than
         repaired: گشادن, افراشتن, نهفتن.

- [x] **1.1 Extract the tables.** Read the three rule tables and the glide
      table out of the .docx into raw structured form. Keep the original row
      numbers.
      *Done when:* a raw dump exists with one record per source row and the
      counts match: ~81 verb-stem rules, ~104 nominal rules, 17 glide rules.
      `tools/extract_source_grammar.py` → `rules/source_rows.json`. Measured:
      **81** verb-stem rows, **105** nominal rows (104 numbered + 1 the
      document left unnumbered), **17** glide rows. The document holds only
      *two* rule tables, not three — there is no separate verbaliser table.
      See task 1.0.

- [x] **1.2 Semantic tag list.** Collect every bracketed tag into
      `rules/semantic_tags.yaml`, each with `gloss_fa` and `gloss_en`.
      *Done when:* every tag used by a rule exists in the file.
      44 bracketed labels in the source, 43 tags after merging the one
      capitalisation variant (kenār / Kenār). Checked both ways: no tag is
      missing and none is declared that no rule uses.
      Two things left for the linguist, flagged in the file:
      the **gloss templates** (the sentence a generated word gets as its
      meaning) are `null` for everything except `ja`, because authoring them is
      a linguistic judgement; and `manand`/`manandi` and `nai`/`nayi` are kept
      separate pending a ruling on whether each pair is one tag.

- [x] **1.3 Write the YAML rule pack.** `verb_stems.yaml`, `nominals.yaml`,
      `stem_rules.yaml`, `glides.yaml` (no `verbalisers.yaml` — see 1.0).
      Every rule carries `id`, `source` row, `affix`, `affix_fa`, input type,
      output type, `strength`, `examples`, `label_fa`, `explanation_fa`.
      Rows that are unclear get `needs_expert_check: true` plus a note. Do not
      invent rules.
      *Done when:* all rows are transcribed and the file validates.
      Built by `tools/build_rule_pack.py` from the two raw transcriptions plus
      two authored tables (`affix_spellings.yaml`, `semantic_tags.yaml`).
      **212 rules: 81 + 105 + 17 + 9.** Only **6 are flagged**, each with the
      exact reason — three affix spellings the source leaves in doubt
      (`-bāž`, `pa-`, `-mānd`, where the source's own example contradicts its
      spelling) and the three stem exceptions the document does not resolve.
      Nothing else was guessed.
      `label_fa` and `explanation_fa` are **composed** from the grammar's own
      Persian type names, not written freehand — for V-010 that reproduces the
      text in RULE_PACK.md exactly. The gloss templates on the semantic tags
      remain the linguist's to author (see 1.2).
      Compounding rows became `kind: template` with typed slots and the
      documented constraints. This caught a real bug: the first parser matched
      only the longest type prefix, so `Kārboné yek + o + Kārboné do` silently
      became a one-slot rule that still looked valid. Now every unparsed
      fragment is reported instead of dropped.

- [x] **1.4 Loader and validator.** Load YAML, check every rule against a
      schema, fail loudly on unknown types or missing Farsi text.
      *Done when:* loading the pack raises on a deliberately broken rule.
      `murfulu/rules/pack.py`. Every failure message names the rule id.
      14 deliberately broken rules are tested — unknown kind, unknown strength,
      unknown word class, empty output, missing Persian affix spelling, missing
      Farsi label or explanation, no source table, a flag with no reason, four
      broken templates, a duplicate id and a broken glide — plus a control that
      the valid rule still loads, so none of them can pass vacuously.
      Also exposes what the engine will need: `taking(word_class)` for rule
      matching, `by_id` for the permanent address, and `needing_expert_check`.

- [x] **1.5 Golden tests from the examples.** Generate one test per rule
      example.
      *Done when:* the test file is generated from the YAML, not written by
      hand, and the count matches the number of examples.
      `tests/test_golden_examples.py` collects every example from the loaded
      pack — **290 examples**, and the count is asserted against the pack so
      the file cannot drift out of step. Until the engine lands (2.1) these
      check each example's *shape*: that it is a Behnevis form, that a worked
      derivation's affix matches the rule carrying it, and that the result
      looks built from its base. When the engine exists, `expected` becomes
      what it must produce.
      They found two real bugs on the first run: the builder was splitting
      `ā + ande = Āyande` into three "examples" on the spaces, and cells
      holding several worked derivations were being merged into one. Both
      fixed.

## Phase 2 — Engine

`engine/` must not import Elasticsearch, Postgres or karbon. It takes a stem
and a rule pack and returns forms.

- [x] **2.1 Affixation.** Apply prefix and suffix rules to a stem, producing
      Latin and Persian forms together.
      *Done when:* the golden tests for simple affix rules pass.
      `murfulu/engine/affix.py`. Latin and Persian are built in the same step
      from `affix` and `affix_fa`; there is no converter anywhere.
      **Capitalisation is computed from the output word class**, not stored:
      a kārnām or nām is written with a capital, everything else without. That
      is what separates *Porsidan* (the asking) from *porsidan* (to ask) —
      verb rows 5 and 6, identical but for the case — and the engine
      reproduces both from one stem.
      Every result carries the rule that made it and can be fed back in, which
      is what 2.4 will need.

- [x] **2.2 Glide rules.** Apply the 17 vowel rules at every join.
      *Done when:* `row + eš → Raveš` and `dānā + i → Dānāyi` pass.
      Both pass, along with all 17 of the table's own worked examples.
      The table mixes two shapes and `murfulu/engine/glides.py` tells them
      apart from the data rather than special-casing: if the result starts with
      the left vowel it spells the whole join (`gu + eš → guyeš`), otherwise it
      replaces the left vowel and the affix is added whole
      (`row + eš → raveš`). All 17 follow one or the other.
      Two things the table cannot answer are reported, not hidden: *e* meeting
      *i* is claimed by both G-09 and G-17, so a join returns the alternatives;
      and there is **no rule for *ow* meeting *ā***, which is why *row + ān*
      comes out as *rowān* when V-029's own example says *ravān*. See
      OPEN_QUESTIONS item J.

- [x] **2.3 Templates.** Compound patterns with typed slots
      (`{a} + o + {b}`), including the `same_verb` / `different_verb` /
      `same_stem` / `negated` constraints.
      *Done when:* `Goftogu` and `Zadoxord` are produced correctly.
      `murfulu/engine/compound.py`. Both, plus every other compounding example
      the grammar gives: *Kešākeš* (same stem), *Budonabud* (negated),
      *Xordoxāb* (two verbs), *Sarāsar* and *Sarāpā* (two nouns).
      **Ten templates, not nine** — nine join verb stems, and N-104 joins two
      nouns, so a slot is filled by either a verb (the rule picks which stem)
      or a plain word.
      A rule that needs two different verbs refuses to run with one, rather
      than quietly compounding a word with itself. A rule that says *same
      verb* refuses a second. A rule that says nothing takes either, because
      silence is not a prohibition — *Sarāpā* is two different nouns.
      Each template carries `pattern_fa` beside `pattern`, so the Persian
      compound is built in the same step as the Latin, exactly as an affix
      carries `affix_fa`.

- [x] **2.4 Recursion.** Feed outputs back in. Hard stop at 5 steps, cycle
      detection on (form, rule).
      *Done when:* `row → ravande → Ravandegi` is produced, and a deliberately
      looping rule terminates.
      `murfulu/engine/generate.py`. Both pass — *Ravandegi* comes out via
      V-022 then V-023, and every form carries its whole chain.
      **Measured growth from one verb stem:** 21 forms at one step, 375 at two,
      **14,692 at three**. So a `max_forms` backstop sits alongside the depth
      limit, and a truncated result says it was truncated rather than looking
      complete. This is why ARCHITECTURE precomputes steps 1–2 only.
      **A known limit, found by the tests and not papered over:** cycle
      detection on (form, rule) does *not* stop a rule that changes the form
      each time. *nā-* on *dorost* gives *nādorost*, a different form, so
      nothing prevents *nānādorost* except the depth limit. Whether Persian
      permits that stacking is a question for the linguist — OPEN_QUESTIONS
      item L. A test records the behaviour as it stands.

- [x] **2.5 Deduplication.** Group by `form_latin` + `output_type`, keep all
      paths, sort shortest first.
      *Done when:* a form reachable by two chains appears once with two paths.
      `murfulu/engine/dedupe.py`. From one verb stem at two steps, 375 forms
      become **293 words**, and **63 of them are reachable more than one way** —
      *ravāndan* comes from both V-001 and V-002, for instance. No path is
      lost: the paths add back up to the original count.
      Case is not folded and the word class is part of the key, so *Rave* the
      noun and *rave* the participle stay two words.

- [x] **2.6 Meaning composition.** Build `meaning_fa` from the semantic tags
      along the path.
      *Done when:* `namak + dān` yields a Persian gloss for "place where salt
      is kept".
      `murfulu/engine/meaning.py`. *namak* + *dān* → **Namakdān** / نمکدان,
      meaning **جایی که نمک در آن است**. The gloss names the *Persian* stem,
      because the reader reads Persian.
      **A word whose tags have no template gets no meaning, not a made-up
      one** — and it reports which tag is missing. Only `Jā` has a template so
      far, so this is what most words get today; writing the other 42 is the
      linguist's task (OPEN_QUESTIONS item E). The machinery is done and waits
      on them.

## Phase 3 — Lexicon

The lexicon is at `data/lexicon-20260808.sqlite` (45,579 active rows,
recovered from karbon's git history). Ask the karbon maintainer for a fresher
snapshot when convenient — this one is good enough to build on.

- [x] **3.1 Read-only wrapper.** `lexicon/` is the only module importing
      karbon. Lookup by spelling, by normalised spelling, and by Latin.
      **The snapshot path comes from configuration, never hardcoded**, and the
      snapshot id is recorded with every result that depends on it.
      Repeated identical readings collapse to one record, but keep
      `source_entry_ids` and `sense_count` so the dictionary's separate senses
      stay reachable.
      *Done when:* looking up رفتن returns the entry with both stems; پی
      returns one record with `sense_count: 4` and four source ids; and
      pointing at a different snapshot file needs no code change.
      All three pass, but **the expected number for پی was wrong**: it is
      `sense_count: 7`, not 4. The four rows counted earlier are soft-deleted
      `Pi` rows. Live, the snapshot has *Pey* ×7 and *Pay* ×1 — so the reading
      split is right and only the count was off. Corrected in
      [LEXICON_ANALYSIS.md](LEXICON_ANALYSIS.md).
      `murfulu/lexicon/`: `snapshot.py` (path from `MURFULU_LEXICON_PATH`, id
      = file name + content hash), `entries.py`, `store.py`. Opened read-only
      at the SQLite level. 19 tests, all against a fixture snapshot — none
      touches the real 28 MB file.

- [x] **3.2 Category mapping.** Map `lexicon_category` (اسم ذات، صفت مرکب،
      مصدر…) to `word_class` (nam, barnam, karnam…), which is what the rules
      match on. Handle `pos = NULL` explicitly — 11 rows have it and SQL
      comparisons skip them silently.
      *Done when:* every category in the lexicon maps to a word class, or is
      explicitly listed as unmappable with a reason.
      **This mapping is a linguistic judgement — mark uncertain rows for
      expert review rather than guessing.**
      `rules/lexicon_categories.yaml`, loaded by `murfulu/lexicon/categories.py`
      and checked against the closed word-class set in `murfulu/rules/types.py`.
      All nine categories are accounted for. **Six are mapped**, each grounded
      in the source grammar's own terminology table or prose: مصدر →
      `nabesudkarvaze`, صفت → `barnam`, اسم معنی → `karnam`, اسم ذات → `nam`,
      اسم مرکب → `nam`, صفت مرکب → `barnam`. **Three are deliberately
      unmapped**, each with a reason and a question for the linguist:
      وام‌واژه (5,347 rows — "loanword" says where a word came from, not what
      class it is), صفت-اسم (296 rows — one class or both?), and the 11 rows
      with no category. Asking for the classes of an unmapped category raises,
      so "we decided not to" can never be mistaken for "there are none".
      Compounds are flagged with `is_compound` rather than given a separate
      class, which keeps the LEXICON_ANALYSIS §7 question open without
      blocking the mapping.

- [x] **3.3 Generate from a real word.** End to end: Persian word in,
      derivations out.
      *Done when:* رفتن produces at least *Raftār*, *Raveš*, *ravande*,
      *Ravandegi*.
      `murfulu/generation.py` — the one place the lexicon, the rule pack and
      the engine meet. All four come out, from the real snapshot and from the
      fixture. رفتن yields **510 words** at two steps.
      A verb is entered through **both** its stems, never through the
      infinitive: *Raftār* comes from *raft*, *Raveš* from *row*. A spelling
      with two readings gives two separate results — مرد stays *mard* and
      *mord*, never one merged pile. A word whose category we deliberately did
      not map yields an empty result rather than a crash or a guess.

## Phase 4 — Corpus and search

- [x] **4.1 Source adapter interface.** One interface, one adapter per corpus.
      *Done when:* a fixture adapter passes the shared adapter test.
      `murfulu/corpus/`: `documents.py` (the `Document` a source yields, which
      validates itself), `adapter.py` (`SourceAdapter` — source id, licence,
      documents), `contract.py` (`check_adapter`, the shared test).
      The shared test lives in the package, not in `tests/`, so the second
      corpus proves itself against the same bar as the first without anyone
      having to remember what it was. It checks: a stated licence, unique
      document ids, ids prefixed with the source, and **repeatability** — two
      passes must yield the same documents in the same order, or two corpus
      versions cannot be compared.

- [x] **4.2 Ganjoor adapter.** Ingest from the Ganjoor SQLite dump or
      `api.ganjoor.net`. One document per poem, with author, title and date.
      *Done when:* a fixture subset ingests with provenance intact.
      `murfulu/corpus/ganjoor.py`. **No download was needed** — the dump was
      already on disk from the earlier prototype, and is now at
      `~/data/murfulu/ganjoor.db` (325 MB, outside both repositories, path from
      `MURFULU_GANJOOR_PATH`).
      237 poets, **133,148 documents**, 3,043,905 verses. One document per
      poem; prose paragraphs are skipped, as is any poem with no verses.
      A bug worth recording: the poet slug must come from the **poet's own root
      category**, not the poem's. A poem sits in a book (`…/khayyam/robaee`),
      so the first attempt produced `ganjoor:robaee:1119` and lost the poet.
      **Only 26% of poems get a century** — the hand-written poet→century table
      inherited from the prototype covers 56 of 237 poets. A poet not in it
      gets `None`, never a guess, and `poets_without_a_century()` lists the
      gaps. See OPEN_QUESTIONS item N.

- [x] **4.3 Elasticsearch mappings.** `documents`, `word_types`,
      `derivations`, per [ARCHITECTURE.md](ARCHITECTURE.md). Versioned index
      names behind aliases.
      *Done when:* indices are created from code and the alias swap works.
      `murfulu/search/mappings.py` and `indices.py`. Verified against a live
      8.17.1 cluster: all three created, mappings survive the round trip, and
      the alias swap is atomic — building `v2` does not release it, and
      releasing `v2` leaves `v1` queryable. Every mapping is
      `dynamic: strict`, so a mistyped field name fails the write instead of
      silently creating a field nothing queries.
      Integration tests skip when no cluster is reachable, so the suite still
      runs on a bare machine.

- [x] **4.4 Word-type pipeline.** Unique spellings with counts, document
      counts, author counts, per-century counts.
      *Done when:* the fixture corpus produces correct counts.
      `murfulu/corpus/wordtypes.py`. On the whole of Ganjoor: **25,497,189
      words, 409,916 distinct spellings, in 18 seconds.**
      The four counts say different things and are kept apart — روش occurs
      1,029 times across 912 poems by 146 poets, while روندگی occurs **4
      times, in 4 poems, by 4 poets, in one century**. That difference is the
      whole point of the corpus.
      Spelling variants are folded before counting: Arabic ي ك ة for Persian
      ی ک ه, and harakat stripped, because editions mix them. The zero-width
      non-joiner is treated as a letter, so می‌رود is one word.
      Documents with no author or no date are counted and reported, since both
      gaps weaken the evidence every word in them carries.

- [x] **4.5 Link pipeline.** Join word types to lexicon entries to attach
      Latin readings. Unmatched get `latin: null`.
      *Done when:* the coverage number is reported: how many word types linked.
      `murfulu/corpus/link.py`. **Measured on the whole of Ganjoor against the
      45,579-word lexicon: 16,714 of 409,916 spellings (4.1%), but 11,644,767
      of 25,497,189 words of running text (45.7%).**
      Both numbers are reported because they answer different questions. Type
      coverage is how much of the vocabulary we can read; **token coverage is
      how much of the text we can read**, and it is far higher because the
      words we know are the words that occur.
      **The gap is not rare vocabulary.** The most common unlinked spellings
      are و (1.1M), ز, بر, آن, او, چون, بود, چو, ای — grammar words and
      inflected verb forms, which a dictionary of headwords was never going to
      list. Worth knowing before anyone reads 4.1% as a quality figure.
      1,037 spellings have more than one reading. Both are kept with the same
      evidence: the corpus has no vowels and cannot tell مرد the man from مرد
      the dead, so picking one would be a guess.

- [x] **4.6 Query language.** Parse the syntax in [SEARCH.md](SEARCH.md) into
      Elasticsearch queries.
      *Done when:* `*nā`, `stem2:gu`, `type:karnam`, `tag:ja`, `count:1` and
      combinations all return correct results on the fixture corpus.
      `murfulu/search/query.py`. All five, and the combinations, verified
      **against a live 8.17.1 cluster** with a fixture index — not only as
      generated JSON.
      `*nā` becomes a **prefix query on `latin_reversed`**, which is why that
      field exists: *ends with* is otherwise a leading wildcard. Persian input
      is detected and searched against the spelling instead of the Latin,
      because someone typing روش means the spelling.
      `count:1` is exactly once — the hapax query — not "at least once".
      A century range matches any **overlap**, so a word used 9th–12th is
      inside a 10th–11th search.
      Nine kinds of unreadable query are refused by name: an unknown field, a
      count that is not a number, a century running backwards, two patterns at
      once, a bare `*`, unbalanced quotes.
      The `*nā` search returns *Sanā* as well as *Tonoknā* and *Derāznā*, which
      is correct and is exactly why SEARCH.md splits results into "formed with
      this affix" and "merely ends in these letters". That split belongs to the
      derivations index, not to the parser.

- [x] **4.7 Fill the `documents` and `word_types` indices.** Found while
      building 6.1: **nothing writes either one.** 4.3 creates the indices,
      4.4 counts the word types and 4.5 links them, but all of it stays in
      memory — only `derivations` has a writer
      (`murfulu/search/derivations.py`, task 5.2). So `/search` has nothing
      to search on real data.
      Mirror the derivations writer: bulk into `<alias>-<version>`, swap the
      alias only when the run is complete, report anything rejected.
      *Done when:* a full ingest fills all three indices and `*nā` returns
      real hits through `/search`. Blocks 6.4.
      `murfulu/search/ingest.py` and `writer.py`, run by
      `tools/run_ingest.py`. The batching, the versioned index and the
      rejected-document reporting moved into `writer.py`, shared by all three
      indices, so the derivations writer stopped being a special case.
      **The whole of Ganjoor in 41 seconds: 133,148 poems and 411,166 word
      types.** More word types than spellings (409,916) because a spelling
      with two readings is two documents — مرد the man and مرد the dead carry
      the same evidence and are not merged.
      `*nā` now returns **57 real hits** through `/search`, and they are
      exactly the mixture SEARCH.md predicted: *Pahnā* and *Ravšanā*, formed
      with the affix, sitting beside *Fanā*, *Bonā* and *Minā*, which merely
      end in those letters. Separating them is task 6.4.
      **A bug this caught:** the route was reporting Elasticsearch's default
      10,000-hit counting cap as the total. "How many words are hapaxes?" came
      back 10,000; the answer is **222,859**. Counted exactly now, with a test.

- [x] **4.8 A corpus version whose analyser keeps every word.** The
      `documents` index analysed Persian with Lucene's stock `persian`
      analyzer, **whose stopword list holds رفت، گفت، شد، بود** — the commonest
      verb forms in the corpus and precisely the words this project is made of.
      Recorded in session 7, fixed here as a **new corpus version**; v1 was
      never touched.
      *Done when:* `/word` for بود and رفت returns quoted citation lines
      through the running stack, and the layout tests still pass.
      Both do. Measured on the two indices side by side, with the same query:

      | `match_phrase` on `text_fa` for رفت | poems |
      |---|---|
      | `documents-v1`, stock `persian` | **0** |
      | `documents-v2`, `persian_every_word` | **10,636** |

      `murfulu/search/mappings.py` defines the analyser and every index carries
      it in its settings. It is the stock chain **minus two things**, and the
      second was not in the original diagnosis:
      **no stopword filter**, for the reason above — a stopword list serves
      relevance ranking in a search engine, and here every word is evidence;
      and **no zero-width-non-joiner character filter**, because the stock one
      maps the ZWNJ to a space, which makes می‌رود two tokens and گفت‌وگو
      three, while `corpus/wordtypes.py` counts each as **one** word. An
      analyser that disagreed with the counting could not find the line a count
      came from.
      What is kept is the rest: lower-casing, Arabic-Indic digits, and the
      Arabic and Persian normalisations, which fold ي ك ة and strip harakat —
      the same folding `wordtypes.normalise` does, in the opposite direction.
      Direction is irrelevant because the text and the query go through the
      same analyser.
      **The whole v2 pipeline: 133,148 poems and 411,167 word types, 43
      seconds**, plus a 59-second precompute for the affix map, which
      reproduced v1's figures exactly (1,573 word types traced to a rule,
      3,691 refused as homographs). `documents` and `word_types` serve v2;
      `derivations` stays on v1 until task 5.7 rebuilds it.
      Four tests hold it: one that no mapping may name the stock analyzer,
      one that all four swallowed words survive tokenisation, one that a
      ZWNJ-joined word stays a single token, and one that indexes a line and
      finds it by phrase query.

- [x] **2.7 The Persian side of a join.** Found by reading the output as a
      writer would: the Behnevis forms were right and the Persian spellings
      were not. *Zandegi* was written **زندهی**.
      *Done when:* the join is spelled as Persian spells it, and the effect on
      attestation is measured.
      `murfulu/engine/glides.join_fa`, corpus version **v4**.
      **Two faults, and the second was not in the diagnosis.** The base's
      silent ه did not drop before a گ; and the گ was **not in the Persian at
      all**, because only the *y* glide had ever been carried across. The
      module already guarded that drift for *y* — گوش against گویش — and
      nobody had asked about *g*.
      **Silent is decided by the Latin.** شاه ends in ه and its ه is a
      consonant, because *šāh* ends in *h*. Reading the Persian letter alone
      would turn شاهگان into شاگان.

      | | v3 | v4 |
      |---|---|---|
      | joins spelled wrong | 38,932 | **0** |
      | attested forms | 24,197 | **24,482** |
      | rules with an attested output | 156 | **158** |

      **The net +285 hides the shape of it: 1,609 gained, 1,324 lost, and both
      are corrections.** Gained: زندگی (4,571 occurrences), مژگان (3,977),
      زندگانی (3,489). Lost: *Šaegi*, which with no گ came out as **شاهی** and
      matched شاهی, "kingship" — a real word, and a different one. A missing
      letter does not only fail to match; it matches the wrong thing.
      Marked unconfirmed and registered as FOR_THE_LINGUIST L7. The test that
      recorded the old wrong answer said the day it was fixed it would say so;
      it now asserts تازگی.

## Phase 5 — Scoring and precompute

- [x] **5.1 Attestation lookup.** Batched. Three levels: reading, spelling,
      none.
      *Done when:* a known word returns `reading` and a novel one returns
      `none`.
      `murfulu/scoring/attestation.py`. Both pass, and the answer never says a
      word does not exist — only "not found in corpus *X*", carrying the
      version, because a count is only true for the corpus that produced it.
      **A fourth distinction was needed inside `spelling`,** found by running
      it on the real corpus. گفتار is written 4,813 times and is plainly a real
      word, but the lexicon has no entry for it, so the reading cannot be
      confirmed and the level is `spelling`. That is a **gap in the dictionary**,
      not a doubt about the word, and it must not look the same to a reader as
      مرد, where the corpus really does read the spelling another way.
      `spelling_unlinked` separates them and `describe()` words them
      differently. Three levels stay three, as ARCHITECTURE specifies.

- [x] **5.2 Derivation precompute.** Apply every rule to every applicable
      lexicon entry, steps 1–2, check attestation, write `derivations`.
      **First run covers verbs (1,752) plus verified nominals (3,519) only** —
      about 508,000 step-1 forms, all from 100%-reviewed input. Sizes are
      measured in [LEXICON_ANALYSIS.md](LEXICON_ANALYSIS.md); extending to all
      38,173 nominals (~4M forms) is a later decision.
      *Done when:* the first run completes and reports run time and output
      size.
      `murfulu/scoring/precompute.py`, run by `tools/run_precompute.py`,
      written to Elasticsearch by `murfulu/search/derivations.py`.
      **The first run: 5,208 readings in, 1,849,284 forms built, 1,738,711
      words written, 28 seconds, 1.62 GB.** With the corpus pass and the write
      it is 61 seconds end to end and peaks at 4.2 GB.
      Two numbers came out different from the estimate and both are recorded in
      [LEXICON_ANALYSIS.md](LEXICON_ANALYSIS.md) §6: the pool is **5,208
      readings, not 5,271 rows**, and depth 2 is **1.85 million forms, not the
      508,000 of depth 1**.
      **1.4% of what the grammar allows was found attested** — 1,824 forms
      confirmed at reading level, 22,337 more at spelling level. **A first
      rough measurement, not a result** (FINDINGS 2026-08-12): the rules are
      unconfirmed, most hits are spelling-level, the corpus is poetry only.
      What the project rests on is that the measurement can be made.
      **29 of the 195 active rules never fired**, each for a stated reason: 9
      stem rules are a different operation, 16 are compounding, which
      [ARCHITECTURE.md](ARCHITECTURE.md) deliberately never precomputes, and 4
      need pronouns or prepositions, which this pool has none of. Task 5.3 has
      to say so rather than report a productivity of zero.
      Merging happens across the whole lexicon, not per entry: **439,078 words
      are built more than one way**, and writing one document per form without
      that merge would have been silent data loss. The merge is keyed on the
      whole path rather than the rule chain, which recovered 95,021 paths that
      a chain-only key was dropping.
      **10,270 words have two Persian spellings under one Behnevis reading.**
      Both are kept — see OPEN_QUESTIONS item Q.

- [x] **5.3 Rule productivity.** Baayen P per rule from the precompute, plus
      hapax counts, stored per corpus version.
      *Done when:* every rule has a measured P, and rules whose measured value
      disagrees with the authored `strength` are listed.
      `murfulu/scoring/productivity.py`, run by `tools/run_productivity.py`,
      which reads the precompute back through `murfulu/scoring/reload.py` and
      writes one row per rule to `rule_productivity-<corpus_version>.json`.
      Every row carries the corpus version, the lexicon snapshot and the
      rule-pack version, because none of the numbers means anything without
      them.
      **Every rule in the pack gets a row. 166 of 195 were measured; the other
      29 carry the reason they could not be** — a stem rule is a different
      operation, compounding is never precomputed, and four rules need word
      classes this pool has none of. A rule that built forms nobody ever wrote
      is measured **at zero**, which is a result; a rule that never fired has
      no rate at all. The two are not the same and are not shown the same.
      **156 rules have a Baayen P, 70 have one over confirmed readings only.**
      P is very small throughout (median 0.0069, and 0.0002 over confirmed
      readings), so the realisation rate — attested built forms over all built
      forms, Monakhov's measure — carries the signal here.
      **Two artefacts were found and are now counted, not described.** Five
      rules score near the top because their output is the same string as
      their input: three zero-affix rules (*Parhiz* is just the stem written
      as a noun) and *-an*, which rebuilds the very infinitive the generation
      started from. `echo_share` reports it, so a rate of 0.77 can be read
      next to an echo share of 1.00 and understood.
      **Only 3 of 195 rules carry an authored `strength` at all**, and all
      three disagree with the measurement. That is the finding, not a
      shortcoming of the method — see FINDINGS and OPEN_QUESTIONS item R.

- [x] **5.4 Sister forms.** For each rule, the attested outputs.
      *Done when:* rule 10 returns *Goftār*, *Raftār*, *Didār* if they are in
      the corpus.
      `murfulu/scoring/sisters.py`. **All three come out of the real corpus**,
      and V-010 has **52 attested outputs** in all.
      Ordering is by strength of evidence, not frequency: a **confirmed
      reading** first, then how many separate documents, then occurrences.
      *Didār* leads (confirmed, 4,434 poems, 212 poets) ahead of *Goftār*,
      which occurs 4,813 times but only at spelling level because the lexicon
      has no entry for it. That is the right order — see UPSTREAM B2.
      **156 rules have at least one attested output.** The per-rule list is
      the artefact; copying a handful onto each of the 1.7 million words as
      well is the denormalisation ARCHITECTURE asks for, and it is measured:
      eight sisters per word costs **380 MB**, taking the run from 1.62 GB to
      2.0 GB. `--sisters 0` turns it off.
      A word reachable by two rules gets the sisters of both, because it
      belongs to two families.
      This task also caught the stored record **losing four fields**: the
      first and last century, the unlinked flag and the other readings were
      never written, so a derivation read back could not draw its own
      dispersion chart and could not tell a dictionary gap from a homograph.
      All four are stored now, and the round trip is pinned by a test.

- [x] **5.7 Put the ground and the semantic part into the index.** Both were
      computed per request in `/generate` and stored nowhere, so search and the
      rules screen could not use them and every reader of the index saw less
      than a build screen did.
      *Done when:* a derivations document read back carries both fields, and
      the run time and size are reported.
      `base_attested` and `semantic_typicality` (with `semantic_bases` beside
      it) are written by `murfulu/scoring/precompute.py`, a new run over corpus
      **v3**. Read back from `derivations-v3`: *kifā* carries
      `base_attested: true`, `semantic_typicality: 0.7688`,
      `semantic_bases: 402`.

      | | |
      |---|---|
      | run time | **34.8 s** for 1,738,928 words |
      | index | **444.1 MB** at rest, against 431.4 MB for v1 — the two fields cost about 13 MB |
      | dump | 2,074 MB of JSON lines |
      | stand on written ground | **279,106**; 1,459,822 do not |
      | carry a semantic part | **595,135**, from the 57 rules with a centroid |

      **Two things the batch had to do differently from the live route, and
      both are in the record rather than smoothed over.**
      **Grounding needs a second pass over everything**, because written ground
      is the *whole run's* attested forms and no record can be judged until the
      last one has been looked up.
      **A stored path keeps the base of its last step only**, so it can answer
      the grounding question at one and two steps and no further — which is
      what the precompute runs. `grounding.stored_grounded` returns a third
      answer, `None`, for a path deeper than that: *not established*, never
      `False`, because a stored `False` would say the corpus was asked and
      answered no. At depth 2 nothing came back unsettled.
      **The semantic part is asked of the first step**, whose base a stored
      path does not keep either — so the run carries the first step's rule and
      base while it merges, and drops them. The cosine is 1,024 multiplications
      in plain Python against 1.7 million records, so it is memoised on
      `(rule, base)`: the same stem enters the same rule again and again.
      **A missing field is *not measured*, never a low score**, and neither
      field is written as a null. The artefact is passed in rather than picked
      up from the environment, so nothing writes a score into the index because
      a variable happened to be set.

- [x] **5.8 The wider test of the 93%.** The go/no-go pilot ran on three
      rules. Run it over every rule with a centroid and record the table.
      *Done when:* the leave-one-out table for all 57 is in
      [RESEARCH_SCORING.md](RESEARCH_SCORING.md).
      It is, with `build/pilot-v3.md` behind it. Board: 57 rules, 2,025
      attested words, at most 40 per rule and at least 6, doubted claims left
      out. **25.4% strict against 1.8% chance, and 64.0% counting a rule with
      the same affix as right.**
      **The strict figure is the wrong number to quote and the run says why.**
      35 of the 57 rules share their affix with another rule on the board —
      V-070 to V-073 are all *vā-* — and those 35 score 105 of 1,266 strictly
      while reaching 90% on the same-affix score. Nothing in a word's meaning
      separates *-an* the infinitive from *-an* the noun; the output class
      does, and no vector was asked about it.
      **On the 22 rules with an affix of their own it is 53.9%**, 409 of 759.
      That is the figure to carry forward.
      **What separates the good rules from the bad is not the model.** *nā-*,
      *-ande*, *-tar*, *-gar* each do one thing to one kind of base and score
      80–88%. *-nā*, *-na-*, *-nā-*, *-ā* are short, collide with each other
      and with Arabic endings, and score 0–15% — the same collision the affix
      backfill refuses *Fanā* over.

- [ ] **5.5 Composite score.** Combine rule strength, productivity and
      attestation. Weights in config, not code.
      BLOCKED on semantic scoring — see 5.6.
      *Done when:* every derivation carries the score parts separately.
      **A second blocker, found while building 5.3.** One of the three
      non-semantic parts barely exists: the source grammar states a `strength`
      for **3 of 195 rules**. So "combine rule strength with productivity"
      has almost nothing on the strength side, and the hybrid RULE_PACK.md
      proposes — authored strength as the prior, measured P as the evidence —
      has no prior for 192 rules. Either the linguist authors them or the
      measure stands alone, and that decision precedes the weights.
      See OPEN_QUESTIONS item R.
      The other two parts are built and measured: attestation (5.1) and
      productivity (5.3), both stored per corpus version.
      **And as of 2026-08-17 the two of them do rank together**, in the live
      route rather than in the index: 9.13 orders a deep answer by attestation
      first and then by the median productivity of the chain. That is not this
      task — nothing is stored, the weights are an order rather than numbers in
      config, and strength is still absent — but it is the first evidence about
      how the parts behave beside each other, and it says the productivity side
      carries a deep list on its own.

- [ ] **5.6 Semantic plausibility (FRACSS).** Affix matrices trained on
      attested stem→derived pairs. See [RESEARCH_SCORING.md](RESEARCH_SCORING.md).
      **BLOCKED on one decision, and it is a smaller one than it was.**
      Researched and measured 2026-08-12 — OPEN_QUESTIONS S6.
      **Two of the three blockers are answered by measurement.** Vectors need
      not be trained on our own Latin forms: keying on the Persian spelling
      costs **6.2%** — 1,037 of 16,714 linked spellings have two readings —
      and the engine composes both spellings anyway. And the bound-stem worry
      is smaller than it looked: **1,753 of 1,930 stem forms (90.8%) occur as
      corpus word types**, because the past stem is also the 3sg past and the
      present stem is the imperative.
      **The go/no-go pilot ran and answers go** (2026-08-13,
      `tools/semantic_pilot.py`): BGE-m3 vectors averaged over our own corpus
      lines separate affix families at **93% against 33% chance** — no
      training, no downloads, the sister project's model. It also caught the
      sister lists of *-dān* and *-stān* being contaminated by plural-ان
      homographs (شاهدان is not شاه + -dān), which is a fault in the affix
      backfill's claims worth having found.
      **The first slice is built and live (2026-08-13).**
      `tools/build_semantic_vectors.py` writes base vectors and per-rule base
      centroids for the **57 rules with ≥10 attested pairs**;
      `murfulu/scoring/semantics.py` reads them; `/generate` carries a
      `semantic` part per form and the build screen shows it and uses it as
      the last tie-breaker. Unmeasured is null and never low; validation
      against the feedback set remains the gate before it is more than a hint.
      **What is left is which measure**, and it is a real question. A 2025
      study on Malay found the **affix centroid** fitted human judgements
      better than FRACSS *and* needs no base vector — which matters here,
      because **76.8% of our attested pairs have a bound stem as the base**.
      But a centroid scores a word that exists, and this project makes words
      that do not.
      **What no choice can fix, measured by `tools/count_semantic_pairs.py`:**
      only **63 of 195 rules have a single attested pair**, 22 have 200 or
      more, and on confirmed readings alone only **7** clear fifty. A per-affix
      semantic model is possible for a few dozen rules and no more.

## Phase 6 — API

- [x] **6.0 Postgres schema.** The authored side: rules loaded from YAML,
      expert feedback, users and roles, corpus versions. Alembic migrations,
      never hand edits. Blocks `/feedback` in 6.1, all of 6.3, and 8.1.
      *Done when:* `alembic upgrade head` builds the schema in the `db`
      container and a feedback row can be written and read back.
      Both pass: `docker compose run --rm api alembic upgrade head` builds
      **seven tables**, and a linguistic verdict written through
      `murfulu/db/feedback.py` comes back with its Persian note, its captured
      context and its corpus version intact.
      `murfulu/db/` — `config.py` (URL from `MURFULU_DATABASE_URL`, never a
      literal), `base.py`, `models/`, `session.py`, `feedback.py`,
      `rulesync.py`. One migration, `migrations/versions/0001_authored_schema`.
      **`expert_feedback` is append-only in the database, not by agreement.**
      The migration installs a trigger that refuses every UPDATE and DELETE,
      and a test proves both are refused. This table is the only human work in
      the system no job can recreate, and it is the evaluation set the scoring
      weights will be fitted against.
      Three things the schema encodes rather than leaves to a caller: a
      linguistic verdict may only come from an **expert**; a graded verdict
      and the `linguistic` category **imply each other**, so a bug report
      cannot carry one and a verdict cannot go ungraded; and feedback about a
      lexicon entry or a stem derivation is marked `owner: karbon`
      automatically, because we mount that lexicon read-only and cannot fix
      it.
      **No `derivations` table was created**, and this is a correction to
      [ARCHITECTURE.md](ARCHITECTURE.md) rather than an omission. That
      document lists one under Postgres *and* says every live result is cached
      in the `derivations` **index**. Only one can be true. By its own rule —
      if losing it means re-running a batch job it goes in Elasticsearch — a
      cache is not authored data, and the index already exists and is written
      by task 5.2. Task 6.2 writes to the index.
      `rules` mirrors the loaded `Rule` field for field, not the shorter list
      ARCHITECTURE sketched: a rule takes several input types, carries several
      tags and gives several examples, and flattening them would lose what the
      YAML already holds. A test loads the real pack — **195 rules and 17
      glide rules** — reads V-010 back and compares it with the YAML. Loading
      twice updates rather than duplicates, and an id in the database the pack
      no longer mentions is **reported, never deleted**: rule ids are
      permanent, so one that vanished is a fault, not a tidy-up.
      Migrations are linted and type-checked like the rest of the code, and a
      live test fails if a model is ever edited without a migration.

- [x] **6.1 Routes.** `/generate`, `/search`, `/word/{id}`, `/explain`,
      `/rules`, `/affixes`, `/corpus`, `/feedback`. Thin — no logic.
      *Done when:* OpenAPI docs render and integration tests pass in Docker.
      **All eight are built** — `murfulu/api/rules.py`, `generate.py`,
      `search.py`, `feedback.py` — plus `/rules/{rule_id}`. OpenAPI renders and
      names every one, and a test lists the eight the plan asks for so none can
      quietly go missing. No route holds logic, and a test asserts it.
      **2,471 tests pass inside the container**, against the real Postgres and
      the real Elasticsearch, with nothing skipped.
      `/feedback` waited on 6.0 and now has it. POST appends; GET reads by
      target or by owner. **There is no route that edits or withdraws a
      record**, and a test asserts that too: the store is append-only and an
      HTTP surface that quietly allowed otherwise would defeat the trigger
      underneath it.
      **The route does not authenticate anybody.** The caller names an
      account, which is looked up and must be active; nothing yet checks that
      the caller is who they say. That is 6.3, the app is local-only until
      then, and the route's own docstring says so — a feedback record naming
      the wrong author is worse than no record, because the set is the
      evaluation set.
      Two things this task settled by measurement rather than assumption:
      **`/search` takes no index parameter.** Every field the query language
      names — `stem1`, `type`, `rule`, `author`, `count` — is a `word_types`
      field. Offering `derivations` as well would have let a query that can
      never match look exactly like one that found nothing.
      **The two-group result split has no data to work on yet.** SEARCH.md
      splits hits into *formed with this affix* and *merely ends in these
      letters*, and only the first needs `word_types.affixes` — which the
      mapping declares and **no pipeline fills**. The route does the split
      honestly, so today everything lands in the second group. Task 6.4.

- [ ] **6.2 Live generation with cache.** Steps 3+ generated on request and
      written back to `derivations`.
      *Done when:* the second identical request is served from cache.
      **Half of this happened on 2026-08-17 without being planned.** 9.13 put
      three steps in front of a reader, so steps 3+ *are* generated on request
      now — ranked and paged, a thousand forms in 1.3s. What is still missing is
      the cache: every request rebuilds the whole 17,717 and throws all but a
      thousand away. So the remaining question is only the storage half below,
      and the latency it would save is now measurable rather than assumed.
      **BLOCKED on two design decisions, both of which change stored data.**
      Measured first, against the real lexicon, because the answer turns on
      what the cost actually is:

      | | |
      |---|---|
      | رفتن at depth 2 | 510 words |
      | رفتن at depth 3 | **15,479 words, 0.2 s** |
      | رفتن at depth 4 | 22,952 words, 0.3 s |

      **Generating is not the expensive part.** The space saturates — depth 4
      adds only half as much again as depth 3 — and the whole of depth 3 is
      built in a fifth of a second. What costs is checking each form against
      the corpus and writing it. So a cache that avoids re-generating saves
      almost nothing; a cache that avoids re-attesting and re-writing saves
      nearly everything.

      1. **What does a cache hit return?** The stored `paths` keep the rule
         ids, the affixes and the glide ids, but **not** the base at each
         step, the *ow → av* stem form, or the glide alternatives — the
         fields `/generate` shows today, one per step. So either the stored
         path grows those fields, on all 1.7 million documents, or a cached
         answer explains itself less fully than a fresh one, which
         contradicts ARCHITECTURE's own constraint 6.
      2. **How do live results reach the index without damaging it?** The
         precompute merges across the whole lexicon — 439,078 words are built
         more than one way — so writing a live record by the same id would
         replace a merged record with a single-source one and drop its sister
         forms. Writing only what is absent keeps the index safe but leaves
         the older forms unmarked, so the cache cannot find them again.
         Attestation is a third part of the same question: `scoring/attestation.py`
         is an **in-memory** index built from a full link pass, and a live
         request has no such pass — it needs a lookup against `word_types`,
         which does not exist yet.

- [x] **6.3 Auth and roles. REVERSED 2026-08-17 — one account, no roles.**
      The project lead's call: a reader needed the site password to see
      anything and an expert token to answer anything, and that is one
      credential too many for a research app with one reviewer. The password
      wall in front of the whole site is the authentication now, and everyone
      behind it may grade, propose and rule. Migration `0008` drops
      `api_tokens` and the `role` column; `murfulu/db/site.py` is the single
      account and makes itself on first use.
      **`users` stays with one row**, because feedback, rulings and proposals
      are append-only precisely so a judgement keeps its author — dropping the
      column would have discarded that on nine stored records. The account
      adopts the oldest existing one rather than adding itself beside it, so
      the history does not split at the upgrade.
      **What it costs is inter-rater agreement**, and that is written into
      REVIEW.md and into the dataset manifest rather than left to be
      discovered: the export's per-author pseudonym is what let two reviewers'
      verdicts on one word be compared, and there is one rater now. Records
      made before today keep their own authors.
      The original entry follows, for the record.

- [x] **6.3 Auth and roles.** User and expert roles.
      *Done when:* an expert verdict is rejected for a normal user.
      It is — over HTTP, against the real containers: **401** with no token,
      **403** for an account with the `user` role, **201** for the same
      verdict from an expert. The refusal now depends on the token, not on
      what the request body claims; `/feedback` no longer accepts an author
      field at all.
      **API tokens, not passwords.** The app is API-first and local
      ([ARCHITECTURE.md](ARCHITECTURE.md)), so a token is issued once, pasted
      in, and revoked when it is done with. Nothing has to hold a password,
      reset one or expire a session, and a login screen can later sit on top
      of the same accounts. Only the SHA-256 of a token is stored: the token
      is 256 bits from the operating system's random source, so it is not
      guessable and not reused anywhere, and a password stretcher would add
      cost without adding safety. That reasoning is written next to the code,
      because it stops holding the moment a human-chosen secret is stored.
      **A token is revoked, never deleted**, and an account is disabled,
      never deleted — feedback is append-only and names its author, so a
      credential that vanished would leave records pointing at nothing.
      Several tokens per account are allowed on purpose: a browser and a
      script are different things to hold one, and either can be withdrawn
      alone.
      `murfulu/db/auth.py`, `murfulu/api/auth.py`, migration `0002`, and
      `tools/manage_accounts.py` for creating accounts and issuing tokens.
      The rule *only an expert may leave a linguistic verdict* stays in the
      store, so it holds however a record arrives; what the API adds is
      **who is calling**.

- [x] **6.4 Write derivations back onto word types.** After the precompute,
      fill `word_types.affixes`, `rule_ids` and `semantic_tags` for the
      spellings a derivation matched, so a suffix search can say which hits
      were *formed* with the affix rather than merely ending in it.
      *Done when:* searching `*nā` splits *Tonoknā* from *Sanā* on real data.
      `murfulu/search/backfill.py`, produced by `run_precompute.py
      --affix-map-out` and consumed by `run_ingest.py --affix-map`. It goes
      into a **new corpus version**, never onto the live index.
      **`*nā` now splits 57 hits into 5 and 52.** The five are *Derāznā*,
      *Farāxnā*, *Karnā*, *Ruhinā* and *Yāninā*, all by N-072, all rare
      (1–16 occurrences). The 52 include *Fanā* (4,315) and *Bonā* — Arabic
      loans where *-nā* is not an affix at all.
      **Only a confirmed reading may claim a word.** The first version also
      claimed spellings the lexicon has no entry for, on the argument that
      گفتار is obviously *goft* + *-ār*. The real corpus refuted it: that rule
      attached *-nā* to **مولانا، نخلنا، لقینا and eighty more Arabic phrases**
      ending in the possessive نا. An unlinked spelling means the dictionary
      knows nothing about the word — including whether it is Persian.
      Those 10,877 are kept as **proposals**, never written to the index, and
      they are now the strongest form of the request in UPSTREAM B2: a word in
      real use, with the rule that would form it, and no entry to confirm it.
      **1,573 corpus word types are traced to a rule, 3,690 refused as
      homographs.** The confirmed number is low partly for a reason worth
      sending upstream: the lexicon reads پهن as `pen` while reading its own
      پهنا, پهنه and پهناور as *pahn-*, so a real word cannot be linked to the
      rule that forms it. 2,437 bases show that shape — UPSTREAM A3.

- [x] **6.5 Homograph contamination in the affix backfill.** The pilot found
      the sister lists of *-dān* and *-stān* contaminated: **شاهدان is the
      plural of شاهد, not شاه + -dān**, and no letter-level check can tell.
      Use the semantic vectors as the detector; measure the distribution and
      pick nothing by hand.
      *Done when:* a measured report in docs with counts and examples, suspect
      claims flagged in the sisters and the affix map rather than silently
      kept, and the *-dān*/*-stān* lists visibly cleaner.
      `tools/flag_homograph_claims.py` and `tools/homograph_fit.py`, run over
      corpus v3. Full working in
      [RESEARCH_SCORING.md](RESEARCH_SCORING.md); the per-rule table is
      `build/homograph-report-v3.md`.
      **The obvious detector was built, measured and refused.** A claim's
      cosine to its own rule's centroid is 0.811; to every other rule 0.780,
      with a standard deviation of 0.05 apiece. The two distributions overlap
      almost entirely and the first run flagged **100% of claims**. So both
      statistics became **ranks** — what share of the candidates a claim has
      nothing to do with fit the word better — where the null is uniform by
      construction and the cut is where the claim density falls to it. Nothing
      is chosen by hand, and the uniformity is checked: a constructed null has
      a median of 0.495.
      **Two checks, because the first is blind exactly where it is needed.**
      A rule whose claims are mostly homographs has a centroid *made of* them,
      and *-dān* is such a rule — rule fit doubted nothing in it. **Base fit**
      — the word against the word it was built from — needs no centroid, works
      per claim, and is what catches شاهدان (84% of other bases fit it better
      than شاه) and لهستان, which is Poland.
      **Measured: 3,613 of 16,627 checkable claims doubted, 21.7%, across 108
      of 120 rules.** The affix map falls from **1,573 word types traced to a
      rule to 1,397**; the `*nā` search's *formed with this affix* group drops
      *Karnā*, a trumpet, and keeps four.
      **Nothing is deleted.** A doubted sister is ranked last and still
      attached; a doubted claim is held out of `word_types.rule_ids` — which is
      an assertion, and what puts a word in the search screen's *formed with
      this affix* group — and recorded in the map's `contested` list. A cosine
      is not a ruling.
      **What cannot be checked is said out loud:** a claim needs two corpus
      lines to average, so 16,627 of 27,276 could be measured at all, and
      *-dān* keeps twelve one-occurrence entries nobody has measured.

## Phase 7 — Frontend

React SPA. See [FRONTEND.md](FRONTEND.md) for screens and design rules. Mobile
first, Persian RTL, Persian digits, minimal.

- [x] **7.1 Shell and design system.** RTL layout, font pair, colour tokens,
      spacing scale, LTR islands for Latin. Test at 375 px.
      `web/` — Vite, React, TypeScript in strict mode. **36 component tests and
      25 layout tests pass**, the image builds, and `docker compose up` serves
      the app at `WEB_PORT` with deep links and the `/api` proxy both working
      against the live API.
      **375 px is a test, not a look.** jsdom has no layout engine, so it
      cannot tell you a row overflows a phone screen or a target came out
      31 px tall. Playwright loads every screen at 375 px and at desktop
      width and checks that nothing pushes the page sideways, that every
      navigation link is at least 44 px, that the last one is reachable, and
      that the layout really is right-to-left.
      **It found two bugs a component test could not.** The skip link sat half
      above the top edge when focused — an arithmetic error between a negative
      `top` and a percentage transform — so a keyboard user's first stop was
      half off screen. And the navigation, which scrolls at 375 px because six
      items do not fit, was cut off flat at the edge, which reads as clipped
      text rather than as "there is more this way"; it now fades.
      **The first version of the skip-link test passed while the bug was
      there**, because it asked whether the element intersected the viewport at
      all. It now checks the whole box, and polls, because the link slides in.
      What the shell is made of: the design system is **tokens**
      (`styles/tokens.css`) and a test fails if a stylesheet names a token
      nobody defined or writes a colour that is not one. **Logical properties
      only** — a test rejects `margin-left` and friends, because a
      right-to-left layout built by mirroring breaks the first time a
      component is nested.
      **`Latin` is the component the interface leans on.** Persian runs one
      way, a Behnevis form the other, and they share a table cell; without
      `dir` *and* `unicode-bidi: isolate` the punctuation around a form jumps
      to the wrong side. It also refuses to lower-case, because *Porsidan* and
      *porsidan* differ by nothing else.
      Numerals go through `Intl` rather than a digit-swapping table: past a
      thousand, Persian has its own grouping, and every corpus count is past a
      thousand.
      **No Persian about the grammar is written in a component.** `Term` takes
      the term, the explanation and the traditional name as props. Nothing
      supplies them yet — OPEN_QUESTIONS S3.
- [x] **7.2 Search screen** with facets and the two-group result split.
      `web/src/screens/search/`, built against the **real corpus** — 133,148
      poems and 411,166 word types ingested, and `*nā` returning its 57 real
      hits through the running stack. 51 component tests and 27 layout tests,
      one of which runs a real search end to end and skips rather than fails
      where no corpus has been ingested.
      **The query lives in the address bar**, so a search can be linked to,
      bookmarked and reloaded.
      **The two groups are the reason the screen exists**, and an empty first
      group says *we have not worked out which of these were formed this way*
      — never *none were*. Today it is always empty, because filling it needs
      the affix map from 6.4 to have been run for this corpus version. The two
      sentences are not the same claim and the screen does not merge them.
      **The facets count the whole result set, not the page.** That needed a
      change on the API side: `/search` now returns aggregations, in the new
      `murfulu/search/facets.py`. Counting the returned page would have given
      a figure that changes with the page size and looks exactly like a real
      one — the same trap as the 10,000-hit cap in 4.7.
      A facet **narrows the query rather than filtering behind the scenes**: it
      writes the term into the box. There is one way to express a search, and
      the reader learns the syntax by using the interface.
      **The examples are shown left to right, as syntax to be copied.** With
      `dir="auto"` the same query in two scripts — `*nā` and `*نا` — puts the
      asterisk on opposite sides, and one of them gets copied wrongly.
      The category shown is the **dictionary's own**, in its own Persian. The
      mapped word class would need a glossary nothing serves yet —
      OPEN_QUESTIONS S3.
- [x] **7.3 Word detail** with dispersion chart and citations.
      `web/src/screens/word/`, plus the API side it needed: `/word/{id}` now
      returns **every reading of the spelling** and **the actual lines**.
      59 component tests and 29 layout tests, two of which run against the
      live corpus.
      **Citations are one line per poet.** Thirty occurrences in one poem is a
      rhyme; one each in thirty poets is a word — so Elasticsearch collapses
      on the author and the reader sees as many different voices as there are.
      `murfulu/search/citations.py` finds the line with the same folding the
      counting used, or a citation would sometimes fail to find the word in
      the very poem its count came from.
      **The chart states what it cannot show.** *Ravšanā* is written 22 times
      and only 2 of those are dated, so the screen says so under the bars
      rather than drawing 2 and letting it stand for 22. A century inside the
      span with no occurrences is drawn as a gap, because the hole is the
      evidence. A word with nothing dated gets no chart and a sentence saying
      why.
      **Readings are not merged**, and the one being read is not repeated in
      the list of others.
      Building it found a real fault in the corpus — see 7.3's note in
      FINDINGS and OPEN_QUESTIONS N: **27 of the century table's 43 entries
      name a poet slug this corpus does not use**, so فردوسی and 26 others are
      undated. Not repaired, because it is not mechanical; now reported
      instead of silent.
- [x] **7.4 Build screen** with grouped results, nested paths. **Go-deeper is
      not built** — see below; it belongs to 6.2.
      `web/src/screens/build/`. 68 component tests, 31 layout tests, and a
      live one that builds رفتن through the whole stack. رفتن gives **510
      words**, of which **2 are confirmed at reading level and 61 at spelling
      level** — possible against attested, now visible on a screen (a first
      rough measurement, not a result: FINDINGS 2026-08-12).
      **Generated forms carry their evidence.** That needed the read half of
      what 6.2 will need: `murfulu/search/attested.py` asks `word_types` about
      every form in one query, and fills the **same** `Index` the batch job
      uses, so the three levels of evidence cannot drift between the pipeline
      and a live request. Writing live results back is still 6.2.
      **Four states of evidence, never merged**: not checked (the corpus was
      not asked), reading, spelling, and *not found in corpus v1* — never
      "does not exist", and the version travels with the sentence.
      **Ranked by evidence, never by depth**, as ARCHITECTURE requires.
      Alternative derivations are kept and nested under the form.
      **Groups are named in Persian by what traditional grammar calls the
      class** — اسم, صفت, اسم مصدر — served from `/rules`, which now returns
      the word-class table. **The project's own coined terms are not in the
      data at all**; they exist only in the design documents, and
      transliterating them is a linguistic act, so nothing here writes them.
      OPEN_QUESTIONS S3 now has a number attached to it.
      **Go-deeper is refused for a measured reason, and the screen says so.**
      رفتن at depth 2 is a 0.5 MB answer; at depth 3 it is **24.7 MB** —
      15,479 words, each carrying its derivation. The answer has to be paged
      before it can be offered, which is part of the same open question as
      caching it. See OPEN_QUESTIONS S1.
      A live layout test caught a real fragility on the way: the client took
      the whole screen down with a `Cannot read properties of undefined` when
      the running API was one version behind the code. It degrades now.
- [x] **7.5 Affixes by meaning.**
      `web/src/screens/affixes/`. **The question the project started from is
      now one screen and one look:** *which affix carries the meaning «جا»?*
      — **five of them**, with their examples: *-ān* (بیابان، گیلان), *-dān*
      (نمکدان), *-stān* (گلستان), *-kade* (میکده), *-gāh* (سحرگاه، دانشگاه).
      The meaning is the heading and the affixes sit under it, because a
      writer arrives with a meaning. The reverse would be a grammar book with
      the index at the back, which is the thing this replaces.
      **Every Persian word on the screen comes from the rule pack** — the
      gloss, the affix's Persian spelling, the examples. No component writes
      any of it.
      **81 of 189 affixes carry no meaning in the source**, and they are shown
      in a section of their own that says so. `/affixes` returns them under
      `without_a_meaning` rather than as a group with a blank name: hiding
      them would leave a reader believing the inventory is complete, and
      mixing them in would let them believe those affixes had been checked and
      found to mean nothing. **43% of the affix inventory is unglossed** — a
      number the linguist's gloss-template work (OPEN_QUESTIONS E) can now be
      sized against.
      76 component tests, 33 layout tests.
- [x] **7.6 Explain.** The *sāzāyi* check — and it did not exist in any form,
      so building it was the task rather than putting a screen on something.
      `murfulu/engine/decompose.py` proposes, `murfulu/analysis.py` verifies,
      `/explain` gained a `word` parameter, and
      `web/src/screens/explain/`.
      **Every account is rebuilt forward, and only what reproduces the word
      survives.** That round trip is the whole design: stripping *-nā* off
      *Mowlānā* leaves a word the dictionary knows, and a decomposer that
      stopped there would announce a famous Arabic name as a Persian
      derivation. It is refused, and so is *Fanā*.
      **Nothing chooses between survivors.** *Ravandegi* comes back with six
      accounts and *Raveš* with two — it can be built from *raftan* or from
      *ravidan*, and which is meant is a question about meaning, not letters.
      Four measurements shaped it, each fixing something:

      | | |
      |---|---|
      | naive stripping, 8 known words | **1 of 8** |
      | + looking stems up, not only headwords | 4 of 8 |
      | + trying both capitalisations | 6 of 8 |
      | + stripping recursively | **7 of 8** |

      Each step was a real fault. Half the words the grammar builds are built
      on a **stem**, and a stem is a column on the verb, not an entry — so
      `Lexicon.by_stem` had to exist. **Capitalisation belongs to the result,
      not to the base**: the engine computes it from the output class, so
      *Raftār* strips to *Raft* and the entry is *raft*. And one level of
      stripping is not enough, because *Ravandegi* strips to *ravande*, which
      is in no dictionary — it is itself built.
      **Measured on 200 real corpus words with a reading: 14% get an account,
      at 12 ms each.** That is not a shortfall. Most words are simple or
      borrowed, and a checker that explained 90% of them would be inventing.
      The screen says what it tried rather than implying the word is malformed.
      Known limits, none guessed at: *Dānešgāh*, *Guyāyi* and *Tonoknā* are
      not accounted for — their bases are themselves derived beyond two steps,
      or the glide is not reversed. Recorded rather than papered over.
- [x] **7.7 Rules screen.**
      `web/src/screens/rules/`, and the pipeline behind it, run here for the
      first time this session: the precompute (**1,738,711 words, 29 s,
      2.0 GB**) and the productivity roll-up. Both reproduce the figures from
      task 5.2 and 5.3 exactly.
      **The disagreements are at the top, because they are the finding.** The
      source states a strength for **3 of 195 rules** — V-010, V-011, V-012,
      all *-ār*, all *typical* — and all three land in the **top** band when
      measured against a thousand years of poetry, where *typical* would put
      them in the middle. The screen calls that a finding, not an error, as
      FRONTEND.md asks.
      **A rule measured at zero and a rule nobody could measure are drawn
      differently**, and the second carries its reason. 29 of 195 could not be
      exercised by this run at all — stem rules are a different operation,
      compounding is never precomputed — and a zero there would be a result
      the run never established.
      Productivity is read from a file the batch job wrote
      (`MURFULU_PRODUCTIVITY_PATH`), never recomputed per request: a figure
      that changed between two page loads would not be a measurement. When no
      run has happened the screen says so rather than showing zeros.
      91 component tests, 37 layout tests.
      **A second test made the same wrong assumption as the ones fixed
      earlier** — it asserted no `derivations` alias existed, which was only
      true on a machine that had never run a precompute. It now asserts what
      it meant: that writing does not move the alias.
- [x] **7.11 The semantic centre on the rules screen.** A rule's centroid was
      used to score words and shown nowhere, so the one screen about rules
      could not say what *typical of this rule* means.
      *Done when:* each rule shows its centroid's size and its typical bases,
      served from the artefact, with nothing invented in a component.
      In the expanded row, under **پایه‌های شاخص**: *the average of 50 written
      bases*, then the eight nearest that average with their Persian spelling
      and their Behnevis reading. V-001 (*-āndan*) gives رو، جه، رس، خو، دم،
      گرد، گیر، ست — verbs of motion and holding, which is what an *-āndan*
      causative is made from, and a reader can now disagree with that.
      **The ranking is done where the vectors are.** The artefact carried a
      centroid and a count and no way to know *which* bases belonged to a rule
      — its vector table is pooled across all of them — so
      `tools/build_semantic_vectors.py` now writes the eight nearest bases per
      rule. The component computes no cosine and writes no Persian about
      meaning: a count, and words the batch job chose.
      **A rule with no centroid says so.** 57 of 195 have one, and a blank row
      would read as *this rule has nothing typical* rather than *nobody has
      measured it*.

- [x] **7.8 Corpus screen** with coverage.
      `web/src/screens/corpus/`, and the artefact behind it:
      `murfulu/corpus/report.py`, written by `tools/run_ingest.py
      --report-out` and read by `/corpus`. 10 component tests, 3 layout tests.
      **The obvious implementation was measured and refused.** Asking
      Elasticsearch for the sizes is wrong twice over and both ways look
      right: `cardinality` is an estimate, so "distinct spellings" comes back
      **409,500** against a true **409,916**; and `word_types` holds one
      document per *reading*, so summing `total_count` gives **29,288,852**
      words of text instead of **25,497,189**. Neither error announces itself.
      So the figures are counted by the batch job, which held the corpus in
      memory, and read by the app — exactly as the rule productivity is. They
      reproduce task 4.5 exactly: **16,714 of 409,916 spellings (4.1%),
      11,644,767 of 25,497,189 words of running text (45.7%)**.
      **Both shares are drawn, side by side.** Anyone shown only the 4.1%
      would take it for a quality figure, and it is not one.
      `--report-only` counts and links without touching an index, so a version
      already in service can be described without being rebuilt. A report
      about another corpus version is labelled, never passed off as current.
      **What the evidence does not cover is on the screen:** 98,627 of 133,148
      poems carry no century — **74.1%** — so the word screen's dispersion
      chart rests on a quarter of the corpus, and the 27 century-table entries
      that match no poet are named. OPEN_QUESTIONS N was recorded and invisible
      until now.
      **The unmatched pile is shown, not summarised away.** 393,202 spellings,
      biggest first, with the sentence that stops it reading as a fault list —
      the largest are و (1.1 million), ز, بر. The whole list leaves as a file
      (`--unlinked-out`, 8.2 MB); no screen shows 393,202 rows.
      A layout test caught **85 px of page overflow at 375 px** from one
      element: the lexicon snapshot id inside `Latin`, which refuses to break.
      That refusal is right for a word form and wrong for an address, so the
      screen passes a class that lets an identifier wrap.
- [x] **7.9 Feedback widget**, present on every screen. See [REVIEW.md](REVIEW.md).
      `web/src/feedback/` — the button is in the **shell**, so it is on every
      view and no screen owns it. 9 component tests, 4 layout tests, plus one
      run end to end against the real containers: a verdict left in the
      browser comes back out of Postgres with its Persian note and its
      captured context.
      **The category is chosen first and the form adapts**, because a graded
      verdict does not fit "this button does nothing" — and the pairing is
      enforced three times over, in the form, in the route and by a check
      constraint in the database.
      **The account is asked once, when the panel opens.** That needed one new
      route, `/me` (`murfulu/api/accounts.py`), which reports the role and
      nothing else. Without it the only way to find out whether somebody may
      grade a word is to let them write a note in Persian and then refuse it
      with a 403. It answers *who am I*, never *who else is there*.
      **Two ways to say what is being judged**, because a record naming the
      screen instead of the word is nearly useless: a screen declares its own
      subject with `useSubject`, and any row can hand over its own with the
      `Judge` button — wired into every built word and every rule. The route
      and the query are added automatically, so a screen cannot forget them.
      **A token is pasted in, not a password**, matching 6.3: it is kept in
      `localStorage` so a reviewer working through a list does not paste it on
      every page, and reading the app needs none.
      **Running it found a case the design had not stated:** the corner button
      on a screen that declares no subject is about the app, and *is this app
      good, possible or wrong* is not a question. A linguistic verdict is now
      refused for the app itself, with the reason on screen — REVIEW.md maps
      the app to a bug report.
      **The optional screenshot is not captured**, and that is stated rather
      than quietly skipped: it needs the mounted volume `screenshot_ref` points
      into, and no such volume exists. See OPEN_QUESTIONS S4. The structured
      context — the reusable half — is captured in full.
- [x] **7.10 Accessibility pass.** WCAG 2.1 AA.
      Two halves, because neither finds what the other does.
      **The palette, computed** (`web/src/styles/contrast.test.ts`): every text
      colour against every ground the app paints, with WCAG's own formula.
      A page can pass an audit by not happening to put two colours together;
      the palette either has the ratio or it does not.
      **Three real failures, all fixed by measurement.** `--ink-faint` — every
      count, every caption — was **4.19:1** on white and **3.91:1** on the sunk
      ground, under the 4.5:1 AA asks. `--line` was **1.26:1** and it was the
      border of every input, which is the only thing saying where to type
      (1.4.11 asks 3:1). And the check itself was too narrow: it tested two
      grounds, and the app paints **three** — the tinted panel behind a finding
      is darker than the sunk grey, where the darkened `--ink-faint` still sat
      at 4.24:1. The page audit caught that one; the palette check should have,
      and now does. `--ink-faint` is `#676d78`, and control edges have a token
      of their own, `--line-strong`, separate from the merely decorative rule.
      **The pages, audited** (`web/tests/accessibility.spec.ts`): axe-core
      against `wcag2a`, `wcag2aa`, `wcag21a` and `wcag21aa`, on all seven
      screens at phone and desktop width, and on the parts behind a click —
      the feedback panel, an expanded rule, a derivation opened out. **32
      checks, no violations.**
      **One more real fault it found:** the unmatched-pile table scrolls, and a
      scrolling box that nothing can focus is a box a keyboard cannot scroll.
      The rows past the fold existed for a mouse only.
      **And what axe cannot check is written out**, because those are the
      failures a reader hits first: every screen reachable by keyboard alone,
      focus visible wherever it lands and not only on the first stop, the
      feedback panel operable from the keyboard, every `aria-label` actually in
      Persian, the document declaring its language and direction, and a page
      title that says which screen it is.

## Phase 8 — Round-trip and release

- [x] **8.1 Rule proposals.** Expert edits stored as proposals, exported to
      YAML, reviewed as a git diff.
      `murfulu/db/models/proposals.py` and migration `0003`, the store in
      `murfulu/db/proposals.py`, the applying logic in
      `murfulu/rules/proposals.py`, the routes in `murfulu/api/proposals.py`,
      and `tools/export_proposals.py`. 23 tests.
      **Run end to end against the containers:** a proposal made over HTTP came
      out as **one changed line** in `rules/verb_stems.yaml`, reviewable as a
      git diff, and was then refused with `git checkout rules/`.
      **The whole method rests on one measured fact:** the pack round-trips
      through PyYAML byte for byte, on all four tables, so an applied proposal
      shows as the line it changed and nothing else. A test pins it — if a
      dump setting ever drifted, every diff would be two thousand lines and
      nobody would read one.
      **Nothing is applied silently.** Every proposal ends in one of four
      states and three of them are reasons not to write: *applied*, *already in
      the pack*, *the rule moved underneath it* — which would silently revert
      whoever changed it, and is the reason a proposal stores the old value at
      all — and *no such rule*.
      **A closed set of fields**, defined in `rules/` because the pack owns
      what its own fields are and enforced by a check constraint in the
      database. Not the id, which is permanent; not the source row, which is a
      fact about the document; not the input and output types, which change
      what the engine does rather than what the grammar says.
      **No request can write to the repository**, and a test asserts it: the
      route stores a row, the command writes the file. A browser with a write
      path into the grammar could change it without anyone reading the change.
      **Running it found a gap nobody had noticed.** `murfulu/db/rulesync.py`
      was written with task 6.0 and **nothing outside the tests ever called
      it**, so the live `rules` table was empty and the first real proposal
      failed on the foreign key. `tools/sync_rules.py` now exists; the route
      answers 503 naming it, instead of returning a page of SQL.
      **Refusing a proposal does not yet stop it coming back** — see
      OPEN_QUESTIONS S5. Nothing is lost, the export just gets noisy.
- [x] **8.2 karbon mirror.** Command exporting the rule pack and opening a
      pull request against karbon.
      **The export is built; no pull request is opened, and the command cannot
      open one.** Sending a change to somebody else's repository is the project
      lead's, and a test asserts that neither file contains the means to do it.
      `murfulu/rules/mirror.py` and `tools/mirror_to_karbon.py`. 12 tests.
      **The mirror is byte-identical, plus a manifest**, and defining it that
      narrowly is the whole design. DECISIONS settles *one master, one mirror*
      — and that is only a real arrangement if anybody can tell whether the
      mirror is current. Copying rather than transforming makes that a
      comparison either repository can run without loading anything or
      agreeing on a schema. A transformed export would need its own version,
      its own tests, and a way to tell a transformation bug from a stale copy.
      **Seven files: everything the loader reads**, so karbon can load the copy
      with the same code. The manifest carries the rule-pack version, the
      commit it came from, a hash per file, and the sentence that stops
      somebody editing the copy.
      **`--check` exits 1 when the copy is stale** and names each file as
      *missing*, *differs* or *extra* — the last one being drift, a file added
      to the copy that the master does not have.
      **A new commit alone does not make the mirror stale.** The manifest names
      the commit, which is worth keeping, but the content decides; otherwise
      every commit here would report karbon's copy as out of date and the
      check would be ignored within a week.
      Run against a scratch directory, not against the karbon checkout: that
      repository is under review and CLAUDE.md says not to modify it.
- [x] **8.3 Feedback export** as a dataset.
      `murfulu/db/dataset.py` and `tools/export_feedback.py`. 16 tests, and a
      run against the real Postgres.
      JSON Lines plus a `README.md` manifest saying what the records are, what
      is in them and what deliberately is not. Persian is written as Persian,
      not as escapes: a dataset nobody can read in an editor is a worse one.
      **No account name leaves.** The author is a stable pseudonym —
      `author-2` — which is all inter-rater agreement needs, and the role
      travels beside it because *only an expert may grade a word* is a fact
      about the record's weight.
      **The manifest claims no licence.** 8.4 is blocked on that decision, and
      a guess in a file that leaves the project would be worse than the gap. A
      test asserts no licence name appears.
      **`--owner karbon` is the share that goes upstream** — feedback about the
      lexicon and about stem derivations, which we mount read-only and cannot
      fix. Marked, never dropped.
      **An empty store is a legitimate result**, not an error: it is the state
      this project is in until the reviewers have used the app, and the command
      says so rather than writing an empty file that looks finished.
      **Exporting found a rule the schema had never enforced.** Two stored
      records grade *the app* — and *is this app good, possible or wrong* is
      not a question; REVIEW.md's own table maps the app to a bug report. The
      widget refuses it (7.9) and now the store does too, so it holds however
      a record arrives. The two existing rows stay: the table is append-only.
- [x] **8.4 Licence and release.** DONE 2026-08-17. **Apache-2.0**, the project
      lead's choice: anyone may use it, with credit, and there is a patent
      grant. `LICENSE` is the canonical text with only the appendix placeholder
      filled; the copyright holder is *The Murfulu Project* rather than a
      person, because this repository is going public and names no individuals.

      **The work was in what the licence must not reach**, and `NOTICE` says so
      for each:

      | | |
      |---|---|
      | the corpus | Ganjoor's poetry. Their FAQ, asked whether the data are copyright-free, answers «لزوماً خیر!» — no legal review has been made, most of it was typed from published books whose own status was never established, and free access is not a licence. Their *service* is GPL-3.0; the poetry is not covered by it. |
      | the lexicon | karbon's, mounted read-only. Its terms are karbon's question. |
      | the feedback set | judgements experts made about the language. Not code, Apache is not a licence for data, and they were not given to us to hand on. |

      **The manifest guessed no licence while this was open and must not
      acquire one by inheritance now that it is closed.** 8.3's test asserted
      no licence name appeared; it now asserts the code's licence is named
      *only* in a sentence that excludes the records — every line mentioning
      Apache must also say "not". Saying "the repository is Apache" and letting
      a reader draw the obvious conclusion would be the same fault as guessing,
      one step further along.

---

## Phase 9 — The loop queue

Written 2026-08-14. Phases 0–8 built the system; this is what is left over
once it works, ordered so that a session can open this file and start.

**These are ordered for a reason.** 9.1 makes three written-but-dormant fixes
live, and everything measured afterwards is measured on the corrected index.
9.2 is quick and its faults are real. 9.3 is the one that keeps paying off.

**The loop is 9.1 to 9.5, and it was run on 2026-08-15.** All five are done
bar the half of 9.5 that S11 blocks. What it found on the way is the section
**What phase 9 left behind**, at the end of this file. 9.6 and 9.7 stay
deferred on the project lead's word — the first because running the coining
loop by hand is still finding faults faster than building it would, and this
session is more evidence of that, the second because upstream work goes in
batches when he says so.

Nothing here needs the linguist. Anything that turns out to need a ruling is
`BLOCKED` with the question, and the rule from the top of this file applies:
**never guess a design decision.**

- [x] **9.1 Corpus v9.** DONE 2026-08-15. Three fixes are written and dormant, because a
      derivations version was built before them: `rule_chain` is now the set
      of rules that build a word, and `affixes` and `glide_rules` still carry
      the same defect it had — the shortest path alone.
      **Fix the other two first**, in `scoring/records.py`, the same way and
      with the same tests. Then build v9 by the six steps in
      [ENGINEERING.md](ENGINEERING.md), which are written out in the order
      they must run.
      *Done test:* `tools/compare_versions.py --report --derivations` shows the
      five release figures unmoved and no rule's output count changed; the
      three aliases serve v9; `/corpus` says v9 after a container rebuild;
      and a record reached two ways names every rule in `rule_chain`.
      **Re-run `tools/measure_compounding.py` and
      `tools/measure_typicality_spread.py` against v9** — both write files
      named for a corpus version and neither is carried forward.

- [x] **9.2 The pack faults the coining run surfaced.** DONE 2026-08-15 — three fixed with tests, one checked and pinned, one filed with the number that stops it. Each was reproduced
      through the API and none is fixed. In rough order of clarity:
      **V-052** is filed `kind: suffix` with affix `-andar` and its own
      example, `andarāmadan`, is a prefix — the generator does what the pack
      says and the pack is wrong.
      **Prefix stacking is unbounded**: depth 4 from اندیشیدن builds
      `farāzfarāzfarāzandišidan`.
      **V-059 and V-060 are both `farāz-`** with different tags, so identical
      strings come back twice under two rule ids.
      **A derived infinitive is never re-stemmed**: V-062 builds
      `hamandišidan` and its stems are never taken, so `hamandišande` and
      `Hamandišandegi` are unreachable by any route.
      **`na-` on an infinitive keeps the whole infinitive** — `nāhamandišidan`,
      labelled barnam — while the rule's own example, `nāšenās`, is on the
      present stem.
      *Done test:* each either has a fix with a test, or a line in
      OPEN_QUESTIONS saying which of the three piles in 9.3 it belongs to and
      why it cannot be fixed here.

- [x] **9.3 Sort the 75 examples the pack cannot rebuild.** DONE 2026-08-15. 88 of 163 rebuild
      and are pinned by `tests/example_baseline.json`; 61 do not rebuild at
      all and 14 rebuild through a rule other than the one that lists them.
      Extend `tools/check_examples.py` to record, for each failure, **what the
      engine did build from the same base** — that is what separates *the
      engine is wrong* from *the two spell the same word differently*, which
      is the difference between a bug and a question for the linguist.
      *Done test:* every one of the 75 carries a pile; the engine-is-wrong
      pile is fixed with tests and the baseline grows; the other two piles are
      written into FOR_THE_LINGUIST as one question with its list, not 75
      questions.
      **Outcome.** Every failure carries a pile and **the engine-is-wrong pile
      is empty**. It was 7 — V-070 to V-076 dropped the infinitive ending — and
      fixing it, with the two 9.2 rulings, took the pinned examples from **88
      to 100 of 163**. The rest: 22 the lexicon has no base for (B2), 21 a
      vowel disagreement (**L13**, one question with its list), 15 a base held
      in another word class (3.2), 5 an example not using its own rule's affix
      (**L14**). The piles needed two corrections before they meant anything —
      case, because stripping a prefix leaves *kenār* where the lexicon holds
      *Kenār*, and evidence, because a consonant skeleton matches *div* to
      *Dāv*: a spelling disagreement is claimed only when the rule then builds
      the expected word bar its vowels.

- [x] **9.4 Clean the karbon gap list before it is sent (UPSTREAM B2b).** DONE 2026-08-15. The
      list of words karbon does not hold is inflated by inflected forms, and
      `corpus/inflection.py` reads those apart already.
      *Done test:* a cleaned list with the count before and after, ready to
      quote in a pull request. Opening the pull requests is 9.7 and is the
      project lead's.

- [x] **9.5 The small route gaps.** DONE 2026-08-17. `/compound` was done
      2026-08-15; `/explain` was blocked on S11 and S11 is now answered — the
      route **looks a Persian spelling up** and analyses **every** reading, so
      کنار comes back as *Kanār*, *Kenār* and *Konār*. Never transliterated: a
      guess measured 5.8% correct, and would put a wrong base under a real
      chain. A spelling the lexicon does not hold is still refused and the
      message now gives that as the reason.
      **It buys less than it looks like, and that is measured**: of 20 derived
      words a reader would plausibly paste, the lexicon holds 9. Half the
      refusals, not all of them.
      **Two other faults on the same route were fixed with it** — the
      `explained` flag is `rebuilt` and carries the base's own corpus evidence
      (S21), and an unfinished search no longer reports itself as a refusal
      (`settled`), which was 5.8% of empty answers at three steps.
      *Done test:* `/compound` pages the way `/generate` does, with the same
      three fields on the answer.

- [ ] **9.6 The coining prototype (S16).** NOT NOW — the project lead's call,
      2026-08-14. It is unblocked and it is not the next thing worth building:
      the loop already works when it is run by hand, and running it by hand is
      what keeps finding faults in everything else. Left written down rather
      than deleted, because the reason it is deferred is timing and not doubt.
      When it is picked up: compounds are served
      and the build route is pageable. The loop is four existing calls and the
      one rule that matters is that **it must put its own proposals back
      through `/explain` or `/compound` before showing them** — that alone
      caught five of eight in the first run.
      *Done test:* a tool that takes a meaning and returns candidates, each
      with the rules that build it, its corpus count, and whether the system
      could reproduce it. **L10 is the ceiling**, not a blocker: the model
      supplies the sense the pack cannot.

- [ ] **9.7 Open the karbon pull requests.** NOT NOW — the project lead's
      call, 2026-08-14, and UPSTREAM has always said they go in batches on his
      word and never unasked. Fifteen items are waiting; A7 and B2b were added
      2026-08-14. 9.4 still prepares the gap list, because a batch that is
      sent later is still sent cleaner.

---

## Open questions that block specific tasks

| Task | Question |
|---|---|
| 3.2 | Which word class does each lexicon category map to? Needs expert input for the unclear ones. |
| 5.2 | Should already-compound entries (44% of the lexicon) feed the compounding rules? Not in the first run either way. |
| 5.5, 5.6 | ~~Which semantic measure~~ **ANSWERED 2026-08-17 (S6): all three, but not until the feedback set (8.3) exists to judge them against. 65 of 195 rules have any attested pair; 79.0% of pairs have a bound stem as base.** |
| 8.4 | ~~Which licence~~ **ANSWERED 2026-08-17: Apache-2.0.** |
| 1.3 | Behnevis joining rules — ZWNJ, joined prefixes, glide *y* → ی — still to be extracted from the specification. |
| 9.1 | ~~What `rule_chain` should be called~~ **ANSWERED 2026-08-17 (S19): `built_by`. No alias kept; takes effect at the next corpus version.** |
| 9.5 | ~~Should `/explain` accept the Persian spelling~~ **ANSWERED 2026-08-17 (S11): yes, by looking it up, and every reading.** |
| 9.7 | Are the upstream items ready to send? |

---

## What phase 9 left behind

Written 2026-08-15, at the end of the session that ran 9.1 to 9.5. **The loop
is finished; these are what it found.** None of them was on the queue when the
queue was written, which is the argument for running it by hand again.

- [x] **9.8 Look up a word by its second reading (S22).** DONE 2026-08-15, approved the day it was found. `by_latin` matches
      the `phonemic` column alone, so **7,106 of the 7,181 second readings the
      snapshot records cannot be found by any lookup** — کنار is *Kanār* or
      *Kenār*, and asking for *Kenār* gets a 404. Generation already builds
      from every reading (question P); lookup never got the same treatment.
      **Not started on purpose:** it changes what every route returns for 7,181
      words, so it wants the project lead's word and a version to be measured
      against. It also caps 9.3's *base is not in the lexicon* pile, which is
      an upper bound while this stands.

- [x] **9.9 Decide what makes the gap list sendable (S23).** DONE 2026-08-15 — restricted to what our rules can build, 4,519 words. 9.4 took the
      inflections out and the head of the list is still و, ز, آن, او — **60 of
      the biggest 100 are three characters or fewer**. Either B3's function-word
      list is settled or the request is restricted to the spellings our rules
      can build. 9.7 cannot open the B2 pull request until one of the two.

- [x] **9.10 Give a prefixed verb its stems (9.2's leftover).** DONE
      2026-08-17. *hamandišidan* was built and nothing could be built from it,
      so *hamandišande* was unreachable by any route. A prefixed verb is now
      entered through its prefixed stems, and *bāzguyande* — بازگوینده, one who
      retells — comes back with it.

      **Filed as multiplying generation by 13; measured at 1.40**, on 40 real
      verbs at depth 2 and depth 3 alike, so the derivations file would go to
      roughly 2.7 GB rather than 25. The ×13 was the cost of giving *every*
      built verb its stems, and that cannot be implemented at all: a verb coined
      by a suffix — *tars* giving *tarsidan* — has a present stem written
      nowhere, and guessing one would be inventing a stem. Restricted to
      prefixes, where the stems are the ones underneath with the prefix in
      front, nothing is invented. **So this was a bug fix wearing the costume of
      a corpus-scale decision.**

      **Nothing has been rebuilt.** The app builds the new words on request; a
      v10 corpus is still the project lead's call, and now costs 1.4× rather
      than 13×.

- [ ] **9.14 A score for a word nobody has written.** Raised 2026-08-17 by
      9.13, and the reason 9.13 had to reach for a second-best measure.

      **The semantic score cannot speak about a deep word, by construction.** A
      base's vector is the mean of BGE-m3 embeddings of up to six *corpus lines
      using the word* — meaning-in-use, which is what made the pilot work at
      93% against 33% for chance. A word nobody has written has no lines, so it
      can never have a vector. Measured on اندیشیدن at depth 3: **the first
      step's base has a vector 17,679 times out of 17,679; the last step's base
      has one twice.** 2,245 bases are covered in all, and 57 rules.

      So typicality is measured on the first step alone — deliberately, and the
      code says why — and 12,999 of a verb's 17,717 forms therefore share **22
      values** between them, in ties two thousand deep. It cannot order a deep
      list and was never built to.

      **What would change that, and neither is plumbing.** Embed the coined
      word's *spelling* rather than its usage; or compose its vector from the
      vectors of its parts. Both give up "as the poets used it", which is the
      principle the current design rests on and the reason it validated. A real
      research question, and the natural place to fit it against the expert
      feedback set (task 8.3) rather than against the corpus.

      **What is in place meanwhile** is 9.13's realisation figure, which asks
      about the rules rather than the words and so has something to say where
      the vectors have nothing. It is a stand-in, not a rival: wherever the
      semantic score *can* speak it remains the better measure.

- [x] **9.13 Offer depth 3 on the build screen, or 9.10 is invisible.**
      DONE 2026-08-17. Three steps are offered; the route ranks and then pages;
      the screen asks for the best thousand and says how many of how many it is
      showing. *hamandišande* — the word 9.10 exists to reach — went from
      **10,551 of 17,717 to 676**, and *vāguyande* from 9,590 to 994.

      **Withheld on the ranking, not on the paging.** The note capping this at
      two steps blamed the size, and the route has paged since 6.2. The real
      blocker was that a page of an unranked list is a random handful: at three
      steps only 50 of 17,717 words are ones the corpus has, so the ordering
      *is* the feature.

      **The criterion added is how often each rule on the chain produces a word
      the corpus has**, summarised by the median. Not the weakest link: *ham-*
      realises 0.04% and *-ande* 21.8% in the same word, and on the weakest link
      the good chain and the nonsense one are within 2× of each other where on
      the median they are 180× apart. An unmeasured rule — 33 of 195 — counts
      as the median of the measured ones, because *not measured* is never a low
      score.

      **A thousand is measured, not picked.** The band worth reading is the
      attested words plus the new ones whose every step is written: 542 for
      اندیشیدن, 843 for گفتن, 2,183 for رفتن. Six hundred covered one of the
      three. A thousand is 2.0 MB and 1.3s, against the 3.94 MB this screen
      already asks for at two steps. رفتن's band still runs past it, which the
      screen says rather than hides.

      **One decision left deliberately unmade.** The new criterion sits *below*
      grounding. Above it, *hamandišande* ranks 189 rather than 676 — and
      grounding is unreliable for exactly this family: it marks False even for
      بازگوینده, which the corpus contains. Reversing a decision already taken
      and written down is the project lead's, so it is recorded and not done.

- [x] **9.12 Attach the evidence to the five questions that only described
      it.** DONE 2026-08-17. L5, L7, L8, L9 and L12 each rested on a
      measurement written out in prose, with a hand-typed sample of four rows or
      nothing at all. All five re-run; **four reproduce their own figures
      exactly** — L8's 28,148 forms, 2,252 attested and *Dideé* at 33,599 among
      them, out of `derivations-v4`, which is still in Elasticsearch and is the
      only reason a measurement about two since-retired rules could be
      reproduced rather than re-taken.

      **L7 could not be reproduced, and that is the useful one.** Its "before"
      state is in no index. Rebuilding both spellings from the rule and putting
      both to the corpus found what the original measurement did not say: the
      rule **creates** collisions as well as removing them — دیه + گر gives
      دیگر, 22,212 occurrences, a different word. Now in front of the linguist,
      in the same column as the gains.

**And the standing lesson of the session, which is not a task.** The rule pack
is generated, and three rulings had been edited into the generated files
instead of into `rules/decisions.yaml`; re-running the builder reverted all
three without a word. `tests/test_rule_pack_build.py` now fails if the
committed pack is ever not what the builder writes. **Anything that looks like
a hand edit to a generated file is a decision that has not been recorded.**

- [~] **9.11 A place in the app for the linguist to answer.** Built 2026-08-15
      and 2026-08-16. Only the Persian wording is left. Today the questions for the
      linguist live in `docs/FOR_THE_LINGUIST.md` and are answered in one
      conversation at the end of a session — which works for us and asks him to
      read Markdown in English, in a repository, in a language he does not work
      in. He works in Persian.
      **The idea is that the app carries the questions and he answers them
      there**, the way the expert reviewers already give graded verdicts
      through it. There is machinery to build on: `/feedback` and the proposals
      store both already take a verdict from a signed-in expert and hold it.
      *Open first:* is this the same thing as the expert-review flow with a
      different question attached, or a second flow beside it? And does an
      answer given in the app become the record — which would make
      FOR_THE_LINGUIST an export rather than the source. **Not started; needs
      the project lead to say which.**

      **Settled and built the same day.** Separate flow, and the ruling given
      in the app is the record — both the project lead's word. Two tables with
      the rulings append-only behind a trigger, `/questions` open to anyone
      signed in and `/questions/{ref}/ruling` to an expert, and
      `tools/export_rulings.py` in both directions. All 15 questions are seeded
      out of the document. 25 tests.
      **Two roles, not three.** A `linguist` role was built for this and taken
      out again on 2026-08-16 before anything was committed: the expert *is*
      the linguist. karbon's maintainer gets no role either — they never sign
      in, and their answers belong on their own issue tracker.

      **The screen is built** (2026-08-16, `/questions`). Persian first and
      largest, the English underneath as a gloss, the evidence behind a
      disclosure beside the question it belongs to, and blocking questions
      marked. A reader is told they cannot answer **before** they write one,
      from `answering_as` on the response, rather than losing a ruling to a 403.
      A second ruling is offered rather than hidden, with a checkbox saying it
      reverses the first — a reversal that does not announce itself reads as
      though the grammar had always said this. 9 screen tests.

      **Three renderings, not two** (2026-08-16). A question and a ruling each
      carry Persian, **Behnevis** and English. Murfulu works in Behnevis and
      never in raw Arabic script, and every example inside a question — *šāhvār*
      against *šāhevār* — is already written in it, so a question readable only
      in Persian is written in the one form the project does not hold. The
      screen shows Persian first, Behnevis under it, English last; the answer
      form takes all three and requires only the Persian.

      **The Persian is written** (2026-08-16), at length, each term explained
      where it is used. **Two questions are withdrawn**: L4, which was a list of
      other questions rather than a question, and L11, which was *answered* —
      karbon's dictionary is «واژه‌نامهٔ کاربن» on every screen, the project
      lead's call, built the same day. **L16 was added 2026-08-17**, out of
      9.10. **Fourteen are open, and every one carries its evidence as files**
      — 24 of them, and none is a description of a file (9.12).

      **The remaining risk is the terminology, not the Persian.** This project
      has its own grammar vocabulary — kārvāže, kārbon-e yek, barnām, nām — and
      a question about morphology that reaches for ordinary Persian words
      instead may be answered as a different question, with nothing on our side
      able to tell. Drafting is ours, checking is the project lead's, and each
      draft names where a term was guessed. Seeding could not have done this:
      translating our English automatically would have made it the original,
      which is the failure this whole change exists to fix.

      **What is left is the linguist's answers, and a token so he can sign
      in.** `docs/FOR_THE_LINGUIST.md` is still hand-written; running
      `tools/export_rulings.py --out` turns it into an export of the store.
