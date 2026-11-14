# Automatic Behnevis, corpus v17: what each threshold costs

Made by `tools/evaluate_behnevis.py`; the model by `tools/build_behnevis.py`.

## Where the text's words get their reading (context-free, by running words)

| source | share of running words |
|---|---:|
| function | 28.8% |
| bank | 24.3% |
| letters | 22.4% |
| choice | 13.9% |
| inflected | 10.7% |
| none | 0.1% |

## 1. Marked words, poets held out (21,899 words, signs hidden)

| threshold | words at or above | of those right |
|---:|---:|---:|
| 0.00 | 100% | 40.7% |
| 0.50 | 42% | 54.0% |
| 0.60 | 34% | 57.6% |
| 0.70 | 30% | 60.0% |
| 0.80 | 25% | 61.9% |
| 0.90 | 20% | 63.5% |
| 0.95 | 9% | 70.4% |

By source, all confidences:

| source | words | right |
|---|---:|---:|
| bank | 3,588 | 38.4% |
| choice | 3,930 | 60.1% |
| function | 1,039 | 42.1% |
| inflected | 2,478 | 51.7% |
| letters | 10,862 | 31.9% |
| none | 2 | 0.0% |

## 1b. Several readings: the choice alone, poets held out (2,318)

Places where the text's signs leave one of the bank's readings; the model
chooses without the signs. Right means it chose that one.

| threshold | places at or above | of those right |
|---:|---:|---:|
| 0.00 | 100% | 81.2% |
| 0.50 | 93% | 83.0% |
| 0.60 | 83% | 86.9% |
| 0.70 | 74% | 89.7% |
| 0.80 | 64% | 91.9% |
| 0.90 | 51% | 93.7% |
| 0.95 | 37% | 96.8% |

## 2. Unknown words: the letter model on held-out bank words (5,507)

| threshold | words at or above | of those right |
|---:|---:|---:|
| 0.00 | 100% | 55.1% |
| 0.50 | 56% | 73.5% |
| 0.60 | 44% | 79.1% |
| 0.70 | 34% | 84.2% |
| 0.80 | 26% | 88.6% |
| 0.90 | 18% | 90.9% |
| 0.95 | 13% | 93.2% |

## 3. What a threshold leaves to a person

Running words of corpus v17: 25,532,059. Each spelling read without
neighbours, so a word the context would settle counts as unsure here.
Hours for Hafez's ghazals (62,300 words) assume 600 words
an hour by hand and 900 checked proposals an hour — assumptions,
not measurements;
by hand they take 104 hours.

| threshold | taken as read | checked by a person | hours for Hafez |
|---:|---:|---:|---:|
| 0.50 | 71% | 29% | 20 |
| 0.60 | 67% | 33% | 23 |
| 0.70 | 63% | 37% | 25 |
| 0.80 | 57% | 43% | 30 |
| 0.90 | 53% | 47% | 32 |
| 0.95 | 14% | 86% | 60 |

## 4. With what certainty

A lower bound is the accuracy we are sure of at the stated level. Two
corrections keep it honest (the review of 2026-11-14):

- **Poets, not words.** The choice was measured on whole poets held out;
  a poet's words hang together, so its bound comes from drawing the poets
  again (a cluster bootstrap), not from the words as independent answers.
  Unknown words were held out one by one, so theirs is the exact
  Clopper–Pearson bound.
- **Ten thresholds searched.** A target is proven only where the bound at
  alpha / 10 = 0.005 (Bonferroni) lies above it,
  so the search among thresholds cannot flatter the result.

Valid for these two measured sets; not for a single bank reading or a
function word, whose confidence is assumed.

### Several readings (the choice, poets held out)

| threshold | places | units | accuracy | 95 % sure of | 95 % sure, all ten |
|---:|---:|---:|---:|---:|---:|
| 0.50 | 2,165 | 37 | 83.0% | 81.0% | 79.5% |
| 0.60 | 1,923 | 35 | 86.9% | 85.2% | 83.8% |
| 0.70 | 1,726 | 34 | 89.7% | 88.0% | 86.7% |
| 0.80 | 1,492 | 33 | 91.9% | 89.8% | 88.2% |
| 0.85 | 1,423 | 32 | 92.7% | 91.1% | 89.9% |
| 0.90 | 1,183 | 32 | 93.7% | 92.5% | 91.7% |
| 0.93 | 1,027 | 31 | 94.4% | 93.0% | 92.2% |
| 0.95 | 851 | 26 | 96.8% | 95.3% | 94.3% |
| 0.97 | 614 | 25 | 97.6% | 95.8% | 94.5% |
| 0.99 | 319 | 21 | 99.1% | 97.6% | 96.5% |

| target | lowest threshold that proves it (all ten) | places left |
|---:|---:|---:|
| 90% | 0.90 | 51% |
| 95% | 0.99 | 14% |
| 98% | not reached | — |
| 99% | not reached | — |

### Unknown words (the letters, bank words held out)

| threshold | places | units | accuracy | 95 % sure of | 95 % sure, all ten |
|---:|---:|---:|---:|---:|---:|
| 0.50 | 3,073 | 3,073 | 73.5% | 72.2% | 71.4% |
| 0.60 | 2,448 | 2,448 | 79.1% | 77.7% | 76.9% |
| 0.70 | 1,859 | 1,859 | 84.2% | 82.7% | 81.9% |
| 0.80 | 1,425 | 1,425 | 88.6% | 87.1% | 86.2% |
| 0.85 | 1,209 | 1,209 | 90.2% | 88.6% | 87.7% |
| 0.90 | 980 | 980 | 90.9% | 89.3% | 88.3% |
| 0.93 | 823 | 823 | 92.3% | 90.6% | 89.6% |
| 0.95 | 722 | 722 | 93.2% | 91.5% | 90.4% |
| 0.97 | 596 | 596 | 93.6% | 91.7% | 90.6% |
| 0.99 | 448 | 448 | 94.6% | 92.5% | 91.3% |

| target | lowest threshold that proves it (all ten) | places left |
|---:|---:|---:|
| 90% | 0.95 | 13% |
| 95% | not reached | — |
| 98% | not reached | — |
| 99% | not reached | — |

### One threshold set beforehand: 0.70, 99.9% sure

Tested once, so no correction for searching is needed.

- Several readings: at least 85.7% right.
- Unknown words: at least 81.4% right.

**100 % cannot be proven by any test.** With every answer right the bound
is alpha^(1/n); at 99.9% certainty 688 right answers in a row prove 99 %, 6,905 prove 99.9 %.
A text without a single error needs a person to read every word.
