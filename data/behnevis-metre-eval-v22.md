# The poem's metre as a signal for the automatic Behnevis, corpus v22

Made by `tools/evaluate_behnevis_metre.py` (the metre step:
`src/murfulu/behnevis/metre.py`; the poems with a metre:
`tools/extract_metre_lines.py`). **A first, rough measurement on poetry,
not a result**: each number carries its limits beside it.

## 0. How much of the corpus has a known metre

- Running words of corpus v22: 25,532,059.
- Poems joined to a Ganjoor metre label: 115,443; of them 5 have a label this step cannot read into a pattern.
- Running words in poems with a readable label: 18,183,304 (71.2% of all running words).

Limits: the label is Ganjoor's, joined by poem id and kept only where the
first verse half agrees (`tools/extract_metre_lines.py` prints what was
dropped); Sokhan's metre study found Ganjoor's labels right for about 99
poems in 100 of those it could scan. A poem of several metres is left out.

## 1. Marked words, poets held out, signs hidden

Poems of the held-out poets with a known metre: 26,375; verse halves with a marked word: 7,936 (left out as quotations, over 30% of words marked: 1,182); marked words: 8,980, by 36 poets. Verse halves that scan with the readings offered: 76.9%.

Limits: editions mark the hard words, so these are pessimistic; a reading
counts as right when the word's signs fit it, which checks only the
marked letters; the whole line's signs are hidden, so the model reads the
neighbours unaided too. The before column differs from
`data/behnevis-eval-v22.md`'s section 1 because only poems with a
known metre are read here, each word between its neighbours in the line.

| threshold | words at or above, before | right, before | words at or above, after | right, after |
|---:|---:|---:|---:|---:|
| 0.00 | 100.0% | 46.2% | 100.0% | 51.0% |
| 0.50 | 50.1% | 60.5% | 53.2% | 62.5% |
| 0.60 | 41.3% | 63.3% | 45.0% | 64.3% |
| 0.70 | 37.1% | 65.4% | 39.2% | 66.8% |
| 0.80 | 30.0% | 66.9% | 33.2% | 68.2% |
| 0.90 | 23.8% | 68.4% | 25.5% | 71.4% |
| 0.95 | 10.8% | 77.8% | 13.4% | 75.7% |

### By where the reading came from (before the metre), all confidences

| source | words | right, before | right, after | below 0.7, before | below 0.7, after |
|---|---:|---:|---:|---:|---:|
| bank | 1,993 | 38.1% | 46.6% | 65.4% | 65.8% |
| choice | 2,307 | 62.5% | 63.8% | 45.2% | 46.4% |
| function | 496 | 36.9% | 36.9% | 0.0% | 0.2% |
| inflected | 1,278 | 53.5% | 60.9% | 89.0% | 88.5% |
| letters | 2,906 | 37.1% | 41.9% | 74.6% | 67.1% |

### What kind of error, and what the metre did to it

| kind of error | before | share of errors | made right | after | share of errors | newly wrong |
|---|---:|---:|---:|---:|---:|---:|
| presence or length | 1,911 | 39.5% | 525 | 1,067 | 24.2% | 91 |
| vowel quality | 1,127 | 23.3% | 0 | 1,537 | 34.9% | 0 |
| not offered | 1,796 | 37.2% | 0 | 1,796 | 40.8% | 0 |

*Presence or length*: some reading the model offered fits the signs
and behaves differently in a line — the metre can prefer it. *Vowel
quality*: every reading offered that fits behaves as the wrong one
does in every line (*kenār*, *kanār*) — no metre can. *Not
offered*: none fits; the metre cannot make it right, though it may
lower its confidence, or raise it by ruling out rivals. *Made right*
counts the errors of that kind before that the metre turned right; *newly
wrong* the right readings it turned into errors of that kind.

### With what certainty (95 %, drawing poets again)

| threshold | places, before | right | at least | places, after | right | at least |
|---:|---:|---:|---:|---:|---:|---:|
| 0.70 | 3,328 | 65.4% | 56.7% | 3,518 | 66.8% | 58.6% |
| 0.90 | 2,136 | 68.4% | 56.3% | 2,290 | 71.4% | 61.9% |

One threshold each, read off, not searched; the lower bound holds for
these poets' marked words, not for a single word.

### Sensitivity: the licences' costs, set beforehand

The numbers above use the costs in `Licences()`, set before measuring.
Other settings, on the same words, to show how much they matter (not to
choose one by the test):

| setting | right at 0.70 or more | words at 0.70 or more | right at 0.90 or more | words at 0.90 or more |
|---|---:|---:|---:|---:|
| as set (the tables above) | 66.8% | 39.2% | 71.4% | 25.5% |
| another reading cheaper (2) | 66.7% | 38.5% | 71.5% | 24.7% |
| another reading dearer (5) | 66.4% | 39.7% | 71.1% | 26.1% |
| ezafe and lengthening free | 66.6% | 39.3% | 68.1% | 27.1% |

## 2. What is left to a person, before and after

One poem in 50 with a known metre (a stable hash of its id): 2,389 poems, 58,889 verse halves, 400,495 running words, read as the reading screen reads them (the full model, the text's own signs, و by the verse rule). Verse halves that scan with the readings offered: 78.4%.

Limits: whether the words taken as read are right is section 1's
question, measured there on the hard marked words only; here only how
many cross each threshold. Each word between its neighbours in the line,
so the before column differs from the context-free section 3 of
`data/behnevis-eval-v22.md`.

| threshold | taken as read, before | after | left to a person, before | after |
|---:|---:|---:|---:|---:|
| 0.50 | 73.0% | 75.4% | 27.0% | 24.6% |
| 0.60 | 68.6% | 70.8% | 31.4% | 29.2% |
| 0.70 | 65.0% | 66.8% | 35.0% | 33.2% |
| 0.80 | 58.6% | 62.0% | 41.4% | 38.0% |
| 0.90 | 52.2% | 55.4% | 47.8% | 44.6% |
| 0.95 | 15.3% | 25.0% | 84.7% | 75.0% |

### By source: below 0.7 (red on the reading screen), before and after

| source | share of words | below 0.7, before | after |
|---|---:|---:|---:|
| bank | 26.2% | 23.1% | 23.4% |
| choice | 14.9% | 63.1% | 61.7% |
| function | 28.7% | 0.0% | 0.3% |
| inflected | 10.9% | 78.1% | 75.9% |
| letters | 19.3% | 57.4% | 49.3% |
