# Murfulu

Murfulu generates the words a language *can* form, not only the ones its
dictionaries already list: it applies word-formation rules to the stems of a
lexicon and returns each possible word with the rule that built it, a composed
meaning where the rule carries one, and whether the word occurs in a corpus.
Today it is a working prototype for **Persian**, with 195 word-formation rules.
The next step is a **language-independent Python library** with an open,
testable rule format and a checker for rule packs, a **German rule pack** beside
the Persian one, and the Persian pack as its reference.

**Kurz auf Deutsch:** Murfulu erzeugt aus den Wortbildungsregeln einer Sprache
mögliche Wörter, jedes mit Herleitung, Bedeutung und Beleg im Korpus. Heute
läuft ein Prototyp für Persisch mit 195 Regeln. Als Nächstes entstehen eine
sprachunabhängige Python-Bibliothek mit einem offenen, prüfbaren Regelformat
und einem Prüfwerkzeug sowie ein deutsches Regelpaket mit rund 40 produktiven
Mustern; das persische Paket dient als Referenz.

## What it does

One Persian verb, *angixtan* انگیختن «to stir, to rouse», gives 38 words in one
step, built from its two stems. Four of them:

| Built from | Rule | Word |
|---|---|---|
| present stem *angiz* | V-022, suffix *-ande* | *angizande* انگیزنده |
| present stem *angiz* | V-033, suffix *-eš* | *Angizeš* انگیزش |
| present stem *angiz* | V-034, suffix *-e* | *Angize* انگیزه |
| past stem *angixt* | V-008, suffix *-e* | *angixte* انگیخته |

Some of the 38 are in every dictionary; others are words Persian could form
and has not used. The rules do not decide which is which: the corpus search
does, and the linguist judges the rest.

Nothing in the idea is Persian. German *Lichtung* is *lichten* + *-ung*, and a
German rule for *-ung* would propose the nouns German has not formed yet in the
same way.

## Where it stands, and where it is going

| | Today (Persian prototype) | Next |
|---|---|---|
| Core | an engine written for Persian; a second language would need code changes | a language-independent Python library, published on PyPI |
| Rules | 195 Persian word-formation rules (plus 17 glide and 9 stem rules) as YAML in [`rules/`](rules), in a Persian-specific schema | an open rule format: each rule with a fixed id, a condition, a change of form, a meaning and its own test cases; a checker validates a pack against the schema and runs its tests, so linguists can write rules without touching the core |
| Languages | Persian | a German pack with about 40 productive patterns, checked against the ~10,000 German Wikidata lexemes (CC0) that record how they are formed; the Persian pack moved into the new format as the reference |
| Use case | — | carrying a term into another language: split it into its parts, give each part a meaning, and look for words with the same structure on the other side |

The Persian prototype runs end to end: rule pack, engine, lexicon wrapper,
corpus pipeline, HTTP API, and a web app in Persian in which the linguist
reviews rules and results. The **Next** column is planned work, not yet built.

## How it works today

- **Three inputs:** a rule pack ([`rules/`](rules)), a lexicon, and a corpus.
  The core never assumes more than those three.
- **Persian is handled in Latin script.** Arabic script leaves out the short
  vowels, which word formation depends on, so Murfulu works on the Behnevis
  transliteration and never on raw Arabic script.
- **karbon** is the companion project that supplies the Latin forms, the stems
  and the lexicon: Persian script to Latin phonemic form, a lexicon derived
  from Dehkhoda's dictionary (about 45,600 entries, most of them reviewed),
  and stem extraction. Murfulu reads its lexicon read-only and never edits it; faults
  found here go to karbon as issues ([docs/UPSTREAM.md](docs/UPSTREAM.md)).
- **The corpus** is classical Persian poetry from Ganjoor, indexed in
  Elasticsearch. It is not part of this repository (see Licence).
- **Stack:** Python 3.11, FastAPI, PostgreSQL, Elasticsearch, a React web app,
  Docker.

## Running it

