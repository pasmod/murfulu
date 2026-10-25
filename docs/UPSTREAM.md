# Things that belong in karbon

**A running register, not a plan.** [OWNERSHIP.md](OWNERSHIP.md) draws the line
between the two repositories. This file collects the concrete items that fall
on karbon's side, so they can be sent as pull requests in batches instead of
being remembered one at a time.

Three kinds of item, and they need different handling:

**A — a fault in karbon's data.** We work around nothing; the wrong value is
carried exactly as karbon has it. Fix belongs upstream.

**B — something karbon is missing.** Not wrong, just absent. An extension.

**C — built here because we could not wait.** It works, it is tested, and it
should eventually move to karbon so it is not implemented twice.

Every item states what was measured, so a pull request can quote a number
rather than an impression.

---

## A — faults in karbon's data

### A1. Two transcription patterns read a vowel as a consonant

Measured 2026-08-11 against snapshot `lexicon-20260808`. Full detail in
[LEXICON_ANALYSIS.md](LEXICON_ANALYSIS.md) §4 and §4b.

| fault | primary readings | variant readings | example |
|---|---|---|---|
| **و read as `v`** where it is a vowel | 71 | 16 | ازدودن → *ozdvdan*, should be *ozdudan* |
| **ه read as `h`** where it is a vowel | 22 | 12 | چمچه‌ساز → *čomčhsāz*, should be *čomčesāz* |
| both in one word | 3 | 2 | خندهٔ دندان‌نمای → *xandahdndānnmāye* |

The ه one was **not previously recorded** — §4 named only the و pattern. Both
are single mechanical patterns and should be cheap to fix at source.

Detection used here: four or more consonants in a row. 215 primary readings
trip it, of 45,579.

### A2. 76 broken readings carry no `needs_review` flag

Of the 215 suspect primary readings, 139 are flagged. The other **76 are
invisible downstream** — nothing consuming the lexicon can tell they are
doubtful. Flagging them costs nothing and is worth more than fixing them.

### A2b. بلند is read two ways and the snapshot contradicts itself about which

Measured against `lexicon-20260808`. بلند has two readings: **`Baland`**,
filed اسم ذات, `needs_review = 1`, confidence 0.4; and **`boland`**, filed
صفت, clean, confidence 1.0. The same snapshot spells سربلند **`sarboland`** —
so it uses one reading in the compound and offers the other as the primary.

This is A2's point with a name on it: the flag is there and it is right, and
the compound is the evidence that settles which reading the dictionary itself
believes. **Worth stating as a fault only if the primary is meant to be the
trusted one** — if the row order carries no such claim, this is ours to
handle, and it now is: readings are ordered on the flag before they reach a
screen (DECISIONS, session 10).

**What it costs, measured 2026-08-17 so a pull request can quote it.** The two
readings do not build the same amount of Persian: *Baland*, the flagged one,
builds **2,335 words** at two steps and *boland*, the clean one, builds **498**.
So whichever reading is right, **2,335 built words currently hang off the
reading karbon itself doubts** — which is what makes this worth a maintainer's
attention rather than only ours. Also now question L19 for the linguist, because
which reading is right is his and not the maintainer's.

### A2c. karbon's own `notes` marker knows something `needs_review` does not

Measured 2026-08-13 (session 10). karbon writes provenance markers into
`notes`, and one of them is **`[v7:badbracket]` — 335 rows** where it knows the
Dehkhoda bracket it read was not diacritics at all. The bracket values in
those rows are plainly wrong: آب has `دریای چین`, آبادان has `هری`, آب‌چین has
`مرا` — definitions and place names where a harakat should be.

**60 of the 335 carry no `needs_review` flag.** آب‌انبار is one: bracket
`اَمْ`, marked badbracket, and served at `confidence = 1.0` with the flag
clear.

This is **A2 with a second signal attached**. A2 asks for 76 unflagged suspect
readings to be flagged; this says karbon already computes an independent
reason to doubt 335 rows and does not fold it into the flag that consumers
read. Cheapest possible fix upstream: set `needs_review` where a badbracket
marker exists.

**We had never read `notes` at all** — see B5 — so this was invisible from
here until the columns were listed.

### A3. A base and its own derived entries are read from different stems

Measured 2026-08-11 against snapshot `lexicon-20260808`, while building the
pass that says which rule formed which corpus word.

The clearest case is پهن:

| entry | reading |
|---|---|
| پهن (the base, صفت) | **`pen`** |
| پهنا | `Pahnā` |
| پهنه | `Pahane` / `Pahne` |
| پهناور | `pahnāvar` |

