# Corpus v18 → v22 (false claims of the short affixes)

Measured 2026-11-19 on the Mac, **before any release**. v22 is v18's recipe
(docs/ENGINEERING.md) with one change of code: the attestation credits
nothing where the letters are another word's (DECISIONS 2026-11-19, *false
claims of the short affixes*). Same text, lexicon, rule pack (0.2.0),
semantic vectors and suspect claims. Built with `tools/build_corpus_mac.sh v22
lexicon-20261111` in **7 minutes 52 seconds**, `--no-release`: the aliases
still serve v17. v19–v21 were intermediate builds while the review's findings
were folded in; they are superseded.

## The five report figures and the build

`tools/compare_versions.py --report … --derivations …`:

| | v17 (served) | v18 | v22 |
|---|---|---|---|
| documents | 133,142 | 133,142 | 133,142 |
| tokens | 25,532,059 | 25,532,059 | 25,532,059 |
| records | 2,949,164 | 3,875,620 | 3,875,620 |
| paths | 4,342,574 | 5,253,430 | 5,253,430 |
| **attested** | 31,490 | 29,201 | **26,058** |
| function-word homographs | 39 | 33 | 50 |
| headword homographs | — | — | **3,126** |

No rule's output moved between v18 and v22: only what the corpus is allowed
to say about the forms did. `compare_documents.py v18 v22`: 0 documents, 0
lines and 0 spelling counts moved.

## What is credited nothing now

**3,176 records**: 3,126 whose letters the bank reads only as other words
(headword homographs) and 50 written as a function word joined to a pronoun
(the `joined` list of `rules/function_words.yaml`). 241 of them were claimed
only by rules new in the corrected rules, 994 by new or changed rules, and
1,941 by rules the August pack already had — the fault is old; the short new
affixes made it larger.

Claimed only by a new rule, by affix: -u (V-091) 76, -ā (N-121) 29, -kār
(N-125) 27, -i (N-124) 21, -āk (V-093) 19, -gun (N-115) 18, kam- (N-106) 10,
be- on a verb (V-087) 9, -u (N-119) 9, xar- (N-110) 6, -gen (N-114) 4, bi-
(N-107) 4, -var (N-118) 3, bā- (V-083) 2, -ize (N-116) 2, -fām (N-113) 1,
-vā (N-136) 1.

| built | letters | count | the bank reads them as | rule |
|---|---|---|---|---|
| *saru*, *soru* | سرو | 13,181 | *Sarv*, *Sorv* | V-091 -u |
| *azu* | ازو | (contraction) | از او | V-091 -u |
| *bāu*, *zatu* | باو، زتو | (contraction) | با او، ز تو | V-091 -u |
| *bamā* | بما | (contraction) | به ما | N-121 -ā |
| *ber*, *beru* | بهر | 26,156 | *Bahr* | N-006 be- |
| *kamr*, *kamru* | کمر | 5,209 | *kamar* | N-106 kam- |
| *škār* | شکار | 2,930 | *Šekār* | N-125 -kār |
| *Alae* | اله | 1,859 | *Ale* | N-001 a- |
| *Afasāne* | افسانه | 2,103 | *Afsāne* | N-001 a- |
| *šae* | شاه | 26,884 | *Šāh* | V-036 -e (August) |
| *re* | ره | 24,728 | *Roh* | V-036 -e (August) |

The counts stay on each record and the build screen still writes whose they
are; the corpus mark reads «نامعلوم», the rule's productivity and the chain's
ground no longer count them, and the affix map records them as contested.

## What is still credited, and why

Letters the bank holds **no reading of at all** keep their credit, ranked
down where the inflection reading applies (DECISIONS 2026-08-13): گفتا (*goftā*,
3,767, the archaic «he said»), هلاک، جزو، سهو (Arabic words the bank lacks), ادراک,
برگی. About 1,500 records claimed only by new rules are of this kind. A
spelling with no reading is a gap in the bank, not proof of another word;
the karbon side of it is UPSTREAM B2.

## The word bank's gaps, corpus v22

`measure_bank_gaps.py v22 --top 1000`: the 1,000 most frequent spellings as in
v18. Over every spelling, the joined contractions now count as function words:
36 spellings and 11,195 running words more (5.9 % against 5.8 %), taken from
the inflected and uninflected rows.

## Behnevis and typicality

`build_behnevis.py v22` and `evaluate_behnevis.py v22`
(`data/behnevis-eval-v22.md`): within 0.1 points of v18. Typicality:
`data/typicality-v22.json`.
