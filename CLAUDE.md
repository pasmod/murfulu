# Murfulu — orientation for Claude

Persian word generation. Read [docs/FINDINGS.md](docs/FINDINGS.md) first; it
carries the domain knowledge and is kept current.

## Working rule: write up each session

**At the end of every working session, update the docs before finishing.**

- `docs/FINDINGS.md` — new entry at the top, dated, for anything learned about
  the domain, the rules, karbon, or the data.
- `docs/DECISIONS.md` — append any choice that was settled, with the reason.
- `docs/OPEN_QUESTIONS.md` — add what surfaced, remove what got answered.
- `docs/UPSTREAM.md` — anything that belongs in karbon rather than here: a
  fault in its data, a gap, or something built here only as a stopgap. Record
  **what was measured**, so a pull request can quote a number. These go
  upstream in batches, on the project lead's word — never opened unasked.
- `docs/FOR_THE_LINGUIST.md` — questions only the linguist can settle, gathered
  for one conversation at the end rather than asked one at a time.

**The working rule when we disagree with upstream or lack a ruling:** build
what we believe is right *now*, mark it unconfirmed, and record it in the file
it belongs to — karbon's side in UPSTREAM, the linguist's in FOR_THE_LINGUIST.
Waiting is never the reason something stays wrong. karbon v1 is finished and
is completed from here by issues and pull requests, not edited directly.
`rules/lexicon_overrides.yaml` is the machinery for holding a different value
without forking.

The point is that planning can start from the docs without re-reading the whole
Drive archive or re-deriving the same conclusions.

## Context

- Source archive: `Geteilte Ablagen/Projekte/Morphology` in Google Drive.
  Indexed in [docs/SOURCES.md](docs/SOURCES.md).
- Companion repo: `~/code/karbon` — Persian → Latin, Dehkhoda lexicon, stem
  extraction. Do not modify it; it is under review with the linguist.
- Murfulu operates on **Latin (Behnevis)** forms, never raw Arabic script.
- Persian grammar terms follow the project's grammar system (kārvāže, kārbon-e yek/do,
  kārnām, nām, barnām…). The table is in FINDINGS.md.

## Roles

Refer to people by role, never by name. The repository is public (github.com/pasmod/murfulu,
since 2026-10-25), so every commit is published: naming individuals in code and docs is
inappropriate, and so is anything about the production host. Before the first commit in a
clone, run `make hooks` and copy `.denylist.example` to `.denylist` with the real terms;
`python tools/public_check.py --all` checks the whole tree (docs/ENGINEERING.md).

| Role | Owns |
|---|---|
| **project lead** | scientific direction; this repository |
| **karbon maintainer** | the karbon library, its workshop server, and the lexicon database |
| **linguist** | the word-formation rules, the grammar terminology, and the Behnevis script. Authority on linguistic rulings — do not override those decisions in code. Works in Persian. |
| **expert reviewer** | anyone giving graded verdicts in the app. **A person, not an account role** — the app has one account and no roles since 2026-08-17, so the site password is what admits a reviewer |