Three derived entries start *pahn-*; the base they are built on does not, and
it carries **no `needs_review` flag**. There is no `pahn` reading anywhere in
the snapshot.

Counted across the whole lexicon: **2,437 bases whose own longer entry starts
from a different Latin stem, 1,964 of them unflagged.**

**Not all 2,437 are faults**, and the list should be triaged before any of it
is applied. A sample shows at least three causes mixed together: the ه-as-`h`
fault already recorded in A1 (آبله = `Ābele` but آبله‌دار = `ābelahdār`);
ordinary vowel reduction inside compounds, which may well be correct; and
plain inconsistency like پهن.

**Why it matters here.** We build a derived word from the base's reading. If
the base is read `pen`, we build *Penā* while the corpus and the lexicon both
have *Pahnā* — so a real Persian word (141 occurrences in 126 poems) cannot be
shown to have been formed by the rule that forms it. It is one reason only
**1,573 of 24,161** attested generated forms could be confirmed.

The unflagged 1,964 are the useful part of this: flagging them costs nothing
and would let every consumer see that the reading is doubtful.

### A4. Diacritics are stripped in karbon but kept in the source document

karbon's stem-exception list writes رشتن، سفتن، گزیدن، رفتن. The source
document writes رِشتن، سُفتن، گُزیدن، رُفتن. Neither is wrong, but **any match
between karbon, the source and the lexicon must strip diacritics first**, or
four verbs silently fail to line up. Worth stating in karbon's own docs.

### A7. Three transliteration faults, found by compounding through the lexicon

Surfaced 2026-08-14 by the coining experiment, which read them off the API
rather than out of the database.

| word | karbon writes | expected |
|---|---|---|
| راه | `Rae` | `Rāh` |
| خودآگاه | `xodāgāe` | `xodāgāh` |
| این | `Ein` | `in` |

The first two are one pattern: **a final `-āh` is read as `-āe`.** The third is
separate and turns a demonstrative into what looks like a German diphthong.

**And one that leaks into built words rather than only being displayed.**
زیستن's present stem is stored with Latin `zi` and Persian **`زیه`** — the two
disagree — so every compound built on it carries the wrong Persian:
`/compound?word=جا&partner=زیستن` returns `jāzi` spelled **جازیه**. A Latin
form and a Persian spelling that disagree produce a word that is right in one
alphabet and wrong in the other, and Murfulu serves both.

Measured against A1's pattern faults: this is the same class and was missed
because nothing had ever joined a stem's Persian to another word's Persian
until the compounding route existed.

### A5. Eleven Latin fields carry a letter from another alphabet

Measured 2026-08-13 against snapshot `lexicon-20260808`, over all 45,579
active rows. Every character in `phonemic`, `past_stem_lat` and
`present_stem_lat` was checked against the Behnevis alphabet. Eleven fields
on eleven rows hold a character that **looks** like a Behnevis letter and is
not one.

| row | field | written | should be | the intruder |
|---|---|---|---|---|
| سپردن | `present_stem_lat` | `sepοr` | `sepor` | Greek omicron |
| چول | `phonemic` | `čοl` | `čol` | Greek omicron |
| خوک‌خور | `phonemic` | `xukxοr` | `xukxor` | Greek omicron |
| خویله | `phonemic` | `xοile` | `xoile` | Greek omicron |
| کو | `phonemic` | `kaο` | `kao` | Greek omicron |
| نو | `phonemic` | `nο` | `no` | Greek omicron |
| پایون | `phonemic` | `Pāyοn` | `Pāyon` | Greek omicron |
| اسور | `phonemic` | `Αsur` | `Asur` | Greek capital alpha |
| افسور | `phonemic` | `Αfsur` | `Afsur` | Greek capital alpha |
| کوشیدن | `past_stem_lat` | `koúšid` | `koušid` | u with acute |
| تباهیدن | `phonemic` | `tabāhهdan` | `tabāhidan` | Arabic **ه** |

`phonemic_variants` repeats each one, so the two columns agree and neither
can be used to correct the other.

**سپردن is the expensive one, because a stem is not one word.** *sepor* is
the present stem of an ordinary and productive verb, so the intruder is
copied into everything built on it: **2,582 forms in the generated index
carry the omicron**, and 10 more carry the alpha. None of them can be typed,
searched or matched against the corpus, and on screen they are indis­tin­guish­able
from a correct form.

