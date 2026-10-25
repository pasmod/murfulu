# For the linguist

**Questions only he can settle.** Gathered here rather than mixed into
[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), which holds engineering decisions for
the project lead, and separate from [UPSTREAM.md](UPSTREAM.md), which holds
work bound for karbon. Three files, three audiences.

**How this file is used.** Nothing waits on it. Where a ruling is missing we
build what we believe is right, mark it unconfirmed, and carry on — the
project's working rule. These are then gone through with him in one sitting
rather than one at a time.

**What each item states:** what was measured, what we did meanwhile, and what
changes if he rules the other way.

---

## L1. Two irregular stems, and one verb the lexicon does not have

Measured 2026-08-12 against snapshot `lexicon-20260808`. Of the 39 exception
verbs in the stem document, **33 of 36 testable ones match the lexicon
exactly**. Three do not.

| verb | the document | the lexicon | we currently use |
|---|---|---|---|
| آزردن | آزرد / **آزار** | آزرد / **آزر** | the document |
| گسیختن | گسیخت / **گسل** | گسیخت / **گسیل** | the document |
| رُفتن | رُفت / **روب** | *no entry at all* | the document |

**This is not obviously a fault in karbon.** karbon was built from his own
rules and many of its readings were checked by hand, so a difference may well
be his later correction rather than an error. We took the document's value
because the document is the written rule, and every override records what it
replaced so it can be undone in one line.

**رُفتن is the one with a consequence.** Without harakat, رُفتن (to sweep) and
رفتن (to go) are the same string. The lexicon has only the second, so a lookup
for the first silently returns the wrong verb and every word built from it is
built on the wrong stem.

**Question:** for each of the three, which is right — the document or the
lexicon? If the lexicon, we drop the override. If the document, it goes to
karbon as a pull request.

---

## L2. Which stem group is NKZ, and which is NKDZ?

V-001 and V-002 both build a verb with `-āndan`, and the only thing separating
them is the stem's group: *Kārboné doé nāgozarā az Goruhé yek (NKZ)* against
*…az Goruhé do (NKDZ)*.

The lexicon carries `stem_rule` and `stem_group` columns, so testing this is a
line of code. What is missing is which of karbon's numbered groups those names
refer to. Guessing would silently mark half the verbs as breaking a rule they
may well keep, so the condition is recorded and not tested.

**Question:** NKZ and NKDZ are which of karbon's stem groups?

**Measured 2026-08-13 (session 10), and it narrows the question.** The column
was never read — `stem_group` is one of the twelve karbon holds and Murfulu
does not. Here is what is in it:

| group | verbs | distinct `stem_rule` values in it |
|---|---|---|
| **1** | **1,547** | 9 |
| 2 | **10** | 5 |
| 3 | 168 | 23 |

**Group 2 holds ten verbs.** So whatever NKZ and NKDZ turn out to be, they are
almost certainly not groups 1 and 2 — a split that put 1,547 verbs on one side
and ten on the other would not be worth two rules. Naming which is which is
still his; the shape of the answer is now known.

**Note that `stem_group` and `stem_rule` are different things** and only the
second is read today, as `karbon_stem_rule`. 37 rules across 3 groups.

---

## L3. Should a rule be stopped when its own condition fails?

The source states a condition on the base for 186 of 195 rules; twelve say
something beyond the word class, and those are now read
(`rules/input_conditions.yaml`).

**Nothing is refused on their account.** V-010 says its stem *mostly* ends in
`-t` or `-d` — **bištar** — and turning a tendency into a filter would claim
more than the grammar does. The engine records whether the condition was met
and builds the word either way.

Measured on رفتن: of 510 words, 483 have no condition to check. Of the 27 that
do, those meeting it occur in the corpus 55% of the time against 12% for those
breaking it.

**Question:** for the conditions written flatly rather than hedged — V-023,
V-025, V-027, V-030, V-031, V-082, N-092, all naming a base by its ending —
should the rule simply not fire when the ending is wrong?

---

## L5. A measurement doubts 3,613 of our own claims. Is it right?

Measured 2026-08-13 on corpus v3, `tools/flag_homograph_claims.py`. The affix
pass says *rule R formed corpus word W*. A meaning-based check now doubts
**3,613 of 16,627 checkable claims (21.7%)**, and the four clearest are:

| we claimed | the check says | what we did |
|---|---|---|
| شاهدان = شاه + *-dān* | 84% of other bases fit it better than شاه | ranked last, held out of the index |
| لهستان = له + *-stān* | it is Poland | ranked last |
| مردمان = مرد + *-mān* | the plural of مردم | ranked last |
| کرنا = کر + *-nā* | a trumpet, a loanword | dropped from the *formed with this affix* group |

**Nothing is deleted and nothing is refused**, because a cosine is evidence
about a claim and not a ruling on one. The doubted claims sink to the bottom
of each rule's sister list and stay checkable.

**Question:** is the *shape* of this right — that a rule may be shown as not
having formed a word it can spell, on semantic evidence alone? And are these
four in particular the plural, the country, the plural and the loanword we
take them for? The list is in `build/suspect-claims-v3.json`, worst first, and
the per-rule table in `build/homograph-report-v3.md`.

**If he says no**, the flag stays as a report and stops feeding the affix map;
the machinery is one argument in one function call.

---

## L6. Four rules with one affix: are they four rules?

Found while measuring the semantic pilot over all 57 rules with a centroid
(RESEARCH_SCORING.md). **35 of the 57 share their affix with another rule** —
V-070 to V-073 are all *vā-*, V-005 and V-006 are both *-an*, V-001 and V-002
are both *-āndan* — and no meaning-based measure can tell them apart, because
what separates them is the output word class or the stem group rather than
anything in the word.

That is not necessarily a fault: the source grammar numbers them separately
and V-005/V-006 differ only by capitalisation, which the engine reproduces
from the output class. It matters here only because it halves what a semantic
score can be asked to do, and the figure has to be reported one way or the
other.

**Question:** where two rules share an affix and an input class, is that one
rule with two outputs, or two rules? Nothing is changed either way — rule ids
are permanent — but the answer decides whether 25.4% or 53.9% is the honest
headline for the pilot.

---

## L7. We now drop the ه before گ. Confirm it, or we undo it in one line

Built 2026-08-13, unconfirmed, per the working rule. A base whose Persian ends
in a **silent** ه loses it when a گ follows: تازه + ی = **تازگی**, بنده + گی =
**بندگی**, دره + گاه = **درگاه**. Silent is read off the Latin — *taze* ends in
*e* — so شاه, whose Latin *šāh* ends in *h*, keeps its ه: شاهگان.

**Two of the grammar's own glide rules already assume this**, G-09
(*taze + i = Tāzegi*) and G-10 (*morde + ān = Mordegān*), so the rule is not
being invented here; it is the Persian half of a rule the source states in
Latin.

**Measured before and after.** 38,932 forms spelled the join wrong. Fixing it
gained 1,609 attested forms — زندگی written 4,571 times, مژگان 3,977, زندگانی
3,489 — and removed 1,324 false matches, where the Persian had no گ at all and
collided with an unrelated word (*Šaegi* was spelled شاهی and matched شاهی,
"kingship").

**Re-measured 2026-08-17, and it does not reproduce — which is the finding.**
The "before" state is in no index: v4 already has the fix. So both spellings
were rebuilt from the rule and both put to the corpus, one step from the
lexicon's own entries. That is a smaller measurement than the one above and its
numbers are not the same ones. What it shows that the first did not: **the rule
creates collisions as well as removing them.** دیه + گر gives دیگر, which occurs
22,212 times and is a different word entirely; بنه + گر gives بنگر, 3,712 times.
A file counting only the words gained would have hidden that, so the attachment
carries both spellings and both counts in the same row, gains and collisions
together.

**Question:** is the rule right as stated, and is *silent by the Latin* the
right test for it? And the neighbouring case is not built and not guessed:
ZWNJ inside a compound — گفت‌وگو against the engine's گفتوگو — which is item K
and still waits on the Behnevis joining specification.

