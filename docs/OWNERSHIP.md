# Who owns which rules

**Status: draft.** 2026-08-11. Needs agreeing with the karbon maintainer.

karbon (`kp-multiverse/karbon`) is not our repository. Changes to it go through
pull requests. So we need a clear line, or the same rule ends up implemented
twice.

Concrete items waiting to go upstream are collected in
[UPSTREAM.md](UPSTREAM.md) — data faults, gaps, and things built here only
because we could not wait for karbon. Add to that file as you find them; send
them as batched pull requests.

## The line today

| Knowledge | Lives in | If it changes |
|---|---|---|
| Phonemic ruleset (Vājnevisi V.7) | karbon | PR to karbon |
| Stem rules 1–9 | karbon | PR to karbon |
| Stem-rule exception lists (irregular verbs) | karbon | PR to karbon |
| The Dehkhoda lexicon | karbon | the karbon workshop |
| Inflectional suffix stripping (8 suffixes) | karbon | PR to karbon |
| **~200 derivational rules** | **murfulu** | our rule pack |
| **Glide rules** | **murfulu** | our rule pack |
| **Semantic tags and glosses** | **murfulu** | our rule pack |
| **Compounding rules** | **murfulu** | our rule pack |
| **Scoring** | **murfulu** | ours |

So expert edits split. "This verb is an irregular exception" → karbon PR.
"Rule 10 is obligatory, not typical" → our rule pack. The review UI must know
which, and route accordingly — see [REVIEW.md](REVIEW.md).

## The collision to resolve

karbon's own roadmap states its morphology module covers *"stem derivation and
(later) affix/decomposition rules"*. If karbon eventually implements affix
rules, and murfulu already has them, there will be two rule engines with
diverging behaviour.

Three options:

1. **murfulu owns derivation permanently.** karbon stays lexicon + phonemics +
   stems. Clean split, but contradicts karbon's stated plan.
2. **The rule pack lives in karbon as data**, murfulu imports it. Matches the
   "everything upstream" instinct, and matches karbon's roadmap — but every
   rule change becomes a PR to someone else's repo, which will be too slow
   while the rule pack is still being built.
3. **murfulu owns it now, upstream later.** Build and stabilise the rule pack
   here, then propose moving it into karbon once the schema stops changing.

## Decided 2026-08-11

**Both repos carry the rules, and they stay in sync.** — project lead.

Implemented as **one master, one mirror**, not two masters:

- the rule pack YAML lives in murfulu and is edited here
- a command exports it to karbon's format and opens a pull request
- karbon never edits the rules directly; changes always start here

Two independently edited copies would drift apart within weeks. One source with
a push path gives the same result with less risk.

## Practical

- Pin a karbon version in `pyproject.toml`. Do not track its main branch.
- Keep a list of upstream fixes we are waiting on.
- Feedback marked `owner: karbon` is exported, not silently dropped.
