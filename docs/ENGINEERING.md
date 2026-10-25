# Engineering standards

**Status: agreed.** 2026-08-11. These are rules, not suggestions.

## Docker

Everything runs in containers. `docker compose up` starts the whole system on a
clean machine with no other setup.

- one service per container: `api`, `web`, `elasticsearch`, `db`, `ingest`
- no host dependencies beyond Docker itself
- `.env.example` committed, real `.env` never
- batch jobs run as one-shot commands in the `ingest` image, not as scripts on
  the host
- images pinned to exact versions, never `latest`
- **a healthcheck names `127.0.0.1`, never `localhost`.** In the web image
  `localhost` resolves to `::1` alone and nginx's `listen 80` binds IPv4, so
  the check was refused every ten seconds for as long as the container ran
  while the site served 200 throughout. `web` is a `depends_on` target with
  `condition: service_healthy`, so a service added downstream of it would
  never have started.

## Building a corpus version

**Write the command down here every time it changes.** It was not recorded
before v6, and rebuilding cost twenty minutes of reading v5's own output to
work out which flags had produced it — which flags were defaults, how many
sister forms had been kept, which suspect-claims file had been fed in. The
same failure as `MURFULU_GANJOOR_PATH` missing from `.env.example`: the
pipeline was reproducible in principle and not in practice.

**Both variables are host paths that no container gets.** Set them on the
command with `env`, never `export` — the compose file reads the shell
environment before `.env`, so an exported `MURFULU_*` hands the container a
host path and `/generate` answers 500.

**The recipe below assumes the development stack, and the deployed one is not
it.** Found 2026-08-20 while trying to rebuild against the running site. Every
step talks to Elasticsearch on `localhost:9200`, which `docker-compose.yml`
publishes and **`docker-compose.prod.yml` deliberately does not** — on a server
a published 9200 is the whole corpus, writable, to anyone who finds the IP. So
against the production stack these commands cannot connect at all, and the
pipeline is reproducible on a laptop rather than where it runs. Whatever the
answer is — a one-shot job inside the compose network, a temporary forward, or
`--out` on the host and a separate write from inside — it is not written down
yet. **Nothing here has been run against production.**

**v12 was the first version built against production (2026-10-17), with a
temporary forward.** A throwaway Caddy container on the compose network,
published on the loopback only, and stopped once the aliases had moved:

```bash
docker run -d --rm --name murfulu-es-forward --network murfulu_default \
  -p 127.0.0.1:9201:9201 caddy:2.9.1-alpine \
  caddy reverse-proxy --from :9201 --to http://elasticsearch:9200
# every step below with MURFULU_ELASTICSEARCH_URL=http://127.0.0.1:9201 added
docker stop murfulu-es-forward
```

Step 6 against production is `docker compose -f docker-compose.prod.yml up -d
--build --no-deps api` (web only if `web/` changed). **Since 2026-10-17 that is
the Mac's fallback stack, not production**: production runs on the server
(DEPLOY.md §0), and a released version reaches it with `deploy/server.sh corpus vN`,
`data` and `deploy` — see DEPLOY.md §0. **The two host paths
moved**: `~/data/murfulu/` no longer exists. v12 read the Ganjoor dump from
`~/Projects/mosaic/mana/data/ganjoor.s3db` and the centuries from
`~/Projects/mosaic/stemma/data/poet_centuries.json`, accepted only after a
`--report-only` run reproduced all five of v11's figures and its lexicon
snapshot id exactly. v12 is v11's recipe otherwise; it exists for L16 (V-003's
verbs entered through their stems), and it also clears the 08-20 affix guard
and spoken-ه forms below: v11 → 08-20 code −32,640 records, all losses;
08-20 code → v12 +51,561 records and +9,335 gained paths, every one through
V-003, nothing lost.