---

## L8. Two rules in the pack are not word formation, and they run on everything

**This is the worst thing a reader sees, and it is the top of the build
screen.** Found 2026-08-13 by building words from an ordinary adjective.

Two rows of the source's nominal table are in the pack as suffix rules:

| rule | affix | what it is | the source's own example |
|---|---|---|---|
| **N-090** | `-é`, written **ِ** | the ezāfe | *Ketābé* *u* — کتابِ او |
| **N-099** | `-í`, written **ی** | the indefinite *-i* | *Ketābí* — کتابی |

Both are enclitics: they join a word to the next one or mark it indefinite.
Neither makes a new word. The engine runs them like any suffix, on every
noun, and lets them stack on each other and on themselves.

**What بلند gives, in order, as the screen shows it:**

| rank | form | Persian | the corpus says |
|---|---|---|---|
| 1 | *Balandé* | بلندِ | 7,353 times, 5,625 poems, 217 poets |
| 2 | *Balandéé* | بلندِِ | 7,353 times, 5,625 poems, 217 poets |
| 3 | *Balandéí* | بلندِی | 1,147 times, 1,059 poems |
| 4 | *Balandí* | بلندی | 1,147 times, 1,059 poems |
| 5 | *Balandíé* | بلندیِ | 1,147 times, 1,059 poems |

Four of the first five are بلند with a clitic on it, and the first two render
on screen as the same word twice.

**The numbers beside them are the base word's own, and they are wrong for the
form.** The corpus has no kasre in it, so بلندِ is looked up as بلند and
inherits everything بلند was ever credited with. Measured over the whole v4
index: **28,148 forms are built by these two rules, and 2,252 of them are
marked attested — 9.2% of every attested form in the index.** The largest is
*Dideé* (دیدهِ), claiming 33,599 occurrences in 22,740 poems.

Row 4 is the one that shows why this is not merely cosmetic. بلندی *is* a
word — "height" — and the engine gets to it by the indefinite rule, so it is
right by accident, filed under the wrong rule, and carrying a count that
belongs to the abstract noun rather than to *a tall one*.

**Built 2026-08-13, unconfirmed, per the working rule.** Both rows now carry
`active: false` and a `retired_reason`. They keep their ids and their
transcriptions — the rules screen still shows what row 90 and row 99 said —
and the generator no longer runs them. One line brings either back.

**Question:** are N-090 and N-099 word-formation rules at all? If they are,
we undo this. If they are not, is `active: false` the right resting place, or
should the pack grow a way to mark a row as *syntax, transcribed but never
generated from* — which is what these two actually are, and what would stop
the next reader wondering why two rows are switched off?

**The project lead's position, 2026-08-13 (session 10).** He has not put it to
the linguist yet and does not want it holding anything up, because he expects
the same answer: these are **not** word-formation rules. They may well earn a
place for some other purpose, but not for building a new word. **So the two
stay retired**, and the second half of the question — what the pack should
call a row like this — is the part still worth his time.

---

## L9. A capital letter inside a word: 16% of everything we build has one

Found 2026-08-13 while reading build results. A prefix rule joins its affix to
a base without touching the base's capital, so سربلندی comes out as
**SarBalandí** and بی‌مهری as **BiMehri**.

Measured on a random sample of 5,000 of the 1.74 million forms in the v4
index: **808 — 16.2% — carry a capital letter after the first position.**
*DošKohbale*, *barFāxmān*, *hamLamāze*, *SarŠivāne*. On بلند alone it is
1,064 of 2,612 forms.

**The source is not consistent, which is why nothing was guessed.** Its own
examples are overwhelmingly flat — *Namakdān*, *Golestān*, *soxanguy*,
*xodaparast*, *tondrow* — but *Došnām* (N-010) keeps the capital on نام, and
that is the transcription in the grammar itself.

Capitalisation carries grammar in Behnevis and the app's rule is never to
lowercase a Latin form, so lowering the base is not a formatting choice we
can make on our own.

**Settled 2026-08-13: the capital is dropped, to match karbon.** It moved
twice in one day and the measurement is what settled it. First the join was
changed to lower the base's letter (*Sarbalandi*); the project lead reversed
that, on the grounds that a capital tells the reader the part inside is a
noun and that the source keeps it in *Došnām* (N-010); then karbon's own
snapshot was measured — see below — and he settled on **matching karbon,
because the linguist is behind that library**. سربلند is *Sarbaland*.

**Still unconfirmed**, and the evidence genuinely cuts both ways: the source's
other examples are flat — *Namakdān*, *Golestān*, *soxanguy*, *xodaparast*,
*tondrow* — and only *Došnām* is not.

**The measurement that settled it.** karbon's own snapshot, never asked
before because twelve of its columns had never been read:

| | |
|---|---|
| readings carrying a capital after the first letter | **0 of 45,579** |
| **compounds** (اسم مرکب, صفت مرکب) carrying one | **0 of 20,263** |

*Ābādbum*, *Ābādjāi*, *Ābādikāqaz*, *Ābāngān* — every one flat inside, with a
capital only at the front. And this is **not an accident of the phonemizer**:
8,116 rows carry karbon's own marker `[v7:rule12-cap]`, so it has a deliberate
capitalisation rule for compounds, and that rule capitalises the front alone.

**What this is and is not.** It is what karbon does, across twenty thousand
compounds, and karbon was built from the linguist's own rules — which is
exactly why the project lead chose to follow it: Murfulu and karbon spelling
the same kind of word two different ways would be worse than either spelling
on its own.

**The honest caveat, and it is his to weigh.** A compound is not a prefixed
form. *Ābādbum* is two nouns joined, where L9 is about a prefix in front of a
base, so karbon's practice is evidence about the neighbouring case rather
than about this one. And the source's *Došnām* (N-010) still keeps its
capital and is still unexplained.

**Question:** is *Sarbaland* right — and if it is, what is *Došnām*? A slip
in the source, a compound rather than a prefixed form, or a real exception
that the rule has to carry?

**One thing this is not.** *SarBalandi* had three faults and only this was one
of them. The other two are settled: the ezāfe (L8) and the reading (S13,
answered — the screen now opens on بلند's clean `boland`, so the word reads
*SarBoland…* and not *SarBaland…*).

---

## L10. A built word almost never says what it means, and one sentence is
## serving five affixes

Raised by the project lead 2026-08-13: it is only sensible to build the words
we can give a *meaning* to, and the meaning is how you tell whether a built
word is a word at all. Measured the same day, because the first question is
whether the sources give us the meanings.

**They give half of it.** Every one of the 43 semantic tags has a gloss
*word* — `Jā` → جا, `Anbuhi` → انبوهی. What almost none has is a gloss
*template*, the sentence that turns a form into a meaning.

| | |
|---|---|
| active rules | 193 |
| naming a semantic tag | 103 |
| naming **no** tag at all | **90** |
| tags with a gloss word | **43 of 43** |
| tags with a gloss **template** | **1 of 43** |
| built forms in v5 carrying a meaning | 70,370 of 1,704,021 — **4.1%** |
| **attested** built forms carrying a meaning | 407 of 22,118 — **1.8%** |

A reader looking at a real word therefore sees a meaning about **once in
fifty-four**.

**But writing 42 more templates would not be enough, and this is the part
that needs his ruling rather than his labour.** A template hangs on the *tag*,
and a tag is shared by rules that plainly do not mean the same thing:

| tag | rules sharing it | some of their affixes |
|---|---|---|
| `Nesbat` | **19** | -āne, -gar, -gān, -vār, -gi, -i, -in, -vand, be- |
| `Mānand` | 12 | -āsā, -gin, -dis, -sār, -sān, -vār |
| `Dāštan` | 11 | bā-, be-, -mand, -nāk, -var, -umand |
| `Jā` | 5 | **-ān, -dān, -stān, -kade, -gāh** |

