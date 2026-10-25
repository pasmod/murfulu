# Corpus v12 → v13 (karbon 1.2.0 lexicon)

Measured 2026-10-18 before the release. v13 is v12's recipe (docs/ENGINEERING.md)
with one input changed: the lexicon, `lexicon-20260808` → `lexicon-20261012`
(karbon 1.2.0). No engine code changed between the two builds (`git diff
9524237` touches only the questions form), so every difference below is the
lexicon's — and the attribution checks that rather than assuming it.

## Summary

| | v12 | v13 | change |
|---|---:|---:|---:|
| documents / tokens / spellings | 133,148 / 25,497,189 / 409,916 | same | — |
| spellings linked | 16,714 | 16,713 | −1 |
| documents without century | 98,627 | 98,627 | — |
| derivation records | 1,870,987 | 1,844,043 | **−26,944 (−1.4%)** |
| paths | 2,824,095 | 2,794,905 | −29,190 |
| attested records | 27,333 | 27,214 | −119 |
| word types (index) | 411,165 | 411,167 | +2 |

**Every lost and every gained path traces to a lexicon row that changed: 0
paths moved whose source reading did not.** Net paths by cause:

| cause | lost | gained | net |
|---|---:|---:|---:|
| adjectives read differently (165 readings, e.g. *rošan* → *rowšan*, *yak* → *yek*, *ke* → *keh*) | 57,040 | 37,200 | −19,840 |
| adjectives' second readings changed or dropped (`phonemic_variants`, swapped primary) | 17,360 | 8,060 | −9,300 |
| adjective rows removed (10 readings, e.g. مزیب *mozayyab*, شوک *šuk*) | 6,200 | 0 | −6,200 |
| verbs read differently (92 readings; typo fixes like *eftālidn* → *eftālidan*) | 47,150 | 47,150 | 0 |
| changed stems or regrouped readings (55 verbs, e.g. کشیدن, نهفتیدن, فشردن; 11 adjectives) | 47,118 | 47,118 | 0 |
| verb rows added (6, e.g. بیوزنیدن, بیوباردن) | 0 | 6,150 | +6,150 |
| **overrides** (آزردن, گسیختن, رُفتن) | 0 | 0 | 0 — all three applied to both snapshots |
| source unchanged | 0 | 0 | 0 |

The net loss is the adjectives: karbon 1.2.0 re-read its adjectives (ruleset
`V.7+V.9e-adj`), and the new readings build fewer forms than the old ones, or
collapse into readings that already existed. The verbs move one-for-one.