A one-character replacement upstream fixes all eleven and clears 2,592
generated forms with them. Worth a validator in karbon's own ingest as well:
the Behnevis alphabet is a closed set, so a character outside it is always a
fault and never a judgement.

**Repaired locally 2026-08-13, and deliberately not as an override.**
`murfulu/lexicon/behnevis.py` maps the look-alikes back as readings are read.
An override records a value this project *believes differently* and is
unconfirmed until the linguist rules; nobody believes a Greek omicron, so
this is not that kind of act — and the override machinery would not take it
anyway, since its correctable fields are the four stems and `phonemic` is
identity.

**Only look-alikes are repaired.** تباهیدن is written `tabāhهdan`, and an ه
does not look like anything in particular, so what was meant is a guess. That
reading is left exactly as the snapshot has it and flagged `needs_review`
instead. The repair goes away when the fix lands upstream.

### A6. The اسم معنی class carries function words. Asking, not asserting

**A second reason to ask, found 2026-08-14 by building the compounding route.**
سخن is filed اسم معنی, which this project maps to `karnam`, and every slot
compounding rule takes a `nām`. So **سخن can form no compound at all** — while
سخندان, سخنور and سخنگو are ordinary Persian and the corpus has سخندان in 199
poems. Whatever the right answer is, the class as it stands makes the
commonest compounding noun in classical poetry incapable of compounding.

Measured against the same route: دل, filed اسم ذات → `nam`, builds 4,652
compounds of which the corpus has 220.

**This is a question for the maintainer, not a fault we are claiming.** The
category comes from Dehkhoda and a dictionary's part-of-speech field is a
judgement, so it is reported as measured and nothing here is filtered.

**Measured across the whole class, 2026-08-17.** It is not only سخن: **1,949
readings are a kārnām and not a nām**, and every one of them is shut out of
every slot compounding rule. Three of سخن's own compounds are ordinary Persian
and the corpus has all three — سخندان **199 documents**, سخنور **178**, سخنگو
**121**.

**And a caution about the wider number, because it would otherwise be quoted.**
We tried to measure the whole class against the whole corpus — every kārnām
against every present stem — and **the result is not usable**: it reports 1,781
"attested" forms whose top rows are روزگار read as روز + گار and بهاران read as
بها + ران, which are not compounds at all. Short strings collide. The three rows
above were checked by hand; the aggregate is not evidence and is recorded here
only so nobody re-derives it and believes it. The same question is L18 for the
linguist, from the rules' side rather than the dictionary's.

Murfulu maps the lexicon's `اسم معنی` onto its own `karnam`, and the search
query `type:karnam` is one of the four examples on the app's home screen. It
returns 1,074 words. Sorted by how often the corpus writes them, the top
twenty include:

| word | what it is | occurrences |
|---|---|---|
| **را** | the object marker, a postposition | 393,813 |
| **گر** | *if* — a conjunction | 71,424 |
| **مرا** | *me* — a pronoun already carrying را | 59,418 |
| **خوش** | an adjective | 22,006 |
| **پنج** | *five* — a numeral | 2,663 |

So the second row a reader sees after clicking the example chip is را. The
other fifteen are ordinary nouns and read correctly.

**Question:** is `اسم معنی` meant as a word class at all here, or is it a
default for rows whose class was never decided? If the second, a value
meaning *undecided* would let both repositories tell the two apart. Nothing
downstream can do so today.

---

### A8. وشتن's present stem is ور, and it makes a noun compound out of a suffix

**Measured 2026-08-18** on `data/lexicon-20260808.sqlite`.

Row 1916: `وشتن / وشت / ور`, `rule_applied 8`, `stem_rule 34`, `confidence 1.0`,
`needs_review 0`, no definition preview. The present stem **ور** is the same
letters as the suffix **-var** (`rules/affix_spellings.yaml`, N-080 *nām +
-var → barnām*, *dānešvar*). So every noun in the lexicon compounds with it
through V-078/V-079, and دست + ور arrives as a verb compound reading *dastvar*
— where the reading a Persian speaker gives دستور is دست + the possessing
suffix, and the corpus's 970 poems for that spelling are the vizier.

**The general shape, measured over the whole snapshot:** of 3,232 verbs with
both stems, **25 have a present stem spelled exactly like a suffix in the
pack** — مان ×5 (ماندن، مانستن، مانیدن), کار ×3 (کاریدن، کاشتن، کشتن), آسا ×2,
دان ×2, ستان ×2, ش ×2, تر ×2, and one each for چه، زار، گار، گر، وار، ور.

