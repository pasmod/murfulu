# Corpus v17 → v18 (the linguist's corrected rules)

Measured 2026-11-19 on the Mac, **before any release**. v18 is v17's recipe
(docs/ENGINEERING.md) with one change of input: the rule pack of the linguist's
corrected rules of 2026-11-19, version 0.2.0 (DECISIONS 2026-11-19). Same
corpus text, same lexicon (`lexicon-20261111`), semantic vectors and suspect
claims carried forward from v4 as for v17. Built with
`tools/build_corpus_mac.sh v18 lexicon-20261111` in **12 minutes 13 seconds**
(22:21–22:33), `--no-release` throughout: the aliases still serve v17.

## The five report figures and the build

`tools/compare_versions.py --report … --derivations …`:

| | v17 | v18 | |
|---|---|---|---|
| documents | 133,142 | 133,142 | same |
| tokens | 25,532,059 | 25,532,059 | same |
| spellings | 409,955 | 409,955 | same |
| spellings_linked | 23,130 | 23,130 | same |
| documents_without_century | 98,621 | 98,621 | same |
| records | 2,949,164 | 3,875,620 | **+926,456 (+31 %)** |
| paths | 4,342,574 | 5,253,430 | +910,856 |
| attested | 31,490 | 29,201 | **−2,289** |
| function_word | 39 | 33 | −6 |

The text is untouched, so the first five do not move; everything that moves
is the rule pack's. **205 rules moved.** The largest:

| rule | v17 | v18 | why |
|---|---|---|---|
| N-032 *-ā* | 20,785 | 303,318 | now makes نام and برنام, not ندایی, so its output feeds the noun rules |
| N-113 *-fām*, N-115 *-gun* | 0 | 145,056 / 145,057 | new, on نام and برنام |
| N-118 *-var*, N-116 *-ize*, N-121 *-ā (Šegefti)* | 0 | 143,767 / 123,722 / 121,208 | new |
| N-069 *-gin* | 26,882 | 145,693 | now on برنام as well |
| V-032 *-gar* | 11,227 | 119,295 | now on both stems, برنام and کارنام |
| N-125 *-kār*, N-106 *kam-* | 0 | 95,210 / 71,647 | new |
| N-098 *-i* | 225,171 | 8,416 | now on the infinitive (xordani), no longer on every کارنام |
| N-033 *-ā* | 224,767 | 62,270 | makes a کارنام now, which fewer rules take |
| V-015, V-073, V-066, V-065, N-007, N-039, N-094, N-019, N-005, V-006, V-026 | 11,225–120,136 | 0 | retired |
| V-070 … V-076 *vā-, var-, zir-* | ~86,600 each | 8,402 each | now on the infinitive, like bar- and dar- |

The verbal prefixes on the infinitive (V-051 … V-062, bar-, dar-, farā- …)
each lose about 5,200 records for the same reason: in v17 they also stood on
the infinitives that vā-, var- and zir- had built in one step
(*barvāgoftan*), which v18 no longer builds at that depth.

## What moved in the corpus's evidence

Records with an attestation, matched record by record
(`build/derivations-v17.jsonl` against `-v18`, not in git): 31,529 → 29,234;
**6,602 lost, 4,307 gained**, of which 2,772 spellings are attested under no
record any more and 1,613 newly are.

**Lost — mostly false credits, now gone.** N-098 put *-i* on every کارنام, so
an inflected verb in the text was taken for a built word: می (113,522 times),
کنی، داری، خواهی، کردی، بودی، هستی، بینی، شوی، گویی، دانی، باشی. Real words lost
with them: چیزی، کاری، یاری (the bank files چیز، کار and یار as کارنام only —
L26) and the retired rules' *vā-* forms.

**Gained — some real, and a new set of false credits from short affixes.**
V-091 (*-u* on a present stem, row 118: zāu) matches سرو (*saru*, 13,181), ازو
(*azu*, «از او»), برو (the imperative), مرو، گاو، لو؛ N-006 (*be-* on a
کارنام) matches بهر (*ber*, 26,156) and بهرام؛ N-106 (*kam-*) matches کمر
(*kamr*); N-001 (*a-*) matches اله and ادراک. Each is a spelling the corpus
writes for another word, credited to a built one: the attestation's known
weakness (it matches a spelling, not a reading), which short affixes on every
base make larger.

## Texts and word counts, v17 → v18

`tools/compare_documents.py v17 v18`: 0 documents added, 0 removed; counted
lines 3,055,058 → 3,055,058; **0 of 409,955 spellings changed their count.**
The text is v17's, exactly.

## The word bank's gaps, corpus v18

`tools/measure_bank_gaps.py v18 --top 1000 --text ganjoor:hafez:2132 --text
ganjoor:saadi:41293`: **identical to v17** in every line — the bank and the
text are both unchanged (one reading 438 of the 1,000 most frequent, several
194, function words 4, inflected 128, uninflected 236; running words 33.0 %
one reading, 27.8 % several, 5.8 % function words, 11.3 % inflected, 22.1 %
uninflected).

## Behnevis and typicality

`tools/build_behnevis.py v18` (1 min 32 s) and
`tools/evaluate_behnevis.py v18` (`data/behnevis-eval-v18.md`): within 0.1
points of v17 at every threshold; the model reads the bank and the text, not
the rule pack. Typicality (`data/typicality-v18.json`): 639,229 scored forms,
median 0.827.
