# Corpus v14 → v15 (karbon 1.3.2, the linguist's word bank)

Measured 2026-11-12 on the Mac, **before any release**: the v15 indices sit in
the Mac's Elasticsearch beside v12, and no alias points at them. v15 is v14's
recipe (docs/ENGINEERING.md) with the lexicon changed, `lexicon-20261012` →
`lexicon-20261111` (karbon 1.3.2), and with the two changes that came with it
(docs/DECISIONS.md, 2026-11-12): word classes are read from the linguist's
word-bank groups, and a loanword builds nothing. Corpus text, semantic vectors
and suspect claims are v14's (all v4). No other engine code changed since v14
(`git diff cb76959 ccd7fee -- src rules` is empty). L26's switch is **off**.

Built with `tools/build_corpus_mac.sh v15 lexicon-20261111` in **7.5 minutes**
(precompute 5.5), **peak 7.2 GB** resident (`/usr/bin/time -l`: 443 s real,
maximum resident set 7,154,024,448 bytes) — on the Mac itself, not in a
container: Docker Desktop has 7.7 GB for everything it runs (S35).

## Summary

| | v14 | v15 | change |
|---|---:|---:|---:|
| documents / tokens / spellings | 133,148 / 25,497,189 / 409,916 | same | — |
| **spellings linked to the lexicon** | 16,713 | **23,127** | **+6,414 (+38%)** |
| words of text linked | 11,644,755 (45.7%) | 15,510,933 (60.8%) | +3,866,178 |
| spellings with more than one reading | 1,039 | 1,394 | +355 |
| input pool (مصدر، صفت، اسم معنی) | 5,209 readings | 14,089 | +8,880 |
| derivation records | 1,844,043 | **2,949,164** | **+1,105,121 (+60%)** |
| paths | 2,794,905 | 4,342,574 | +1,547,669 |
| attested records | 27,176 | 30,158 | +2,982 |
| corpus word types traced to a rule (affix map) | — | 3,030 | |

**Every lost and every gained path traces to a lexicon reading that changed
in a way the build can feel — 0 paths are left unexplained.** That line is the
check, and it is strict: a change in the review flag alone, or in the
dictionary's label without a change in word classes or in membership of the
build's input pool, explains nothing and counts against it. Two rounds made it
so. The first run read 19: 1.3.2 added کشنی *Košni* as a row of its own (a
کارنام, so in the pool), which 1.2.0 had only as a second reading of *Kešni*,
and the tool matched the key to the older row; it now prefers a word's own
reading. The second read 4,960 lost paths "label only": فری and وش went from
صفت to صوت and پسوند, still برنام by group, but out of the pool, which is still
chosen by the dictionary's label; the tool now names that "left the input
pool".

**No rule builds less than in v14.** The growth is the pool: 14,089 readings
against 5,209, and 8,754 of them are made only of rows that are new to the
bank — neither 1.2.0 rows nor merged from them: 7,961 اسم معنی (کارنام; the
former اسم مصدر was folded in on 2026-10-24), 789 صفت, 4 مصدر. A word in more
than one group now feeds each of them (2,986 words in the bank). The largest
causes of new paths, counted by the tool in reading keys (a spelling with one
Latin form, second readings included): added صفت rows (1.01 million paths),
added اسم معنی rows (0.31 million), a category and word-class change
(0.10 million).

**What was lost is small and named**: 120,268 paths, 86,217 records. Most of
it is the linguist's re-reading — صفت readings changed (35,340 paths), words
moved between groups (29,140), changed stems (6,320, among them آزردن and
گسیختن, now built on *āzār* and *gosal*: v14 had built them on *āzor* and
*gosil* because the override corrected only the Persian stem, DECISIONS
2026-11-12), and rows removed or merged (3,100 each).

**More of the poetry is now the lexicon's.** 60.8% of the corpus's running
words are linked to a lexicon reading, against 45.7%. Measured by linking the
corpus against both lexicons: **6,488 spellings are newly linked, 3,921,470
occurrences**, and 74 are no longer linked (55,292). The newly linked are the
short frequent words the bank added: بر 265,119, آن 240,366, او 184,486, چون
157,382, چو 134,032, ما 115,948, چه 105,045.

**And with them, three verb forms that are not words of their own.** بود
143,873, شد 100,612 and نیست 81,302 are newly linked to کارنام entries the bank
added (*Bud*, *Šod*, *Nist*). The corpus's بود is the verb *was*, so whatever
is built on *Bud* is credited with the verb's occurrences — the shape of که in
v13, which the function-word list answered. They are not on that list, which
left verb forms out on purpose; whether to add them is the project lead's call
(OPEN_QUESTIONS). The bank's suffix entries are the same risk on a smaller
scale: a پسوند entry claims every corpus spelling written like it.

