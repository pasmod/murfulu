# Automatic Behnevis, corpus v17: what each threshold costs

Made by `tools/evaluate_behnevis.py`; the model by `tools/build_behnevis.py`.

## Where the text's words get their reading (context-free, by running words)

| source | share of running words |
|---|---:|
| function | 28.8% |
| bank | 24.3% |
| letters | 22.5% |
| choice | 13.9% |
| inflected | 10.6% |
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
| 0.50 | 62% | 38% | 26 |
| 0.60 | 56% | 44% | 30 |
| 0.70 | 52% | 48% | 33 |
| 0.80 | 48% | 52% | 36 |
| 0.90 | 28% | 72% | 50 |
| 0.95 | 10% | 90% | 62 |