Two separable questions for karbon: whether وشتن's present stem is ور at all
(rule 8 produced it mechanically), and whether a stem that collides with a
productive suffix should carry a flag. The first is a data fault if the stem is
wrong; the second is B-shaped. Nothing is worked around here — the value is
carried exactly as karbon has it.

## B — gaps in karbon

### B1. نهفتن has no present stem

The stem document writes ؟ and karbon leaves the verb out of its exception
list rather than guess — the right call. But the verb then has no stems at
all. Needs the linguist, then a karbon PR. Also OPEN_QUESTIONS item I.

### B2. Common words missing from the lexicon

Found while measuring corpus coverage. These are written thousands of times in
classical poetry and have no lexicon entry, so their reading cannot be
confirmed:

| word | occurrences in Ganjoor |
|---|---|
| گفتار | 4,813 |
| رفتار | 1,206 |
| روش | 1,029 |
| رونده | 360 |

نویسنده and بینا are absent too. The full list is producible: it is the
unlinked spellings from the link pass, sorted by frequency
(`LinkResult.biggest_gaps()`).

**This is the single most useful thing we can send upstream.** It is derived
from real usage, ranked by how much it matters, and every entry added closes a
measurable gap.

**Four more, found 2026-08-14 by watching what a caller actually reached for.**
Two language models were given the same word-coining questions and the bases
they picked were checked against the lexicon. These are not rare words:

| word | | poems | in the lexicon |
|---|---|---|---|
| نزدیک | near | **4,609** | **no reading** |
| دانش | knowledge | **3,136** | **absent** |
| نابود | annihilated | 330 | yes, `barnam` |
| کتاب | book | — | **absent** |

نزدیک is one of the commonest adjectives in the language and the corpus writes
it 4,609 times with no reading behind it. **کتاب is the sharper one**: the
source grammar's own examples for two of its rules are *Ketābé u* and
*Ketābí*, so the rule pack cites a word the lexicon does not hold.

**And the reason this matters more than the raw gap count:** a caller choosing
a base by *meaning* — which is what any word-coining tool does — reaches for
exactly these, and gets a 404.

**The list is smaller and better than it was, measured 2026-08-13 on corpus
v3.** The homograph pass (PLAN 6.5) puts a semantic check on every claim, and
the proposals fall from 10,877 to **9,716**: **1,331 spellings are dropped
because every rule that could have built them is doubted**, and 527 more keep
some rules and lose others. Those are words like شاهدان — real Persian, but
not what our rule said made them — so sending them would have asked the
lexicon to confirm a derivation we have measured against. What is left is the
same request with the weakest entries taken out of it.

**Now producible with a derivation attached.** The affix pass
(`murfulu/search/backfill.py`) keeps a `proposed` list: **10,877 corpus
spellings that our rules can build and that no lexicon entry confirms.** Each
carries the rule and affix that would form it, so the request upstream is not
"please add گفتار" but "گفتار occurs 4,813 times and is *goft* + *-ār* by rule
V-010". The list is raw and needs ranking by frequency before it is sent —
its tail includes single letters and degenerate forms.

### B2b. The gap list is inflated by inflection, and can be cleaned before it is sent

Measured 2026-08-13 (session 10), `tools/measure_inflection.py`. B2 above
proposes sending karbon the unlinked corpus spellings ranked by frequency.
**48,039 of the 409,916 spellings — 11.7% — are not missing headwords at
all.** They read as an **inflection** of something karbon already holds:
رفتی on رفت, کتاب‌ها on کتاب, نمی‌رفت on رفت.

| | spellings | occurrences |
|---|---|---|
| karbon has a reading | 16,714 | 11,644,767 |
| a verb stem karbon carries | 1,082 | 1,491,886 |
| **an inflection of one of those** | **48,039** | **3,211,202** |
| nothing we can account for | 344,081 | 9,149,334 |

**So a gap list sent raw would ask karbon to add tens of thousands of
conjugated verbs and plurals to a headword dictionary**, which is not what a
headword dictionary is for — the same mistake B3 warns about with function
words, at forty times the size.

**How trustworthy the filter is, measured rather than claimed.** Run over
karbon's own 43,225 headwords — every one a word by definition — the analyser
reads **3,262 of them, 7.5%,** as an inflection anyway. Per pattern that
ranges from **0.0%** for the `‌های` plural to **20.2%** for the Arabic `-ون`,
so a cleaned list should drop only what the safe patterns catch. **None of
this is a fault in karbon**; it is our list that would have been wrong.