`Jā` is the one with a template, and the index shows the cost directly:
**آبادانیدگان، آبادانیدهدان، آبادانیدهستان، آبادانیدهکده and آبادانیدگاه all
carry the identical sentence «جایی که آبادانیده در آن است».** Five affixes,
one meaning. But نمکدان is a *container*, گلستان is a *land*, میکده is a
*house*, دانشگاه is an institution — the tag they share cannot carry one
sentence for all of them.

**And N-068 (-gāh) is tagged `Jā` and `Zamān` at once**, so سحرگاه would be
told it is a place. It is one of only three rules in the whole pack naming two
tags, and whichever template is met first wins.

**Question, in two parts.**
1. Does the meaning sentence belong to the **tag** — 43 sentences, coarse,
   and five affixes share one — or to the **rule** — 193 sentences, exact,
   and four times the writing? The engine can do either; the choice decides
   how much there is to author and how good the answer is.
2. For the **90 rules with no tag at all**: is the tag simply missing from
   the transcription, or do those rules carry no meaning a template could
   state? If the second, a word built by one of them can never be given a
   meaning, and that is worth knowing before it is treated as a defect.

**Nothing has been built on this and no Persian has been invented.** The one
template that exists came from RULE_PACK.md, not from us.

---

## L12. بودن's present stem is بو, and باش is filed as a noun

Found 2026-08-14 while testing a word-coining tool, which wanted *bāšande*
("the one who is") and could not get the engine to build it.

| | the snapshot says |
|---|---|
| بودن | `budan`, مصدر, past **بود**, present **بو** |
| باش | `Bāš`, **اسم ذات** — a concrete noun, with no stems |
| هستن | `hastan`, مصدر, past **empty**, present هست |

So the engine cannot build *bāšande* from بودن: باش is not registered as its
present stem, and as an اسم ذات it takes nominal rules only. **باشنده is in
the corpus 8 times across 4 authors**, so the word exists and we cannot make
it.

**This is not obviously an error.** بو is the classical present stem — *bovad*
— and karbon was built from the linguist's own rules on a classical corpus.
باش may be the later form. Nothing was changed and no override was written.

**Question:** does بودن have one present stem or two, and if two, is باش the
later one or a separate word? And هستن's past stem is empty — is that right,
or is هستن defective?

---

## L11. «فرهنگ» is the wrong word for the thing the screens call فرهنگ

Raised by the project lead 2026-08-13 while reading the search screen:
**«فرهنگ» is not a good word for it.** Nothing is blocked and he is content to
leave it — recorded so the choice is made once rather than drifting.

**What it names now.** The lexicon: karbon's Dehkhoda-derived table of
headwords and their readings. The interface uses it two ways, and only the
first is a name:

| where | what it is |
|---|---|
| the search row's badge, and the same facet | a **label** — where a word was found: پیکره / فرهنگ / ساخته‌شده |
| ten other places | **prose** — «خوانشی در فرهنگ نیست», «پوشش فرهنگ», «فرهنگ این خوانش را بازبینی‌نشده نشان کرده است» |

**15 occurrences across 8 screens**, and the badge and the facet must agree
with the prose, so this is one decision and not fifteen.

**Why nothing was changed.** فرهنگ ordinarily means *culture*, and it means
*dictionary* only in the compound فرهنگ لغت — so the objection is real. But
choosing the replacement is naming, in Persian, for the project's own
terminology, which is his and not ours. Guessing would put a coined term in
front of readers with nobody's authority behind it.

**Question:** what should this be called — واژه‌نامه, فرهنگ واژگان, or a term
from the project's own system? Whatever it is, it also names the badge beside
پیکره and ساخته‌شده, so it has to sit in that set.

**Settled by the project lead, 2026-08-16: «واژه‌نامهٔ کاربن»** — the
dictionary is named after the library that holds it. Built the same day; the
name lives in `web/src/text/lexicon.ts` and nothing else spells it out. Reading
all the occurrences to make the change found **twenty, not fifteen**, and one
of them was not this thing at all: «فرهنگِ سرواژه‌ها» in the gap list means *a
dictionary of headwords*, any of them, and it stays.

**Withdrawn from the store the same day**, with that reason, so it is not in
front of him as an open question. It is recorded here and in DECISIONS instead.

**Not asked, but written down.** «کاربن» is already this project's term for a
verb stem — کاربن یک، کاربن دو, which the app prints on the same screens — so
«واژه‌نامهٔ کاربن» can be read for a moment as *the dictionary of stems*. The
project lead chose the name knowing this and chose not to put it to him.

---

## L13. The grammar and karbon disagree about a vowel, in 21 places at once

**This is one question, not twenty-one.** PLAN 9.3 put every rule's own example
back through the engine and asked, for each failure, what the engine built from
the same base. Twenty-one came back as **the same word spelled two ways**, and
the difference is nearly always a single *e* between two consonants: the
grammar writes the cluster, karbon writes the vowel.

| rule | the grammar's example | what we build from karbon's word |
|---|---|---|
| N-075 | `šāhvār` | `šāhevār` |
| N-079 | `Māhvāre` | `Māhevāre` |
| N-082 | `talxvaš` | `talxevaš` |
| N-052 | `Kuhsār` | `Kuhesār` |
| N-004 | `bexrad` | `bexerad` |
| N-062 | `Meykade` | `Meyekade` |
| N-034 | `barqāsā` | `baraqāsā` |
| N-051 | `divsār` | `advisār` |
| N-056 | `divsān` | `advisān` |
| N-033 | `Pahnā` | `Pahinā` |
| N-065 | `dahgān` | `dehgān` |
| N-019 | `nastuh` | `naseteh` |
| N-025 | `Pādšāh` | `Pādšāhe` |
| N-044 | `Drabān` | `Darbān` |
| N-046 | `Kuče` | `Kueče` |
| N-053 | `Roxsār` | `Orxsār` |
| N-003 | `barkenār` | `barkenār` |
| N-008 | `bigāne` | `bigune` |
| N-042 | `māhāne` | `mehāne` |
| N-103 | `dirine` | `darine` |
| N-105 | `Damāvand` | `Adamvand` |

**Question:** when a suffix meets a word ending in a consonant, does an *e* go
in? The grammar's examples say no and karbon's readings say yes, and the two
cannot both be the spelling the app shows.

**Nothing is blocked and nothing has been guessed.** These 21 are recorded in
`tests/example_baseline.json` as not rebuilding, and the list may grow but
never shrink, so whichever way this is settled the effect is visible
immediately. **A ruling here is worth 21 of the pack's own examples becoming
tests** — the largest single block left.

**Where it is not the same word.** The instrument only calls this a spelling
difference when the rule goes on to build the expected word bar its vowels. A
bare consonant skeleton matches *div* to *Dāv*, which is a different word, and
those are filed as a missing base instead.

## L14. Five examples do not use the affix their own rule declares

Same pass, and much smaller. In each of these the rule states one affix and its
example uses another:

| rule | affix declared | example | what the example ends in |
|---|---|---|---|
| V-040 | `-āk` | `kāvak` | `-ak` |
| V-041 | `-nāk` | `andišnak` | `-nak` |
| V-051 | `-ā` | `ākandan` | `-an` |
| N-063 | `-gar` | `Ruzgār` | `-gār` |
| N-001 | `-ā` | `Amardād` | neither |

Four are the same long-against-short vowel question as L13, one rank lower —
in the **affix** rather than the base. **N-001 is different**: امرداد is a month
name and does not end in the rule's affix at all, so it looks like an example
filed under the wrong row. **Question:** is each of these a typo in the
transcription, or is the affix genuinely written both ways?

## L15. Three rulings we made from the source's own examples — please confirm

All three follow the project's working rule: build what looks right now, mark
it unconfirmed, and ask. **All three are already in the code**, and each is
one line in `rules/decisions.yaml` to undo.

**V-052 is a prefix.** The source writes `-andar (darun)` with the dash on the
wrong side — exactly as it did for `-bāž`, which was settled the same way on
2026-08-11 — and its own example *andarāmadan* (اندرآمدن) puts it in front.
**N-038 is untouched**: the nominal table's `-andar (nātani)` really is a
suffix, and its example *Mādarandar* (مادراندر, stepmother) is right to put it
on the end. One spelling, two affixes.

