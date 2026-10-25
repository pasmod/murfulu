# What is actually in the lexicon

Analysis of `data/lexicon-20260808.sqlite`, 45,579 active rows. Run
2026-08-11, before implementation started.

## 1. The verbs are complete and clean

All **1,752** infinitive rows have both stems, in Persian and Latin. No
infinitive is missing a stem, and nothing that is not an infinitive has one.

Those 1,752 rows are **1,742 distinct readings** — ten verbs are listed twice
with the same spelling and the same Latin form. The generation input pool is
therefore 1,742, not 1,752. (Measured 2026-08-11 through the lexicon wrapper.)

Spot-checked against the source grammar's exception lists — رفتن → *raft*/*row*,
گفتن → *goft*/*gu*, کردن → *kard*/*kon*, دیدن → *did*/*bin*, پختن →
*poxt*/*paz*. All correct.

**The whole verb side of the engine can be built and tested today.**

## 2. Trap: karbon's `stem_rule` numbers are not the source grammar's

The source grammar has stem rules 1–9 plus exception lists. karbon's
`stem_rule` column runs to **43**, and the numbers do not correspond:

| Verb | karbon `stem_rule` | In the source grammar |
|---|---|---|
| رفتن | 17 | exception to rule 9 |
| گفتن | 19 | exception to rule 9 |
| کردن | 9 | exception to rule 3 |
| شدن | 8 | exception to rule 3 |
| نوشتن | 37 | exception to rule 8 |
| دیدن | *null* | exception to rule 2 |

karbon appears to give each exception its own number. Two regular buckets carry
most of the mass — rule 6 (1,138 verbs, the `-idan` case) and rule 1 (299).

**Never assume the two numbering schemes match.** Our rule pack uses the source
grammar's numbering. If we ever show karbon's number to a user, it must be
labelled as karbon's, or mapped explicitly.

## 3. One spelling, many entries

**1,805 spellings appear more than once**, covering 4,152 rows. Two different
situations, and they need different handling:

**Real homographs** — different readings:

```
کله  →  Kale (noun) · kole (adjective) · Kole (noun) …   9 rows
```

Our design already handles this: one document per reading.

**The same reading repeated** — Dehkhoda's separate senses:

```
پی  →  Pey (اسم معنی) × 7   ·   Pay (اسم معنی) × 1
```

**Corrected 2026-08-11 while building the wrapper.** This entry first said
*Pey* × 4. That counted four **soft-deleted** rows spelled *Pi*. Among live
rows the count is seven, plus one separate reading *Pay*. Anything reading this
table must filter `deleted_at IS NULL`; 6,238 of the 51,817 rows are deleted
and a query that forgets silently resurrects retracted readings.

Identical spelling, identical Latin, identical category. Keying `word_types` on
spelling + Latin collapses these into one, which is right for search but throws
away the sense distinction.

**Open question:** do we keep a link back to all source entries so a word can
show "Dehkhoda lists this in 4 senses"? Cheap to keep, impossible to recover
later.

## 4. Latin quality is good — 0.5% suspect

Of 45,579 rows, **215** have four or more consonants in a row, which almost
always means a broken transcription. 139 of those are already flagged
`needs_review`, leaving about **76 bad rows that nobody has caught**.

They share one cause — و read as a consonant `v` where it should be a vowel:

```
ازدودن   → ozdvdan    (should be ozdudan)
آگورگر   → āgvrgar
ابروبند  → Abrvband
```

Small, and a single pattern. Worth sending upstream to the karbon maintainer as
a targeted fix rather than working around it.

## 4b. The same fault reaches the variant readings — and there are two faults,
not one

Measured 2026-08-11, after the wrapper started reading `phonemic_variants`.

**The alternative readings are as clean as the primaries, and broken the same
way.** 48 of 8,281 extra readings look broken (0.6%), against 215 of 45,579
primaries (0.5%). So the variants are not a dumping ground; they were produced
by the same process and carry the same faults at the same rate.

**§4 named one cause. There are two.** Splitting the broken forms by which
consonant is sitting where a vowel belongs:

| fault | broken primaries | broken variants | example |
|---|---|---|---|
| و read as `v` | 71 | 16 | آبخوست → *Ābxvast* / *ābxvst* |
| **ه read as `h`** | **22** | **12** | چمچه‌ساز → *čomčhsāz*, should be *čomčesāz* |
| both in one word | 3 | 2 | خندهٔ دندان‌نمای → *xandahdndānnmāye* |
| neither pattern | 119 | 18 | — |

The **ه-as-`h`** fault is new here; §4 recorded only the و one. It is the same
shape of mistake: a letter that is a vowel in this position read as the
consonant it is elsewhere. Both are single, mechanical patterns.