### B2c. The cleaned list, and why it is still not sendable

**Built 2026-08-15 (PLAN 9.4), `tools/clean_gap_list.py`.** B2b said the gap
list is inflated by inflection and can be cleaned before it is sent. It now is,
against corpus v9, and the counts reproduce B2b's exactly:

| | spellings |
|---|---|
| unlinked corpus spellings, before | **392,120** |
| inflections of something karbon holds, removed | **48,039** (11.7%) |
| **after** | **344,081** |

**Which inflections come off is measured, not chosen.** Every karbon headword
is a word by definition, so a headword the analyser strips down to another
headword is a false positive; each pattern's error rate is measured on all
43,225 of them. Only patterns at or under a stated ceiling may remove anything,
the tool prints what other ceilings would have cost — at 0% it drops 9,300, at
1% 38,199, at 5% and above 48,039 — and **every dropped row is written out with
the pattern, the base and that pattern's error rate**, so the filter can be
argued with rather than trusted.

**It is still not ready to send, and the reason is B3, not inflection.**

| | |
|---|---|
| **60 of the 100 biggest surviving gaps** | three characters or fewer |
| 32 single-letter spellings | **15.6%** of all kept occurrences |

The head of the list reads و, ز, آن, او, چون, ای, ما, همه, هم, بی — the first
content word is عشق at position 11. Sent like this it asks a headword
dictionary for the hundred function words B3 already agreed are out of scope.
**Decided 2026-08-15 by the project lead: restrict it to the spellings our own
rules can build.** Not a function-word list — "and" is not built from anything,
so it drops out on its own and no list has to be written or maintained.

| | spellings |
|---|---|
| unlinked, before | 392,120 |
| inflections removed | 48,039 |
| our rules can build | **4,519** |
| of those, three characters or fewer | **99** (was 5,681) |

Produced by `tools/clean_gap_list.py --buildable build/affix-map-v9.json`.
**Every row now carries the rules and affixes that would form it**, so the
request is not *please add گفتار* but *گفتار occurs 4,813 times and is goft +
-ār by rule V-010*. The head of the list is ناله, اندیشه, خنده, **زندگی**,
پادشاه — and زندگی, پادشاه, اندیشه and خنده were each checked by hand and are
genuinely absent.

**The known cost, stated rather than hidden.** A borrowed word has no Persian
derivation, so کتاب — B2's sharpest example — is absent from this list as well
as from the lexicon. Those need a separate, shorter ask.

**And they go as issues, not pull requests** — the project lead's call, same
day. Text prepared for all ten in `build/upstream/ISSUES-for-karbon.md`, with
the four attachments beside it.

### B5. Twelve of karbon's twenty-seven columns reach nothing of ours

Measured 2026-08-13 (session 10) by `tools/audit_lexicon_use.py`, which exists
because برنا was not a missing-data fault: karbon held `bornā`, the reading
carried it, the API sent it, and no screen drew it. **Nobody had ever listed
what karbon holds beside what we consume.** The tool is meant to be re-run
against every new snapshot, because a column added upstream is unused by
default.

**This is not a fault list.** Every one of these is karbon doing more than we
asked for. It is our gap, recorded here because the maintainer is the one who
can say what each column means and whether it is safe to lean on.

| column | filled | what is in it |
|---|---|---|
| `vowelized` | **100%** | the headword with harakat — آبادانیدَن |
| `file_path` | 100% | provenance, one path per row |
| `tag` | 96.1% | a **second** grammar notion beside `pos`: اِ, اِ مرکب, ص مرکب, نف مرکب — 7 values |
| `definition_preview` | **96.1%** | **Dehkhoda's own definition**, 43,747 distinct |
| `bracket_raw` | 84.1% | the Dehkhoda diacritics karbon's phonemizer takes |
| `notes` | 50.7% | karbon's own markers — see A2c |
| `subgroup` | 13.1% | a domain: کشاورزی 4,005, جانوران 1,802, موسیقی 182 |
| `transitivity_source` | 3.9% | how transitivity was decided — 5 values |
| `transitivity_confidence` | 3.9% | how sure |
| `rule_applied` | 3.9% | 8 values; distinct from `stem_rule`, which we do read |
| `transitivity_reason` | 3.8% | a Persian sentence giving the reason |
| `stem_group` | 3.8% | 1, 2, 3 — and this is L2's question |

**Three questions for the maintainer**, none of them urgent:

1. **`definition_preview`** — is it fit to show a reader, or is it a raw first
   line that happens to read well in the rows we sampled? It is the single
   most valuable column here: the app can say what a **base** word means for
   96.1% of the lexicon, against the 1.8% of *built* words that carry a
   meaning today.

   **Measured 2026-08-18, and the answer looks like *a raw first line*.** In
   the served v11 index 17,471 word types carry a definition. The longest is
   exactly 200 characters and **9,353 of them (53.5%) sit at 199 or 200** —
   the cut, showing up as a spike. The other 8,118 are whole sentences.

   The worked example is **فنا**. Its `definition_preview` is 90 characters
   and complete: «دارویی است که آن را به فارسی روباه تربک خوانند و به عربی عنب
   الثعلب. (فهرست مخزن الادویه).» — a plant, a medicine. Dehkhoda's own entry
   for فنا opens **«نابودی»**, the Sufi term, and that is plainly the sense in
   use: the corpus has فنا **4,315 times across 3,095 documents and 182
   poets**, in عطار, مولانا, بیدل and جامی. Not one of them means the
   fox-berry.

   So the column is not *the* definition but *a* definition — whichever sense
   happened to be first in the source row. **Two questions rather than one:**
   is there an ordering that could put the principal sense first, and is the
   sense number recoverable at all, so a reader can be told this is one of
   several? `sense_count` already travels with the record and is often > 1,
   which is what makes the current display misleading rather than merely
   partial.
2. **`tag` against `pos`** — two grammar columns, both ~96% full, seven
   values against eight. Which is authoritative, and what is the other for?
3. **`transitivity_source` and `transitivity_reason` carry a person's name**
   in some rows. This repository is to be made public and does not put names
   in code or docs, so those two cannot be shown as they stand. Is the name
   meant to be data, or is it an editing artefact?

### B3. Function words are out of scope, and that should be stated

و, از, که, را, به, در and about a hundred others have no entry, which is
correct for a headword dictionary. But it drags measured corpus coverage from
what would be ~75% down to 45.7%, and anyone quoting that figure will
misread it. Either a small function-word list is added, or the exclusion is
documented. Agreed 2026-08-11: **later, not now.** OPEN_QUESTIONS item O.

### B4. Three irregular verbs where the lexicon and the grammar differ

Measured 2026-08-12. Different from the C1 cross-check below: that compares
karbon's stem-rule **code** with our transcription of the same document. This
compares the **stem values in the lexicon snapshot** with what the grammar
document says they are.

**karbon is downstream of the same authority.** It was built from the
linguist's rules and many of its results were checked by hand, so a difference
here is at least as likely to be his later correction as an error. That is why
none of these is called a fault, and why all three are also in
[FOR_THE_LINGUIST.md](FOR_THE_LINGUIST.md).

| | |
|---|---|
| exception verbs the lexicon agrees with | **33 of 36** |
| stems that differ | **2** |
| verbs absent from the lexicon | **1** |
| left unclear by the source document itself | 3 (گشادن، افراشتن، نهفتن) |

| verb | the grammar document | the lexicon |
|---|---|---|
| آزردن | آزرد / **آزار** | آزرد / **آزر** |
| گسیختن | گسیخت / **گسل** | گسیخت / **گسیل** |

**And one verb is absent.** The document lists **رُفتن** (to sweep), stems
رُفت / روب. The lexicon has no entry — only رفتن (to go), رفت / رو. Stripped of
harakat the two spellings are identical, so a lookup for رُفتن returns the
other verb and raises nothing.

We hold our own values meanwhile, in `rules/lexicon_overrides.yaml`, so this
does not block generation — and every one of them is marked unconfirmed and
carries the reading it overrode. When the linguist rules, either the override
is dropped or this goes upstream as a pull request.

---

## C — built here, belongs in karbon eventually

### C1. The nine stem rules exist in both repositories

karbon implements them in `src/karbon/morphology/rules.py`, with Latin forms.
This repository transcribes them again in `rules/stem_rules.yaml`, from the
same source document, because the rule pack needs them as data a linguist can
edit.

**Cross-checked 2026-08-11: the two agree on all 36 shared exception verbs.**
The duplication is deliberate and currently harmless, but it is duplication.
When karbon exposes the rules as data rather than code, ours should become a
loader over karbon's copy.

### C2. Spelling normalisation

`murfulu/corpus/wordtypes.normalise()` folds Arabic ي ك ة أ إ ؤ to their
Persian equivalents and strips harakat. karbon's resolver has its own
normalisation with **deliberately different behaviour** — it documents that
the workshop's `headword_normalized` does not fold أ, and that 47 headwords
are affected.