**v13 was built on the server itself (2026-10-18), not on the Mac**, and that
is the recipe from now on. v12's 58 minutes were almost all the copy of
finished indices over the VPN; the inputs are small (lexicon 19 MB, Ganjoor
341 MB, centuries, suspect claims) and rsync's compression moved them in 46
seconds. The build runs as a one-shot container of the deployed `murfulu-api`
image on the compose network — no forward, nothing published — capped at 7 GB
so it can never crowd out Sokhan, with the inputs in `~/murfulu/build/inputs`
(outside `deploy`'s rsync, which excludes `/build`):

```bash
. deploy/host.env                            # MURFULU_SSH_HOST, MURFULU_REMOTE_DIR (DEPLOY.md §0)
rsync -az -e "ssh -F deploy/ssh_config" ~/Projects/mosaic/mana/data/ganjoor.s3db \
  ~/Projects/mosaic/stemma/data/poet_centuries.json build/suspect-claims-v4.json \
  "$MURFULU_SSH_HOST:$MURFULU_REMOTE_DIR/build/inputs/"
rsync -az -e "ssh -F deploy/ssh_config" data/lexicon-20261012.sqlite \
  "$MURFULU_SSH_HOST:$MURFULU_REMOTE_DIR/data/"
deploy/server.sh deploy                     # the image must hold the code being built
# on the server: deploy/build_corpus.sh holds steps 1–3 below with /build paths
docker run -d --name murfulu-build-v13 --memory 7g --memory-swap 7g --cpus 6 \
  --network murfulu_default -v ~/murfulu/data:/data:ro \
  -v ~/murfulu/build:/build -v ~/murfulu/deploy:/deploy:ro \
  murfulu-api:latest sh /deploy/build_corpus.sh v13 lexicon-20261012
```

Steps 1–3 exactly as below with `--corpus-version v13`,
`MURFULU_LEXICON_PATH=/data/lexicon-20261012.sqlite`, the semantic and
suspect-claims inputs still v4's. **16 minutes in all** (precompute 11, ingest
3, productivity and spread 2), with the site serving v12 throughout. Then
`derivations-v13.jsonl` came back to the Mac (rsync, 2.3 GB in about 5
minutes) for step 4, and the release is `deploy/server.sh data` followed by
`deploy/server.sh release v13 lexicon-20261012` (aliases, server `.env`, api).
The comparison is `data/compare-v12-v13.md`: −26,944 records (−1.4%), every
lost and gained path traced to a lexicon row karbon changed —
`tools/attribute_lexicon_change.py` — and none to a row it did not. **The Mac's
Elasticsearch no longer holds every version**: it stops at v12, and v13 lives
only on the server (its `derivations-v13.jsonl` is on both).

**v14 (2026-10-18) is v13's recipe with one rule added: a function word's
letters credit nothing.** `rules/function_words.yaml` (43 spellings, each
closed-class and among the corpus's 200 most frequent — recheck with
`tools/check_function_words.py`, which recounts the corpus and fails
otherwise) is read by `scoring/attestation.py`: a listed spelling answers at
level `spelling` with `function_word` set and zero counts, for the lexicon
entry and for every form written with it, in the batch job and live alike. The
trigger was که, read *keh* by karbon 1.2.0 and credited with the conjunction's
609,699 occurrences. Same inputs, same container, `build_corpus.sh v14
lexicon-20261012`, 15 minutes; but **the image was built without restarting
the app** (rsync as `deploy` does, then `docker compose … build api`), so the
site kept serving v13 on the old code until the comparison was clean. The
comparison adds `--function-words`, which matches the two files record by
record and must read zero on every line marked so:

```bash
.venv/bin/python tools/compare_versions.py \
  --report data/corpus_report-v13.json data/corpus_report-v14.json \
  --derivations build/derivations-v13.jsonl build/derivations-v14.jsonl \
  --function-words
```

Result in `data/compare-v13-v14.md`: records, paths and the five report
figures unchanged; 38 records credited nothing, all on the list; 32 groundings
and 7,118 sister lists moved, all following from them; nothing else.
`word_types` gains 25 documents (a listed spelling's count moves off its
readings onto a document of its own). Released with `deploy/server.sh data`,
`release v14 lexicon-20261012`, then `deploy` for the web.

**The precompute runs first, and this order is not cosmetic.** The ingest
takes the precompute's affix map, so an ingest run before it has nothing to
pass. This file listed the two the other way round until 2026-08-14, and **v6
and v7 were both built and released with no affix map at all** — measured by
counting the field on each version: v4 1,415 word types carry a rule, v6 **0**,
v7 **0**, v8 1,435. Leaving it out does not fail. It builds a `word_types`
index where no corpus word was formed by any rule, so every `rule:` search
answers nothing and a rule that formed a hundred words looks exactly like one
that formed none. The tool now says so out loud, like the century line.

**Step 1 — the derivations.** Six or seven minutes, most of it writing the
2 GB file.