The library and its tests need Python 3.11 or newer, and neither the lexicon
nor the corpus:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e ".[dev,api]"
make check
```

`make check` runs the linter, strict type checks and the test suite;
`make web-check` checks the web app, and `make check-all` runs both.

The whole system runs on a machine with Docker. Copy `.env.example` to `.env`,
put the karbon lexicon snapshot into `data/` ([data/README.md](data/README.md)),
then:

```bash
docker compose up
```

The schema is built by migration, never by hand:

```bash
docker compose run --rm api alembic upgrade head
```

Building the corpus index is described in
[docs/ENGINEERING.md](docs/ENGINEERING.md) ("Building a corpus version").
Running on a server, behind HTTPS and a password, is in
[docs/DEPLOY.md](docs/DEPLOY.md), which also says why the password is
required: the corpus terms are unsettled.

## How we work

Murfulu is built by a team of three: the **project lead** (concept and
direction, development), an **engineer** (architecture and development;
maintains karbon), and a **linguist** (the word-formation rules, the grammar terminology and the
Behnevis script). The docs refer to people by role.

- **We use AI coding assistants** to draft code, tests and documentation, and
  we say so: commits made with one carry a `Co-Authored-By` line, and we leave
  it in. A team member decides what each change does, reads the diff, runs the
  tests and is responsible for what is committed.
- **Linguistic decisions are never left to a tool.** The rule pack is
  transcribed from the linguist's grammar and built from that transcription by
  a script; a ruling goes into `rules/decisions.yaml`, and a test fails if the
  committed pack differs from what the builder produces. Where a ruling is
  missing, the question goes to
  [docs/FOR_THE_LINGUIST.md](docs/FOR_THE_LINGUIST.md) and the provisional
  choice is marked as unconfirmed.
- **Every push is checked** in CI ([`.github/workflows/check.yml`](.github/workflows/check.yml)):
  ruff, strict mypy, about 2,900 tests, the web app's lint, types, tests and
  browser layout tests, and the tests again inside the container image.
- **Nothing private reaches the repository.** A pre-commit hook
  ([`tools/public_check.py`](tools/public_check.py), installed with
  `make hooks`) refuses a commit that would publish a credential, a server's
  details or a person's name.
- **Every working session ends with the docs updated**: what was learned in
  [FINDINGS.md](docs/FINDINGS.md), what was settled in
  [DECISIONS.md](docs/DECISIONS.md), what is still open in
  [OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md).

Development started in August 2026 in a private repository. This public
repository begins with a cleaned snapshot of 25 October 2026, because the
earlier history contained details of the server the demo ran on.

## Licence

**Apache-2.0**, see [LICENSE](LICENSE). Take the code, change it, build on it,
sell it; keep the notice, and you have a patent grant.

**It covers what this project wrote** and nothing else. [NOTICE](NOTICE) sets
out the three things it does not reach and why:

| | |
|---|---|
| the corpus | Ganjoor's poetry. Their own FAQ, asked whether the data are copyright-free, answers *not necessarily*: no legal review has been made, and free access is not a licence. Do not assume it is redistributable. |
| the lexicon | karbon's, mounted read-only. Its terms are karbon's question. |
| the expert feedback set | judgements experts made about the language. Not code, and not ours to hand on. |

## Documentation

To get a picture of the system:

| Doc | What it covers |
|---|---|
| [WALKTHROUGH_RAFTAN.md](docs/WALKTHROUGH_RAFTAN.md) | One verb traced end to end through the whole system |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Containers, storage, indices, pipelines, API |
| [RULE_PACK.md](docs/RULE_PACK.md) | The rules as data: the schema |
| [ENGINEERING.md](docs/ENGINEERING.md) | Standards: Docker, modules, file size, tests, docs |

The working record:

| Doc | What it covers |
|---|---|
| [FINDINGS.md](docs/FINDINGS.md) | Everything established so far, newest session first |
| [DECISIONS.md](docs/DECISIONS.md) | Settled choices, with reasons |
| [OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) | What is still undecided |
| [FOR_THE_LINGUIST.md](docs/FOR_THE_LINGUIST.md) | Questions only the linguist can settle |
| [UPSTREAM.md](docs/UPSTREAM.md) | What belongs in karbon rather than here, with measurements |
| [PLAN.md](docs/PLAN.md) | The prototype's build tasks, each with a test for "done" |

Further detail: [SEARCH.md](docs/SEARCH.md) (query language and index design),
[FRONTEND.md](docs/FRONTEND.md) (screens and UI rules),
[REVIEW.md](docs/REVIEW.md) (expert feedback, also the evaluation set),
[USER_JOURNEYS.md](docs/USER_JOURNEYS.md) (six journeys and the gaps they
found), [RESEARCH_SCORING.md](docs/RESEARCH_SCORING.md) and
[RULE_DISCOVERY.md](docs/RULE_DISCOVERY.md) (literature basis for judging
words and finding new rules), [OWNERSHIP.md](docs/OWNERSHIP.md) (which rules
belong to karbon, which to us), [LEXICON_ANALYSIS.md](docs/LEXICON_ANALYSIS.md)
(what is in the lexicon, measured), [SOURCES.md](docs/SOURCES.md) (index of
the project archive).

## Layout

```
src/          the Python package
rules/        the Persian rule pack, as data
tools/        build, measurement and check scripts
tests/        test suite
migrations/   Alembic migrations; the schema is never edited by hand
web/          the React app, with its own toolchain (`make web-check`)
data/         lexicon snapshot and build outputs (large files gitignored)
docs/         design and findings, updated at the end of every session
```
