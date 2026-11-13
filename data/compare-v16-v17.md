# Corpus v16 → v17 (Ganjoor's own positions; texts keep their units)

Measured 2026-11-13 on the Mac, **before any release**. v17 is v16's recipe
(docs/ENGINEERING.md) with one change of input: the Ganjoor adapter reads each
verse's `position` as Ganjoor's own `VersePosition` enum defines it
(`ganjoor/desktop`, `DesktopGanjoorDbBrowser/Base Data Models/VersePosition.cs`,
commit `caecff0`; the same enum in `ganjoor/GanjoorService`,
`RMuseum/Models/Ganjoor/VersePosition.cs`, commit `448fb20`):

| position | Ganjoor's name | v16 | v17 |
|---|---|---|---|
| 0, 1 | Right, Left — a couplet's halves | counted | counted |
| 2 | CenteredVerse1 — a band couplet's first half, or a band line alone | counted | counted |
| **3** | **CenteredVerse2 — a band couplet's second half** | **dropped, taken for prose** | **counted** |
| 4 | Single — free verse | counted | counted |
| **5** | **Comment — the source's own note** | **counted as text** | **kept for the reader, not counted** |
| −1 | Paragraph — prose | counted (by accident) | counted |

Lexicon (`lexicon-20261111`), semantic vectors and suspect claims are v16's
(the last two carried forward although the text changed: DECISIONS
2026-11-13, OPEN_QUESTIONS S41). Built with `tools/build_corpus_mac.sh v17
lexicon-20261111` in **88 minutes** (15:32–17:00) on a Mac whose load average
stood near 29 throughout, against 6.5 minutes for v16 on an idle one: the same
steps, slower by the machine, not by the change.

## The five report figures and the build

`tools/compare_versions.py --report … --derivations …`:

| | v16 | v17 | |
|---|---|---|---|
| documents | 133,148 | 133,142 | −6 |
| tokens | 25,497,189 | 25,532,059 | **+34,870** |
| spellings | 409,916 | 409,955 | +39 |
| spellings_linked | 23,127 | 23,130 | +3 |
| documents_without_century | 98,627 | 98,621 | −6 |
| records | 2,949,164 | 2,949,164 | same |
| paths | 4,342,574 | 4,342,574 | same |
| attested | 31,484 | 31,490 | +6 |
| function_word | 39 | 39 | same |

No rule's output count moved: the build is the same; only what the corpus says
about its forms moved.

**What the v17 texts are made of** (`data/corpus_report-v17.json`, `units`):
1,436,087 couplets, 78,656 verse halves standing alone, 82,499 prose
paragraphs, and 1,332 notes kept beside the text and not counted.

## Texts, v16 → v17

Documents: 133,148 → 133,142; **0 added, 6 removed**.

Removed: `ganjoor:mmon:88974`, `ganjoor:mmon:88975`, `ganjoor:mmon:88976`, `ganjoor:rhedayat:88111`, `ganjoor:rhedayat:88284`, `ganjoor:rhedayat:88391`

Counted lines: 3,049,631 → 3,055,058 (+5,427), in 1,732 documents.

| line | lines |
|---|---|
| band_second | +7,122 |
| a note in v17 | −1,351 |
| not in v17 | −344 |

## Word counts, v16 → v17

Spellings whose corpus count moved: **10,380** of 409,955; 351 appear, 312 disappear. Running words: 25,497,189 → 25,532,059.

Largest gains:

| spelling | v16 | v17 | change |
|---|---|---|---|
| و | 1,109,915 | 1,111,210 | +1,295 |
| از | 634,849 | 635,813 | +964 |
| به | 499,649 | 500,285 | +636 |
| تو | 318,631 | 319,222 | +591 |
| که | 609,699 | 610,225 | +526 |
| ز | 279,353 | 279,856 | +503 |
| را | 393,813 | 394,250 | +437 |
| بر | 265,119 | 265,527 | +408 |
| این | 186,084 | 186,455 | +371 |
| من | 227,318 | 227,642 | +324 |
| است | 242,690 | 243,001 | +311 |
| در | 469,313 | 469,606 | +293 |
| تا | 141,206 | 141,483 | +277 |
| شد | 100,612 | 100,874 | +262 |
| باد | 35,043 | 35,300 | +257 |
| ای | 123,476 | 123,712 | +236 |
| دل | 148,466 | 148,697 | +231 |
| جان | 77,693 | 77,920 | +227 |
| سر | 100,874 | 101,096 | +222 |
| چون | 157,382 | 157,559 | +177 |
| بود | 143,873 | 144,048 | +175 |
| چو | 134,032 | 134,206 | +174 |
| جهان | 50,660 | 50,827 | +167 |
| با | 131,697 | 131,863 | +166 |
| ما | 115,948 | 116,111 | +163 |

Largest losses:

| spelling | v16 | v17 | change |
|---|---|---|---|
| جواب | 5,120 | 4,869 | -251 |
| الله | 44,536 | 44,414 | -122 |
| رباعی | 381 | 268 | -113 |
| گفت | 78,381 | 78,276 | -105 |
| علیه | 7,606 | 7,507 | -99 |
| رحمه | 1,459 | 1,367 | -92 |
| ایضا | 248 | 182 | -66 |
| بیت | 3,603 | 3,542 | -61 |
| ق | 139 | 90 | -49 |
| له | 4,291 | 4,242 | -49 |
| شعر | 5,314 | 5,267 | -47 |
| تعالی | 10,676 | 10,637 | -39 |
| وله | 130 | 92 | -38 |
| رباعیات | 111 | 75 | -36 |
| توحید | 2,671 | 2,636 | -35 |
| گوید | 13,707 | 13,672 | -35 |
| گفته | 6,705 | 6,671 | -34 |
| قدس | 1,476 | 1,442 | -34 |
| شیرازی | 167 | 134 | -33 |
| منغزلیاته | 32 | 0 | -32 |
| منمثنوی | 31 | 2 | -29 |
| مثنوی | 324 | 297 | -27 |
| پرسیدند | 970 | 943 | -27 |
| قطعه | 432 | 406 | -26 |
| محبت | 5,542 | 5,520 | -22 |

Appear, most frequent first: جفنگیم (9)، المظفرست (9)، ناماندنی (7)، چونگارین (6)، المناظرین (6)، مغربئی (6)، ماجاء (5)، اتسزست (5)، شکرکه‌این‌آمد (3)، عمرخاص (3)، جمهوریتان (2)، رارام (1)، شکر‌ها (1)، کانشاهباز (1)، نیائیش (1)، غلطان‌تست (1)، جبانید (1)، بوالفتوحش (1)، استبدادیان (1)، نفتادستم (1)، دارالعبادم (1)، ایبکم (1)، ملبیا (1)، فلاتوجه (1)، اردشیرکنم (1)

Disappear, most frequent first: منغزلیاته (32)، منرباعیاته (10)، مناشعاره (9)، رباعیاته (9)، غزلیاته (7)، منمثنویاته (6)، منقطعاته (4)، مثنویاته (4)، قصایده (4)، قطعاته (3)، سنگ‌پشت (2)، وانشدناه (2)، منقصائده (2)، نخشبیگفته (2)، شنیده‌های (2)، والتحقیق (2)، منغزلیات (2)، ذررا (2)، شیبهگفت (2)، حاشیه‌های (2)، منحقایقه (2)، وبگاه (2)، عبداللهگوید (2)، بلیانی (2)، ذوالنونگوید (2)

**Reading the line table against the dump.** The dump holds 7,122 non-empty
lines at position 3 and 1,676 at position 5. Every one of the 7,122 is counted
in v17. Of the 1,676 notes, 1,332 stay with their texts as notes (1,351 lines
of `text_fa` in v16, because some hold a line break) and 344 were the only
lines of the six removed pages — two headings pages of a tazkira (`rhedayat`)
and three one-line pages (`mmon`). Nothing else moved.

**Which spellings moved, and why.** The gains are the band halves' ordinary
words (و +1,295, از +964, دل +231). The losses are the notes' words: جواب
−251, رباعی −113, ایضا −66, الله −122, and the run-together headings that
disappear altogether (منغزلیاته 32, مناشعاره 9). A note's words were counted
as poetry for three months; they are not.

## What moved, record by record

`build/derivations-v16.jsonl` against `-v17` (not in git): **22 records
changed their attestation level, 3,329 more changed a count only.**

| | records | examples |
|---|---|---|
| newly found at spelling level | 14 | نیازمان، بریزا، پایگانه، ناتاب، درشتانه، سپاهیی، گردترا — each once, in a band half |
| no longer found | 8 | هراتی، امروزیان، ورآمده، ناجنبیدن — each once, in a note: a heading's *of Herat* was the only evidence for *Herāti* |

## The word bank's gaps, corpus v17

### The 1,000 most frequent spellings

- **one reading**: 438 — را، او، چون، بود، تا، چو، هر، ما، می، چه، شد، نیست، گفت، جان، همه، هم، مرا، دست، روی، دو
- **several readings**: 194 — از، که، به، در، تو، بر، است، آن، من، این، دل، با، ای، سر، خود، نه، گر، اگر، کرد، کند
- **function word**: 4 — و، ز، بی، همی
- **inflected**: 128 — باشد، گردد، جای، کنم، نور، کنی، اوست، خواهد، نباشد، دهد، گوید، دولت، ندارد، اما، گفتم، رسید، ماند، چیست، کردم، کردی
- **uninflected**: 236 — عشق، الله، غم، عالم، آید، صد، فی، نفس، چند، خلق، حال، تیغ، نظر، عقل، خدا، آفتاب، عمر، حسن، جمله، علم

### Every spelling

| | spellings | running words |
|---|---|---|
| one reading | 21,736 (5.3%) | 8,423,574 (33.0%) |
| several readings | 1,394 (0.3%) | 7,110,435 (27.8%) |
| function word | 4 (0.0%) | 1,484,047 (5.8%) |
| inflected | 55,685 (13.6%) | 2,876,176 (11.3%) |
| uninflected | 331,136 (80.8%) | 5,637,827 (22.1%) |

### Texts, word by word

- `ganjoor:hafez:2132` (حافظ · غزلیات · غزل شمارهٔ ۳): 159 words — one reading 52, several readings 42, function word 12, inflected 20, uninflected 33
- `ganjoor:saadi:41293` (سعدی · گلستان · دیباچه): 2,442 words — one reading 632, several readings 615, function word 183, inflected 273, uninflected 739

`tools/measure_bank_gaps.py v17 --top 1000 --text ganjoor:hafez:2132 --text
ganjoor:saadi:41293`. What it means is in UPSTREAM B9 and FOR_THE_LINGUIST L38.