```bash
env MURFULU_LEXICON_PATH="$PWD/data/lexicon-20260808.sqlite" \
    MURFULU_GANJOOR_PATH="$HOME/data/murfulu/ganjoor.db" \
    MURFULU_GANJOOR_CENTURIES="$HOME/data/murfulu/poet_centuries.json" \
    MURFULU_SEMANTIC_PATH="$PWD/data/semantic-v4.json" \
  .venv/bin/python tools/run_precompute.py --corpus-version v10 \
    --out build/derivations-v10.jsonl --elasticsearch --no-release \
    --affix-map-out build/affix-map-v10.json \
    --sisters-out build/sisters-v10-all.json --sisters-keep 0 \
    --suspect-claims build/suspect-claims-v4.json
```

**Step 2 — the corpus and the word types**, taking the affix map step 1 wrote.

```bash
env MURFULU_LEXICON_PATH="$PWD/data/lexicon-20260808.sqlite" \
    MURFULU_GANJOOR_PATH="$HOME/data/murfulu/ganjoor.db" \
    MURFULU_GANJOOR_CENTURIES="$HOME/data/murfulu/poet_centuries.json" \
  .venv/bin/python tools/run_ingest.py --corpus-version v10 --no-release \
    --report-out data/corpus_report-v10.json \
    --affix-map build/affix-map-v10.json
```

**Step 3 — the per-rule figures and the score spread**, which every screen
quoting a number needs. Both read the file step 1 wrote, and both belong to
one corpus version: a spread measured on one says nothing about another.

```bash
.venv/bin/python tools/run_productivity.py --from build/derivations-v10.jsonl \
  --out build/rule_productivity-v10.json
cp build/rule_productivity-v10.json data/rule_productivity-v10.json

.venv/bin/python tools/measure_typicality_spread.py \
  --from build/derivations-v10.jsonl --out data/typicality-v10.json
```

**Step 4 — compare the new version with the one it replaces, before
releasing.** Reading one report tells you nothing; v6 was released because
nobody put it beside v4.

```bash
.venv/bin/python tools/compare_versions.py \
  --report data/corpus_report-v9.json data/corpus_report-v10.json \
  --derivations build/derivations-v9.jsonl build/derivations-v10.jsonl
```

The five report figures, and what they were on a corpus whose text has not
changed since v4 — all five should still read `same`:

| what to compare | v4 … v10 |
|---|---|
| `documents` | 133,148 |
| `tokens` | 25,497,189 |
| `spellings` | 409,916 |
| `spellings_linked` | 16,714 |
| **`documents_without_century`** | **98,627** |

**`--no-release` is deliberate, on both tools.** The aliases stay where they
are until the new version has been looked at, and the previous version stays
queryable until somebody drops it. The precompute gained the flag on
2026-08-14; before that, writing a new derivations version put it into service
in the same breath.

**Step 5 — release, once the comparison checks out.** All three aliases move
together, or two screens quote different corpus versions.

```bash
.venv/bin/python -c "
from murfulu.search.indices import IndexAdmin, connect
admin = IndexAdmin(connect())
for alias in ('documents', 'word_types', 'derivations'):
    print(alias, '->', admin.release(alias, 'v10'))
"
```

**Step 6 — point the app at the new version's files and rebuild the
containers.** They hold built code and **a restart is not a rebuild**. Then
call the running API and check it is serving the new version, because the
rebuild is the step most often skipped and it fails silently.

```bash
# .env: MURFULU_PRODUCTIVITY_PATH, MURFULU_CORPUS_REPORT_PATH,
#       MURFULU_TYPICALITY_PATH
docker compose build api web && docker compose up -d api web
curl -s localhost:8010/corpus | head -c 120   # must say the new version
```

**The semantic and suspect-claims inputs are carried forward, not rebuilt**,
while the corpus *text* is unchanged — v4's are still the current ones. If the
text ever changes, they have to be rebuilt with it.

### Waiting for the next rebuild

**Things already known to be wrong in the released version, to be checked off
when the next one is built.** They are here rather than in a tracker because
the list is only ever read at rebuild time.

- ~~**~44,676 forms with one suffix added twice**~~ **Cleared by v12,
  2026-10-17**: the index no longer serves them. 116 of the forms it dropped
  were attested at the *spelling* level only — آلهه, خواجهه — Arabic or ه-final
  homographs of a doubled *-e*, not evidence for the forms. — *goftee*, *Goftbānbān*,
  *varguvar*. The generator stopped building these on 2026-08-20 and
  `derivations-v11` was built before it, so the index still serves them.
  Counted by regexp over each active suffix, so it is a lower bound. **None of
  them is attested** — the 1,830 distinct spellings measured that day were
  checked against the whole corpus and found nowhere — so nothing that quotes
  evidence is wrong; the forms are only reachable by browsing. Decided
  2026-08-20 to let the next rebuild clear them rather than edit a released
  index by hand.