Two normalisations that disagree will eventually cause a silent mismatch. One
of them should win, and it should live in karbon.

### C3. Reading `phonemic_variants`

7,212 lexicon rows carry a second reading that karbon's own consumers appear
not to use. We read them now. If that is the right behaviour, karbon should
expose them through its API rather than leaving each consumer to parse the
JSON column.

### C4. The rule pack mirror

Not a fault and not a gap: the thing DECISIONS already settled, now with a
command behind it. `tools/mirror_to_karbon.py` writes the pack into a
directory in the karbon checkout, **byte-identical, plus a manifest** naming
the rule-pack version, the commit and a hash per file.

Seven files — everything `murfulu.rules.pack` loads — so karbon can load the
copy with the same code.

`--check` compares and exits 1 when the copy is stale. That is the piece worth
proposing to karbon as well: a job on its side that fails when the mirror
drifts turns *one master, one mirror* from an agreement into something the
machine keeps.

**Nothing has been sent.** The command opens no pull request and cannot; a
test asserts it. The first mirror goes upstream on the project lead's word.
Measured: rule pack `0.1.0`, 7 files, written and re-checked as current.

---

## How to use this file

When something lands here, write down **what was measured**, not just what is
wrong. A pull request that says "71 rows match this pattern, here they are"
gets accepted; one that says "the transcription looks off" does not.

Batch them. The karbon maintainer should get one pull request with a theme,
not five with one line each.

---

## Drafted issue text, ready to post

**Written 2026-08-17, on the project lead's word, and deliberately not posted.**
karbon's tracker is empty and these would be first contact, so the wording is
his to approve before anything is opened. Each is written to stand on its own —
a maintainer should not have to read this repository to answer it.

**Both are questions, not asserted faults.** Everything they rest on is a
measurement against snapshot `lexicon-20260808`, quoted with its number, and
nothing on our side is filtered or worked around while they wait.

### Issue 1 — `بلند`: 2,335 derived words hang off the reading the dictionary doubts

> **Title:** `بلند` has two readings and the snapshot disagrees with itself about which
>
> Working from `lexicon-20260808`, `بلند` has two readings:
>
> | reading | `pos` | `needs_review` | `confidence` |
> |---|---|---|---|
> | `Baland` | اسم ذات | **1** | 0.4 |
> | `boland` | صفت | 0 | 1.0 |
>
> The same snapshot spells `سربلند` as **`sarboland`**, with an *o*, and files it
> `صفت مرکب` with no flag. So the compound uses one reading while the simple word
> offers the other first.
>
> **Why we are raising it rather than handling it quietly.** We generate words
> from every reading, and the two do not produce comparable amounts: `Baland`
> builds **2,335** words at two steps and `boland` builds **498**. So most of
> what we derive from `بلند` rests on the reading the dictionary has itself
> flagged at confidence 0.4.
>
> We have not filtered anything. Readings are ordered by your flag and then by
> your confidence before they reach a screen, so a reader sees `boland` first and
> `Baland` is one press away — an order, not a judgement, because the flag reads
> to us as *check this* rather than as a verdict.
>
> **Question:** is `بلند` `Baland`, `boland`, or genuinely both? And if the row
> order is not meant to carry a claim about which is trusted, we are happy to say
> so on our side instead.

### Issue 2 — `اسم معنی` and compounding: 1,949 readings cannot form a compound

> **Title:** Is `اسم معنی` right for `سخن`? It stops 1,949 entries compounding
>
> Our word-formation rules take a noun on the front of a compound. We map the
> lexicon's `اسم معنی` onto our own *kārnām* class — the action noun — because
> the source grammar states that mapping outright, so an `اسم معنی` entry is not
> a noun as far as those rules are concerned.
>
> `سخن` is filed `اسم معنی`. The consequence is that **`سخن` can form no compound
> at all**, while these are ordinary Persian and the corpus has all three:
>
> | word | parts | documents in our corpus |
> |---|---|---|
> | سخندان | سخن + دان | **199** |
> | سخنور | سخن + ور | **178** |
> | سخنگو | سخن + گو | **121** |
>
> It is not only `سخن`: **1,949 active readings are `اسم معنی`** and every one of
> them is affected the same way. For comparison, `دل` — filed `اسم ذات` — builds
> 4,652 compounds of which the corpus has 220.
>
> **This is a question about a judgement, not a bug report.** The category comes
> from Dehkhoda and a part-of-speech field is an editorial decision; we have
> filtered nothing and are carrying your value exactly as it stands. It may also
> be that our mapping is what should change, and we are asking our own linguist
> that in parallel.
>
> **Question:** is `اسم معنی` the right class for `سخن`, and does it carry other
> entries that a reader would call ordinary nouns?
>
> *(A separate note, in case it saves you time: we also tried to measure this
> across the whole class by joining every `اسم معنی` entry to every present stem
> and checking the corpus. That measurement is unusable — it reports 1,781 hits
> whose top rows are `روزگار` read as `روز + گار` and `بهاران` as `بها + ران`,
> which are not compounds. Short strings collide. The three rows above were
> checked by hand.)*

