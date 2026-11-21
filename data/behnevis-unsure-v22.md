# The spellings the reading screen leaves to a person, corpus v22

Made by `tools/measure_unsure_spellings.py` (the counting:
`src/murfulu/behnevis/unsure.py`). **A first, rough measurement, not a
result**: each number carries its limits beside it.

## 0. How it was read

Every text of corpus v22, word by word, as the reading screen reads it: the model, the text's own signs, و by the verse rule, and the poem's metre on, as served since 2026-11-21. Each word between its neighbours in its line. A word is *left to a person* when its confidence is below 0.7 (red on the screen) or the model has no reading for it. Read in 24 minutes.

- Running words read: 25,532,059.
- Left to a person: 9,101,335 (35.6%).
- Spellings with at least one such place: 323,395.

Limits: the share left to a person says nothing about whether the words
taken as read are right; `data/behnevis-eval-v22.md` and
`data/behnevis-metre-eval-v22.md` measure that, on the hard marked words.
The metre measurement's sample (one poem in 50) left 33.2 % to a person;
this reads every text, prose and poems without a known metre too.

## 1. How many running words the most frequent unsure spellings hold

Spellings ranked by the running words they leave to a person. Each kind
is what a decision there means (`unsure.kind_of`): *a choice among the
bank's readings* is learned at the model's next build; *the bank's one
reading, doubted* is learned when a person confirms the bank's reading,
and goes to karbon when they name another; *missing from the word bank*
goes to karbon, and the model learns it only once the bank holds it
(DECISIONS 2026-11-14).

| top spellings | unsure running words they hold | share of all left to a person | share of all running words | a choice among the bank's readings | the bank's one reading, doubted | missing from the word bank |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 2,532,194 | 27.8% | 9.9% | 5.5% | 3.2% | 1.2% |
| 500 | 4,441,071 | 48.8% | 17.4% | 7.6% | 4.8% | 5.0% |
| 1,000 | 5,342,041 | 58.7% | 20.9% | 8.2% | 5.2% | 7.6% |
| 2,000 | 6,189,579 | 68.0% | 24.2% | 8.5% | 5.5% | 10.2% |
| 5,000 | 7,162,605 | 78.7% | 28.1% | 8.8% | 5.7% | 13.5% |

The kind columns are shares of all running words. For comparison, all
323,395 spellings with an unsure place hold 9,101,335.
Of the 1,400 listed spellings *missing from the word bank*,
1,176,164 unsure places are inflected forms the bank's
stems build readings for (*konam*, *nabāšad*) and 1,424,415
are guesses from the letters (الله، نور، شمع): words karbon lacks.

## 2. If they were decided: what would be left to a person

Upper bounds: every unsure place of a decided spelling counted as taken
from the person, as if one decision (or a few, by neighbour) fitted all
its places. Section 3 says how far one reading per spelling is from
that. Read from the listed spellings, so up to the list's length.

| top spellings decided | left to a person now | after the next build | after karbon also takes the readings it lacks |
|---:|---:|---:|---:|
| 100 | 35.6% | 28.2% | 25.7% |
| 500 | 35.6% | 25.0% | 18.3% |
| 1,000 | 35.6% | 24.0% | 14.7% |
| 2,000 | 35.6% | 23.4% | 11.4% |

*After the next build* counts the choices among the bank's readings and
the spellings with one bank reading that the editions' marks do not
contradict. The 45 listed spellings whose marks fit another
reading (section 2b) wait for karbon with the missing ones.

Limits: a *one* spelling the editions never marked often enough is
counted as learned, though a person may name another reading there too;
and a decided place counts as taken although a decision *everywhere*
can read a place wrong that the model read right (section 3).

## 2b. Where the bank's one reading is not the one the editions mark

Listed spellings with one bank reading and at least 5
marked places, whose marks fit another reading more often than any
the bank holds: mostly verb forms the bank reads as nouns (UPSTREAM B9).
45 spellings, 457,255 unsure running words. The first twelve:

| spelling | unsure | the bank's reading | the editions' marks fit |
|---|---:|---|---|
| بود | 143,938 | Bud | bovad (1,463 of 1,464) |
| روی | 54,747 | Ruy | ravi (29 of 34) |
| شود | 51,326 | Ševed | šavad (9 of 9) |
| خوش | 22,027 | xoš | Xavaš (34 of 37) |
| نبود | 20,890 | Nabud | nabovad (285 of 285) |
| برد | 15,822 | Bard | borad (208 of 339) |
| مردم | 13,915 | Mardom | mordam (67 of 105) |
| رسد | 11,040 | Rasad | resad (4 of 7) |
| رود | 9,899 | Rud | ravad (54 of 54) |
| آرد | 8,284 | Ārd | ārad (29 of 29) |
| خورد | 7,461 | xord | xorad (42 of 45) |
| افتد | 6,040 | afted | oftad (31 of 31) |

## 3. Would one reading per spelling do?

For each listed spelling the corpus's marked places (`behnevis-marked`,
the editions' vowel signs, quotations left out), read against the
readings the list names for it: the share of places whose signs fit the
one reading that fits most often. Weighted by the spelling's unsure
running words; only spellings with at least 5 marked places that fit a
named reading.

| top spellings | kind | spellings with 5+ fitting marked places | their unsure running words | one reading fits |
|---:|---|---:|---:|---:|
| 100 | a choice among the bank's readings | 27 | 1,049,387 | 79% |
| 100 | the bank's one reading, doubted | 17 | 476,090 | 93% |
| 100 | missing from the word bank | 8 | 151,327 | 83% |
| 500 | a choice among the bank's readings | 62 | 1,211,729 | 80% |
| 500 | the bank's one reading, doubted | 50 | 632,505 | 92% |
| 500 | missing from the word bank | 98 | 588,511 | 86% |
| 2,000 | a choice among the bank's readings | 116 | 1,285,558 | 80% |
| 2,000 | the bank's one reading, doubted | 85 | 683,006 | 92% |
| 2,000 | missing from the word bank | 364 | 919,700 | 88% |

Limits: editions mark the hard places, so a spelling's marked places
lean to its rarer reading and the share is pessimistic; the signs check
only the letters they mark, so two readings that differ elsewhere both
fit; and a reading none of the named ones (a reading the bank lacks) is
not counted at all. Where the share is low, a decision *by neighbour*
(after or before one word) is the safer scope; the screen offers both.

## 4. The 100 spellings that leave the most to a person

*Unsure* counts the running words the screen shows red (below 0.7);
*places* all of the spelling's running words; *read as* the model's most
frequent reading at the unsure places; the last column the reading that
fits most of the spelling's marked places (section 3), and how often.
The full list (the top 2,000) is the JSON file beside the model,
served on the reading screen's list of the most frequent unsure words
(`/texts?view=unsure`).