## Run `make check-all` before pushing, not `tsc` by hand

CI runs `make check` and `make web-check`. Running a piece of that by hand
misses things, and on 2026-08-16 it did twice in one session:

- `npx tsc --noEmit` passed while `npm run typecheck` — which is `tsc -b` —
  failed. Build mode reads the project references and sees the test files;
  the bare invocation did not.
- `ruff check` passed while `ruff format --check` had eight files to reformat.
  `make lint` runs both.

**And a test that skips is not a test that passes.** `tests/test_repository.py`
errored on every CI run for two days because its own *is git available?* guard
raised instead of returning False — the API image has no git. Seven red tests
that said nothing about the repository, and loud enough that a real failure
hid behind them for a day.

## Nothing private reaches the repository: `make hooks` once per clone

**The repository is public since 2026-10-25**, and its history is one commit
on purpose: the earlier one named the production host and people. What must
stay out is the host's specifics (DEPLOY.md §0), credentials, and the names of
the people who work on the project — the docs refer to them by role.

`make hooks` points git at `tools/hooks/`, whose `pre-commit` runs
`tools/public_check.py` over the lines and paths a commit adds. It refuses
two kinds of thing:

| | where the rule lives |
|---|---|
| a private IPv4 address, a real tunnel id or credentials file, a private key or token, a filled-in secret on an env-style line, a host path in the root user's home, and the local deploy files being staged at all | in the code — the patterns reveal nothing |
| the host name, its address, the tunnel id, people's names in Latin and Persian script | in **`.denylist`**, gitignored — the terms are exactly what must not be published. `.denylist.example` is the format |

**Without `.denylist` only the generic half runs**, and the hook says so on
every commit. A false alarm on a generic pattern takes `public-check: allow`
on its line; nothing lifts a denylist term. `python tools/public_check.py
--all` checks every tracked file instead of the staged lines — run it after
editing `.denylist`, since the hook only ever judges new lines. On
2026-10-25 it reports one line, the guard list in
`tests/test_load_questions.py`, which was public before the check existed.

**Corpus lines are described, not quoted.** Ganjoor's text is not ours to
publish (NOTICE), so a coining run that reads a verse says which poet and what
the line does with the word, and leaves the verse out. No pattern catches that;
it is a rule for whoever writes the entry.

## Never hand-edit the rule pack

`rules/verb_stems.yaml`, `nominals.yaml`, `glides.yaml`, `stem_forms.yaml` and
`stem_rules.yaml` are **written by `tools/build_rule_pack.py`** from the
transcription and `rules/decisions.yaml`. Editing them directly works until
somebody runs the builder, and then the edit is gone with no error.

**That happened three times before it was noticed**, on 2026-08-15, by running
the builder to correct V-052: N-090 and N-099 came back `active: true` after
being retired for measured reasons, and V-021's Persian pattern lost its
negation again — the builder's own `JOINER_FA` had never been fixed, only its
output. Same failure as `MURFULU_GANJOOR_PATH` missing from `.env.example`:
reproducible in principle, not in practice.

**A ruling goes in `rules/decisions.yaml`.** It can retire a rule, or correct
its `kind`, `affix` or `input_types`, and the transcription is never rewritten
— `affix_source` keeps what the document says beside what we build.
`tests/test_rule_pack_build.py` fails if the committed pack is ever not what
the builder produces, so this cannot go quiet again.

**Correct a rule, not an affix, when a spelling is two affixes.** `-andar` is
V-052's prefix (*andarāmadan*) and N-038's suffix (*Mādarandar*). Changing
`affix_spellings.yaml` moves every rule that uses the spelling.

## Modules

The code is split by responsibility. Each module can be understood and tested
alone.

```
murfulu/
  rules/        load and validate the rule pack; no I/O beyond reading YAML
  engine/       apply rules to stems: affixation, glides, compounding, recursion
  scoring/      productivity, attestation, semantics, composite
  lexicon/      thin wrapper over karbon; the only place karbon is imported
  search/       Elasticsearch queries and index mappings
  corpus/       source adapters and ingest pipelines
  db/           the authored store: models, migrations, feedback, rule sync
  api/          FastAPI routes; thin, no logic
```

Rules:

- **`engine/` must not know about Elasticsearch.** It takes a stem and a rule
  pack, returns forms. That is what makes it testable without infrastructure.
- **`api/` holds no logic.** Routes call modules and return their results.
- **karbon is imported in one place only** (`lexicon/`). If karbon changes, one
  file changes.