### A9. A final ه that is pronounced is transliterated as *e*, and it reaches our output

Found 2026-08-20 by a coining run that could not analyse گلوگاه. Measured on
snapshot `lexicon-20260808`.

**A Persian word ending in ـاه ends in a consonant.** شاه is *šāh*, ماه is
*māh*, راه is *rāh*, گاه is *gāh*. karbon writes the *h* as an **e**:

| spelling | karbon's reading | what it should be |
|---|---|---|
| شاه | `Šāe` | *šāh* |
| ماه | `Māe` | *māh* |
| راه | `Rae` | *rāh* |
| چاه | `Čāe` | *čāh* |
| کلاه | `Kolāe` | *kolāh* |
| گاه | `Gāe` | *gāh* |

**How wide.** Of the **803 readings whose Persian ends in ـاه, 777 are written
`-āe`.** Only گیاه (`Giāh`) and گناه (`Gonāh`) among the common ones are right.
Taking the ـگاه family alone: **457 of 463** entries — دانشگاه، آرامگاه،
خوابگاه، زادگاه، جایگاه، درگاه — are `-gāe`.

**It is not cosmetic. It changes the Persian we build.** Murfulu decides
whether a final ه is the silent one by reading the Latin, and that is
deliberate: a silent ه is dropped before a گ — بنده + گی is بندگی — while a
consonantal one is kept, شاه + گان is شاهگان. The rule is written to read the
Latin *because* the Persian alone cannot tell the two apart. With karbon's
value it reads the wrong answer:

```
join_fa("شاه", "Šāe", "", "گان")  →  شاگان      ← karbon's reading
join_fa("شاه", "šāh", "", "گان")  →  شاهگان     ← the right one
```

And it reaches real output. Building one step from شاه gives **شاگان، شاگین،
شاگیدن، شاگانیدن**. Sampled over 40 of the 779 affected readings: **550 of
1,935 forms at one step — 28% — lose the ه.**

**A second consequence, on the reading side.** No ـگاه word can be taken apart
from its Persian spelling, because the rule pack's affix is `-gāh` and every
entry is `-gāe`:

```
/explain?word=گلوگاه   → rebuilt: false
/explain?word=Golugāe  → rebuilt: false     ← karbon's own reading
/explain?word=Golugāh  → rebuilt: true      ← گلو + -gāh, N-068
```

So a word karbon holds, written the way karbon writes it, is reported as a word
that cannot be built.

**The reading is carried exactly as karbon has it** — `Šāe` is still what the
lexicon hands us and what every screen shows. What changed on our side is our
own **orthographic rule**, not karbon's value: `join_fa` no longer deletes a ه
that stands after ا, whatever the Latin says, because a silent ه writes a short
*e* and a short vowel cannot follow a long ā. So we stop building شاگان while
still holding *Šāe*. Same day, `engine/glides.py`, with the tests beside it.

**Two things that stay broken until this is fixed upstream.**

- **The analysis side.** `/explain?word=گلوگاه` is still `rebuilt: false`, and
  so is every one of the 457 ـگاه entries, because the affix in the rule pack
  is `-gāh` and the reading is `-gāe`. Nothing on our side can bridge that: it
  is a value, not a rule.
- **ـوه and ـیه.** کوه is *kuh* and میوه is *mive*; both are written وه, and
  **204 of the 221 ـوه readings and 295 of the 297 ـیه readings end their Latin
  in *e***. Some of those are right and some are the same fault, and no rule
  over the Persian alone can tell them apart. We guessed at none of them.

What we would ask for: the final ه of a pronounced word transliterated as
**h** — ـاه first, since it is unambiguous and the largest single group.

---

**The other sixteen items above are not drafted.** They are older, several are
gaps rather than faults, and a first batch of two questions is easier to answer
than a tracker filled in one afternoon.