| # | spelling | unsure | places | kind | bank's readings | read as | fits most marked places |
|---:|---|---:|---:|---|---:|---|---:|
| 1 | است | 220,461 | 243,133 | choice | 3 | Est | Est 40% of 5 |
| 2 | بود | 143,938 | 144,050 | one | 1 | Bud | bovad 100% of 1,464 |
| 3 | سر | 100,687 | 101,097 | choice | 2 | Sar | Sar 98% of 218 |
| 4 | خود | 89,272 | 89,272 | choice | 2 | Xod | Xod 100% of 14 |
| 5 | کرد | 67,178 | 67,319 | choice | 2 | Kard | Kard 78% of 9 |
| 6 | کند | 60,645 | 60,714 | choice | 2 | konad | konad 76% of 116 |
| 7 | روی | 54,747 | 54,753 | one | 1 | Ruy | ravi 85% of 34 |
| 8 | شود | 51,326 | 51,326 | one | 1 | Ševed | šavad 100% of 9 |
| 9 | جهان | 50,826 | 50,828 | choice | 3 | jehān | Jahān 67% of 6 |
| 10 | خویش | 46,802 | 46,802 | choice | 2 | Xiš | Xoyaš 100% of 5 |
| 11 | الله | 44,418 | 44,418 | missing | 0 | alle | alle 100% of 10 |
| 12 | پیش | 43,716 | 43,716 | choice | 2 | Piš | Peyaš 100% of 15 |
| 13 | باز | 38,075 | 38,077 | choice | 3 | Bāz | — |
| 14 | یکی | 37,653 | 37,668 | choice | 2 | yaki | — |
| 15 | دارد | 37,351 | 37,706 | one | 1 | Dārd | dārad 100% of 1 |
| 16 | باد | 35,301 | 35,301 | choice | 2 | Bād | — |
| 17 | گل | 31,217 | 43,920 | choice | 3 | Gel | Gel 51% of 788 |
| 18 | سخن | 29,550 | 29,570 | choice | 4 | Saxon | Soxon 89% of 38 |
| 19 | کسی | 29,297 | 29,297 | choice | 2 | Kasi | kasi 60% of 5 |
| 20 | خون | 28,303 | 33,504 | choice | 2 | Xon | Xun 100% of 3 |
| 21 | کرده | 26,738 | 26,759 | choice | 3 | Karde | Karde 50% of 4 |
| 22 | سوی | 26,221 | 26,225 | one | 1 | Suy | Suy 100% of 2 |
| 23 | بهر | 26,161 | 26,162 | choice | 2 | Bahr | Bahr 100% of 9 |
| 24 | کی | 26,079 | 26,081 | choice | 5 | Kay | key 100% of 167 |
| 25 | بس | 24,764 | 24,784 | choice | 3 | Bos | Baso 100% of 8 |
| 26 | ره | 24,728 | 24,728 | one | 1 | Roh | — |
| 27 | تن | 24,513 | 24,514 | choice | 3 | Tan | Tan 100% of 24 |
| 28 | لب | 24,159 | 24,167 | one | 1 | Lab | Lab 100% of 3 |
| 29 | ملک | 22,694 | 23,196 | choice | 2 | Molk | Molk 94% of 407 |
| 30 | دیگر | 22,220 | 22,223 | choice | 2 | Diger | — |
| 31 | خوش | 22,027 | 22,036 | one | 1 | xoš | Xavaš 92% of 37 |
| 32 | ی | 21,481 | 21,481 | choice | 2 | i | — |
| 33 | علی | 21,018 | 21,021 | one | 1 | oli | oli 100% of 2 |
| 34 | نبود | 20,890 | 20,935 | one | 1 | Nabud | nabovad 100% of 285 |
| 35 | زلف | 20,543 | 20,552 | one | 1 | Zolf | Zolf 100% of 3 |
| 36 | جای | 20,412 | 20,412 | missing | 0 | Jāy | — |
| 37 | چشم | 20,161 | 49,619 | choice | 2 | češm | Čašom 86% of 29 |
| 38 | کنم | 19,984 | 20,027 | missing | 0 | konam | konam 73% of 45 |
| 39 | چند | 19,842 | 19,842 | missing | 0 | čand | čand 100% of 2 |
| 40 | شده | 19,701 | 19,701 | choice | 2 | Šade | — |
| 41 | زین | 19,575 | 19,575 | choice | 2 | Zin | zin 100% of 1 |
| 42 | باید | 19,152 | 19,153 | one | 1 | bāyad | bāyad 100% of 1 |
| 43 | دور | 19,143 | 19,164 | one | 1 | dur | dur 100% of 15 |
| 44 | لا | 18,620 | 18,620 | choice | 2 | Lā | Lā 100% of 96 |
| 45 | نور | 18,619 | 18,619 | missing | 0 | nur | nur 91% of 89 |
| 46 | مهر | 18,337 | 18,476 | one | 1 | Mehr | Mehr 100% of 103 |
| 47 | پی | 17,696 | 17,696 | choice | 5 | Pay | Pey 100% of 43 |
| 48 | رفت | 17,526 | 17,530 | one | 1 | Raft | Raft 100% of 2 |
| 49 | زیر | 16,934 | 16,934 | one | 1 | zir | — |
| 50 | دلم | 16,778 | 16,781 | one | 1 | Dolom | Delam 67% of 3 |
| 51 | اهل | 16,746 | 16,755 | one | 1 | Ohl | Ohl 100% of 8 |
| 52 | فلک | 16,692 | 16,725 | one | 1 | Falak | Falak 100% of 19 |
| 53 | بدان | 16,437 | 16,451 | one | 1 | bedān | bedān 56% of 25 |
| 54 | زبان | 16,177 | 16,177 | choice | 2 | Zabān | — |
| 55 | هزار | 16,092 | 16,102 | one | 1 | hezār | hezār 100% of 2 |
| 56 | برد | 15,822 | 15,859 | one | 1 | Bard | borad 61% of 339 |
| 57 | آخر | 15,624 | 15,641 | one | 1 | Āxor | Āxor 100% of 17 |
| 58 | دارم | 15,543 | 15,546 | one | 1 | Dārem | dāram 100% of 1 |
| 59 | کنی | 15,134 | 15,151 | missing | 0 | koni | koni 58% of 24 |
| 60 | نیز | 15,122 | 15,122 | choice | 2 | Niz | — |
| 61 | گه | 15,110 | 15,120 | one | 1 | Goh | Goh 100% of 9 |
| 62 | اوست | 14,649 | 14,649 | missing | 0 | ust | — |
| 63 | حسن | 14,624 | 14,624 | missing | 0 | hasn | hosn 94% of 336 |
| 64 | برون | 14,401 | 14,401 | choice | 2 | Borun | Borun 90% of 10 |
| 65 | آسمان | 14,328 | 14,328 | choice | 2 | Āsemān | — |
| 66 | نباشد | 14,134 | 14,134 | missing | 0 | nabāšad | — |
| 67 | علم | 14,092 | 14,092 | missing | 0 | alam | alam 56% of 345 |
| 68 | تر | 14,013 | 14,013 | choice | 2 | Tar | Tar 100% of 131 |
| 69 | مردم | 13,915 | 13,964 | one | 1 | Mardom | mordam 64% of 105 |
| 70 | غیر | 13,820 | 13,823 | one | 1 | Qir | Qir 100% of 3 |
| 71 | شمع | 13,743 | 13,743 | missing | 0 | šama | šama 100% of 1 |
| 72 | کان | 13,642 | 13,987 | one | 1 | Kān | Kān 100% of 12 |
| 73 | روان | 13,180 | 13,180 | choice | 3 | Ravān | Ravān 100% of 6 |
| 74 | دولت | 13,119 | 13,119 | missing | 0 | Davlat | — |
| 75 | شیر | 12,791 | 12,791 | choice | 2 | Šir | — |
| 76 | ندارد | 12,688 | 12,688 | missing | 0 | nadārad | — |
| 77 | مکن | 12,371 | 12,371 | missing | 0 | mokon | makon 100% of 36 |
| 78 | ار | 12,215 | 12,294 | choice | 3 | Ar | Ar 100% of 48 |
| 79 | اما | 12,085 | 12,085 | missing | 0 | amā | amā 53% of 160 |
| 80 | بدین | 11,985 | 11,993 | one | 1 | bedin | bedin 100% of 3 |
| 81 | آورد | 11,972 | 11,972 | choice | 3 | Āvard | āvarad 96% of 46 |
| 82 | مست | 11,944 | 11,955 | choice | 2 | mast | Messat 43% of 7 |
| 83 | گاه | 11,931 | 11,931 | choice | 2 | Gāh | — |
| 84 | برای | 11,794 | 11,795 | one | 1 | barāy | borrāy 100% of 2 |
| 85 | کوه | 11,712 | 11,712 | choice | 2 | Kovve | Kuh 100% of 1 |
| 86 | کنند | 11,683 | 11,684 | one | 1 | Kanand | konand 67% of 3 |
| 87 | آید | 11,593 | 29,728 | missing | 0 | āid | — |
| 88 | عاشق | 11,591 | 11,601 | missing | 0 | aāšeq | aāšeq 100% of 4 |
| 89 | گوهر | 11,494 | 11,499 | choice | 2 | Gowhar | Gowhar 100% of 2 |
| 90 | روشن | 11,465 | 11,465 | one | 1 | ravešn | — |
| 91 | شما | 11,291 | 11,291 | choice | 2 | šamā | — |
| 92 | زن | 11,074 | 11,074 | choice | 3 | Zan | Zan 100% of 3 |
| 93 | رسد | 11,040 | 11,045 | one | 1 | Rasad | resad 57% of 7 |
| 94 | بدو | 10,896 | 10,912 | choice | 2 | bedow | bedow 100% of 9 |
| 95 | الا | 10,654 | 11,066 | one | 1 | alā | alā 100% of 203 |
| 96 | چیست | 10,493 | 10,493 | missing | 0 | čist | — |
| 97 | کردم | 10,471 | 10,471 | missing | 0 | kardam | — |
| 98 | بین | 10,454 | 10,454 | one | 1 | bin | — |
| 99 | روزگار | 10,442 | 10,442 | one | 1 | Ruzgār | — |
| 100 | من | 10,427 | 227,645 | choice | 2 | man | man 100% of 1,711 |