- **`db/` holds no scoring or generation.** It stores what a human authored and
  reads it back. Anything countable and rebuildable belongs in Elasticsearch.
- **A migration never imports a model.** It is a snapshot of the schema as it
  was, and importing the current models would let a later edit rewrite what an
  old migration did. `migrations/` is linted and type-checked with everything
  else, and a live test fails if a model is changed without a migration.
- one source adapter per corpus, behind a shared interface. Adding a book
  collection must not touch anything outside `corpus/`.

The frontend is its own tree, with its own toolchain:

```
web/
  src/styles/   the design system as tokens; no component hard-codes a value
  src/shell/    the frame: navigation, routing, the list of screens
  src/text/     Persian and Latin together — the LTR island, numerals, terms
  src/screens/  one module per screen
```

`make check` runs the Python side and `make web-check` the frontend, so the
backend still checks on a machine with no Node installed. `make check-all` runs
both, and CI runs them as separate jobs.

## File size

**No file over 400 lines.** Past that, split it. This holds for TypeScript and
CSS as well as Python.

This is not style — karbon has a 1,257-line phonemizer, and six near-duplicate
versions of it, which is why nobody can tell what changed between v6 and v7. We
do not repeat that.

Corollary: no `v2`, `v3` copies of a module. Changes go through git, not
through filenames.

## Tests

**The rule pack is its own test suite.** Every rule in the source grammar carries an
example — `goft + ār = Goftār`. Each becomes a test case automatically. That is
roughly 200 golden tests for free, and any change to the engine that breaks one
is caught immediately.

Layers:

| Level | Covers |
|---|---|
| unit | rule loading, affixation, glide rules, dedup, recursion limits, cycle detection |
| golden | every example in the rule pack, generated from the YAML |
| integration | API routes against a test Elasticsearch and Postgres, in Docker |
| pipeline | ingest a small fixture corpus end to end |
| layout | the interface in a real browser at 375 px and at desktop width |
| accessibility | axe against WCAG 2.1 AA, plus the checks it cannot make |

Requirements:

- tests run in Docker, one command, no manual setup
- new rules land with their examples, so coverage grows with the rule pack
- every bug that reaches the app gets a test before it gets a fix
- no test depends on the real lexicon or the real corpus — fixtures only
- **layout is tested in a browser, not in jsdom.** jsdom has no layout engine,
  so it cannot tell you a row overflows a phone screen or a touch target came
  out 31 px tall — which are the failures a reader hits first
- **accessibility is checked twice, and neither half is redundant.** The
  palette is computed against every ground the app paints, because a page can
  pass an audit by not happening to put two colours together; the pages are
  audited with axe, because a palette cannot tell you a scrolling box has
  nothing to focus. Both found real failures on their first run
- **nothing under a source tree may be ignored by git.** `build/` for the
  batch job's output also matched `web/src/screens/build/`, and a whole screen
  went uncommitted for a week with every test still passing

## Code quality

- Python 3.11+, type hints everywhere, `mypy` in CI
- `ruff` for linting and formatting, one config, no arguments
- Postgres schema changes through migrations (`alembic`), never by hand
- dependencies pinned; `karbon-nlp` pinned to an exact version, not `main`
- structured logging with the corpus version and request id
- no secrets in the repository, ever

## Naming

**No personal names anywhere** — not in code, not in comments, not in docs, not
in commit messages. The repository will be public. Refer to people by role:
*project lead*, *karbon maintainer*, *linguist*, *expert reviewer*.

**Field and variable names describe the thing, not its origin.** A reader who
has never met the team must understand them.

| Bad | Good | Why |
|---|---|---|
| a field named after a team member | `word_class` | names a person |
| `category_dehkhoda` | `lexicon_category` | names a source, not the meaning |
| `pos_corpus` | `pos_observed` | says where, not what |
| `bon1`, `bon2` | `past_stem`, `present_stem` | opaque abbreviation |

Persian technical terms are kept where they are the precise term (`karnam`,
`barnam`, `kārbon`), but always with a one-line definition in the module
docstring and a tooltip in the interface.

## Documentation

- `docs/` is the design record and is updated at the end of every session
- every module has a short docstring saying what it owns and what it does not
- `DECISIONS.md` records why, not just what
- the API is self-documenting through FastAPI's OpenAPI output
- a `CHANGELOG.md` once there is something to release

## Definition of done

A change is done when: it has tests, the tests run in Docker, the docs are
updated, `ruff` and `mypy` pass, and no file crossed 400 lines.