Worth sending to the karbon maintainer as two targeted fixes rather than
working around here. Note that **76 of the broken primaries are not flagged
`needs_review`**, so nobody downstream has any signal about them.

Nothing is filtered on our side. A broken reading is carried exactly as the
lexicon has it — if it is wrong, it is wrong in karbon and should be fixed
there, not hidden.

## 5. Review status lines up with what we need

| Category | Rows | Reviewed |
|---|---|---|
| مصدر — verbs | 1,752 | **100%** |
| صفت — adjectives | 1,528 | **100%** |
| اسم معنی — abstract nouns | 1,991 | **100%** |
| اسم ذات — concrete nouns | 14,391 | 64% |
| صفت مرکب — compound adjectives | 12,131 | 66% |
| اسم مرکب — compound nouns | 8,132 | 64% |
| وام‌واژه — loanwords | 5,347 | 59% |

The three categories the rules apply to most are **fully reviewed**. The
unreviewed mass is concrete nouns, compounds and loanwords.

This is a good position: we can build and evaluate against clean data from day
one, and the messy 60%-reviewed material is exactly the material where
generation matters least.

## 6. Precompute size — measured, not guessed

Step 1 only:

| Input pool | Entries | Rules | Candidate forms |
|---|---|---|---|
| verbs | 1,752 | ~81 | **142,000** |
| verified nominals (صفت + اسم معنی) | 3,519 | ~104 | **366,000** |
| all nominals | 38,173 | ~104 | **4,000,000** |

Not every rule applies to every entry, so the real numbers are lower.

**Recommendation: the first precompute run covers verbs plus verified
nominals — about 508,000 step-1 forms.** That is small enough to run in
minutes, uses only 100%-reviewed input, and produces the rule productivity
figures we need. Extending to all nominals is a later decision, taken with
measurements from the first run.

This answers the open question in PLAN task 5.2.

### What the first run actually measured (2026-08-11)

The table above estimated the pool by counting **rows**. The precompute reads
**readings**, and those are two different numbers:

| | estimated | measured |
|---|---|---|
| input pool | 5,271 rows | **5,208 readings** |
| forms, step 1 | ~508,000 | ~177,000 |
| forms, steps 1–2 | not estimated | **1,849,284** |
| words after merging | not estimated | **1,738,711** |

Two things the estimate got wrong, both worth knowing before the pool widens.

**Step 1 was over-estimated and step 2 was not estimated at all.** The row
estimate multiplied every entry by every rule in its family. In practice a
verb produces 34 forms at one step, not 81, because most rules do not fit it.
But the *second* step is where the size actually is: one more step multiplies
the count by roughly eleven.

**The three categories differ enormously**, and averaging them hides it:

| category | entries | forms at 1 step | at 2 steps |
|---|---|---|---|
| مصدر — verbs | 1,742 | 34 each | 510 each |
| صفت — adjectives | 1,517 | 24 each | 612 each |
| اسم معنی — abstract nouns | 1,949 | **1 each** | 24 each |

Abstract nouns produce almost nothing at one step because they map to
`karnam`, and **exactly one rule in the pack takes a kārnām** (N-098). The
82 rules that take a `nām` are reached only at the second step. That is not a
fault; it is what the pool costs. اسم ذات — the category those 82 rules are
really for — is 64% reviewed and deliberately outside the first run.

**Cost, on a laptop:** 26 seconds of generation, 61 seconds end to end
including the corpus pass, 4.0 GB peak memory, 1.55 GB of JSON out. All
nominals would be roughly ten times that in both, which is a real constraint
on widening the pool, not a formality.

## 7. Compounds are 44% of the lexicon

اسم مرکب (8,132) plus صفت مرکب (12,131) = 20,263 entries that are **already
compound words**. Feeding them back into the compounding rules mostly produces
noise.

**Open question:** exclude compounds from compounding, or allow it? Some
genuine Persian words are compounds of compounds, so a blanket exclusion is
probably wrong — but they should not be in the first precompute run.

## 8. Loanwords stay in

5,347 entries. The source grammar explicitly permits making Persian verbs from
Arabic loans with `-idan` / `-āndan`, and the project has an explicit position
against purging Arabic vocabulary. So loanwords are not excluded — but they are
flagged, because Persian derivational affixes do not attach to them as freely.

## 9. Small data gotchas

- **11 rows have `pos = NULL`.** SQL comparisons like `pos != 'مصدر'` silently
  skip them. Eight of the eleven carry stems. Always handle null explicitly.
- **`stem_group`** holds 1 (1,547), 3 (168), 2 (10) — probably the source
  grammar's NKZ / NKDZ split, but this is unconfirmed. Do not rely on it until
  it is checked.
- **13 rows have no vowel at all** in the Latin form.