**V-063 to V-066 attach to a stem, not to the infinitive.** All four rows write
`attaches_to: Nābesudkārvāže`, produce `Barnām`, and are otherwise identical —
no tag tells them apart. Their examples split two and two:

| | example | base | stem |
|---|---|---|---|
| V-063 | nasuz | suz | present, of suxtan |
| V-064 | nadid | did | past, of didan |
| V-065 | nāšenās | šenās | present, of šenāxtan |
| V-066 | nāšāyest | šāyest | past, of šāyestan |

Read as the infinitive, the engine kept the whole infinitive and called the
result an adjective — *nāhamandišidan*, which is not a word. This is also the
only reading we can find that explains why the source carries **a pair** for
each of the two prefixes. **Question:** is that right, and is the pattern
present-stem first, past-stem second, throughout?

**V-070 to V-076 add the infinitive ending.** These seven take kārbon-e yek and
say they produce a nābesudkārvāže, so *goft* must give *vāgoftan* — the prefix
alone left *vāgoft*, a past stem carrying the label of an infinitive. All
**seventeen** examples the seven rules carry end in *-an*, and stem rule S-01
says the converse: removing *-an* from the end of every infinitive leaves
kārbon-e yek. This one we are confident about; it is listed for completeness.

## L4. The rulings already recorded elsewhere

These sit in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) under *for the linguist*
and are listed here so one conversation covers everything. None blocks work.

| | |
|---|---|
| **H** | Is the prefix باژ or واژ? V-055 is the only rule still flagged. |
| **M** | Persian joining when a word ends in ه. **Built 2026-08-13 — see L7**, which supersedes this line. |
| **K** | ZWNJ inside a compound — گفت‌وگو against the engine's گفتوگو. |
| **L** | Can an affix stack on itself? **Answered by measurement — prefixes 2026-08-15, suffixes 2026-08-20**: 4,968 and 1,830 such words, and not one of either is attested. What is left is narrow: the guard keys on the affix's spelling, so a repeated *-i* is refused with the rest — is *andišidegiyi* ever right? |
| **Q2** | Two Persian spellings, one Behnevis reading — one word or two? 10,270 of them. |
| **R** | The source states a `strength` for 3 of 195 rules. Author the rest, or let the measurement stand alone? |
| **E** | The gloss templates. **Now L10 below**, with the measurement. |
| **C, D** | Are the lower-case bracketed labels tags or plain glosses? Is *Mānand* the same tag as *Mānandi*? |
| **I** | نهفتن has no present stem; the document writes ؟. |

### And one the app puts in front of a reader

**One spelling, two readings, and the same evidence printed under both.**
رفتن as *raftan* (to go) and رفتن as *roftan* (to sweep) each get their own
word page, and each states **3,886 occurrences in 3,202 poems by 208 poets**
— the count of the spelling, which is almost entirely the first verb. The
page says plainly that the two readings do not merge, and then gives both the
same number. This is item **Q2** seen from the reader's side; it needs no new
ruling, but it is what Q2 costs in practice.

---

## L16. A verb our own rules coin — what is its present stem?

Raised by PLAN 9.10 on 2026-08-17, and it is the half of that task no code
could settle.

**Giving a *prefixed* verb its stems needed no ruling.** A prefix is
transparent, so the stems of *hamandišidan* are the stems of *andišidan* with
*ham-* in front. Nothing is invented, and *hamandišande* — and *bāzguyande*,
بازگوینده — come back with it.

**Six rules coin a verb with a suffix instead**, and those are the case the
same change could not touch: V-001 to V-004 and V-051. *tars*, a noun, gives
*tarsidan*. Its past stem follows from S-01, which states the converse —
removing *-an* from an infinitive leaves it — so *tarsid*. **Its present stem
is written nowhere.**

The obvious guess is the base it was coined from, *tars*. We did not make it.
We measured what it would give:

| | |
|---|---|
| verbs these rules coin in one step from the lexicon | **74,116** |
| where the guessed present stem plus *-ande* is a real corpus word | **780** |
| the largest of those | فرخنده 1,924, تابنده 761, پاینده 761 |

**The caveat is in the attachment and it matters.** The coined verb's own corpus
count is almost always zero — فرخیدن is not in the corpus though فرخنده is, so
فرخنده may have reached that spelling by another road entirely. Evidence, not a
verdict, and the file carries both columns so he can see that for himself.

**Question:** does a verb coined by a suffix have a present stem; if so, is it
the base it was coined from; and is the answer the same for the causatives in
*-āndan* and *-ānidan* — *andišāndan* from *andiš*?

**Meanwhile these stay dead ends**, which is the safe direction: a verb is
built and nothing is built from its stems. Written into
`murfulu/engine/generate.py`, and one branch to change if he rules the other
way.

**Where the Persian may need checking**, per the working rule. The draft uses
بن گذشته / بن حال rather than کاربن یک / کاربن دو, following L12's wording, so
that a reader meeting the question cold is not asked to learn the project's own
vocabulary first. The project lead's to confirm.

---

## L17. Four of your own grammar terms, spelled by us. Are they right?

Raised by S3 on 2026-08-17, and it is the half of that task no code could
settle.

**What was wrong.** Your terminology table replaces the Arabic-derived grammar
vocabulary with a Persian one, and the machine ids in this project are
transliterations of it — `karnam`, `barnam`, `karandekarbahr`. But the Persian
those ids stand for lived only in a design document, so the only Persian in the
data was the **traditional** term. Every screen therefore labelled its groups
اسم مصدر, in exactly the vocabulary the project exists to replace.

**Eight are yours and are quoted, not invented.** کاربن یک، کاربن دو،
نابِسودکارواژه، کارنام، نام، برنام، کارنده‌کاربهر، کاریده‌کاربهر — straight from
your table.

**Four are not in that table, and we wrote them.** Each is read off the
Behnevis the source grammar itself uses in its rule rows, which looks mechanical
and is not:

| id | the source writes | we spell it | traditional | our reading |
|---|---|---|---|---|
| `jonvaze` | *Čonvāže* | چون‌واژه | قید | چون + واژه |
| `janam` | *Jānām* | جانام | ضمیر | جا + نام |
| `pisvaze` | *Pišvāže* | پیش‌واژه | حرف اضافه | پیش + واژه |
| `nedayi` | *Nedāyi* | **nothing** | ندایی | — |

**The last row is the one worth your attention.** *Nedāyi* is itself derived
from Arabic ندا, so it is a term in the vocabulary being replaced rather than a
replacement. We left it empty on purpose: writing ندایی into the column
reserved for your term would have hidden the gap. The screen falls back to the
traditional word and says that it fell back. **Question:** is there a Persian
term for the vocative, or is the class simply outside the table?

**And there is a spelling we did not touch.** The id is `jonvaze` with a *j*
where the source writes *Čonvāže* with a *č* — it comes from the Latin
convention this project used before the current one. The id stays, because an
id is permanent and is written into the rule files, the engine and every stored
derivation; the Behnevis is carried beside it. Nothing here needs a ruling
unless *Čonvāže* is itself the wrong reading.

**Twelve explanations are also ours, and none is confirmed.** The interface has
to explain *kārnām* without a manual, and no explanation existed in any data
file. One plain Persian line was written for each class, using only your own
vocabulary so that an explanation cannot quietly reintroduce the terms it
replaces — for example, کارنام reads «خودِ کار، که همچون نام آورده می‌شود،
مانندِ گفتار». **Question:** is each line right, and is any of them saying more
than the class does?

**Meanwhile all of it is on screen**, per the working rule, and the API marks
which terms you have ruled on and which you have not. Everything is in
`rules/word_classes.yaml`; each row is one line to change.

---

## L18. Six compounding rules take a *nām*, so a *kārnām* can form no compound

