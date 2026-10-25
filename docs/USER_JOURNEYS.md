# User journeys, and the gaps they expose

**Status: draft.** 2026-08-11. Each journey is walked against the current
design. Gaps are marked **GAP** and collected at the end.

---

## J1 — Translator needs a Persian word for *Lichtung*

The flagship case from `درآمد_پروژه`. The translator has a German word and a
concept: "thinning a wood so light reaches the ground".

1. He has no Persian word to type. He has a *meaning*. He wants to ask: which
   suffix turns an adjective into "the thing that is X"?
   **GAP 1 — no way to search by meaning.** Our query language covers form
   (`*nā`), type and rule, but not semantic tag. the founding complaint was
   exactly this: a writer who wants to use *-gān* has to open a grammar book to
   learn what it means. Browsing affixes by meaning is a headline requirement we
   have not designed.
2. He finds تنک (*tonok*), builds *Tonoknā*. This works today.
3. Now he needs **روشن‌تنکنا** — *Rowšan* + *Tonoknā*. Two independent words
   joined.
   **GAP 2 — compounding is missing.** Our rule pack does affixation
   (وندافزایی) and a few fixed stem+o+stem templates. Free compounding
   (هم‌نهی) of two arbitrary words is not modelled at all. The concept document
   names it as one of the two main Persian word-formation processes, and the
   NGI abstract promises generation "by combining words". This is the largest
   gap in the design.
4. He wants to copy the result into his translation. Covered.

---

## J2 — an expert reviews a rule

1. Opens rule V-010. Measured productivity disagrees with his `strength`.
   Covered — that disagreement is flagged by design.
2. He asks to see the evidence: every word this rule produced, attested and
   not. Covered by the `derivations` index filtered on `rule_chain`.
3. He decides `strength` should be `obligatory` and edits it in the app.
   **GAP 3 — no round-trip back to YAML.** We settled "YAML is the source of
   truth, loaded into Postgres". If an expert edits in the app, Postgres and YAML
   diverge immediately. Needs a defined flow: app edit writes a proposed
   change, which is exported to YAML and committed. Same problem for adding a
   new rule or a new exception to a stem rule.
4. He wants to add an exception: this verb should not take this affix.
   Same gap, plus: exceptions live in karbon's stem rules, not ours.

---

## J3 — Writer checks a word they invented themselves

Types خردیدن (*xeradidan*) — formed from خرد by rule, but not in any dictionary.

1. Lexicon lookup fails. karbon's OOV resolver returns a low-confidence guess.
2. But Murfulu *can* derive this word: خرد + `-idan` → intransitive infinitive.
   **GAP 4 — novel input is not handled as a first-class case.** The right
   answer is "not a recorded word, but well-formed: derivable from خرد by rule
   3". Today the flow treats it as a failed lookup.
3. The Latin is knowable — not by phonemizing the string, but because we
   derived it. This only works if the derivation space is precomputed, which
   strengthens the case for the batch job.

---

## J4 — Researcher studies the suffix ‑nā

The headline use case: "show me every Persian word ending in *-nā*".

1. Searches `*nā`. Gets *Tonoknā*, *Pahnā*, *Derāznā* — and also *Banā*,
   *Sanā*, and anything else whose last two letters happen to be those.
   **GAP 5 — string suffix search is not affix search.** We noted this as
   "later", but it is the flagship query. Mitigation available now: split
   results into "confirmed *-nā* derivations" (present in `derivations` with
   that affix) and "merely ends in these letters".
2. She wants the whole result set charted over time — is this suffix alive or
   medieval?
   **GAP 6 — no aggregate statistics over a result set.** We designed
   dispersion per word. She needs it per query.
3. She exports the result set as a dataset. Not designed. Cheap to add; the NGI
   application promises open outputs.

---

## J5 — Anyone finds something wrong

Not only generated words. The thing being criticised can be:

| Target | Example | Owner |
|---|---|---|
| generated word | *Raftorow* is not a word | murfulu |
| rule | rule 10 should not fire here | murfulu |
| composed meaning | this gloss is wrong | murfulu |
| statistics | this count looks wrong | murfulu |
| lexicon entry | the Latin for this word is wrong | **karbon** |
| stem derivation | this exception is missing | **karbon** |
| the app itself | this button does nothing; RTL broken | bug |

**GAP 7 — feedback targets outside murfulu.** Two of these belong to karbon,
whose lexicon we mount read-only. We cannot fix them and must not silently
drop them. Needs a routing rule: record locally, mark as karbon-owned, export
for the karbon maintainer and the karbon workshop.

**GAP 8 — bug reports are a different shape.** A linguistic verdict
(good/possible/wrong) does not fit "this button is broken". Feedback needs a
category, and bug reports need browser and app version rather than rule chain.

**GAP 9 — who may leave feedback?** Bugs should be reportable by any user;
linguistic verdicts should carry weight only from experts. That is two
permission levels on one mechanism.

---

## J6 — project lead adds a book corpus

1. Ingest runs, corpus v4 is built. Counts change everywhere.
2. Every precomputed derivation's attestation is now stale.
   **GAP 10 — no rebuild strategy.** Needs ES aliases and a defined
   reindex-and-swap, plus a decision on whether old corpus versions stay
   queryable.
3. Expert feedback recorded against v3 still refers to v3 scores.
   Feedback stays valid — it judged the *form*, not the count — but the UI must
   show which corpus version it was given under. We already store that field;
   the display rule needs stating.

---

# Gap summary

| # | Gap | Severity |
|---|---|---|
| 1 | Search by meaning / semantic tag | high — headline requirement |
| 2 | **Compounding (هم‌نهی) not modelled** | **highest — promised in the proposal** |
| 3 | Rule edits have no round-trip back to YAML | high — blocks expert review |
| 4 | Novel word as input not a first-class case | medium |
| 5 | String suffix search ≠ affix search | high — flagship query |
| 6 | No aggregate statistics over a result set | medium |
| 7 | Feedback on karbon-owned data has no route | medium |
| 8 | Bug reports need their own shape | low, easy |
| 9 | Two permission levels on feedback | low, easy |
| 10 | No reindex/rebuild strategy across corpus versions | medium |

Gaps 2, 3 and 5 change the design. The rest are additions.

## Resolutions agreed 2026-08-11

**Gap 2 — compounding.** In scope, but **only for the combinations the linguist's
tables already license** (nām + kārbon-e do, nām + nām, stem + o + stem, and
the other documented patterns). Free compounding of any two words is not
attempted. The set grows as rules are added.

**Gap 1 — search by meaning.** In scope, done properly. Semantic tags become a
first-class searchable dimension: `tag:ja`, plus a browse-affixes-by-meaning
view. This answers the founding complaint directly.

**Gap 5 — affix vs string search.** Results split into "confirmed derivations
with this affix" and "merely ends in these letters".

**New: rule discovery.** Generating new rules and new combinations from data is
a planned feature, not v1. Research basis in
[RULE_DISCOVERY.md](RULE_DISCOVERY.md).
