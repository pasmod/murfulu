# Corpus v13 → v14 (function words credit nothing)

Measured 2026-10-18 before the release. v14 is v13's recipe (docs/ENGINEERING.md)
on the same inputs — corpus text, `lexicon-20261012`, semantic and
suspect-claims v4 — with one change in the code: **a spelling on
`rules/function_words.yaml` credits no corpus count to any reading or built
form written with it.** Approved by the project lead on 2026-10-18.

The trigger, from `compare-v12-v13.md`: karbon 1.2.0 reads row 28296 «که» as
the adjective *keh* ("small"), correctly, and the link pass credited it with
the conjunction's 609,699 occurrences. Every form written که inherited them.

## The rule

- `murfulu/scoring/attestation.py` `Index.look_up`: if the normalised spelling
  is listed, the answer is level `spelling`, `function_word` = the entry's
  class, counts **0** (meaning *unknown*), other readings kept. Decided on the
  spelling alone, so the lexicon entry, every form written with the same
  letters, the batch job and a live request agree.
- Consumers treat it as no evidence: not written ground (grounding), not an
  attested output (productivity, compare), ranked last among a rule's sisters
  (never dropped), held out of the affix map as *contested* ("the letters are
  a function word"), standing 1 on the build screen.
- `word_types`: a listed spelling's **reading** documents carry
  `function_word` and null counts; the spelling's own document (`latin` null,
  `function_word` set) carries the count. Nothing is dropped.
- A form built *on* such an entry is judged on its own spelling: کهتر keeps
  its 314 occurrences, کهین its 160.

## The list

43 spellings, version 1.0.0. Criteria, written in the file: closed-class
(conjunction, preposition/postposition, contraction, pronoun, demonstrative,
particle); among the **200 most frequent** spellings of the corpus — checked by
`tools/check_function_words.py`, which recounts and fails otherwise (all 43
pass; together 28.8% of the text); and the function use plainly dominating any
content homograph, which is a judgement. Left out on that judgement: می
(wine), خود/خویش, کان, کی, زین (saddle), numerals, است and verb forms, چرا (B7).
23 of the 43 shadow a lexicon reading in `lexicon-20261012`.

## Summary

`tools/compare_versions.py --report data/corpus_report-v13.json
data/corpus_report-v14.json --derivations build/derivations-v13.jsonl
build/derivations-v14.jsonl --function-words`

```
corpus report      v13 -> v14
  documents                         133,148       133,148   same
  tokens                         25,497,189    25,497,189   same
  spellings                         409,916       409,916   same
  spellings_linked                   16,713        16,713   same
  documents_without_century          98,627        98,627   same

derivations        derivations-v13.jsonl -> derivations-v14.jsonl
  records                         1,844,043     1,844,043   same
  paths                           2,794,905     2,794,905   same
  attested                           27,214        27,176   -38
  function_word                           0            38   +38
  no rule's output count moved

function words     rules/function_words.yaml 1.0.0
  unchanged                                   1,836,879
  changed in some field                           7,164
  evidence moved, spelling on the list               38
  evidence moved, spelling not listed                 0   must be 0
  grounding moved, stood on such a form              32
  grounding moved otherwise                           0   must be 0
  sisters moved, rule made such a form            7,118
  sisters moved otherwise                             0   must be 0
  any other field moved                               0   must be 0
  appeared                                            0   must be 0
  gone                                                0   must be 0
  32 forms credited nothing, made by 5 rules
```

**Every difference is the list's.** Records, paths and the five report
figures are identical; 38 records lost their credit, all spelled with a listed
word; the 32 grounding changes all stand on such a form; the 7,118 sister-list
changes are all on words of the five rules that made one (V-049 alone carries
most of them: its eight stored sisters were Az, Dar, Beh, Tav, Dal, Tā, Bā, Sar
and are now Dal, Sar, Sor, Jahān, Kand, Piš, Kār, Ruz).

## The 38 records

All built forms; most are V-049's zero-derived noun from a present stem.

| v13 count | spelling | record | v13 level | class | rule | source |
|---:|---|---|---|---|---|---|
| 634,849 | از | Az:karnam | reading | preposition | V-049 | ازدن |
| 609,699 | که | Koh:karnam | spelling | conjunction | V-049 | کهیدن |
| 609,699 | که | **Keh:karnam** | spelling | conjunction | V-049 | **که *keh*** |
| 499,649 | به | Beh:karnam | reading | preposition | V-049 | به *beh* |
| 499,649 | به | Bah:karnam | spelling | preposition | V-049 | بهیدن |
| 469,313 | در | Dar:karnam | reading | preposition | V-049 | دریدن |
| 393,813 | را | rā (karidekarbahr, karandekarbahr) | spelling | postposition | V-026, V-024 | ریدن |
| 318,631 | تو | Tav:karnam | reading | pronoun | V-049 | تویدن |
| 265,119 | بر | Bor, Ber, Bar :karnam | spelling | preposition | V-049 | بریدن، برشتن، بردن |
| 141,206 | تا | Tā:karnam | reading | conjunction | V-049 | تاییدن |
| 134,032 | چو | Ču:karnam | spelling | conjunction | V-049 | چستن |
| 131,697 | با | Bā:karnam | reading | preposition | V-049 | باییدن |
| 115,948 | ما | mā (2 classes) | spelling | pronoun | V-026, V-024 | میدن |
| 105,045 | چه | Čah:karnam | spelling | conjunction | V-049 | چهیدن |
| 73,781 | نه | Neh, Nah :karnam | spelling | particle | V-049 | نهستن؛ نهادن، نهفتن، نهیدن |
| 71,424 | گر | Ger:karnam | spelling | conjunction | V-049 | گریدن |
| 59,418 | مرا | morā, marā (2 classes each) | spelling | contraction | V-026, V-024 | مریدن |
| 42,336 | وی | Vi:karnam | spelling | pronoun | V-049 | ویدن |
| 33,022 | جز | Jaz:karnam | reading | preposition | V-049 | جزیدن |
| 24,775 | ترا | torā, tarā (2 classes each); Tarā:karnam | spelling; reading | contraction | V-026, V-024, V-049 | تریدن، تراییدن |
| 17,623 | مگر | mgar:karandekarbahr, Megar:nam | spelling | conjunction | V-032, N-063 | میدن |
| 16,841 | ازین | Azin:karnam | spelling | contraction | V-049 | ازین *azin* |
| 16,598 | وز | Vaz:karnam | spelling | contraction | V-049 | وزیدن |
| 14,215 | مر | Mor, Mar :karnam | spelling; reading | particle | V-049 | مریدن |

## Per-rule figures (rule_productivity)

Only the five rules above moved; built counts are unchanged.

| rule | attested | confirmed | tokens |
|---|---|---|---|
| V-049 | 2,074 → 2,050 | 486 → 477 | 8,802,457 → 3,472,643 |
| V-024, V-026 | 673 → 667 | — | 852,430 → 174,283 |
| V-032 | 132 → 131 | — | 20,327 → 2,704 |
| N-063 | 128 → 127 | — | 21,026 → 3,403 |

Their realisation rates and Baayen's P move with them — V-049's token count
had been 60% function words.

## Indices

- `word_types` 411,167 → **411,192** (+25): one document per listed spelling
  that the lexicon also reads, carrying the count the 28 reading documents no
  longer do (43 spelling documents marked in all).
- Affix map: 1,641 → 1,633 word types claimed, 2,202 → 2,236 claims contested,
  4,157 → 4,139 refused.
- The precompute ran 159 s for the pass; 15 minutes for steps 1–3.