Raised by S18 on 2026-08-17, from the compounding route.

**What happens.** The six slot rules — the *soxanguy* / *tondrow* shape, a word
joined directly to a verb stem — all declare their front slot as a **nām**. The
source grammar states that what traditional grammar calls اسم معنی is a
**kārnām**, and karbon files سخن as اسم معنی. So سخن builds **nothing**, while

| word | what it is | the corpus |
|---|---|---|
| سخندان | سخن + دان (present stem of دانستن) | **199 documents** |
| سخنور | سخن + ور | **178 documents** |
| سخنگو | سخن + گو (present stem of گفتن) | **121 documents** |

are ordinary Persian and the corpus has all three. Measured against the same
snapshot: **1,949 readings are a kārnām and not a nām**, and every one of them
is shut out of every slot rule.

**Two things this is not.** It is not a claim that karbon has سخن wrong — that
question is already with the maintainer, and nothing here is filtered on it. And
it is not a claim that the rules are wrong; it is a question about what the
front slot means.

**One thing we deliberately did not do.** The mapping اسم معنی → kārnām in
`rules/lexicon_categories.yaml` is grounded in your own prose, so it was left
alone. Changing it would have been the engine overruling a ruling, which this
project does not do.

**And a caution about the number, because it would otherwise be quoted.** We
tried to measure the whole class — every kārnām against every present stem,
checked against the corpus — and **the result is not usable**. It reports 1,781
"attested" forms, and its top rows are روزگار read as روز + گار and بهاران read
as بها + ران, which are not compounds at all. Short strings collide. The three
rows above were checked by hand and are real; the aggregate is not evidence and
is recorded here only so nobody re-derives it and believes it.

**Question:** should a slot rule's front position accept a kārnām as well as a
nām — and if not, what is سخندان?

