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
| 0.00 | 100% | 39.3% |
| 0.50 | 39% | 56.1% |
| 0.60 | 31% | 60.5% |
| 0.70 | 27% | 63.6% |
| 0.80 | 22% | 66.6% |
| 0.90 | 16% | 70.5% |
| 0.95 | 9% | 71.6% |

By source, all confidences:

| source | words | right |
|---|---:|---:|
| bank | 3,588 | 38.4% |
| choice | 3,930 | 60.1% |
| function | 1,039 | 42.1% |
| inflected | 2,478 | 39.1% |
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
| 0.50 | 62% | 38% | 26 |
| 0.60 | 56% | 44% | 30 |
| 0.70 | 52% | 48% | 33 |
| 0.80 | 48% | 52% | 36 |
| 0.90 | 28% | 72% | 50 |
| 0.95 | 10% | 90% | 62 |

## 4. With what certainty (one-sided, exact, alpha = 0.05)

The lower bound is the accuracy we are 95 % sure of (Clopper–Pearson,
`murfulu.behnevis.stats`). A target counts as proven at a threshold when
the bound lies above it — the hypothesis "accuracy ≤ target" is rejected
at alpha. Valid for the measured sets, the two below; not for a single
bank reading or a function word, whose confidence is assumed.

### Several readings (the choice, poets held out)

| threshold | places | right | accuracy | 95 % sure of at least |
|---:|---:|---:|---:|---:|
| 0.50 | 2,165 | 1,798 | 83.0% | 81.7% |
| 0.60 | 1,923 | 1,671 | 86.9% | 85.6% |
| 0.70 | 1,726 | 1,548 | 89.7% | 88.4% |
| 0.80 | 1,492 | 1,371 | 91.9% | 90.6% |
| 0.85 | 1,423 | 1,319 | 92.7% | 91.5% |
| 0.90 | 1,183 | 1,109 | 93.7% | 92.5% |
| 0.93 | 1,027 | 969 | 94.4% | 93.0% |
| 0.95 | 851 | 824 | 96.8% | 95.7% |
| 0.97 | 614 | 599 | 97.6% | 96.3% |
| 0.99 | 319 | 316 | 99.1% | 97.6% |

| target | lowest threshold that proves it | places left above it |
|---:|---:|---:|
| 90% | 0.80 | 64% |
| 95% | 0.95 | 37% |
| 98% | not reached | — |
| 99% | not reached | — |

### Unknown words (the letters, bank words held out)

| threshold | places | right | accuracy | 95 % sure of at least |
|---:|---:|---:|---:|---:|
| 0.50 | 3,073 | 2,260 | 73.5% | 72.2% |
| 0.60 | 2,448 | 1,936 | 79.1% | 77.7% |
| 0.70 | 1,859 | 1,565 | 84.2% | 82.7% |
| 0.80 | 1,425 | 1,262 | 88.6% | 87.1% |
| 0.85 | 1,209 | 1,090 | 90.2% | 88.6% |
| 0.90 | 980 | 891 | 90.9% | 89.3% |
| 0.93 | 823 | 760 | 92.3% | 90.6% |
| 0.95 | 722 | 673 | 93.2% | 91.5% |
| 0.97 | 596 | 558 | 93.6% | 91.7% |
| 0.99 | 448 | 424 | 94.6% | 92.5% |

| target | lowest threshold that proves it | places left above it |
|---:|---:|---:|
| 90% | 0.93 | 15% |
| 95% | not reached | — |
| 98% | not reached | — |
| 99% | not reached | — |

**100 % cannot be proven by any test.** With every answer right the bound
is alpha^(1/n): 299 right answers in a row prove 99 %, 2,995 prove 99.9 %.
A text without a single error needs a person to read every word.
