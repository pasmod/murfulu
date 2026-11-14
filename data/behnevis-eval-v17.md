# Automatic Behnevis, corpus v17: what each threshold costs

Made by `tools/evaluate_behnevis.py`; the model by `tools/build_behnevis.py`.

## Where the text's words get their reading (context-free, by running words)

| source | share of running words |
|---|---:|
| letters | 33.0% |
| bank | 26.6% |
| function | 25.6% |
| choice | 14.7% |
| none | 0.1% |

## 1. Marked words, poets held out (21,899 words, signs hidden)

| threshold | words at or above | of those right |
|---:|---:|---:|
| 0.00 | 100% | 39.9% |
| 0.50 | 45% | 55.1% |
| 0.60 | 36% | 59.0% |
| 0.70 | 29% | 63.2% |
| 0.80 | 23% | 67.4% |
| 0.90 | 17% | 70.5% |
| 0.95 | 10% | 71.9% |

By source, all confidences:

| source | words | right |
|---|---:|---:|
| bank | 3,994 | 41.2% |
| choice | 3,650 | 61.5% |
| function | 913 | 43.9% |
| letters | 13,340 | 33.4% |
| none | 2 | 0.0% |

## 1b. Several readings: the choice alone, poets held out (2,497)

Places where the text's signs leave one of the bank's readings; the model
chooses without the signs. Right means it chose that one.

| threshold | places at or above | of those right |
|---:|---:|---:|
| 0.00 | 100% | 77.8% |
| 0.50 | 98% | 79.0% |
| 0.60 | 84% | 83.4% |
| 0.70 | 72% | 88.2% |
| 0.80 | 61% | 90.7% |
| 0.90 | 48% | 93.0% |
| 0.95 | 33% | 96.0% |

## 2. Unknown words: the letter model on held-out bank words (5,519)

| threshold | words at or above | of those right |
|---:|---:|---:|
| 0.00 | 100% | 54.3% |
| 0.50 | 58% | 72.7% |
| 0.60 | 47% | 78.4% |
| 0.70 | 37% | 83.4% |
| 0.80 | 28% | 87.8% |
| 0.90 | 20% | 90.9% |
| 0.95 | 15% | 92.4% |

## 3. What a threshold leaves to a person

Running words of corpus v17: 25,532,059. Each spelling read without
neighbours, so a word the context would settle counts as unsure here.
Hours for Hafez's ghazals (62,300 words) assume 600 words
an hour by hand and 900 checked proposals an hour — assumptions,
not measurements;
by hand they take 104 hours.

| threshold | taken as read | checked by a person | hours for Hafez |
|---:|---:|---:|---:|
| 0.50 | 70% | 30% | 21 |
| 0.60 | 63% | 37% | 26 |
| 0.70 | 57% | 43% | 30 |
| 0.80 | 50% | 50% | 35 |
| 0.90 | 33% | 67% | 46 |
| 0.95 | 15% | 85% | 59 |
