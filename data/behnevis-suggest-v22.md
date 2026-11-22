# Automatic suggestions for the most frequent unsure spellings, corpus v22

Written by `tools/import_reading_suggestions.py` (the file the API reads:
`src/murfulu/behnevis/suggest.py`). **Unconfirmed, and only shown**: a
person accepts a suggestion with the list's decide controls or does not.

## 0. How they were made

Read offline and blind by a language model: each listed spelling with its two neighbours from its first example line, vowel signs and answer hidden; a reading in Behnevis letters and the model's own certainty, 0 to 100. Made 2026-11-22, offline, one row per
spelling of `behnevis-unsure-v22.json` (measured 2026-11-21).
What the certainty is worth was measured on 1,200 held-out
vowel-marked words of the poets the reading screen's model did not learn
from (*right*: the editions' marks accept the reading; *at least*: the exact
95 % lower bound):

| certainty | test words | right | at least | listed spellings |
|---|---:|---:|---:|---:|
| 0–50 | 241 | 64% | 58% | 112 |
| 50–70 | 352 | 69% | 65% | 267 |
| 70–85 | 305 | 80% | 76% | 477 |
| 85–100 | 302 | 88% | 85% | 1,144 |

Limits: the test words are the hard ones editions mark, not these frequent
words; one line was read per spelling, so where a spelling has several
readings the suggestion is the reading in that line, not necessarily
everywhere.

## 1. What they offer, by kind

*In the bank*: one of the bank's (or the function-word list's) readings, the
same when case, accents, the ezafe and the mark for ع are set aside.
*Offered*: a reading the panel offers that the bank lacks (what the model
read or built). *To type*: none the panel offers; a person types it, and it
goes to karbon's list like any typed reading. *Several*: the bank holds the
letters with and without a capital (*Xod*, *xod*); the suggestion writes no
capitals, so the screen marks both and leaves the choice to the person.

| kind | spellings | in the bank | offered | to type | several |
|---|---:|---:|---:|---:|---:|
| choice | 336 | 283 | 10 | 43 | 141 |
| one | 264 | 122 | 44 | 98 | 27 |
| missing | 1,400 | 0 | 960 | 440 | 203 |

## 2. Against the editions' marks, on these spellings

Spellings whose suggestion can be lined up with at least 5 of
their marked places (a place a reading cannot be lined up with says
nothing of it). *The bank's best*: of the bank's readings, the one that
fits the largest share of the places it is checked on.

| kind | spellings | places checked | the suggestion fits | the bank's best fits |
|---|---:|---:|---:|---:|
| choice | 127 | 23,986 | 63% | 52% |
| one | 159 | 12,600 | 62% | 10% |
| missing | 430 | 39,189 | 82% | — |

**257 suggestions fit fewer than half of the marked places they
are checked on**; the screen says so beside them. The most unsure:

| spelling | unsure | suggestion | certainty | fits marked places |
|---|---:|---|---:|---:|
| است | 220,461 | ast | 95 | 2 of 5 |
| بود | 143,938 | bud | 95 | 115 of 1,465 |
| خود | 89,272 | xod | 92 | 14 of 40 |
| کرد | 67,178 | kard | 95 | 7 of 31 |
| روی | 54,747 | ruy | 70 | 3 of 34 |
| خویش | 46,802 | xiš | 88 | 0 of 5 |
| پیش | 43,716 | piš | 80 | 2 of 15 |
| گل | 31,217 | gol | 75 | 311 of 788 |
| سخن | 29,550 | soxan | 80 | 5 of 38 |
| سوی | 26,221 | suy | 85 | 2 of 11 |
| لب | 24,159 | lab | 85 | 3 of 13 |
| خوش | 22,027 | xoš | 90 | 3 of 37 |
| نبود | 20,890 | nabud | 75 | 44 of 286 |
| زلف | 20,543 | zolf | 90 | 3 of 21 |
| چشم | 20,161 | češm | 88 | 2 of 29 |
| زین | 19,575 | zin | 90 | 1 of 45 |
| دور | 19,143 | dur | 93 | 15 of 40 |
| مهر | 18,337 | mehr | 70 | 103 of 313 |
| رفت | 17,526 | raft | 95 | 2 of 31 |
| دلم | 16,778 | delam | 90 | 2 of 5 |
| فلک | 16,692 | falak | 65 | 19 of 40 |
| هزار | 16,092 | hezār | 92 | 2 of 14 |
| علم | 14,092 | ˈelm | 60 | 153 of 372 |
| مردم | 13,915 | mardom | 92 | 34 of 106 |
| کان | 13,642 | kān | 92 | 12 of 25 |