**The same question came back from the affix side on 2026-08-20, and there the
evidence is stronger — see [L26](#l26-four-nominal-rules-cannot-build-their-own-examples).**
L18 is about six compounding rules. L26 is about *-mand*, *-vār*, *-gāh* and
*-var*, whose own examples are دانشمند، امیدوار، دانشگاه and دانشور.

---

## L19. بلند has two readings and they disagree with each other. Which is right?

Raised by S13. The engineering half is settled and built; this is the half only
you can answer.

**What the dictionary holds**, measured on snapshot `lexicon-20260808`:

| reading | filed as | the dictionary's own flag | words it builds at two steps |
|---|---|---|---|
| *Baland* | اسم ذات | **needs_review**, confidence 0.4 | **2,335** |
| *boland* | صفت | clean, confidence 1.0 | 498 |

**The snapshot contradicts itself.** The same dictionary spells سربلند as
*sarboland*, with an **o**, and files it صفت مرکب with no flag at all. So the
compound agrees with the reading the dictionary doubts least, and the simple
word opens on the other one.

**What we did meanwhile, and it is an order and not a filter.** Readings are
now sorted by the dictionary's own flag and then by its own confidence, so بلند
opens on *boland* and the screen writes *SarBoland…* rather than *SarBaland…*.
Both readings are still returned and both are still built from; the flagged one
is one press away. This was the project lead's call after reading the screen and
asking why it wrote *Sarbalandi*.

**Nothing here is a reading of Persian.** We sorted on karbon's flag, which is
karbon saying *check this*, not on any judgement of ours — and 31.5% of active
rows carry that flag, so it is a note and not a verdict.

**Question:** is بلند *Baland*, *boland*, or genuinely both? If it is one, the
other is a fault to send upstream, and 2,335 built words currently hang off the
flagged reading. If it is both, is اسم ذات right for one of them — an adjective
filed as a concrete noun is what lets it take the noun rules.

---

## L20. Interface Persian we wrote on 2026-08-17. Does it read well?

**Not grammar terms** — those are yours and are quoted from your table, and
where four were not in it they are L17. These are the interface talking about
itself, which is ours to write. They went in during one pass through the app
and nobody with Persian as a first language has read them.

**Nothing waits on this.** They are live. What changes if you rule otherwise is
the wording, in one file each.

**The menu, three or four words under each name.** The complaint they answer is
that ساخت، ترکیب and تحلیل are three nouns a new reader cannot tell apart.

| screen | what we wrote |
|---|---|
| جست‌وجو | واژه‌ها را پیدا کنید |
| ساخت | از یک واژه، واژه‌های تازه |
| ترکیب | دو واژه، یک واژهٔ تازه |
| وندها | از معنا به وند |
| تحلیل | این واژه از چه ساخته شده؟ |
| دستورها | دستورهای واژه‌سازی |
| پرسش‌ها | آنچه هنوز نمی‌دانیم |
| پیکره | متن‌هایی که خوانده‌ایم |

**The corpus screen, under a small ⓘ.** «املای جداگانه» and «واژه‌گونه» sit
beside each other as ۴۰۹٬۹۱۶ and ۴۱۱٬۱۶۷ and nothing said why they differ. We
now say: واژه‌های جداگانه، آن‌گونه که **نوشته** شده‌اند / آن‌گونه که **خوانده**
می‌شوند. Is *نوشته / خوانده* the right pair for *spelling / word type*?

**The three stores** are glossed as سروده‌ها = متن‌هایی که خوانده‌ایم،
واژه‌گونه‌ها = واژه‌های جداگانه در آن متن‌ها، ساخته‌ها = آنچه ما با دستورها
ساخته‌ایم.

**The search errors.** Nine sentences, one per fault, e.g. «‹poem› چیزی نیست که
بتوان بر آن جست‌وجو کرد» and «سده باید عدد یا بازه باشد». They replace English
the reader used to see.

**The search builder's own labels**: الگوی حرفی، پایان‌یافته به، آغازشده با،
دربردارندهٔ، دقیقاً همین، کجا پیدا شده، بسامد در پیکره، سده. *الگوی حرفی* for
*letter pattern* is the one we are least sure of.

**And one sentence that is not ours to phrase lightly** — Ganjoor's licence,
which the corpus screen showed in English until now: «شعر کلاسیک، گردآوردهٔ
گنجور. گنجور خود می‌گوید داده‌هایش لزوماً از حق تکثیر آزاد نیست و هیچ تضمینی
نمی‌دهد.» It states a fact about someone else's terms, so it should be exact
rather than graceful.

---

## L21. The menu's three verbs-as-nouns. Are these the right words?

Raised 2026-08-18. **Nothing is changed yet** — this one is his to rule on,
because two of the three are real grammar words.

**What happened.** The project lead, who knows this project better than any
reader will, asked what the difference between **ساخت** and **ترکیب** is. The
menu had already been given a gloss line under each name on 2026-08-17 for
exactly this reason, and the gloss is carrying the whole load: the names
themselves say nothing that tells them apart.

| screen | now | what it does |
|---|---|---|
| `/build` | **ساخت** | one word + an affix → new words |
| `/compound` | **ترکیب** | two whole words → one word |
| `/explain` | **تحلیل** | a word → the parts it is made of |

All three are abstract nouns meaning roughly *doing something to a word*. The
one distinction a reader needs — how many words you start with, and which
direction you go — is in none of them.

**What we would propose, if he wants a proposal.** Verbs, because a verb names
what the reader does, and the three actions are visibly different where the
three nouns are not. All three are Persian rather than Arabic-derived, which is
the direction the rest of the grammar vocabulary has already gone.

| now | proposed |
|---|---|
| ساخت | **ساختن** |
| ترکیب | **چسباندن** |
| تحلیل | **شکافتن** |

The worry we cannot settle ourselves: **چسباندن** may read as too plain — it is
what you do with glue — for a term that names compounding in a scholarly tool.
A second option keeps the current words and puts the count into them: «ساخت با
وند» and «ترکیب دو واژه». It is clearer and it is longer, and the menu is
already 893px wide, which is why it cannot sit exactly centred on a 1280px
window.

**What changes if he rules the other way.** Nothing in the data or the rules —
these are menu labels and the screens keep their addresses. If he keeps
ترکیب and تحلیل, the gloss line stays as the thing that distinguishes them, and
we should expect to keep explaining the difference to readers.

---

## L22. Interface Persian written on 2026-08-18. Does it read well?

Same kind as L20 and gathered the same way. **None of it is grammar
terminology** — where a grammar term was needed it came from the rule pack, as
it must. This is the interface explaining itself, which is ours to write and
his to correct.

**The build screen's four sentences about one word.** The score used to be a
bare percentage; it is now said in words, one part per line:

- «۵ بار، در ۵ سروده از ۲ شاعر (پیکرهٔ v11). واژه‌نامه برای این املا خوانشی
  ندارد، پس این شمار برای املاست، نه برای این خوانش.»
- «وارفته از vāraft ساخته شده است، و vāraft در پیکرهٔ v11 پیدا نشد — آن را ما
  ساخته‌ایم. پس این واژه دو گام از متنی که خوانده‌ایم دور است.»
- «V-070 — ۵٬۱۹۶ واژه ساخته، ۳۵ تای آن‌ها در پیکرهٔ v11 پیدا شد.»
- «دستور V-009 از ۴۳۲ بن واژه‌ای ساخته که در پیکرهٔ v11 پیدا شده است.
  نزدیک‌ترین‌های آن بن‌ها به مرکزِ معنایی این دستور:»

**The one we are least sure of is «مرکزِ معنایی».** We coined it, the screen
never explains it, and it describes a method rather than a thing in the
language: the average of up to six corpus lines per stem, averaged again across
a rule's attested stems. A reader meets the phrase cold. Is there a better
Persian for *the middle of a set of meanings* — or should the screen drop the
phrase and let the list of stems speak for itself?

**Our own labels on the build screen**: «گامِ میانی»، «دستورهای این ساخت»،
«معنای پایه»، «راه ۱ از ۴». And two everyday words used as verdicts rather than
as terms: «کم‌بار» for a rule that seldom produces a written word, and «جور
بودن» for a base that suits a rule.

**The corpus screen** now names its source «گنجور» rather than printing
`ganjoor`.

**The search screen's purpose line** is the project lead's own wording: «در
اینجا می‌توانید واژه‌ها را بر اساس وندها، گونه یا بسامد جست‌وجو کنید.» Recorded
because it **drops الگوی حرفی**, which the screen can still do.

**What changes if he rules the other way.** Nothing measured and no data — this
is wording, and every sentence above is one string.

---

## L23. The meaning tags have no sentence, and the screen is showing the bare word

**This one is already visible to readers and is his field, not ours.**

`rules/semantic_tags.yaml` carries `gloss_template_fa` — described in the file
as *the sentence shown to the user for a word carrying this tag* — and it is
**null for every tag**, because the file says the linguist authors it and not
the engine.

On 2026-08-18 the build screen began showing the sense a rule carries, because
without it four rules building وارفتنی printed a word-for-word identical
explanation and a reader could not see why there were four. With no template to
use, it shows `gloss_fa` — a single word. So the screen now says:

| rule | shown | intended |
|---|---|---|
| V-070 | **پس** | back, behind |
| V-071 | **دوباره** | again |
| V-072 | **باز** | open, back again |
| V-073 | **آخشیج** | opposite, counter- |

The project lead read «پس» and asked what it meant — fairly, because «پس»
standing alone reads as *so / then*, not as a direction. The English gloss in
the same file says «back, behind», which is richer than the one Persian word.

**And the file already flags this.** Its own header marks these lower-case
labels — *bālā, pāyin, darun, pas* — as needing a ruling: they *may be
plain-language glosses of a prefix rather than tag names*, since Behnevis
capitalises a name and these are not capitalised.

**Two questions.** First, are these tag names or glosses? Second, would he
author `gloss_template_fa` for the tags the build screen shows, so a rule's
sense is a sentence rather than a word that can be misread?

**What we did meanwhile**: show `gloss_fa` as it stands, unchanged and
unqualified. It is his string; we did not dress it up.

---

## L24. دستور — دست + ور. Which ور?

Raised by the project lead on 2026-08-18, reading the compound screen for دست.

The screen offers **دستور** twice, as کارنده‌کاربهر (V-078) and as
کاریده‌کاربهر (V-079), both reading it as دست + **ور** where ور is the
**کاربن دو of وشتن** — that is what karbon's lexicon records for that verb.

The pack also holds N-080, *نام + -var → برنام* (*dānešvar*), which would read
the same letters as دست + the possessing suffix.

**Three questions, and only the first is really ours to lose sleep over:**

1. Is دستور دست + پسوندِ -var, and not a verb compound at all?
2. Is **ور** a present stem of **وشتن**? karbon derives it with its stem rule 8
   and marks it certain; we have not touched it.
3. When a verb stem is spelled like a productive suffix — we count **25 of
   3,232 verbs** in that position — should the compound screen show both
   readings side by side, or is the suffix reading simply the right one and the
   compound one noise?

**What we did meanwhile**, per the working rule: nothing was suppressed. The
row now shows which verb the second half is a stem of, so the claim is at least
visible and checkable instead of being a bare ور.

---

## L25. Two vowels touch at the front of a word, and no rule stops them

Surfaced 2026-08-20 while running the glide table backwards.

The table's first line is that Persian does not let two vowels meet, and all
seventeen rules describe a meeting at the **end** of the base: *gu* + *-eš*,
*dānā* + *-i*. Nothing in it describes a **prefix** ending in a vowel landing
on a base that begins with one, so the engine joins those with nothing between
them:

| built | the two vowels |
|---|---|
| *beemšipāš* (be- + Emšipāš, N-004) | e meets e |
| *naemšipāš* (na- + Emšipāš, N-019) | a meets e |
| *foruemšipāš* (foru- + Emšipāš, N-014) | u meets e |
| *biemšipāš* (bi- + Emšipāš, N-008) | i meets e |

**Measured**: **24 of the 53 active prefix rules end in one of the table's own
vowels**, and over a random 300 readings of the snapshot the engine makes
**119 such joins at one step alone**.

**Only one of those four pairs is in the table at all**: *u* meets *e* is
G-05 (*uye*). There is no left-hand *a* anywhere in the seventeen rules, no
*i* meets *e*, and no *e* meets *e*.

**The questions:**

1. Does the glide rule apply at a prefix join at all, or is a prefix written
   separately (ناآگاه, بی‌انصاف) and the two vowels simply allowed to stand?
2. If it does apply, is it the same table read with the prefix as the left
   side, or a different set of joins?
3. Is *e* meeting *e* a gap in the table, or does it never arise in the
   grammar's own terms?

**What we did meanwhile**, per the working rule: nothing changed. The forward
engine joins a prefix by concatenation, as it always has, and the decomposer
now reverses **exactly** what the forward engine does — no glide at a prefix
join in either direction. If the answer is that a glide belongs there, both
directions change together and the round-trip test in
`tests/test_engine_affix.py` will hold them to it.

---

## L26. Four nominal rules cannot build their own examples

Raised by the project lead on 2026-08-20, from the build screen. It is
[L18](#l18-six-compounding-rules-take-a-nām-so-a-kārnām-can-form-no-compound)
seen from the affix side, and this side carries the harder evidence: the words
these rules cannot build are **the examples the rules themselves carry**.

| rule | affix | its own example | can the engine build it? |
|---|---|---|---|
| N-071 | *-mand* | **dānešmand** — دانشمند | no |
| N-068 | *-gāh* | **Dānešgāh** — دانشگاه | no |
| N-074 | *-vār* | **omidvār** — امیدوار | no |
| N-080 | *-var* | **dānešvar** — دانشور | no |
| V-078 | slot | **soxanguy** — سخنگو | no — this one is L18 |

**One cause, and it is a word class.** All four nominal rules declare their
input as **nām**. The words their examples need are not nāms:

- امید، هنر، سخن، کار are filed **اسم معنی**, which your prose makes a
  **kārnām**.
- دانش is not a headword at all — but the engine builds it, from دانستن by
  V-033, and **labels its own output a kārnām**. So the chain breaks against
  itself: the engine makes دانش and then cannot put *-mand* on it.

Tested directly, with nothing else changed:

```
N-071 on dāneš as a nām     → dānešmand
N-071 on dāneš as a kārnām  → refused: "N-071 takes ['nam'], not 'karnam'"
```

### What it costs, measured on snapshot `lexicon-20260808`

**80 active rules take a nām. Exactly one takes a kārnām** — N-098, the *-i*
that makes a barnām. That is the whole of what a kārnām can do.

| class | readings | forms built at one step (median) |
|---|---|---|
| اسم معنی → kārnām | **1,949** | **1** |
| اسم ذات → nām | 13,746 | **65** |

Of the 163 rule examples that are checked against the engine, **11 fail with
the base held in another word class, and all 11 are this one**: the rule wants
a nām and the lexicon holds اسم معنی (N-002, N-010, N-011, N-022, N-026,
N-047, N-074, N-081, N-089, V-003, V-004). Three more — N-068, N-071, N-080 —
fail on دانش, which is the same fault reached through a built form rather than
a held one. **Fourteen of 163 examples, one cause.**

### These are ordinary Persian, and the dictionary already has them

| word | in the corpus |
|---|---|
| امیدوار | **538 documents, 130 poets** |
| هنرمند | **211 documents, 70 poets** |
| دانشمند | **137 documents, 45 poets** |
| سخنگو | **121 documents, 56 poets** |
| دانشگاه | 1 document — a modern word, and the corpus is classical |

All four of the first are in karbon's lexicon as **صفت مرکب**. The dictionary
has the words; only the derivation is shut.

### The question, and it is not the one it first looks like

There are **no sub-types of kārnām to name**. Your terminology table is
explicit that اسم مصدر, حاصل مصدر and اسم معنی all collapse into the one
class, so "which kinds of kārnām may take *-mand*" has no vocabulary to be
answered in. The question underneath is about the other word:

> **Does «نام» in the nominal rule table mean a nām and nothing else, or a
> noun in the ordinary sense — a nām *or* a kārnām?**

The document's own examples answer *the second*: دانشمند and امیدوار are its
examples for *-mand* and *-vār*, and both need a kārnām in front. Which makes
this a place where the document disagrees with itself rather than a place
where we have read it wrong — but that is yours to say, not ours.

**What we did meanwhile**: nothing, and deliberately. The mapping اسم معنی →
kārnām is grounded in your prose, and widening the rules would overrule it just
as surely as editing the mapping would. This is the same restraint as L18 and
the same reason.

**What changes if you rule that a kārnām may stand there**: `input_types` on
the nominal rules widens to `[nam, karnam]`, the slot rules' front class widens
with it, and **1,949 readings go from a median of one form to something near
the nām median of 65**. Every one of the fourteen examples above then has a
route. Nothing else in the engine has to change.

**And one thing that comes back with them, which you should weigh before
ruling.** Words the engine currently refuses *only* because of this mapping
would start being built again — not all of them wanted. **بوستان** is the
worked case: the analysis screen refuses it today, and it refuses it because بو
is filed اسم معنی and N-057 wants a nām. Tested: N-057 on *Bu* as a nām gives
بوستان. That one is very likely right — بوستان is بو + ستان in the ordinary
account. But the same widening will also let through joins that are only
letters, and the project has no way to refuse those in code: see
[FINDINGS](FINDINGS.md) on داستان, which rebuilds as دا + ستان today with a
base carrying 111 documents. **Widening this class buys correct words and
costs plausible-looking wrong ones**, and which trade is right is part of the
same ruling.

---

## L27. Candidates for the terms, and what the engine says about each

Asked for by the project lead on 2026-08-20. Three coining runs were made
against the **running app** — the same protocol as the *Dasein* experiment:
propose, then verify every proposal through `/explain`, `/generate`,
`/compound` and `/search`, and say plainly what could not be verified. Nothing
in the code or the rules has changed. **These are candidates for you to accept
or throw out.**

Every number below was read off the running system against corpus v11
(133,148 documents, 25,497,189 words) and snapshot `lexicon-20260808`.

### The four we think are worth changing

| | now | candidate | reading |
|---|---|---|---|
| **مصدر** | نابِسودکارواژه | **بن‌کارواژه** | *Bonkārvāže* |
| **صفت فاعلی** | کارنده‌کاربهر | **کننده‌برنام** | *konandebarnām* |
| **صفت مفعولی** | کاریده‌کاربهر | **شده‌برنام** | *šodebarnām* |
| **ندایی** | — none — | **بانگا** | *bāngā* |

And two the numbers do not force but the memory argument does: **گذشته‌بن** and
**اکنون‌بن** for کاربن یک and کاربن دو.

### مصدر — نابِسودکارواژه

Six syllables, and the only term in the family that cannot be read without a
harakat.

**نابِسود is real Persian and that is a point for keeping it** — 37 documents
by 6 poets, Ferdowsi among them, and بسودن in 22 by 12. The complaint is the
harakat and the length, not the word.

**بن‌کارواژه** — four syllables, no harakat, and it keeps کارواژه whole so the
term still says *this is a verb form*: بن the differentia, کارواژه the genus.
What is lost is *uninflected*, which نابِسود states exactly.

### صفت فاعلی and صفت مفعولی — and this pair is the sharpest case

**Your own term does not mean what it is meant to mean.** `/explain?word=kārande`
rebuilds it — from **کشتن، کاریدن، کاشتن**. Every route is *to sow*. There is no
route from کار to کارنده at all, so «آن که کار را انجام می‌دهد» reads, on this
project's own engine, as *the sower*.

**And کاربهر is in no Persian text we hold**: 0 occurrences in 25,497,189
words. کاریده has 1.

The pair fault is the second thing: five syllables each, identical at syllables
1, 3, 4 and 5, differing only at 2. Read aloud they are one word.

**کننده‌برنام / شده‌برنام** split at the **first** syllable — *ko-* against
*šo-*. Both halves are the engine's own output: `/explain` rebuilds *konande*
from کردن by V-022 and types it **karandekarbahr**; it rebuilds *šode* from شدن
by V-008 and types it **karidekarbahr**. Each word is an instance of the class
it would name. And برنام is already your word for صفت, which is what the
traditional term literally says — *agent adjective* — where کاربهر introduces a
word no Persian text contains.

Attestation: شده 10,588 documents by 229 poets, کننده 407 by 77.

**The runner-up pair is کننده‌برنام / کرده‌برنام**, both from کردن, so the two
would be one verb's own two participles — tidier, but they differ only in a
vowel, which is the fault being fixed.

### ندایی — and here the engine builds the answer itself

**بانگا.** It is the **one word in this entire experiment that our own rules
derive today, with no ruling from you needed at all.** Asked, the running app
answers:

```
/explain?word=bāngā
  rebuilt: true, settled: true, one account
  bāngā  ←  بانگ (Bāng, اسم ذات)  by  N-032
  the base: 4,230 occurrences in 3,306 documents by 205 authors, 11th–20th c.
```

**N-032 is the pack's single vocative rule** — `-ā` on a nām, producing a
**ندایی** — and the source table names the class exactly once against it. Its
own examples are ordinary Persian: *xošā* — خوشا in 1,161 documents by 160
poets — and *dardā*, 487 by 114. And karbon's own entry for بانگ glosses it
with **نداء**, beside فریاد and آواز بلند. So بانگا is the lexicon's word for
*the call*, put through the one rule that makes vocatives, and it is free:
**0 occurrences** in the whole corpus.

Against it: it demonstrates rather than defines — a reader who does not know
the ā rule learns nothing from the letters — and the capitalised *Bāngā* is
taken by a different rule (N-001, output nām), so the term has to be written
lower-case where the family capitalises class names.

**ناما was the first recommendation and is withdrawn.** It would have been
more elegant — the class naming itself — but it does not survive the engine.
نام is filed اسم معنی → kārnām, so N-032 refuses it outright
(`N-032 takes ['nam'], not 'karnam'`); the `-ā` suffix is **four different
rules**, not one; and because نام is also the present stem of نامیدن,
`/explain` accounts for ناما by V-024 and V-026 and never offers the vocative
rule at all.

**The plainer fallback is بانگ‌نام**, which cannot be built and carries one
cost we did not expect: of the 35 lexicon entries ending in ـنام, **18 are
صفت مرکب** — خوشنام، گمنام، نکونام، زشت‌نام — words meaning *of X repute*. So
بانگ‌نام reads as *of loud repute* before it reads as *the calling name*.

### کاربن یک and کاربن دو

Not a length question — گذشته‌بن is four syllables against four. It is that the
numbers must be memorised and a reader holding them the wrong way round gets no
warning from the words, where **گذشته‌بن** and **اکنون‌بن** are your own two
explanations word for word.

**The shape is well attested.** 45 lexicon entries end in ـبن and most are
اسم مرکب: گلبن (971 documents, 145 poets), خاربن (55/29), سروبن (45/20), رزبن،
خرمابن، کاج‌بن، شاخ‌بن، چاه‌بن.

**The tails, since they decide more of this than the meanings do.** Counted
over the whole lexicon:

| tail | entries | what they are |
|---|---|---|
| ـبند | **215** | 97 اسم مرکب, 84 صفت مرکب — the liveliest of the four |
| ـبن | **45** | mostly اسم مرکب — گلبن, خاربن, سروبن, رزبن |
| ـنام | **35** | **18 of them صفت مرکب** — *of X repute*, not *the nām that X* |
| **ـواژه** | **2** | گواژه and بلواژه, and neither is a compound of واژه |

**Four of your terms ride the last one** — کارواژه، نابِسودکارواژه، چون‌واژه،
پیش‌واژه. That is not fatal: a technical vocabulary is allowed to be
consistent with itself rather than with the poets. But it is worth knowing
that ـواژه is a tail this corpus does not compound with, while ـبن and ـبند
are tails it uses constantly.

**One thing blocks اکنون‌بن today**: karbon has **no reading for اکنون** at all,
though the corpus has it in 5,218 documents. Same for هست and دی. That is an
UPSTREAM item, not an argument against the term.

### The three we would leave alone, and why

**کارنام** stays. Two syllables, free in the whole corpus, transparent. The
alternatives are occupied — کنش is a live word in 205 documents, and کردار is
worse than occupied: `/generate` on کردن produces it under **three different
classes**, so it cannot name one. The only mark against کارنام is that کارنامه
is a real word (81 documents), so it can be heard as a clipped form of it.

**چون‌واژه** stays. It is in the source table 14 times, it is three syllables,
and the objection we expected — that the class is not only manner — does not
hold: the nine rules producing a چون‌واژه include *bāmdādān* and *māhāne*,
which are time, and چون carries time as readily as manner in Persian.

**جانام** stays. Two syllables, in the source table 5 times, an exact calque of
your own gloss. Its one collision is a single line by one poet. **جای‌نام**
should be avoided — in modern Persian that is a toponym.

### حرف اضافه — پیش‌واژه, and one clash worth your ruling

Two arguments against it. **را is a حرف اضافه and it follows its noun**, so a
term built on پیش- is wrong for it. And **پیش‌واژه collides with پیشوند**, the
settled modern word for *prefix* — in a morphology tool full of actual
prefixes. That clash is not hypothetical inside this project: **rule N-084
carries `Pišvand` as its own worked example.**

**بندواژه** says the linking rather than the position, in the same three
syllables, and survives را. Against it: بند is polysemous — bond, fetter,
joint, verse, dam — so it has to be learned rather than read off, and
پیش‌واژه is yours while بندواژه is ours.

### What none of them collides with

Checked against all 409,916 corpus spellings: **بن‌کارواژه، کننده‌برنام،
شده‌برنام، بانگ‌نام، گذشته‌بن، اکنون‌بن، بندواژه** — none appears anywhere in
25,497,189 words. Of the terms you already use, only **برنام** (15 documents,
11 poets) and **جانام** (1) are attested at all.

### What could not be verified

- **No candidate's Behnevis is a lexicon reading**, because no candidate is a
  word yet. Each is composed from halves whose readings were looked up. Nothing
  was transliterated by guess.
- **اکنون، هست، دی، بر، چون، خوانده have no reading in karbon** at all, so any
  candidate using them has no writable Behnevis today. UPSTREAM.
- **کنون's reading is `Kanun` and carries `needs_review: true`**, where the
  ordinary reading is *konun*. UPSTREAM.
- **The modern-usage claims are not measured.** پیشوند returns 0 hits in the
  corpus, as do جای‌نام and بندواژه — the corpus is classical poetry and cannot
  see modern technical Persian. The one hard piece of evidence for the پیشوند
  clash is N-084's own example.
- **Meaning is unchecked throughout.** N-104 carries no semantic tag and
  `meaning_fa` is null on every form the engine built. Whether بن‌کارواژه reads
  as *infinitive* to a Persian ear is your judgement and not ours.
- **Syllable counts were made by reading aloud.** The project has no
  syllabifier.

## L28. Your own terminology is coined by a rule the document does not have

Found while checking the candidates above, and it is the larger of the two.

**کارنام، کارواژه، جانام، چون‌واژه، پیش‌واژه are all a nām joined straight to
a nām.** So are ordinary Persian words in their thousands — کتابخانه، گلاب،
روزنامه، شبنم. **The nominal table has no row for that shape.** The only
two-noun row in all 110 is row 104, transcribed verbatim in
`rules/source_rows.json` as:

```
affix: -ā-   attaches_to: Nām + ā + Nām   produces: Nām / Čonvāže
examples: Sarāsar, sārāsar, Sarāpā
```

— which puts an **ā** between the two. So the engine, asked for the ordinary
compounds, builds:

| asked | the engine builds | the word |
|---|---|---|
| کتاب + خانه | کتاباخانه | کتابخانه |
| گل + آب | گلاآب | گلاب |
| روز + نامه | روزانامه | روزنامه |
| شب + نم | شبانم | شبنم |

And asked for **کارنام** — کار + نام — it builds **کارانام**.

**Two ways this could be, and only you can say which.** Either the document
means row 104 to cover both, with the ā optional, or plain juxtaposition is a
row nobody wrote down because it is too obvious to state. It is not in the
document either way, and the pack may not invent a rule.

### And it is worse than that, because L26 sits on top of it

**نام and واژه are both filed اسم معنی**, which your prose makes a **kārnām**,
and every nominal rule takes a **nām**. So the two words this entire
terminology is built out of are, to the engine, not nouns:

```
بانگ (nām)  + نام (kārnām)  →  nothing
پیش  (nām)  + واژه (kārnām) →  nothing
کار (kārnām) + نام (kārnām) →  nothing
```

Not even the wrong ā-form. **کارواژه — the base of the whole vocabulary —
cannot be built by any route at all.**

The single sharpest measurement in this session is the same fault seen from
one word: **نام builds one form at one step, `nāmi`. جا, which differs from it
only by being filed اسم ذات, builds 65.**

So both L26 and L28 have to be ruled on before the engine can build any term
in the grammar it implements.

**What we did meanwhile**: nothing, which is why the engine still builds
کتاباخانه. **What changes if you rule that the shape is a rule**: it becomes
N-106 or so, the engine gains what is probably the most productive compound
pattern in the language, and — for the first time — it can build the words this
project's own grammar is written in.

**A caution about counting it.** We tried to measure how much of the corpus is
this shape by splitting every common spelling into two lexicon nouns. **The
result is not usable** and is recorded here so nobody re-derives it and
believes it: it reports 43 of the 4,000 commonest spellings, and its top rows
are پیوسته read as پیو + سته, دیگران as دیگ + ران and داستان as داس + تان.
The same failure as the L18 measurement, for the same reason: short strings
collide. The four words in the table above were checked by hand.