Attested records: 1,287 gone, 1,168 new. The largest moves are the same words
re-read — یک *Yak* (55,782 occurrences) gone with *yak* → *yek*; روشن
*Rošan* → *Rowšan*; کو *Kao* → *Kav* (karbon's *kaο* carried a Greek omicron);
ازین *Āzin* → *Azin*. One to check with karbon: که is now read *keh* (was *ke*),
and *Keh* claims the conjunction's 609,699 occurrences as attestation of an
adjective — a homograph, not evidence.

## Lexicon and derivations, path by path

`tools/attribute_lexicon_change.py data/lexicon-20260808.sqlite
data/lexicon-20261012.sqlite build/derivations-v12.jsonl
build/derivations-v13.jsonl`

## Lexicon

- `lexicon-20260808:45e05ff66c37`: overrides 3 applied on lexicon-20260808:45e05ff66c37 (3 unconfirmed)
- `lexicon-20261012:af0310b6446c`: overrides 3 applied on lexicon-20261012:af0310b6446c (3 unconfirmed)

### Input-pool readings that differ

- reading changed (صفت): 165
- needs_review changed: 128
- reading changed (مصدر): 92
- stems changed: 66
- stems changed + variants changed: 24
- stems changed + variants changed + primary/variant swapped: 11
- row removed (صفت): 10
- row added (مصدر): 6
- variants changed + primary/variant swapped: 3
- category changed + variants changed: 1
- stems changed + variants changed + needs_review changed: 1

## Derivations

- records 1,870,987 → 1,844,043 (-26,944)
- records gone 105,732, new 78,788
- paths lost 174,868, gained 145,678
- **paths whose source did not change: lost 0, gained 0** (must be 0 for the difference to be the lexicon's alone)

### Records gone, by what happened to their source

- reading changed (صفت): 40,612
- stems changed: 24,560
- reading changed (مصدر): 22,213
- stems changed + variants changed: 12,162
- row removed (صفت): 5,149
- stems changed + variants changed + needs_review changed: 521
- category changed + variants changed: 515

### Records new, by what happened to their source

- reading changed (صفت): 29,681
- stems changed: 24,214
- reading changed (مصدر): 21,721
- row added (مصدر): 3,172

### Paths lost, by cause

- reading changed (صفت): 57,040
- reading changed (مصدر): 47,150
- stems changed: 47,118
- stems changed + variants changed: 15,500
- row removed (صفت): 6,200
- category changed + variants changed: 1,240
- stems changed + variants changed + needs_review changed: 620

### Paths gained, by cause

- reading changed (مصدر): 47,150
- stems changed: 47,118
- reading changed (صفت): 37,200
- stems changed + variants changed + primary/variant swapped: 6,820
- row added (مصدر): 6,150
- variants changed + primary/variant swapped: 1,240

### Examples

- gained: reading changed (صفت)
  - `forupalanginegā:barnam` ← پلنگینه *palangine* N-033/N-014
  - `nānowbāšsār:barnam` ← نوباش *nowbāš* N-055/N-021
  - `nānowbāšsār:barnam` ← نوباش *nowbāš* N-021/N-055
  - `nākondvālegāne:jonvaze` ← کندواله *kondvāle* N-021/N-040
- gained: reading changed (مصدر)
  - `Dožlaqqāndbān:nam` ← لقاندن *laqqāndan* V-015/N-011
  - `nazodāye:barnam` ← زدودن *zodudan* V-063/N-087
  - `nazodāye:barnam` ← زدودن *zodudan* V-034/N-019
  - `Tabāhākdān:nam` ← تباهیدن *tabāhidan* V-039/N-048
- gained: row added (مصدر)
  - `biyowbardgār:karandekarbahr` ← بیوبردن *biyowbardan* V-013
  - `andarbiyowzanidan:nabesudkarvaze` ← بیوزنیدن *biyowzanidan* V-005/V-052
  - `Nābiyowgande:nam` ← بیوگندن *biyowgandan* V-066/N-088
  - `Biyowbārdebār:nam` ← بیوباردن *biyowbārdan* V-009/N-043
- gained: stems changed
  - `bišakibāyide:barnam` ← شکیباییدن *šakibāyidan* V-009/N-008
  - `Boxridbānzār:nam` ← بخریدن *boxridan* V-015/N-050
  - `čarastvarsār:barnam` ← چرستیدن *čarastidan* V-042/N-055
  - `Vidbāngāni:nam` ← ویدن *vidan* V-015/N-067
- gained: stems changed + variants changed + primary/variant swapped
  - `nazodāye:barnam` ← زدا *zodā* N-018/N-087
  - `nazodāye:barnam` ← زدا *zodā* N-087/N-018
  - `nazodāye:barnam` ← زدا *zodā* N-088/N-019
  - `bāzšegarfidan:nabesudkarvaze` ← شگرف *šegarf* V-003/V-054
- gained: variants changed + primary/variant swapped
  - `gatevārin:barnam` ← گته *gate* N-077/N-101
  - `gatenāvār:barnam` ← گته *gate* N-072/N-074
  - `gatenāvār:barnam` ← گته *gate* N-072/N-076
  - `gatenāvār:barnam` ← گته *gate* N-072/N-075
- lost: category changed + variants changed
  - `yakgānegi:jonvaze` ← یک *yak* N-066/N-096
  - `yeksirumand:barnam` ← یک *yak* N-058/N-083
  - `yekegi:barnam` ← یک *yak* N-088/N-094
  - `yekegi:barnam` ← یک *yak* N-088/N-092
- lost: reading changed (صفت)
  - `vāsatorgidan:nabesudkarvaze` ← سترگ *sotorg* V-003/V-073
  - `vāsatorgidan:nabesudkarvaze` ← سترگ *sotorg* V-003/V-071
  - `vāsatorgidan:nabesudkarvaze` ← سترگ *sotorg* V-003/V-070
  - `vāsatorgidan:nabesudkarvaze` ← سترگ *sotorg* V-003/V-069
- lost: reading changed (مصدر)
  - `ozdvdegān:jonvaze` ← ازدودن *ozdvdan* V-009/N-036
  - `Beyāvāgi:karnam` ← بیاویدن *beyāvidan* V-026/V-082
  - `Beyāvāgi:karnam` ← بیاویدن *beyāvidan* V-024/V-023
  - `farānoxidan:nabesudkarvaze` ← نوخیدن *noxidan* V-005/V-058
- lost: row removed (صفت)
  - `gezāfvārgān:barnam` ← گذاف *gozāf* N-077/N-065
  - `Lašnsirgāni:nam` ← لشن *lašen* N-058/N-067
  - `qalahjingānegidan:nabesudkarvaze` ← غله‌جین *qalahjin* N-066/V-003
  - `šukāān:jonvaze` ← شوک *šuk* N-033/N-036
- lost: stems changed
  - `čašānmānine:barnam` ← چشانیدن *češānidan* V-038/N-103
  - `čašānmānine:barnam` ← چشاندن *češāndan* V-038/N-103
  - `nākašānidi:jonvaze` ← کشانیدن *kešānidan* V-066/N-096
  - `hamfašānmān:barnam` ← فشاندن *fešāndan* V-038/N-015
- lost: stems changed + variants changed
  - `Gondelielāx:nam` ← گندلی *gondoli* N-088/N-070
  - `Raxjsirzār:nam` ← رخج *raxaj* N-058/N-050
  - `gāvorsirgin:barnam` ← گاور *gāvar* N-058/N-035
  - `gāvorsirgin:barnam` ← گاور *gāvar* N-058/N-069
- lost: stems changed + variants changed + needs_review changed
  - `pazuigānee:barnam` ← پزوی *pazvi* N-066/N-087
  - `farāpazuiyidan:nabesudkarvaze` ← پزوی *pazvi* V-003/V-058
  - `Pazuinā:nam` ← پزوی *pazvi* N-072
  - `pazuisārgān:barnam` ← پزوی *pazvi* N-055/N-065

## compare_versions.py

`tools/compare_versions.py --report data/corpus_report-v12.json
data/corpus_report-v13.json --derivations build/derivations-v12.jsonl
build/derivations-v13.jsonl`

```
corpus report      v12 -> v13
  documents                         133,148       133,148   same
  tokens                         25,497,189    25,497,189   same
  spellings                         409,916       409,916   same
  spellings_linked                   16,714        16,713   -1
  documents_without_century          98,627        98,627   same
  lexicon snapshot moved: lexicon-20260808:45e05ff66c37 -> lexicon-20261012:af0310b6446c

derivations        derivations-v12.jsonl -> derivations-v13.jsonl
  records                         1,870,987     1,844,043   -26,944
  paths                           2,824,095     2,794,905   -29,190
  attested                           27,333        27,214   -119
  162 rules moved:
  N-072                             134,575       130,208   -4,367
  N-058                             134,575       130,208   -4,367
  N-033                             131,365       127,112   -4,253
  N-088                             124,752       120,731   -4,021
  V-003                             122,738       119,078   -3,660
  N-081                              68,325        66,601   -1,724
  N-082                              68,325        66,601   -1,724
  V-004                              65,095        63,486   -1,609
  N-066                              55,937        54,363   -1,574
  N-101                              55,889        54,315   -1,574
  N-055                              55,937        54,363   -1,574
  N-045                              55,937        54,363   -1,574
  N-065                              55,937        54,363   -1,574
  N-077                              55,938        54,364   -1,574
  N-087                              54,284        52,767   -1,517
  N-018                              41,633        40,451   -1,182
  N-021                              41,632        40,450   -1,182
  N-040                              36,676        35,786   -890
  N-096                              32,972        32,139   -833
  N-095                              40,552        39,740   -812
  N-103                              17,241        16,919   -322
  N-044                              12,342        12,125   -217
  N-036                              14,074        13,865   -209
  N-027                              14,074        13,865   -209
  N-035                              14,074        13,865   -209
  N-028                              14,074        13,865   -209
  N-025                              14,074        13,865   -209
  N-067                              14,074        13,865   -209
  N-005                              14,074        13,865   -209
  N-050                              14,074        13,865   -209
  N-047                              14,074        13,865   -209
  N-069                              14,074        13,865   -209
  N-053                              14,074        13,865   -209
  N-060                              14,074        13,865   -209
  N-042                              14,074        13,865   -209
  N-015                              14,074        13,865   -209
  N-100                              14,074        13,865   -209
  N-002                              14,074        13,865   -209
  N-008                              14,074        13,865   -209
  N-061                              14,074        13,865   -209
  N-014                              14,074        13,865   -209
  N-079                              14,074        13,865   -209
  N-078                              14,074        13,865   -209
  N-007                              14,074        13,865   -209
  N-094                              14,074        13,865   -209
  N-037                              14,074        13,865   -209
  N-048                              14,074        13,865   -209
  N-057                              14,074        13,865   -209
  N-031                              14,074        13,865   -209
  N-074                              14,074        13,865   -209
  N-022                              14,074        13,865   -209
  N-063                              14,074        13,865   -209
  N-026                              14,074        13,865   -209
  N-049                              14,074        13,865   -209
  N-012                              14,074        13,865   -209
  N-073                              14,074        13,865   -209
  N-046                              14,074        13,865   -209
  N-052                              14,074        13,865   -209
  N-003                              14,074        13,865   -209
  N-070                              14,074        13,865   -209
  N-038                              14,074        13,865   -209
  N-105                              14,074        13,865   -209
  N-030                              14,074        13,865   -209
  N-054                              14,074        13,865   -209
  N-093                              14,074        13,865   -209
  N-029                              14,074        13,865   -209
  N-062                              14,074        13,865   -209
  N-068                              14,074        13,865   -209
  N-011                              14,074        13,865   -209
  N-056                              14,074        13,865   -209
  N-084                              14,074        13,865   -209
  N-019                              14,074        13,865   -209
  N-051                              14,074        13,865   -209
  N-076                              14,074        13,865   -209
  N-092                              14,074        13,865   -209
  N-010                              14,074        13,865   -209
  N-071                              14,074        13,865   -209
  N-004                              14,074        13,865   -209
  N-043                              14,074        13,865   -209
  N-039                              14,074        13,865   -209
  N-024                              14,074        13,865   -209
  N-059                              14,074        13,865   -209
  N-083                              14,074        13,865   -209
  N-034                              14,074        13,865   -209
  N-041                              14,074        13,865   -209
  N-075                              14,074        13,865   -209
  N-006                              14,074        13,865   -209
  N-080                              14,074        13,865   -209
  N-064                              14,074        13,865   -209
  N-086                               9,420         9,259   -161
  N-089                               9,420         9,259   -161
  N-085                               9,420         9,259   -161
  N-032                              12,474        12,320   -154
  N-001                              12,474        12,320   -154
  N-016                               3,208         3,094   -114
  N-102                               3,208         3,094   -114
  V-069                               9,657         9,570   -87
  V-053                              11,382        11,303   -79
  V-060                              11,382        11,303   -79
  V-059                              11,382        11,303   -79
  V-058                              11,382        11,303   -79
  V-062                              11,382        11,303   -79
  V-054                              11,382        11,303   -79
  V-051                              11,360        11,281   -79
  V-061                              11,382        11,303   -79
  V-057                              11,382        11,303   -79
  V-056                              11,382        11,303   -79
  V-068                              11,382        11,303   -79
  V-055                              11,382        11,303   -79
  V-052                              11,382        11,303   -79
  V-067                              11,400        11,321   -79
  V-063                              34,311        34,248   -63
  V-065                              34,311        34,248   -63
  V-049                               8,722         8,664   -58
  N-097                               1,605         1,548   -57
  V-034                              91,785        91,730   -55
  V-038                              99,363        99,308   -55
  V-039                              99,362        99,307   -55
  V-035                               8,681         8,627   -54
  V-037                               8,716         8,662   -54
  V-024                              10,154        10,100   -54
  V-050                               8,681         8,627   -54
  V-036                               8,681         8,627   -54
  V-040                              10,154        10,100   -54
  V-028                              10,155        10,101   -54
  V-026                              10,154        10,100   -54
  V-048                              10,154        10,100   -54
  V-032                              10,155        10,101   -54
  V-041                              36,042        35,988   -54
  V-022                               8,681         8,627   -54
  V-042                              36,042        35,988   -54
  V-029                              10,154        10,100   -54
  V-033                               8,681         8,627   -54
  V-001                              25,927        25,874   -53
  V-002                              25,927        25,874   -53
  V-007                              10,182        10,167   -15
  V-006                              10,182        10,167   -15
  V-008                              10,182        10,167   -15
  V-014                              10,182        10,167   -15
  V-010                              10,182        10,167   -15
  V-020                              10,182        10,167   -15
  V-012                              11,914        11,907   -7
  V-011                              11,914        11,907   -7
  V-013                              11,914        11,907   -7
  V-023                              12,048        12,062   +14
  V-025                              12,048        12,062   +14
  V-030                              12,048        12,062   +14
  V-082                               7,753         7,768   +15
  V-027                               7,753         7,768   +15
  N-098                              53,307        53,338   +31
  V-005                              30,913        30,993   +80
  V-064                              41,358        41,487   +129
  V-066                              41,358        41,487   +129
  V-071                              84,815        84,988   +173
  V-076                              84,808        84,981   +173
  V-070                              84,815        84,988   +173
  V-073                              84,815        84,988   +173
  V-075                              84,810        84,983   +173
  V-072                              84,815        84,988   +173
  V-074                              84,810        84,983   +173
  V-009                             110,630       111,076   +446
  V-015                             117,558       118,036   +478
```