Limits: editions mark the hard places, and often the classical reading
(*bovad*) where the suggestion gives today's (*bud*); the signs check only
the letters they mark.

## 3. Where the bank holds one reading and the suggestion another

**142 spellings**, candidates for a fault in karbon's word bank
(UPSTREAM A20), to be weighed with the marks: where the editions' signs fit
the suggestion and not the bank's reading, the bank is the likelier fault.

| spelling | unsure | the bank's reading | suggestion | certainty | marks fit the suggestion | marks fit the bank's |
|---|---:|---|---|---:|---:|---:|
| شود | 51,326 | Ševed | šavad | 93 | 9 of 9 | 0 of 9 |
| دارد | 37,351 | Dārd | dārad | 95 | 1 of 1 | 0 of 1 |
| ره | 24,728 | Roh | rah | 90 | 152 of 157 | 0 of 157 |
| علی | 21,018 | oli | ˈalā | 90 | 1,818 of 1,822 | 2 of 1,822 |
| دلم | 16,778 | Dolom | delam | 90 | 2 of 5 | 1 of 5 |
| اهل | 16,746 | Ohl | ahl | 92 | 150 of 156 | 8 of 156 |
| برد | 15,822 | Bard | bord | 65 | 186 of 344 | 33 of 344 |
| آخر | 15,624 | Āxor | āxer | 88 | 64 of 108 | 17 of 108 |
| دارم | 15,543 | Dārem | dāram | 92 | 1 of 1 | 0 of 1 |
| گه | 15,110 | Goh | gah | 85 | 53 of 66 | 9 of 66 |
| غیر | 13,820 | Qir | qeyr | 85 | 168 of 169 | 3 of 169 |
| کنند | 11,683 | Kanand | konand | 92 | 2 of 3 | 1 of 3 |
| روشن | 11,465 | ravešn | rowšan | 70 | 0 of 1 | 0 of 1 |
| الا | 10,654 | alā | ellā | 93 | 1,593 of 1,794 | 203 of 1,794 |
| رود | 9,899 | Rud | ravad | 85 | 54 of 54 | 0 of 54 |
| آرد | 8,284 | Ārd | ārad | 92 | 29 of 29 | 0 of 29 |
| نهاد | 7,548 | Nahād | nehād | 70 | 3 of 4 | 1 of 4 |
| خورد | 7,461 | xord | xorad | 70 | 42 of 80 | 3 of 80 |
| برو | 6,819 | baru | borow | 75 | 18 of 40 | 23 of 40 |
| بیند | 6,600 | bined | binad | 93 | 1 of 1 | 0 of 1 |
| نمود | 6,529 | nemud | namud | 60 | 0 of 3 | 0 of 3 |
| افتد | 6,040 | afted | oftad | 88 | 31 of 31 | 0 of 31 |
| نزد | 6,005 | nazd | nazad | 60 | 5 of 8 | 0 of 8 |
| غبار | 5,189 | Qebār | qobār | 88 | 4 of 4 | 0 of 4 |
| خواند | 4,668 | Xānd | xānad | 85 | 17 of 25 | 8 of 25 |

Of the 142, the editions' marks back the suggestion over the
bank's reading (checked on at least 5 marked places, a larger
share fits) for
**73**.