## What it means for the release

- **Size**: derivations-v15 778 MB (v12's 492 MB), documents-v15 195 MB,
  word_types-v15 72 MB — about 1.05 GB to move by snapshot.
- **Where it is built**: not on the VPS beside Sokhan (7.2 GB peak against the
  ~3 GB left there). Built on the Mac, and moved as a snapshot of the three v15
  indices; `deploy/server.sh corpus` snapshots on the previous host and
  includes `passages`, so the Mac route is prepared in DEPLOY, not yet run.
- **L26's switch**, if turned on, multiplies the pool's forms about tenfold
  (3.0 to 29.1 million, `tools/measure_karnam_switch.py`), which neither the
  Mac's Elasticsearch nor the VPS was sized for. It waits for the ruling.

## Commands

```
tools/build_corpus_mac.sh v15 lexicon-20261111
tools/compare_versions.py --report data/corpus_report-v14.json data/corpus_report-v15.json \
  --derivations build/derivations-v14.jsonl build/derivations-v15.jsonl
git show ccd7fee:rules/lexicon_overrides.yaml > /tmp/overrides-v14.yaml
tools/attribute_lexicon_change.py data/lexicon-20261012.sqlite data/lexicon-20261111.sqlite \
  build/derivations-v14.jsonl build/derivations-v15.jsonl --old-overrides /tmp/overrides-v14.yaml
```

# Lexicon and derivations, path by path

The attribution tool's own output follows.

## Lexicon (attribution)

- `lexicon-20261012:af0310b6446c`: overrides 3 applied on lexicon-20261012:af0310b6446c (3 unconfirmed)
- `lexicon-20261111:e300dbc27083`: overrides 1 applied on lexicon-20261111:e300dbc27083 (1 unconfirmed)

### Input-pool readings that differ

- row added (اسم معنی): 8,480
- row added (صفت): 839
- reading changed (اسم معنی): 417
- reading changed (صفت): 207
- category changed + word classes changed + entered the input pool: 158
- variants changed: 134
- stems changed + category changed + word classes changed + entered the input pool: 88
- stems changed: 87
- merged into another row (اسم معنی): 59
- metadata only (needs_review changed): 59
- category changed + word classes changed + left the input pool: 47
- row removed (اسم معنی): 38
- word classes changed: 27
- stems changed + variants changed + primary/variant swapped: 17
- stems changed + category changed + word classes changed + left the input pool: 16
- category changed + word classes changed: 15
- reading changed (مصدر): 14
- stems changed + variants changed: 12
- variants changed + primary/variant swapped: 11
- category changed + needs_review changed + word classes changed + entered the input pool: 9
- category changed + variants changed + primary/variant swapped + word classes changed + entered the input pool: 8
- stems changed + category changed + word classes changed: 8
- category changed + left the input pool: 8
- variants changed + needs_review changed + primary/variant swapped: 8
- category changed + variants changed + word classes changed + entered the input pool: 6
- variants changed + word classes changed: 6
- stems changed + variants changed + needs_review changed + primary/variant swapped: 5
- row removed (صفت): 5
- stems changed + category changed + left the input pool: 4
- needs_review changed + word classes changed: 4
- stems changed + category changed + needs_review changed + word classes changed + left the input pool: 4
- merged into another row (صفت): 4
- stems changed + needs_review changed: 4
- variants changed + needs_review changed: 3
- stems changed + category changed + variants changed + word classes changed + entered the input pool: 3
- stems changed + category changed + variants changed + needs_review changed + primary/variant swapped + word classes changed + left the input pool: 3
- row added (مصدر): 2
- row changed otherwise (اسم معنی): 2
- stems changed + category changed + variants changed + primary/variant swapped + word classes changed + entered the input pool: 2
- stems changed + variants changed + needs_review changed: 2
- stems changed + category changed + needs_review changed + word classes changed: 1
- stems changed + category changed + variants changed + word classes changed + left the input pool: 1
- stems changed + variants changed + primary/variant swapped + word classes changed: 1
- variants changed + needs_review changed + word classes changed: 1
- stems changed + category changed + needs_review changed + word classes changed + entered the input pool: 1
- stems changed + category changed + needs_review changed + left the input pool: 1
- category changed + primary/variant swapped + word classes changed + entered the input pool: 1
- stems changed + word classes changed: 1
- category changed + variants changed + word classes changed + left the input pool: 1
- category changed + variants changed + word classes changed: 1

## Derivations

- records 1,844,043 → 2,949,164 (+1,105,121)
- records gone 86,217, new 1,191,338
- paths lost 120,268, gained 1,667,937
- **paths no change in their source explains: lost 0, gained 0** (source unchanged, metadata only, or in neither snapshot; must be 0 for the difference to be the lexicon's alone)

### Records gone, by what happened to their source

- reading changed (صفت): 26,940
- category changed + word classes changed + left the input pool: 23,169
- stems changed + category changed + word classes changed + left the input pool: 7,900
- category changed + left the input pool: 4,069
- stems changed: 3,997
- reading changed (اسم معنی): 3,509
- merged into another row (صفت): 2,593
- reading changed (مصدر): 2,212
- stems changed + category changed + needs_review changed + word classes changed + left the input pool: 1,901
- stems changed + category changed + left the input pool: 1,743
- row removed (صفت): 1,554
- variants changed: 1,092
- stems changed + variants changed + needs_review changed: 1,039
- stems changed + category changed + variants changed + needs_review changed + primary/variant swapped + word classes changed + left the input pool: 1,021
- merged into another row (اسم معنی): 938
- stems changed + variants changed: 765
- row removed (اسم معنی): 721
- stems changed + category changed + variants changed + word classes changed + left the input pool: 519
- stems changed + category changed + needs_review changed + left the input pool: 516
- variants changed + primary/variant swapped: 19

### Records new, by what happened to their source

- row added (صفت): 684,328
- row added (اسم معنی): 251,550
- category changed + word classes changed + entered the input pool: 80,720
- stems changed + category changed + word classes changed + entered the input pool: 45,092
- reading changed (صفت): 44,595
- variants changed: 33,154
- reading changed (اسم معنی): 8,524
- category changed + needs_review changed + word classes changed + entered the input pool: 8,404
- category changed + variants changed + word classes changed + entered the input pool: 6,236
- reading changed (مصدر): 5,622
- variants changed + word classes changed: 3,855
- word classes changed: 3,314
- stems changed + category changed + variants changed + primary/variant swapped + word classes changed + entered the input pool: 2,864
- needs_review changed + word classes changed: 2,209
- category changed + variants changed + primary/variant swapped + word classes changed + entered the input pool: 2,144
- stems changed + category changed + variants changed + word classes changed + entered the input pool: 2,110
- stems changed: 2,092
- variants changed + needs_review changed: 1,555
- row added (مصدر): 902
- variants changed + needs_review changed + word classes changed: 555
- category changed + variants changed + word classes changed: 552
- stems changed + category changed + needs_review changed + word classes changed + entered the input pool: 535
- category changed + word classes changed: 260
- stems changed + category changed + word classes changed: 129
- stems changed + word classes changed: 17
- stems changed + category changed + needs_review changed + word classes changed: 17
- stems changed + variants changed + primary/variant swapped + word classes changed: 3

### Paths lost, by cause

- reading changed (صفت): 35,340
- category changed + word classes changed + left the input pool: 29,140
- stems changed + category changed + word classes changed + left the input pool: 9,920
- stems changed: 6,320
- variants changed + needs_review changed + primary/variant swapped: 4,960
- category changed + left the input pool: 4,960
- reading changed (مصدر): 4,100
- reading changed (اسم معنی): 3,952
- merged into another row (صفت): 3,100
- row removed (صفت): 3,100
- stems changed + category changed + left the input pool: 2,480
- stems changed + category changed + needs_review changed + word classes changed + left the input pool: 2,480
- variants changed + primary/variant swapped: 2,031
- variants changed: 1,316
- stems changed + variants changed + needs_review changed: 1,240
- stems changed + category changed + variants changed + needs_review changed + primary/variant swapped + word classes changed + left the input pool: 1,240
- merged into another row (اسم معنی): 1,121
- stems changed + variants changed: 867
- row removed (اسم معنی): 722
- category changed + variants changed + word classes changed + left the input pool: 620
- stems changed + category changed + variants changed + word classes changed + left the input pool: 620
- stems changed + category changed + needs_review changed + left the input pool: 620
- row changed otherwise (اسم معنی): 19

### Paths gained, by cause

- row added (صفت): 1,011,999
- row added (اسم معنی): 308,530
- category changed + word classes changed + entered the input pool: 103,376
- reading changed (صفت): 61,292
- stems changed + category changed + word classes changed + entered the input pool: 56,006
- variants changed: 41,067
- category changed + needs_review changed + word classes changed + entered the input pool: 12,035
- reading changed (اسم معنی): 11,599
- reading changed (مصدر): 10,250
- category changed + variants changed + word classes changed + entered the input pool: 7,668
- stems changed: 6,320
- word classes changed: 5,276
- variants changed + word classes changed: 4,656
- stems changed + category changed + variants changed + primary/variant swapped + word classes changed + entered the input pool: 4,420
- variants changed + needs_review changed + primary/variant swapped: 4,340
- needs_review changed + word classes changed: 3,898
- stems changed + variants changed + needs_review changed + primary/variant swapped: 3,100
- category changed + variants changed + primary/variant swapped + word classes changed + entered the input pool: 2,643
- stems changed + category changed + variants changed + word classes changed + entered the input pool: 2,556
- row added (مصدر): 2,050
- variants changed + needs_review changed: 1,860
- category changed + variants changed + word classes changed: 658
- variants changed + needs_review changed + word classes changed: 658
- stems changed + category changed + needs_review changed + word classes changed + entered the input pool: 639
- category changed + word classes changed: 353
- stems changed + variants changed + primary/variant swapped: 323
- stems changed + category changed + word classes changed: 152
- variants changed + primary/variant swapped: 133
- stems changed + variants changed + primary/variant swapped + word classes changed: 23
- stems changed + word classes changed: 19
- row changed otherwise (اسم معنی): 19
- stems changed + category changed + needs_review changed + word classes changed: 19

### Examples

- gained: category changed + needs_review changed + word classes changed + entered the input pool
  - `xunriznāāsā:barnam` ← خونریز *xunriz* N-072/N-034
  - `Bināyiyandargar:nam` ← بینایی *Bināyi* N-038/N-063
  - `Gušpičvašsir:nam` ← گوش‌پیچ *gušpič* N-082/N-058
  - `Bināyisānsir:nam` ← بینایی *Bināyi* N-056/N-058
- gained: category changed + variants changed + primary/variant swapped + word classes changed + entered the input pool
  - `Došbornāye:nam` ← برنا *bornā* N-088/N-010
  - `Došbornāā:nam` ← برنا *bornā* N-033/N-010
  - `bornāknāsār:barnam` ← برناک *bornāk* N-072/N-051
  - `bornāknāsār:barnam` ← برناک *bornāk* N-072/N-054
- gained: category changed + variants changed + word classes changed
  - `Zirkalikaynā:nam` ← کلیکی *kaliki* N-072/N-031
  - `kalikaysārgāne:barnam` ← کلیکی *kaliki* N-055/N-066
  - `kalikiyi:barnam` ← کلیکی *kaliki* N-098
  - `kalikayāānidan:nabesudkarvaze` ← کلیکی *kaliki* N-033/V-004
- gained: category changed + variants changed + word classes changed + entered the input pool
  - `Sartāsbāgāh:nam` ← سرتاسب *sartāsb* N-033/N-068
  - `Kamāsenāvāre:nam` ← کماسه *komāse* N-072/N-078
  - `Kamāsenāvāre:nam` ← کماسه *komāse* N-072/N-079
  - `Gardesir:nam` ← گرد *gord* N-087/N-058
- gained: category changed + word classes changed
  - `nāxabregi:barnam` ← خبره *xabre* N-098/N-021
  - `šekofti:barnam` ← شکفت *šekoft* N-098
  - `nāxaraštegi:barnam` ← خرشته *xarašte* N-098/N-021
  - `barāmadigāne:barnam` ← برآمد *barāmad* N-098/N-066
- gained: category changed + word classes changed + entered the input pool
  - `nāsarābilisir:barnam` ← سرآبیلی *sarābili* N-058/N-022
  - `nāzāyesfānvaš:barnam` ← زایسفان *zāyesfān* N-021/N-082
  - `nāzāyesfānvaš:barnam` ← زایسفان *zāyesfān* N-082/N-021
  - `dabirtarvār:barnam` ← دبیر *dabir* N-045/N-077
- gained: needs_review changed + word classes changed
  - `sarpišeumand:barnam` ← پیشه *Piše* N-028/N-083
  - `Pišegāhdān:nam` ← پیشه *Piše* N-068/N-048
  - `Pādpišedis:nam` ← پیشه *Piše* N-024/N-049
  - `Pādpišedis:nam` ← پیشه *Piše* N-049/N-025
- gained: reading changed (اسم معنی)
  - `vāyestnāye:barnam` ← وایست *Vāyest* N-072/N-085
  - `Yeknādān:nam` ← یک *Yek* N-072/N-048
  - `naxeyriegi:jonvaze` ← نخیری *Naxeyri* N-087/N-096
  - `xāmyāzegisār:barnam` ← خامیازه *Xāmyāze* N-098/N-055
- gained: reading changed (صفت)
  - `istādeeur:barnam` ← ایستاده *istāde* N-088/N-081
  - `istādeeur:barnam` ← ایستاده *istāde* N-087/N-081
  - `Inhasesirdān:nam` ← اینهسه *inhase* N-058/N-048
  - `gedāygānevaš:barnam` ← گدای *gadāy* N-066/N-082
- gained: reading changed (مصدر)
  - `Pišāčāridbān:nam` ← آچاریدن *āčāridan* V-015/N-026
  - `Sarowbāride:nam` ← اوباریدن *owbāridan* V-009/N-028
  - `Nāāčārsir:nam` ← آچاریدن *āčāridan* V-065/N-058
  - `bākobāk:barnam` ← کبیدن *kobidan* V-039/N-002
- gained: row added (اسم معنی)
  - `Šuriderāyiyiyā:nam` ← شوریده‌رایی *Šuriderāyi* N-098/N-033
  - `nājahāngošāyiyi:barnam` ← جهانگشایی *Jahāngošāyi* N-098/N-021
  - `gezāfguyiyiyāne:jonvaze` ← گزاف‌گویی *Gazāfguyi* N-098/N-040
  - `čarbandegiyiyāne:jonvaze` ← چربندگی *Čarbandegi* N-098/N-040
- gained: row added (صفت)
  - `Došhijdahomināne:nam` ← هیجدهمین *hijdahomin* N-010/N-041
  - `Došhijdahomināne:nam` ← هیجدهمین *hijdahomin* N-041/N-010
  - `nowruzisirgi:barnam` ← نوروزی *nowruzi* N-058/N-092
  - `hiždahtarsār:barnam` ← هیژده *hiždah* N-045/N-055
- gained: row added (مصدر)
  - `vānemudār:karandekarbahr` ← وانمودن *vānemudan* V-011
  - `navānemāgāne:barnam` ← وانمودن *vānemudan* V-063/N-066
  - `vānemudenāk:barnam` ← وانمودن *vānemudan* V-009/N-073
  - `hamvaravbāaštan:nabesudkarvaze` ← اوباشتن *avbāaštan* V-074/V-062
- gained: row changed otherwise (اسم معنی)
  - `jadāviyiur:barnam` ← جداوی *Jadāvi* N-098/N-081
  - `jadāviyitar:barnam` ← جداوی *Jadāvi* N-098/N-045
  - `Jadāviyisir:nam` ← جداوی *Jadāvi* N-098/N-058
  - `najadāviyi:barnam` ← جداوی *Jadāvi* N-098/N-018
- gained: stems changed
  - `hamgosalmān:barnam` ← گسیختن *gosixtan* V-038/N-015
  - `varāzārnāk:barnam` ← آزردن *āzordan* V-074/V-041
  - `varāzārnāk:barnam` ← آزردن *āzordan* V-075/V-041
  - `Pičmāngāni:nam` ← پیختن *pixtan* V-038/N-067
- gained: stems changed + category changed + needs_review changed + word classes changed
  - `vādidiyāne:jonvaze` ← وادید *vādid* N-098/N-040
  - `vādidiur:barnam` ← وادید *vādid* N-098/N-081
  - `vādidisār:barnam` ← وادید *vādid* N-098/N-055
  - `vādiditar:barnam` ← وادید *vādid* N-098/N-045
- gained: stems changed + category changed + needs_review changed + word classes changed + entered the input pool
  - `simābdargušgānur:barnam` ← سیماب در گوش *simābdarguš* N-065/N-081
  - `Simābdargušāzār:nam` ← سیماب در گوش *simābdarguš* N-033/N-050
  - `Nasimābdargušsir:nam` ← سیماب در گوش *simābdarguš* N-018/N-058
  - `Simābdargušsirvand:nam` ← سیماب در گوش *simābdarguš* N-058/N-105
- gained: stems changed + category changed + variants changed + primary/variant swapped + word classes changed + entered the input pool
  - `bipādgolfešān:barnam` ← گلفشان *Golfešān* N-025/N-008
  - `bipādgolfešān:barnam` ← گلفشان *Golfešān* N-024/N-008
  - `Dožpādgolfešān:nam` ← گلفشان *Golfešān* N-024/N-011
  - `Dožpādgolfešān:nam` ← گلفشان *Golfešān* N-025/N-011
- gained: stems changed + category changed + variants changed + word classes changed + entered the input pool
  - `nābovandvār:barnam` ← بوند *bovand* N-077/N-021
  - `nābovandvār:barnam` ← بوند *bovand* N-021/N-077
  - `narregāmand:barnam` ← نره *nare* N-033/N-071
  - `Nāštābinsir:nam` ← ناشتاب *nāštāb* N-101/N-058
- gained: stems changed + category changed + word classes changed
  - `ruzegisār:barnam` ← روزه *ruze* N-098/N-055
  - `kālivār:barnam` ← کال *kāl* N-098/N-077
  - `xāstigāne:barnam` ← خواست *xāst* N-098/N-066
  - `xāstiyānidan:nabesudkarvaze` ← خواست *xāst* N-098/V-004
- gained: stems changed + category changed + word classes changed + entered the input pool
  - `nakafčukid:barnam` ← کفچوک *kafčuk* V-003/V-064
  - `sālukeumand:barnam` ← سالوک *sāluk* N-088/N-083
  - `Doškahnkinā:nam` ← کهنکین *kahnkin* N-033/N-010
  - `Kātuzivārnā:nam` ← کاتوزی *kātuzi* N-077/N-072
- gained: stems changed + variants changed + needs_review changed + primary/variant swapped
  - `pāyandegānetar:barnam` ← پایندگان *pāyandegān* N-087/N-045
  - `nažandgānegin:barnam` ← نژند *nažand* N-066/N-101
  - `Nažandekade:nam` ← نژند *nažand* N-088/N-062
  - `bādramegi:jonvaze` ← بادرم *bādram* N-087/N-096
- gained: stems changed + variants changed + primary/variant swapped
  - `zalifaniyidan:nabesudkarvaze` ← زلیفن *Zalifan* N-098/V-003
  - `nahādivaš:barnam` ← نهاد *Nahād* N-098/N-082
  - `namārivaš:barnam` ← نمار *Namār* N-098/N-082
  - `natāzegāni:barnam` ← تازگان *Tāzegān* N-098/N-018
- gained: stems changed + variants changed + primary/variant swapped + word classes changed
  - `Faribie:nam` ← فریب *Farib* N-098/N-088
  - `faribiur:barnam` ← فریب *Farib* N-098/N-081
  - `Faribi:karnam` ← فریب *Farib* V-025
  - `Faribi:karnam` ← فریب *Farib* V-030
- gained: stems changed + word classes changed
  - `Čeliyā:nam` ← چل *čel* N-098/N-033
  - `čeliyin:barnam` ← چل *čel* N-098/N-101
  - `čelivār:barnam` ← چل *čel* N-098/N-077
  - `Čelisir:nam` ← چل *čel* N-098/N-058
- gained: variants changed
  - `Kanjesirsār:nam` ← کنجه *konje* N-058/N-052
  - `Kanjesirsār:nam` ← کنجه *konje* N-058/N-053
  - `varberhanee:barnam` ← برهنه *berahne* N-088/N-029
  - `Dožnvārsir:nam` ← دژن *dožan* N-077/N-058
- gained: variants changed + needs_review changed
  - `hamnazaqdegā:barnam` ← نزغده *nazqade* N-033/N-015
  - `nazaqdegāyidan:nabesudkarvaze` ← نزغده *nazqade* N-033/V-003
  - `Nazaqdeure:nam` ← نزغده *nazqade* N-081/N-088
  - `Nazaqdeekade:nam` ← نزغده *nazqade* N-088/N-062
- gained: variants changed + needs_review changed + primary/variant swapped
  - `pažmānvārsār:barnam` ← پژمان *pežmān* N-077/N-055
  - `pažmānsirānidan:nabesudkarvaze` ← پژمان *pežmān* N-058/V-004
  - `vornāyidgār:karandekarbahr` ← ورنا *vornā* V-003/V-013
  - `požmāntargān:barnam` ← پژمان *pežmān* N-045/N-065
- gained: variants changed + needs_review changed + word classes changed
  - `vaššigānidan:nabesudkarvaze` ← وشی *vaši* N-065/V-003
  - `Vaššigānesir:nam` ← وشی *vaši* N-066/N-058
  - `bevaššie:barnam` ← وشی *vaši* N-088/N-004
  - `nāvašiyi:barnam` ← وشی *vaši* N-098/N-021
- gained: variants changed + primary/variant swapped
  - `Vejininā:nam` ← وجین *Vejin* N-098/N-072
  - `āgaftiyāne:jonvaze` ← آگفت *Āgoft* N-098/N-040
  - `vajinitar:barnam` ← وجین *Vejin* N-098/N-045
  - `Nahibie:nam` ← نهیب *Nahib* N-098/N-088
- gained: variants changed + word classes changed
  - `Estuhegāni:nam` ← استوه *ostuh* N-088/N-067
  - `Estuhāān:nam` ← استوه *ostuh* N-033/N-037
  - `Šahesār:nam` ← شه *šoh* N-088/N-053
  - `Šahesār:nam` ← شه *šoh* N-088/N-052
- gained: word classes changed
  - `bāfarāmoštlāx:barnam` ← فرامشت *Farāmošt* N-070/N-002
  - `befarāmoštzār:jonvaze` ← فرامشت *Farāmošt* N-050/N-005
  - `befarāmoštzār:jonvaze` ← فرامشت *Farāmošt* N-050/N-006
  - `āyāninvaš:barnam` ← آیان *āyān* N-102/N-082
- lost: category changed + left the input pool
  - `Vašidmān:karnam` ← وش *vaš* V-003/V-014
  - `axnāānidan:nabesudkarvaze` ← اخ *ax* N-072/V-004
  - `Bolnāyak:nam` ← بل *bol* N-072/N-060
  - `Bolnāyak:nam` ← بل *bol* N-072/N-061
- lost: category changed + variants changed + word classes changed + left the input pool
  - `Yeknādān:nam` ← یک *yek* N-072/N-048
  - `yekāsār:barnam` ← یک *yek* N-033/N-054
  - `yekāsār:barnam` ← یک *yek* N-033/N-051
  - `nāyeki:jonvaze` ← یک *yek* N-021/N-096
- lost: category changed + word classes changed + left the input pool
  - `tanhāyi:jonvaze` ← تنها *tanhā* N-096
  - `Hāmvāresirgāh:nam` ← هامواره *hāmvāre* N-058/N-068
  - `hamvašnādā:barnam` ← وشناد *vašnād* N-033/N-015
  - `dastādānāk:barnam` ← دستاد *dastād* N-033/N-073
- lost: merged into another row (اسم معنی)
  - `nājiki:barnam` ← جیک *Jik* N-098/N-021
  - `Lāxie:nam` ← لاخ *Lāx* N-098/N-088
  - `fini:barnam` ← فین *Fin* N-098
  - `Vānie:nam` ← وان *Vān* N-098/N-088
- lost: merged into another row (صفت)
  - `Penhāninnā:nam` ← پنهان *panhān* N-101/N-072
  - `Panhānāsār:nam` ← پنهان *panhān* N-033/N-053
  - `Panhānāsār:nam` ← پنهان *panhān* N-033/N-052
  - `Peidāvašā:nam` ← پیدا *paidā* N-082/N-033
- lost: reading changed (اسم معنی)
  - `Xorndie:nam` ← خورند *Xornd* N-098/N-088
  - `tāzagāniyānidan:nabesudkarvaze` ← تازگان *Tāzagān* N-098/V-004
  - `govharāniur:barnam` ← گوهران *Gavharān* N-098/N-081
  - `nehādiyidan:nabesudkarvaze` ← نهاد *Nehād* N-098/V-003
- lost: reading changed (صفت)
  - `Kiyākannā:nam` ← کیاکن *kiyākan* N-072
  - `čapalakingān:barnam` ← چپلک *čapalak* N-101/N-065
  - `aškiyudtarānidan:nabesudkarvaze` ← اشکیود *aškiyud* N-045/V-004
  - `pāyandegānetar:barnam` ← پایندگان *pāyandagān* N-087/N-045
- lost: reading changed (مصدر)
  - `Ziršodyāreš:karnam` ← شدیاریدن *šodyāridan* V-076/V-033
  - `navākine:barnam` ← نویدن *navidan* V-039/N-103
  - `farāvānavidan:nabesudkarvaze` ← نویدن *navidan* V-070/V-058
  - `farāvānavidan:nabesudkarvaze` ← نویدن *navidan* V-073/V-058
- lost: row changed otherwise (اسم معنی)
  - `jadāviyiur:barnam` ← جداوی‌ *Jadāvi* N-098/N-081
  - `jadāviyitar:barnam` ← جداوی‌ *Jadāvi* N-098/N-045
  - `Jadāviyisir:nam` ← جداوی‌ *Jadāvi* N-098/N-058
  - `najadāviyi:barnam` ← جداوی‌ *Jadāvi* N-098/N-018
- lost: row removed (اسم معنی)
  - `muāqivaš:barnam` ← مواق *Muāq* N-098/N-082
  - `kulāyiyānidan:nabesudkarvaze` ← کولا *Kulā* N-098/V-004
  - `betiyāriyidan:nabesudkarvaze` ← بتیار *Betiyār* N-098/V-003
  - `Gaihāniyā:nam` ← گیهان *Gaihān* N-098/N-033
- lost: row removed (صفت)
  - `naborāqur:barnam` ← براق *borāq* N-081/N-018
  - `naborāqur:barnam` ← براق *borāq* N-018/N-081
  - `čelingargānee:barnam` ← چلینگر *čelingar* N-066/N-087
  - `laqvar:barnam` ← لغ *laq* V-003/V-042
- lost: stems changed
  - `šekibānidbānāsā:barnam` ← شکیبانیدن *šakibānidan* V-015/N-034
  - `našekibānsār:barnam` ← شکیبانیدن *šakibānidan* V-063/N-055
  - `gosilegin:barnam` ← گسیختن *gosixtan* V-034/N-035
  - `gosilegin:barnam` ← گسیختن *gosixtan* V-034/N-069
- lost: stems changed + category changed + left the input pool
  - `Sirnākade:nam` ← سیر *sir* N-072/N-062
  - `xāmušsirvār:barnam` ← خاموش *xāmuš* N-058/N-074
  - `xāmušsirvār:barnam` ← خاموش *xāmuš* N-058/N-075
  - `xāmušsirvār:barnam` ← خاموش *xāmuš* N-058/N-076
- lost: stems changed + category changed + needs_review changed + left the input pool
  - `Nikāyeak:nam` ← نیکا *nikā* N-088/N-059
  - `Nikāyeak:nam` ← نیکا *nikā* N-088/N-061
  - `Nikāyeak:nam` ← نیکا *nikā* N-088/N-060
  - `nikāyiyin:barnam` ← نیکا *nikā* N-096/N-102
- lost: stems changed + category changed + needs_review changed + word classes changed + left the input pool
  - `pāksirin:barnam` ← پاک *pāk* N-058/N-100
  - `Nikeče:nam` ← نیک *nik* N-088/N-046
  - `varniknā:barnam` ← نیک *nik* N-072/N-029
  - `nabišāne:jonvaze` ← بیش *biš* N-018/N-040
- lost: stems changed + category changed + variants changed + needs_review changed + primary/variant swapped + word classes changed + left the input pool
  - `yakigāni:jonvaze` ← یکی *yaki* N-065/N-096
  - `Yakigānegi:karnam` ← یکی *yaki* N-066/N-095
  - `yekiyinur:barnam` ← یکی *yaki* N-101/N-081
  - `daryekiyānidan:nabesudkarvaze` ← یکی *yaki* V-004/V-056
- lost: stems changed + category changed + variants changed + word classes changed + left the input pool
  - `Yekkee:nam` ← یکه *yekke* N-088
  - `varyekkegidan:nabesudkarvaze` ← یکه *yekke* V-003/V-075
  - `varyekkegidan:nabesudkarvaze` ← یکه *yekke* V-003/V-074
  - `yekkevašur:barnam` ← یکه *yekke* N-082/N-081
- lost: stems changed + category changed + word classes changed + left the input pool
  - `Nahbahregmān:karnam` ← نهبهره *nahbahre* V-003/V-037
  - `negunsārāne:jonvaze` ← نگون *negun* N-055/N-040
  - `nikuyingāne:barnam` ← نیکو *niku* N-101/N-066
  - `basgānsār:barnam` ← بس *bas* N-065/N-055
- lost: stems changed + variants changed
  - `Čexinsirgān:nam` ← چخین *čaxin* N-058/N-064
  - `Sepahbodānisir:nam` ← سپهبدان *Sepahbadān* N-098/N-058
  - `Nāčexini:karnam` ← چخین *čaxin* N-021/N-095
  - `načexinvaš:barnam` ← چخین *čaxin* N-018/N-082
- lost: stems changed + variants changed + needs_review changed
  - `monlāksirur:barnam` ← منلاک *manlāk* N-058/N-081
  - `Monlāksirāne:nam` ← منلاک *manlāk* N-058/N-041
  - `hakuievaš:barnam` ← هکوی *hakvi* N-087/N-082
  - `hakuievaš:barnam` ← هکوی *hakvi* N-088/N-082
- lost: variants changed
  - `veiliyānidan:nabesudkarvaze` ← ویل *Vil* N-098/V-004
  - `naxvastvār:barnam` ← خوست *xost* N-018/N-077
  - `naxvastvār:barnam` ← خوست *xost* N-077/N-018
  - `vailiur:barnam` ← ویل *Vil* N-098/N-081
- lost: variants changed + needs_review changed + primary/variant swapped
  - `pažmānvārsār:barnam` ← پژمان *pažmān* N-077/N-055
  - `pažmānsirānidan:nabesudkarvaze` ← پژمان *pažmān* N-058/V-004
  - `vornāyidgār:karandekarbahr` ← ورنا *varnā* V-003/V-013
  - `požmāntargān:barnam` ← پژمان *pažmān* N-045/N-065
- lost: variants changed + primary/variant swapped
  - `dežandāāsā:barnam` ← دژند *dežand* N-033/N-034
  - `Dežandsirstān:nam` ← دژند *dežand* N-058/N-057
  - `nakuppegānidan:nabesudkarvaze` ← کوپه *kuppe* N-018/V-004
  - `Emkuppegā:nam` ← کوپه *kuppe* N-033/N-012
