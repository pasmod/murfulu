# Murfulu

Persian word generation. Give it a verb stem, a noun or an adjective, and it
returns the family of words Persian can form from it — each one with the rule
that produced it, what it means, and whether it is attested anywhere.

Working name. The funding application calls the project **Stemma**.

## Where this sits

| Project | Job |
|---|---|
| **karbon** (`~/code/karbon`, pip `karbon-nlp`) | Persian script → Latin phonemic form; the reviewed Dehkhoda lexicon; stem extraction (kārbon-e yek / do) |
| **murfulu** (this repo) | stems + word-formation rules → new words, with derivation path, meaning and evidence |

Murfulu works on the **Latin** (Behnevis) level, not the Arabic-script level.
karbon supplies the Latin. The interface is in Farsi.

## Status

**Phases 0–4, 7 and 8 are complete.** The rule pack, the engine, the lexicon
wrapper, the corpus pipelines, the derivation precompute, the HTTP API and every
screen run — including the one where the linguist answers questions in Persian.

What is left is small and mostly not code:

| | |
|---|---|
| Phase 5 | 2 scoring tasks, both blocked — a composite score needs rule strengths the source states for 3 of 195 rules, and a score for coined words is research (9.14) |
| Phase 6 | caching a live generation; generating it ships already |
| Phase 9 | 3 open and 2 part-done, of which the karbon issues and a sign-in for the linguist are the only ones waiting on a person |

**Phase 8 closed 2026-08-17** with the licence — see below.

See [docs/PLAN.md](docs/PLAN.md) for the detail and
[docs/FINDINGS.md](docs/FINDINGS.md) for what each session established.

## Licence

**Apache-2.0** — see [LICENSE](LICENSE). Take the code, change it, build on it,
sell it; keep the notice, and you have a patent grant.

**It covers what this project wrote** and nothing else. [NOTICE](NOTICE) sets
out the three things it does not reach and why:

| | |
|---|---|
| the corpus | Ganjoor's poetry. Their own FAQ, asked whether the data are copyright-free, answers *not necessarily* — no legal review has been made, and free access is not a licence. Do not assume it is redistributable. |
| the lexicon | karbon's, mounted read-only. Its terms are karbon's question. |
| the expert feedback set | judgements experts made about the language. Not code, and not ours to hand on. |

## Running it

Locally, on a machine with Docker:

```
docker compose up
```

On a server, behind HTTPS and a password — see
[docs/DEPLOY.md](docs/DEPLOY.md), which is also where the reason for the
password is written down: the corpus terms and this project's licence are both
unsettled, and the wall is what makes deploying before they are settled
defensible.

The schema is built by migration, never by hand:

```
docker compose run --rm api alembic upgrade head
```

## Documentation

Read in this order:

| Doc | What it covers |
|---|---|
| [FINDINGS.md](docs/FINDINGS.md) | What the project is and everything established so far. Start here. |
| [DECISIONS.md](docs/DECISIONS.md) | Settled choices, with reasons |
| [OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) | What is still undecided |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Containers, storage, indices, pipelines, API |
| [RULE_PACK.md](docs/RULE_PACK.md) | The ~200 rules as data — schema |
| [WALKTHROUGH_RAFTAN.md](docs/WALKTHROUGH_RAFTAN.md) | One verb traced end to end through the whole system |
| [SEARCH.md](docs/SEARCH.md) | Query language and index design |
| [FRONTEND.md](docs/FRONTEND.md) | Screens and UI rules |
| [REVIEW.md](docs/REVIEW.md) | Expert feedback — also the evaluation set |
| [USER_JOURNEYS.md](docs/USER_JOURNEYS.md) | Six journeys walked, and the gaps they found |
| [RESEARCH_SCORING.md](docs/RESEARCH_SCORING.md) | How to judge a generated word — literature basis |
| [RULE_DISCOVERY.md](docs/RULE_DISCOVERY.md) | Finding new rules from data — literature basis |
| [OWNERSHIP.md](docs/OWNERSHIP.md) | Which rules belong to karbon, which to us |
| [ENGINEERING.md](docs/ENGINEERING.md) | Standards: Docker, modules, file size, tests, docs |
| [PLAN.md](docs/PLAN.md) | Ordered build tasks, each with a done test |
| [LEXICON_ANALYSIS.md](docs/LEXICON_ANALYSIS.md) | What is actually in the lexicon — measured, with traps |
| [SOURCES.md](docs/SOURCES.md) | Index of the Google Drive project archive |

## Layout

```
docs/         design and findings — updated at the end of every session
src/          the Python package
migrations/   Alembic migrations; the schema is never edited by hand
tests/        test suite
web/          the React app — its own toolchain, `make web-check`
data/         rule packs and build outputs (large files gitignored)
```

## Getting the data

The lexicon (45,579 entries) is recovered from karbon's git history — see
[data/README.md](data/README.md). Nothing is blocked.

## Build plan

[docs/PLAN.md](docs/PLAN.md) — ordered tasks, each with a test for "done".
