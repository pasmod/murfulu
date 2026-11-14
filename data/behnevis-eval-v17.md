# Automatic Behnevis, corpus v17: what each threshold costs

Made by `tools/evaluate_behnevis.py`; the model by `tools/build_behnevis.py`.

## Where the text's words get their reading (context-free, by running words)

| source | share of running words |
|---|---:|
| letters | 33.0% |
| function | 26.5% |
| bank | 24.3% |
| choice | 16.2% |
| none | 0.1% |

## 1. Marked words, poets held out (21,899 words, signs hidden)

| threshold | words at or above | of those right |
|---:|---:|---:|
| 0.00 | 100% | 39.4% |
| 0.50 | 44% | 54.6% |
| 0.60 | 35% | 58.9% |
| 0.70 | 30% | 62.4% |
| 0.80 | 23% | 66.0% |
| 0.90 | 17% | 69.2% |
| 0.95 | 10% | 70.3% |

By source, all confidences:

| source | words | right |
|---|---:|---:|
| bank | 3,588 | 38.4% |
| choice | 4,051 | 59.4% |
| function | 918 | 43.8% |
| letters | 13,340 | 33.3% |
| none | 2 | 0.0% |

## 1b. Several readings: the choice alone, poets held out (2,510)

Places where the text's signs leave one of the bank's readings; the model
chooses without the signs. Right means it chose that one.

| threshold | places at or above | of those right |
|---:|---:|---:|
| 0.00 | 100% | 81.4% |
| 0.50 | 94% | 83.0% |
| 0.60 | 84% | 86.6% |
| 0.70 | 75% | 90.1% |
| 0.80 | 65% | 92.2% |
| 0.90 | 52% | 93.9% |
| 0.95 | 37% | 96.9% |

## 2. Unknown words: the letter model on held-out bank words (5,519)

| threshold | words at or above | of those right |
|---:|---:|---:|
| 0.00 | 100% | 55.3% |
| 0.50 | 56% | 74.1% |
| 0.60 | 44% | 79.7% |
| 0.70 | 34% | 84.4% |
| 0.80 | 26% | 88.5% |
| 0.90 | 18% | 91.1% |
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
| 0.50 | 69% | 31% | 22 |
| 0.60 | 61% | 39% | 27 |
| 0.70 | 56% | 44% | 31 |
| 0.80 | 49% | 51% | 36 |
| 0.90 | 31% | 69% | 48 |
| 0.95 | 13% | 87% | 60 |
