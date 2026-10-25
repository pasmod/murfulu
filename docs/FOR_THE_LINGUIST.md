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

---

## L29. Rechtsstaat — a Persian word for it, and the two rules that stop us building one

Asked for by the project lead on 2026-08-24. Same protocol as L27: propose,
then verify every proposal through `/explain`, `/generate`, `/compound` and
`/search`, and say plainly what could not be verified. Nothing in the code or
the rules has changed. **These are candidates for you to accept or throw out.**

Every figure below was read off the running app against corpus v11
(25,497,189 words) and snapshot `lexicon-20260808`.

### What the German word says, since the candidates turn on it

*Rechtsstaat* is **Recht** + **Staat**, and the head is *Staat*: it names a
kind of **state**, not a kind of law. What it says is that the state is itself
**bound** by law — the state is law's author and law's subject at once. Its
opposites are named words in German: *Machtstaat*, *Polizeistaat*,
*Willkürstaat*, *Unrechtsstaat*.

**And *Recht* is not *Gesetz*.** *Gesetz* is the enacted statute; *Recht* is
law-as-right, and it carries justice inside it. The German constitution binds
the state to «Gesetz **und** Recht» — both words, deliberately.

This is why the standing Persian, **دولت قانونمدار**, is not quite the word.
It is three Arabic loans (دولت، قانون، مدار), and قانون is *Gesetz*, the
statute — so the term says *statute-centred state* and loses the half of
*Recht* that means what is right.

**داد is the Persian that has both halves.** karbon's own entry glosses it
«عدل. مَعدِلَه. قسط. نصفت. **مقابل ستم**»; Middle Persian *dād* is *law*. And
Persian already carries the antonym as one word — **بیداد**, which is
*Willkür* exactly. The pair Recht/Unrecht is the pair داد/بیداد.

| | occurrences | documents | authors | centuries |
|---|---|---|---|---|
| **داد** | 23,731 | 13,149 | 229 | 11th–20th |
| **بیداد** | 2,210 | 1,935 | 190 | 11th–20th |

### The candidates

| | reading | what it says | in the corpus |
|---|---|---|---|
| **دادبوم** | *Dādbum* | the land held under داد | **0** |
| دادشهر | *Dādšahr* | the realm of داد | 0 |
| دادکشور | *Dādkešvar* | the country of داد | 0 |
| دادبنیاد | *Dādbonyād* | *rechtsstaatlich*, the adjective | 0 |
| دادسالاری | *Dādsālāri* | **rule of law**, not *Rechtsstaat* | 0 |
| دادسامان | *Dādsāmān* | **Rechtsordnung**, not *Rechtsstaat* | 0 |

**We recommend دادبوم**, and the reason is your own lexicon's tails rather
than our taste. Counted over the 45,579 active entries:

| tail | entries | what they are |
|---|---|---|
| ـستان | 249 | 159 اسم مرکب — the tail that names countries (گلستان, هندوستان) |
| **ـبوم** | **14** | 12 اسم مرکب, **every one of them «[X]-land»** |
| ـکشور | 4 | |
| **ـشهر** | **3** | کهنه‌شهر، هم‌شهر، بی‌شهر — all about the *city*, not one a realm |

The ـبوم entries are ریگ‌بوم، شوره‌بوم، شوربوم، سنگ‌بوم، شن‌بوم، غله‌بوم،
میوه‌بوم، مرزبوم، زادبوم، آبادبوم، تازه‌بوم، فراخ‌بوم، پاکیزه‌بوم and
**پاک‌بوم, which Dehkhoda glosses «کشور پاک. خطهٔ پاک»** — so a ـبوم compound
is read as a country in the dictionary's own words. مرزبوم it glosses
«سرحد مملکت».

**Against دادشهر, and it is this project's own evidence.** ـشهر compounds in
the corpus are town names — گلشهر، بوشهر، آبادشهر — so دادشهر reads as a
suburb before it reads as a polity. What is on the other side is that modern
political Persian does use شهر for a polity type (آرمانشهر for *utopia*), and
that ایرانشهر is in the corpus in 10 documents. If you weigh the modern
pattern above the classical tail, دادشهر is the better word and we will change.

**دادبوم's own cost, stated.** بوم also names the owl — بوف's entry says
«آنرا بوم نیز گویند» — though no ـبوم compound in the lexicon carries that
sense. And بوم is a territory where *Staat* is an institution.

**دادستان was the first candidate and is withdrawn**, but the reason is worth
your eye: karbon holds **two** readings of it, and the second is
`Dādastān`, اسم مرکب, glossed «مرکب از «داد» به معنی عدل و «ستان» از ادات
اتصاف به مکان، **یعنی محل داد**». Persian made *the place of justice* out of
these exact two pieces already — 14 occurrences, 12th–13th century — and the
modern language then took the word for the public prosecutor.

**دادمندی was proposed for *Rechtsstaatlichkeit* and is withdrawn**: it is in
use, and it is in use meaning عدالت — a synonym of دادگری, not a name for the
quality of being bound by law. **دادبنیادی** is the fallback, at four
syllables.

### And the engine cannot build a single one of them

`/explain` on every candidate returns **`rebuilt: false`**. Two rules stop it,
and both are already your questions.

**L26, on the word this task needs.** داد is filed **اسم معنی**, which your
prose makes a **kārnām**. **80 active rules take a nām and exactly one takes
a kārnām** — N-098, the *-i*. So:

| داد classed as | forms at one step |
|---|---|
| kārnām, as it stands | **1** — دادی |
| nām | **79** |

The 79 are not exotic. They include **دادگاه، دادستان، دادگر، دادور، دادبان،
دادوند، دادمند، دادکده، دادگان** — real Persian words, most of them the
vocabulary of the courts, none of which the engine can reach from داد today.

**L28, on the compound.** N-104 is the only two-noun row and it puts an ā
between the halves, so asked for دادبوم the engine offers:

```
N-104   داد + بوم    →   دادابوم
N-104   داد + شهر    →   داداشهر
```

**The sharpest way to put both faults together.** The engine builds the
Persian for *Unrechtsstaat* today and cannot build the Persian for
*Rechtsstaat*:

```
/explain?word=Bidādstān   rebuilt: true,  settled: true,  one account
    Bidādstān  ←  بیداد (Bidād, اسم مرکب)  by N-057
    the base: 2,210 occurrences in 1,935 documents by 190 authors

/explain?word=Dādbum      rebuilt: false, no account
/explain?word=Dādšahr     rebuilt: false, no account
```

بیداد is an اسم مرکب and so a nām; داد is an اسم معنی and so is not. One
category mapping is the whole difference between the two words.

The route itself is sound, which was checked rather than assumed:
`/explain?word=Šahrvand` returns **`rebuilt: true`** — شهروند, the modern word
for *citizen*, is the engine's own output from شهر by N-084 and N-105.

**What we did meanwhile**: nothing. **What changes if you rule L26 the way its
evidence points**: دادبوم and دادشهر still need L28, but دادمند، دادستان،
دادگاه، دادبان and the rest of the court vocabulary start building from داد
the same afternoon.

---

## L30. Demokratie — the Persian is already good, and the tail under it says the opposite

Asked for by the project lead on 2026-08-25, straight after L29 and by the same
protocol: propose, verify every proposal through the running app, say plainly
what could not be verified. Nothing in the code or the rules has changed.

**Unlike L29, this is not a gap.** Persian already has a wholly Persian,
established, understood word — **مردم‌سالاری** — and we recommend keeping it.
There is one question underneath it, and it is yours.

### What the Greek says, since the question turns on it

*Demokratie* is a Greek loan in German, not a German compound: δῆμος +
κράτος. German's own native gloss is *Volksherrschaft*.

**δῆμος is the citizen body of the polis** — not *Volk* as a people or a
nation. In Athenian mouths it also carried a class sense, the commons against
the few.

**κράτος is power, might, holding-the-upper-hand — it is not an office.**
Greek keeps two suffixes apart and the pair is the whole point:

| | | |
|---|---|---|
| ‑αρχία | *archē*, rule, office | μοναρχία — *the rule of one* |
| ‑κρατία | *krátos*, power held | δημοκρατία — *the people hold the power* |

So the word does not say *the people have a ruler*. It says **the power is in
the people's hands**.

### مردم is not داد, and that matters

Where داد stopped the engine dead (L26), مردم does not:

| | filed | one-step forms |
|---|---|---|
| داد | اسم معنی → kārnām | **1** |
| **مردم** | **اسم ذات → nām** | **65** |

مردم: 13,953 occurrences in 8,900 documents by 226 authors, 11th–20th century.
سالار: 1,660 in 1,187 by 124.

So **Demokratie is one wall away from being derivable and Rechtsstaat is two.**
`/explain?word=Mardomsālāri` returns **`rebuilt: false`**, and L28 alone is why
— the single two-noun rule puts its ā in and offers:

```
N-104   مردم + سالار   →   مردماسالار
```

### The finding: every ـسالار in your lexicon is *the chief of X*

Counted over the 45,579 active entries, **ـسالار has 16 entries, 14 of them
اسم مرکب** — the strongest of the rival tails by a distance (ـشاهی has 5,
ـداری 3, ـفرمانی and ـتوانی and ـسروری none at all). The tail is the right
one. What it *means* is the question:

| | Dehkhoda's own gloss |
|---|---|
| سپهسالار | «سالار و رئیس لشکر» — 88 occurrences, 80 documents, 45 poets |
| دریاسالار | «امیرالبحر… صاحب‌منصب نیروی دریایی» |
| ناوسالار | «فرماندهٔ ناو» |
| خوانسالار / خانسالار | «رئیس میز پادشاهی» — 20 occurrences |
| **بارسالار** | **«سالار بار»** |
| **نوبت‌سالار** | **«سالار نوبت. سرکردهٔ نوبتیان»** |
| گندسالار | «فرماندهٔ واحدهای سپاه در زمان ساسانیان» |
| سابقه‌سالار | «سرلشکر. پیشرو لشکر» |

**All sixteen are «the سالار of X».** The last two rows are the sharpest,
because the dictionary unpacks the compound in so many words: بارسالار *is*
«سالار بار». The first noun is what is commanded, never who commands.

**Read by that rule, مردم‌سالار is «سالار مردم» — the chief over the people**,
which is the thing democracy is defined against.

### And the fair answer to our own objection

**The modern ـسالاری words all reverse the relation and none of them is in the
lexicon**: دیوان‌سالاری، شایسته‌سالاری، نخبه‌سالاری، تک‌سالاری. Every one means
*rule by X*. So modern Persian did not misuse the classical tail — it gave the
tail a **new relation**, and مردم‌سالاری is one member of that new series.

**The question is only whether that reversal is licit.** If you rule that it is
not, مردم‌سالاری does not fall alone; the whole series falls with it, and
Persian loses its words for bureaucracy and meritocracy at the same time. We
think that is the argument for letting it stand, and we say so rather than
hiding it inside a recommendation.

### The one candidate the engine builds today — and why we are not offering it

```
/explain?word=Mardomgāni   rebuilt: true,  two accounts
    مردمگانی  ←  مردم (Mardom, اسم ذات)  by N-067  (-gāni)
    مردمگانی  ←  مردم  by N-064 (-gān) + N-095 (-i)
```

مردمگانی is built by exact analogy with N-067's own worked example,
**خدایگانی** — and it is the only candidate in this run the engine derives with
no ruling needed, the بانگا of L27 all over again.

**We reject it on the evidence, and the evidence is about N-067 itself.**
خدایگانی **is not a headword at all**. Only خدایگان is, and karbon files that
as a **وام‌واژه**. And the 16 entries ending in ـگانی are grape varieties and
tanned leather — کرنگانی، گوزگانی، کورگانی، کوزگانی، گوژگانی — coins, and six
compounds of زندگانی. **There is no word of government anywhere on that tail.**

Recorded because it is the cleanest case we have of the thing this project
keeps having to say: **the engine building a word is not the engine approving
it.** N-067's example not being a headword is a separate small fault worth
your eye.

### Two more that were proposed and dropped

**مردم‌شاهی** — ـشاهی has **5** lexicon entries and they are coins and a plant:
چارشاهی، چهارشاهی، نیم‌شاهی، ارده‌شاهی، اورنگ‌شاهی. Not a tail that names a
form of government, whatever پادشاهی suggests.

**مردم‌داری** — occupied. It is a live word meaning affability and courtesy,
and it is in the corpus.

### What we recommend

**Keep مردم‌سالاری.** Wholly Persian, established, understood, on the only tail
with real support, and free in all 25,497,189 words of the corpus — which for
a modern term means only that the poets did not write it (see S33).

**مردم‌سالار** for *demokratisch*, and **مردم‌سالارانه** for the adverb.

What we want from you is the ruling on the relation, not on the word.

---

## L31. امکان، ضرورت، واقعیت — three terms, and the first set the engine can build

Asked for by the project lead on 2026-08-25: pure-Persian renderings of the
three modal terms, in **فارسی سره**. Three runs against the running app, one
per term, same protocol as L27, L29 and L30. Nothing in the code or the rules
has changed. Every figure was read off corpus v11 (25,497,189 words) and
snapshot `lexicon-20260808`.

### The recommendation

| | now | candidate | reading | adjective | rules |
|---|---|---|---|---|---|
| **امکان** | Möglichkeit | **شایایی** | *Šāyāyi* | شایا | V-024 + V-025 |
| **ضرورت** | Notwendigkeit | **بایایی** | *Bāyāyi* | بایا | V-024 + V-025 |
| **امتناع** | Unmöglichkeit | **ناشایایی** | *Nāšāyāyi* | ناشایا | V-065 + N-033 + N-095 |
| **واقعیت** | Wirklichkeit | **کردمان** | *Kardmān* | — | V-014 |

**And this is the first term set in the project's history that the engine
builds today, with no ruling from you needed on L26 or L28.** Every one of
those four returns `rebuilt: true`. دادبوم could not be built; مردم‌سالاری
could not be built; these can.

### Why they build where the last two runs failed

**Because they go in through a مصدر instead of a noun.** L26 is a rule about
what a *noun* is; a verb is neither a nām nor a kārnām, and the V-rules take
verb stems.

| base | filed | forms at one step |
|---|---|---|
| کار | اسم معنی → kārnām | **1** |
| توان | اسم معنی → kārnām | **2** |
| یارا | اسم معنی → kārnām | **1** |
| داد (L29) | اسم معنی → kārnām | 1 |
| **شایستن** | **مصدر** | **38** |
| **بایستن** | **مصدر** | **38** |
| **کردن** | **مصدر** | **38** |

So the whole modal vocabulary was reachable all along, and the two previous
runs failed because they reached for nouns. **Worth stating as a method:
where a concept has a native verb, coin off the verb.**

### امکان — and the one Persian verb that means *to be possible*

**شایستن**, Middle Persian *šāyistan*, the verb of the Pahlavi *Šāyest nē
Šāyest*. There is no second candidate root: توانستن is *ability* (δύναμις's
sense, which Islamic philosophy rendered **قوّه**, not امکان), شدن is
*becoming*, بودن is *being*. None of those is a modality.

**A trap we nearly fell into, and you should know it exists.** karbon holds
**ناور**, صفت, glossed «به معنی ممکن باشد که **برابر واجب** است» — the exact
modal pairing — and **ناوران** for ممکنات. Both entries end
«**از لغات ساختگی دساتیر است**». They are eighteenth-century forgeries of the
Āzar Kayvān school. Refused.

### ضرورت — and the split your dictionary has already made

The Arabic Persian inherited holds **two** words where the concept needs one.
**ضرورة** is from ض-ر-ر, *harm* — its home is exigency and duress. The term
Islamic logic actually uses for modal necessity is **وجوب**. This term is for
وجوب.

**And بایستن's two participles have already been pulled apart along that
line, by Dehkhoda, not by us:**

| entry | filed | gloss |
|---|---|---|
| **نابایا** | صفت مرکب | «مقابل بایا. **ممتنع. مقابل واجب**» |
| **نابای** | صفت مرکب | «**محال. مقابل ممکن.** ضد ممکن» |
| نابایست | صفت مرکب | «**نالایق. نامناسب**… که سزاوار نیست. که درخور نیست» |

**بایا is on the modal square; بایسته is on the fitting-and-worthy square.**
That is why the recommendation is بایایی and not بایستگی — and بایستگی is the
better-attested word (**42 occurrences, 17 documents, 9 authors, 12th–20th**,
against بایا's 2). It is rejected because it is the *ought* word: if ضرورت
becomes بایستگی, Persian has nothing left for *Sollen*.

**Two headwords of yours sit on the modal square and both are built on بای-.**
No other candidate root in this run has any such support.

### واقعیت — the one that should not join the family

*Wirklichkeit* is **wirken**, to work and have effect. **It does not say
*really there*.** Pfeifer's *Etymologisches Wörterbuch* has late Middle High
German *wirkelīcheit* meaning «Tätigkeit, Wirksamkeit, Aktivität» — activity
and efficacy, before ever meaning reality. German keeps Sein, Dasein,
Existenz, Realität, Wirklichkeit and Tatsache apart; Persian واقعیت is asked
to carry all six.

**A correction to what we first wrote, since it was asserted and is not
established.** We said Meister Eckhart coined *Wirklichkeit* to render
*actualitas*, itself Aristotle's ἐνέργεια. **Neither half is confirmed.**
Pfeifer does not mention Eckhart or *actualitas*; Grimm's dictionary gives the
Latin equivalents as *operatio, actus, operabilitas, efficacia, existentia* —
**not *actualitas*** — and names nobody. The attribution is carried unfootnoted
by German Wikipedia, and the best source found for it (W. J. Hoye) hedges it
himself as «so die Angaben der philosophischen Wörterbücher». Hoye also says
*actualitas* is «keineswegs aristotelisch»: it arises in thirteenth-century
theology, earliest in Albertus Magnus, and Eckhart took it from Aquinas.
**What survives, and it is what the argument rests on, is that *Wirklichkeit*
is built on *wirken* and first meant efficacy.** The *Historisches Wörterbuch
der Philosophie* entry is the citation that would settle the rest; it was not
read.

**And واقعیت translates the wrong one.** و-ق-ع is *to fall, to occur*, so
واقعیت says **occurredness** — which is *Tatsache*, «was der Fall ist», where
the German *Fall* is a fall exactly as Latin *casus* is. It is a good
rendering, filed under the wrong heading. It occurs **12 times in 12 documents
by 7 authors** in the whole corpus: an import, not an inheritance.

**Note that the Islamic tradition got the root right where the modern word got
it wrong**: بالفعل / بالقوه is built on ف-ع-ل, *to do* — *agere*, ἐνέργεια. A
Persian term should follow بالفعل's root choice, so it is built on **کردن**.

**هستی is not available and must not be taken.** 8,710 occurrences in 6,390
documents by 211 authors — the largest attestation in this run. It is
Persian's *Sein* and taking it would collapse the distinction the term exists
to keep.

**کردمان** — کردن + `-mān` on the past stem, **V-014, one account, no
competing parse**. The suffix makes a standing state and not an act, which is
the Wirklichkeit/Handlung difference: Dehkhoda glosses **ساختمان** «نهاد. وضع.
ساخت. ترتیب. **خلقت**» — the constitution of a thing — and **کشتمان** «صحرای
کشته و زراعت شده». So `[past stem] + مان` is *the standing whole of what has
been done*.

**Its cost, stated:** ـمان is also the first-person-plural clitic, so کردمان
can be read *we did*. Its 4 corpus occurrences are probably exactly that — we
could not read the lines. What answers the objection is **گفتمان, which
carries the identical ambiguity, has 0 occurrences in the whole corpus, and
won completely.**

**And one word we are rejecting although the engine builds it and its gloss is
the best in the field.** **کنشمندی** rebuilds by one rule from کنشمند, which
Dehkhoda glosses «خداوند کردار و **صاحب عمل**… یعنی **کننده و فاعل**» — *being
in act*, almost word for word. The same entry ends «**و این لغت از دساتیر
است**», and its stated synonym کنور is «دساتیری است… از **برساخته‌های فرقهٔ
آذرکیوان**». Forgeries again. **132 lexicon entries mention دساتیر and 52
mention آذرکیوان**; a سره coining run walks into them constantly.

### Two things a check outside the corpus found, and one of them moves the word

**There is already a rigorous pure-Persian system for these terms, and L30's
rule says we must report it rather than coin past it.** Mohammad Heidari
Malayeri's *Etymological Dictionary of Astronomy and Astrophysics* carries a
complete, internally consistent set:

| | Persian | from |
|---|---|---|
| real / reality | **هسیا / هسیایی** | Old Persian *hašya‑* «true, real», the same PIE root as هستن |
| actual / **actuality** | **ژیروند / ژیروندی** | ژیر, Avestan *žirā‑* «active, agile» |
| potential / potentiality | **توند / توندی** | تو‑, the stem of توان |
| energy | **کاروژ** | کار |

He rejects **کنش** explicitly, and his reason is one you should weigh: Persian
has only کردن for both *do* and *act*, so کنش «confounds 'to do' with 'to
act'». That objection lands on **کردمان** too, and we did not have it when we
recommended it. `/explain?word=Hasyāyi` returns `rebuilt: false` — none of
Malayeri's stems is in karbon.

**Kazzazi's سره tradition gives واقعیت → راستینه / راستینگی**, consistently
across four independent lists. **We refuse it and the reason is the analysis
above**: راستین is *true*, so راستینه is **Wahrheit**, and German keeps
Wahrheit and Wirklichkeit apart. راستینه rebuilds (`true`, N-101 + N-088 on
راست) and has 1 corpus occurrence; راستین has 319.

**And the finding that changes our recommendation.** **ورزیدن, Greek ἔργον and
German *wirken* are the same Proto-Indo-European root, \*werǵ-.** Persian
ورز/ورزیدن ← Middle Persian *warz/warzīdan* ← Proto-Iranian \*warj‑; Greek
ἔργον ← \*wérǵom, whose cognate list names Avestan *varəzəm* outright; German
*wirken* ← Proto-Germanic \*wirkijaną. And **ἐνέργεια is ἐν + ἔργον**.

**So a Persian term coined on ورز‑ reproduces in Persian exactly the move
German made from *wirken* and Greek made from *ergon* — with the genuine
Iranian cognate of both.** کردن does not do that: کردن is *facere/tun*, and
*wirken* is the other verb, which Persian also has.

```
/explain?word=Varzidmān   rebuilt: true, ONE account
    ورزیدمان  ←  ورزیدن (مصدر)  by  V-014
```

Free: **0 occurrences**, no lexicon entry. Identical shape and identical
cleanliness to کردمان, on the etymologically exact verb.

**Its cost, and it is the neighbourhood again.** Every ورز‑ headword in your
lexicon is a farmer or an athlete: ورزکار «زارع. کشاورز», ورزگر «برزگر»،
ورزیگر «کشاورز»، ورزگاو and ورزو the plough‑ox, and the ورزش family. On its own
tail, a ورز‑ word reads as *the ploughing*. And ورزیدمان is four syllables
against کردمان's two.

**The short form of the ورز‑ line is already taken**: **ورزمان** was approved
by the Farhangestān in 1390 for **ماساژ**. Worth knowing — it was on our list.

**Where we now stand: ورزیدمان leads on the argument and کردمان on the form.**
Four syllables is the length of بن‌کارواژه, which L27 recommended, so we lean
**ورزیدمان** — but this is a ruling and it is yours.

### The verses, read at last — and they settle the first question against us

Every run in this project has reported counts and said it could not read a
line. **That was wrong about our own system**: the corpus is in an
Elasticsearch index called `documents`, each record carrying `text_fa` whole,
and a phrase query returns the verse. The counts were never the only thing
available. Read now, the lines move the recommendation.

**شایایی is used, in the one place it occurs, to mean *worthy*** — which is
the sense §1 said the term must not swallow. In ملک‌الشعرا بهار's «ای زن» it
stands in one row with **لایق**, and **درخور** follows in the next couplet.
There is no modal reading available.

**بایش is used, in the one place it occurs, as a term of logic.**
ادیب‌الممالک, in a poem that glosses a vocabulary line by line, glosses
**بایش as ایجاب and رانش as سلب** — necessitation against negation, the exact
opposition the term is for, in a Persian poet's own gloss.

**بایا's single occurrence is not the word at all.** ابن یمین uses it in a
riddle about reversing letters. So بایا, on which we rested the
recommendation, has no attested use in 25,497,189 words.

**بایستگی's classical use pairs it with شایستگی in the *fitting* sense**,
which supports the split we drew: فرخی سیستانی and خواجوی کرمانی both set
**بایستگی** and **شایستگی** side by side as a pair, one in each half of the
line.

**But ناصرخسرو uses it philosophically, and this is against us**, in the
prose of «صف پنجاه و دوم», arguing the necessity of time. **واجب and بایستگی
in one passage, by a philosopher.** So بایستگی is not purely deontic, and our
§2 argument is weaker than it read.

**کردمان's four occurrences are all the clitic, now verified rather than
inferred** — in بهار, افسرالملوک عاملی and اثیر اخسیکتی each is کرد + مان,
*did to us*. The word itself is free.

**So we revise the first question's answer.** ـش was argued for on brevity and
an empty slot; it now has the better *usage* evidence too, and ـایی has an
attestation pointing the wrong way. **We now recommend شایش and بایش**, and
the cost stays what it was: **ناشایش does not build** (`rebuilt: false`), so
امتناع has to come from the ـا adjective — **نابایا** (`rebuilt: true`,
V-065 + N-033) and **نابایی** (`rebuilt: true`), and نابایا and نابای are your
own headwords. A set of two ـش nouns with an ـا negative is not tidy, and we
would rather say so than force symmetry.

### The two questions we could not settle, and they are yours

**1. ـایی or ـش?** Both shapes build off the same two verbs:

| | ـایی | ـش (V-033) |
|---|---|---|
| امکان | شایایی (3 syllables) | **شایش** (2) |
| ضرورت | بایایی | بایش |
| امتناع | ناشایایی — **`rebuilt: true`** | **ناشایش — `rebuilt: false`** |

**ـش is shorter and its slot is emptier**: شایش has 0 occurrences and the
wildcard `شایش*` returns **0 distinct spellings in all 409,916**. Its tail is
the most productive deverbal class in the language — دانش 4,488 occurrences,
آفرینش 1,871, کوشش 1,221, بینش 688 — and دانش and بینش are *state* nouns, so
the "possibility is not a process" objection does not hold. Two سره
dictionaries already give **شایش** for امکان.

**ـایی closes under negation and ـش does not**, and the two headwords above sit
on it. Against ـایی: `شایا*` returns 8 spellings and seven are شایان and its
inflections — 131 occurrences meaning *worthy* — so شایایی has the axiological
family as its neighbour where شایش has no neighbour at all.

**We recommend ـایی for the set and would not argue with ـش for امکان alone.**

**2. Is امتناع ناشایایی or نابایایی?** Logically امتناع is the negation of
امکان, so ناشایایی. But your dictionary glosses **نابایا** as «ممتنع» while
glossing **نابای** as «مقابل ممکن» — the negative pole is recorded on بای- in
both entries, and the two glosses are not consistent with each other. We have
not smoothed this over.

### Evidence

`/explain` at depth 3, and corpus counts as occurrences / documents / authors.

| candidate | Behnevis | rebuilt | rules | corpus |
|---|---|---|---|---|
| **شایایی** | Šāyāyi | **true**, 3 | V-024+V-025, V-024+V-030, V-026+V-027 ← شایستن | **1 / 1 / 1** — ملک‌الشعرا بهار, 20th c. |
| **بایایی** | Bāyāyi | **true**, 4 | same three ← بایستن, **+ one spurious** N-002+N-095 ← یا | **0** |
| **ناشایایی** | Nāšāyāyi | **true**, 1 | V-065 + N-033 + N-095 ← شایستن | 0 |
| نابایایی | Nābāyāyi | true, 3 | N-095 ← نابایا (a headword) | 0 |
| **کردمان** | Kardmān | **true**, 1 | **V-014 ← کردن** | 4 / 4 / 4 |
| شایش | Šāyeš | true, 2 | V-033 ← شایستن; V-033 ← شاییدن (base 0 occ) | **0**, and `شایش*` = 0 spellings |
| بایش | Bāyeš | true, 2 | V-033 ← بایستن; ← باییدن | 2 / 2 / 2, 13th c. |
| ناشایش | Nāšāyeš | **false** | نا- takes an infinitive, not a kārnām | 0 |
| شایا | šāyā | true, 2 | V-024, V-026 ← شایستن | 0 |
| بایا | bāyā | true, 3 | V-024, V-026 ← بایستن, + N-002 ← یا | 2 / 2 / 2, 13th c. (عطار، ابن یمین) |
| بایستگی | Bāyestegi | true, 3 | V-008+V-082 ← بایستن | 42 / 17 / 9 — **the *ought* word** |
| شایستگی | Šāyestegi | true, 3 | — | 133 / 97 / 41 — **occupied: merit** |
| کنندگی | Konandegi | true, 6 | V-022+V-023 ← کردن | 0 — runner-up for واقعیت |
| کنمان | Konmān | true, 4 | V-037, V-038 ← کردن (present stem) | 0 |
| کنشمندی | Konešmandi | true, 1 | N-095 ← کنشمند | 0 — **دساتیر** |
| ناور | nāvar | true, 2 | both spurious | 8 / 8 / 7 — **دساتیر** |
| هستی | Hasti | **false** | — | 8,710 / 6,390 / 211 |
| کارایی | Kārāyi | true, 9 | **every base کشتن، کاریدن، کاشتن** | 0 |

**کارایی is L27's کارنده fault reproduced on a second word**: on this
project's own engine it means *sower-hood*. So does کارگری, by the same three
bases.

### What could not be verified

- **Meaning, throughout.** V-014, V-024, V-025 and V-033 carry no semantic tag
  and `meaning_fa` is null on every form. Whether شایایی reads as *امکان* to a
  Persian ear is your judgement and not the engine's.
- **Modern usage.** The corpus is classical, so a zero means the poets did not
  write it and nothing more — S33. Whether an accepted سره term for actuality
  already exists was not established.
- **No corpus line was read.** We know کردمان occurs 4 times and not what any
  of the four writers meant by it.
- **Syllable counts were made by reading aloud.** The project has no
  syllabifier.

---

## L32. Windtelefon — the wind phone, and a compound the engine builds forward

Asked for by the project lead on 2026-08-29. Same protocol; nothing in the
code or rules changed. Figures from corpus v11 and `lexicon-20260808`.

**The thing being named.** The *kaze no denwa* of Ōtsuchi: a disconnected
telephone in a garden booth where mourners speak to their dead, the wind
carrying the words. German *Windtelefon*, Japanese «the wind's telephone».
Persian media already call it **تلفن باد** (fa.wikipedia has the article under
that title) — a half-loan, تلفن being French.

**What the word must carry**: the wind as bearer, and the act of speaking to
one who cannot answer. It is not a technology term; the obliqueness is the
point in every language that has named it.

### The recommendation: بادگو — *bādgu*

**The engine builds it, forward, by the same rule that builds سخنگو:**

```
/compound?word=باد&partner=گفتن   →   بادگو (bādgu)   V-078, V-079
```

باد is اسم ذات → nām (one reading, 65 one-step forms), so the slot rules
take it without any ruling. **بادگو is 0 in 25,497,189 words, and neither
بادگو nor بادگوی is a lexicon headword.** The slot is empty.

The shape has a modern device-precedent: **بلندگو** for loudspeaker — noun +
گو naming an instrument, not a person. (Outside the corpus, S33: بلندگو is 0
in the classical corpus, as expected of a modern word.)

**S32 stated plainly**: `/explain?word=Bādgu` returns `rebuilt: false`,
because nothing reverses a compound. The verification here is the forward
build only — the same standing limitation the third Dasein run reported.

### The wind-as-messenger reading is massively native, and we read the verses

| | documents |
|---|---|
| باد صبا | **1,231** |
| پیک صبا | 46 |
| شاد باد | 119 |

And the exact concept — the wind carrying words to the unreachable — is in
the corpus in so many words: in ادیب صابر the morning wind carries the poet's
message to the friend, and مهستی گنجوی (also مجد همگر) addresses the wind as
the bearer of a message.

The مهستی line carries **both readings of باد in one hemistich**: the wind
addressed as messenger, and the optative بادِ دعا — the same بادِ that Persian
says over the dead in «روانش شاد باد». The engine even builds **بادا** from
باد by N-032, the vocative rule (بانگا's rule): *O wind* — which is also the
بادا of «هرچه بادا باد». A resonance, not an argument; recorded because it is
pretty and true.

### The cost, and it is a real branch

**باد compounds have a futility/vanity branch, documented in your own
entries**: بادپیما «مردمِ مفلس... بی‌فایده‌گوی و **دروغ‌گوی**» (13 documents),
بادسر «متکبر», باد در سر «غرور», بادبدست «مفلس». So بادگو *can* be heard as
«حرفِ باد زن» — an idle talker. Against it: the messenger branch above
outweighs it in the corpus by orders of magnitude, and the سخنگو/بلندگو
pattern pulls the reading toward the device. Your call whether the risk is
tolerable.

### Rejected, with reasons

| candidate | why |
|---|---|
| **بادگاه** | occupied, fatally: your entry reads «**بیت‌الخلا** و طهارت‌جای». Recorded so nobody proposes it again. |
| بادنامه | letter, not speech; and `rebuilt: false` (L28) |
| بادپیام | پیام is not even a headword; پیغام is اسم معنی → blocked; and L28 |
| بادرسان | builds (V-078) and is free, but names the *wind*, not the device |
| **بادکده** | builds (N-062, one account), 0 in corpus, and lovely for the *booth* — «house of the wind» — but drops the speaking, which is the working half of the concept. Offered as the word for the booth if you want a pair: بادگو the phone, بادکده the hut. |

**What we did meanwhile**: nothing. تلفن باد remains the standing Persian;
بادگو is the سره candidate, yours to accept or throw out.

---

## L33. جوهر، علت، معلول — a word Persian lent and can take back, and a pair the engine builds off one verb

Asked for by the project lead on 2026-09-05: pure-Persian renderings of the
three metaphysical terms, in **فارسی سره**. Same protocol as L31 and L32 —
propose, verify every proposal through `/explain` or `/compound`, count in the
corpus, **read the lines**, then check outside the corpus. Nothing in the code
or the rules changed. Every figure is corpus v11 (25,497,189 words) and
snapshot `lexicon-20260808`.

### The recommendation

| | now | candidate | reading | rules | corpus |
|---|---|---|---|---|---|
| **جوهر** | substance, οὐσία | **گوهر** | *Gavhar* | a headword — nothing to build | **11,466 / 8,236 / 210** |
| جوهری | substantial | **گوهرین** (or گوهری) | *gavharin* | N-100 ← گوهر | 45 / 42 / 20 |
| **علت** | cause, αἰτία | **انگیزنده** | *angizande* | V-022 ← انگیختن | 3 / 3 / 3 |
| **معلول** | effect, the caused | **انگیخته** | *angixte* | V-008 ← انگیختن | 371 / 232 / 93 |
| علیت | causality | انگیزندگی | *Angizandegi* | V-022 + V-023 ← انگیختن | 0 |
| علت, as *the reason why* | | **چرایی** | *Čerāyi* | **cannot be built — چرا is not a headword** (B7) | 297 / 221 / 68, of which the noun is 22 lines |

Two kinds of answer, to be judged differently. **گوهر is L30's case:
Persian already has the word, so we report it and coin nothing.** انگیزنده /
انگیخته is L31's case: a concept with a native verb, coined off the verb, and
the engine builds every member of the family today. چرایی is a third thing —
an established word for one sense of علت that the engine cannot reach.

### جوهر — Arabic borrowed it from Persian, and Persian can have it back

**جوهر is Middle Persian گوهر.** *gōhr* is glossed «substance, essence,
nature; jewel; stock, lineage» (MacKenzie), Arabic *jawhar* is the loan from
it, and your own dictionary says so: «معرب گوهرِ فارسی», and under گوهر «از
gohr پهلوی، به معنای سرشت و نهاد یا طبیعت». The philosophical sense was in
the Persian word **before** Arabic took it; the loan carried both senses
across. So this is not a coinage but a loan-return: the Arabic term is the
Persian word in Arabic dress.

**Avicenna made this choice before us.** A secondary source reports that the
دانشنامهٔ علایی — the first Persian rendering of the Arabic philosophical
vocabulary — writes گوهر for جوهر; and the same work's «ایستاده به خود» for
قائم به ذات is documented separately, which is the definition of a substance.
We have not read the passage itself; it is listed below among the unverified.

**The corpus.** گوهر: **11,466 occurrences, 8,236 documents, 210 authors**,
11th–20th century — the largest attestation in any run so far, above هستی's
8,710. جوهر: 4,526 / 2,692 / 168. And the poets use گوهر in exactly the sense
wanted — read, not counted:

- فردوسی and قطران: **چار گوهر** / **چهار گوهر**, the four elements — the
  physical substances a body is made of.
- رودکی, Dehkhoda's own citation: **گوهر اصل** beside گوهر تن.
- مسعود سعد: a ذات that is a **گوهر**.
- عطار, both words in one couplet in one sense: **جوهر عشق** and **گوهر
  عشق**.

**Where the poets kept the Arabic: the technical compound.** جوهر فرد, the
atom, is **35 lines** (حافظ among them, and جامی beside جزو لایتجزی) against
گوهر فرد **3**, and those three are ornaments. The loan-return is free in the
general sense and has to be made deliberately in the term of art.

**The engine.** گوهر is اسم ذات → nām, one reading in two spellings (*Gavhar*
/ *Govhar*, both carried), **130 one-step forms**. For جوهری: **گوهرین**
rebuilds by N-100 — the *made-of* adjective of سیمین and زرین — 45
occurrences, 12th–15th; **گوهری** rebuilds by N-095 and is 1,060, but گوهری
is also *the jeweller*, which is why گوهرین is first. گوهرمند (N-071) and
گوهرگی (N-092) rebuild and are 0.

**The cost, stated:** گوهر's first sense is the pearl and will stay so. But
that was equally true of *gōhr*, and it is true of Arabic *jawhar*, which is
also a jewel. The polysemy is the word's, not the proposal's.

### علت and معلول — off one verb, as the Arabic is off one root

**The Arabic pair is one root twice** — علّة and معلول, the cause and the
*caused*. L31's rule says coin off the verb, and here the verb also settles
the pairing: a Persian cause and effect should be the two participles of one
کارواژه, as فاعل / مفعول are.

**The verb is انگیختن** — *to rouse into being, bring about*. Your dictionary
already holds the noun: **انگیزه** «سبب و باعث چیزها... موجب. **علت**», and
**انگیز** «آنچه باعث انگیزش و تحریک باشد. محرک» — 646 occurrences by 137
authors, the classical form; انگیزه itself is 17 occurrences, **all twentieth
century**. فرهنگ فارسی lists انگیزه first among the Persian equivalents of
علت, and the encyclopaedia article on علیت glosses the final cause as
«انگیزهٔ فاعل».

**The engine builds the whole family, and every member rebuilds:**

| | reading | `/explain` | rules | corpus |
|---|---|---|---|---|
| **انگیزنده** — علت | *angizande* | **true**, 2 | V-022 ← انگیختن (and ← انگیزیدن) | 3 / 3 / 3 |
| **انگیخته** — معلول | *angixte* | **true**, 1 | V-008 ← انگیختن | 371 / 232 / 93 |
| برانگیخته | *barangixte* | true, 2 | V-009 + N-003; V-005 + V-053 + V-008 | 96 / 91 / 54 |
| انگیزندگی — علیت | *Angizandegi* | true, 4 | V-022 + V-023 ← انگیختن | 0 |
| انگیزه | *Angize* | true, 4 | V-034 / V-035 ← انگیختن, ← انگیزیدن | 17 / 17 / 12 |
| انگیزش | *Angizeš* | true, 2 | V-033 | 14 / 14 / 13 |

**The lines were read.** انگیزنده's one line in the passages is مولانا's,
where every atom is a rouser. انگیخته's 371 are the participle of *stir up* —
a wave, a tumult, a passion stirred up, in فردوسی, مولانا and صائب. That is the
cost and the argument at once: the pair says *the
rouser and the roused*, a live metaphor rather than a dead technical term;
and انگیزه has narrowed in modern Persian to *motive*, so انگیزنده will be
heard first as *what motivates* and only second as *what causes*.

### چرایی — the word for *the why*, and it is older than we thought

Aristotle's αἰτία is the answer to διὰ τί, *on account of what*; the four
causes are four ways of answering *why*. Persian has the noun for that:
**چرایی**, فرهنگ عمید «**علت، دلیل، سبب**», and فرهنگ فارسی lists it among
the equivalents of علت.

**The count lies and the lines correct it.** 297 occurrences, 221 documents,
68 authors — but **221 of the 243 lines are «چرا + یی», *why are you***, in
فردوسی and مولانا among others. **22 lines are the noun**, nearly all in the
fixed pair چون و چرایی, *the how and the why*:

- فردوسی, the cleanest: **چرایی و چون** as the object of a question that
  reason answers.
- عطار, beside the Arabic word itself: **بی علت** next to **چون و چرایی**.
- انوری: **علت** next to **چونی و چرایی**.
- سنایی، عراقی، جامی، اهلی، بیدل and others, 12th–19th century.

So چرایی is classical, nominal, and sits next to علت in the poets' own
lines. **What it is not**: a term for the efficient cause. Its home is the
reason-question — *why is this so* — which is one of علت's senses, the one
modern Persian already gives it. And **it has no partner**: nothing on چرا
names the effect.

**The engine cannot build it, and the reason is a gap upstream.**
`/explain?word=Čerāyi` is `rebuilt: false` and `/generate?word=چرا` is 404:
**چرا is not a headword** in the snapshot, with **14,869 occurrences in 9,897
documents by 228 authors** — the third most frequent word in this run. B7 in
UPSTREAM. Even entered, it would come in as a چون‌واژه, and N-097 makes a
برنام from that, not a کارنام; so چرایی-the-noun needs a ruling on its class
as well as an entry.

### شوند — Kasravi's word, and why it is not offered yet

**شوند** is in your dictionary: «باعث و سبب و مادهٔ هر چیز. ج، شَوَنْدان.
رجوع به شَوه شود» — sources **برهان، انجمن‌آرا، آنندراج, and no verse**. That
is the profile L31 taught us to check: the three dictionaries that carried
the دساتیر, a gloss that lands on a philosophical term, and no citation.
Nothing found marks it ساختگی, and Pourdavoud's essay does not name it; but
nothing found vouches for it either.

**The corpus has the string 2,940 times and the noun never**: every line is
the verb *they become*; «به شوند», «شوندان» and «شوند آن» are 0 lines each.
Its twin شَوه is 4 lines by one author.

**Its case rests on morphology and on one modern writer.** شو + ـند is the
shape of روند، پیوند، گزند، خورند — a real Persian formation — and Kasravi
revived it as شَوَند in زبان پاک, where it means *cause, reason*; فرهنگ
فارسی lists it. **And the engine cannot build it**, because the rule document
has no [کاربن دو + ـند] rule — that is L34. Until you rule on L34, شوند is a
word you would have to hand us, not one the engine can derive; and it is a
homograph of one of the commonest verb forms in the language.

### Rejected, with reasons

| candidate | for | why |
|---|---|---|
| مایه | جوهر | Pahlavi ماتک «جوهر، مادهٔ اولی» in your own entry — the *materia*, not the substance; and occupied four times over (yeast, capital, the she-camel, the month of May). A headword: nothing to build. |
| بن و بر | علت و معلول | the folk pair, *root and fruit*; the encyclopaedia article on علیت records it. بن is a headword («بنیاد. پایه. اصل») but **بر is not**, the pair cannot be checked as a phrase in the corpus, and بن is this project's own word for a stem. |
| پیامد | معلول | 1 occurrence; `rebuilt: false`; `/compound?word=پی&partner=آمدن` returns **0 rows for both readings** — پی is اسم معنی, so L26 blocks it. The Farhangestān's word for *consequence* is پیایند. |
| برآیند | معلول | modern *resultant*; the 75 corpus hits (12th–17th) are the verb; `rebuilt: false` — the same missing ـند rule as شوند (L34). |
| زاینده / زاده | علت / معلول | both rebuild (V-022, V-008) and are well attested (102; 1,908) — and every line read is a mother and a child. The metaphor is Neoplatonic and Persian would hear it literally. |
| شده، کننده، کرده | معلول / علت | rebuild, and mean nothing in particular: 19,660, 620, 26,725. |
| بهانه | علت | Pahlavi وهان, *cause* — your entry says so — and the sense is dead: *pretext*, 1,339 occurrences all in that sense. |
| گوهری | جوهری | rebuilds (N-095) and is 1,060 — but it is *the jeweller* first. Second choice after گوهرین. |

### Evidence

`/explain` at depth 3; corpus as occurrences / documents / authors. **The
Behnevis case is part of the query**: a برنام or کاربهر is lowercase and a
نام or کارنام capitalised, so `Konande` and `angizandegi` return `rebuilt:
false` while `konande` and `Angizandegi` rebuild. An early pass of this run
recorded four *-ande* words as unbuildable on that mistake alone.

| candidate | Behnevis | rebuilt | rules | corpus |
|---|---|---|---|---|
| **گوهر** | Gavhar | headword | — | **11,466 / 8,236 / 210** |
| **گوهرین** | gavharin | **true**, 1 | N-100 ← گوهر | 45 / 42 / 20 |
| گوهری | Gavhari | true, 1 | N-095 ← گوهر | 1,060 / 952 / 156 |
| گوهرمند | gavharmand | true, 1 | N-071 | 0 |
| گوهرگی | gavhargi | true, 1 | N-092 | 0 |
| **انگیزنده** | angizande | **true**, 2 | V-022 ← انگیختن، انگیزیدن | 3 / 3 / 3 |
| **انگیخته** | angixte | **true**, 1 | V-008 ← انگیختن | 371 / 232 / 93 |
| برانگیخته | barangixte | true, 2 | V-009 + N-003; V-005 + V-053 + V-008 | 96 / 91 / 54 |
| انگیزندگی | Angizandegi | true, 4 | V-022 + V-023 | 0 |
| انگیزه | Angize | true, 4 | V-034, V-035 | 17 / 17 / 12, 20th only |
| انگیز | Angiz | headword | V-049 | 646 / 593 / 137 |
| **چرایی** | Čerāyi | **false** — چرا absent | — | 297 / 221 / 68; the noun 22 lines |
| شوند | Šavand | **false** — no ـند rule | — | 2,940, all the verb |
| پیامد | Peyāmad | false | compound: 0 rows | 1 |
| برآیند | Barāyand | false | — | 75, the verb |
| زاینده / زاده | zāyande / zāde | true / true | V-022 / V-008 ← زادن | 102 / 1,908 |
| جوهر | — | — | — | 4,526 / 2,692 / 168 |
| علت / معلول | — | — | — | 1,758 / 1,123 / 151; 230 / 134 / 49 |

### What could not be verified

- **Avicenna's گوهر.** That the دانشنامه writes گوهر for جوهر rests on one
  secondary source; the passage was not read. «ایستاده به خود» for قائم به
  ذات is from a second, independent one.
- **Meaning, throughout.** No rule in the family carries a semantic tag;
  whether انگیزنده reads as *cause* to a Persian ear is your judgement.
- **Modern usage beyond the dictionaries.** Heidari Malayeri's dictionary —
  the check that moved L31 — could not be reached this session. Whether a
  سره philosophy already uses a fixed pair for علت / معلول was not
  established.
- **شوند's provenance.** Not found in any list of دساتیر words; not found
  vouched for either.
- **Phrase counts with «و».** «چون و چرا» and «بن و بر» cannot be counted as
  phrases on the passages index — a phrase containing و returns either 0 or
  the bare word's count — so the 22 noun lines of چرایی were found by pulling
  all 243 and reading them, not by a query.

### The questions, and they are yours

1. **Is a loan-return سره?** گوهر → جوهر → گوهر. If yes, جوهر is settled with
   no coinage; and say whether the technical compound follows (گوهر فرد for
   the atom).
2. **گوهرین or گوهری for جوهری?**
3. **انگیزنده / انگیخته as the pair** — or a pair on a different verb? The
   engine will build any you name; every candidate off a مصدر rebuilds.
4. **چرایی**: accept it for the reason-sense of علت, or keep علت one word?
   And should چرا enter the lexicon, and as what class?
5. **L34** decides شوند and برآیند.

**What we did meanwhile**: nothing in code or rules. The three words stand as
they were.

---

## L34. A suffix the document does not have: [کاربن دو + ـند]

Found in L33: شوند and برآیند cannot be built because **no rule in the pack
puts ـند on a present stem**, while روند، پیوند، گزند، خورند are ordinary
Persian words of exactly that shape.

**Measured** on `lexicon-20260808`: **759 headwords end in ـند**; for **58** of
them the string in front is the present stem of some verb in the snapshot.
Read by hand, most are coincidence (سمند، کمند، پرند). The ones that are the
pattern:

| headword | stem | verb | your gloss |
|---|---|---|---|
| شوند | شو | شدن | «باعث و سبب» |
| خورند | خور | خوردن | «درخور. سزاوار» |
| مانند | مان | ماندن | «مثل و شبیه» |
| تنند | تن | تنیدن | «عنکبوت» — *the spinner* |
| کنند | کن | کندن | «افزاری که... بدان زمین کنند» — *the digger* |
| بساوند | بساو | بساویدن | «قافیهٔ شعر» — *the touching* |
| دوسند | دوس | دوسیدن | «التصاق و چسبندگی» |
| پیچند | پیچ | پیچیدن | «پیشانی‌بند» |
| پیوند، گزند | پیو، گز | پیوستن، گزیدن | headwords; گزند is Pahlavi *wizand*, your entry says |

روند is not a headword at all. So the suffix is real, old, and small.

**The question:** is [کاربن دو + ـند] a rule — live enough that شوند and
برآیند count as derivations — or a closed list of inherited words? If a
rule, it needs a row: input کاربن دو, output نام or کارنام, examples روند،
پیوند، گزند، خورند. If a closed list, شوند is a dictionary word to be judged
on its own, and the engine is right to refuse it.

**What we did meanwhile**: nothing. No rule was added; L33 reports شوند as
unbuildable rather than building it on a rule you have not written.

### L33, addendum (2026-09-05, later) — the definitions read, and the candidates they yield

The project lead's note: his own rendering comes from Aristotle's definitions,
which the app cannot reach. So the definitions were read — Categories 5;
Metaphysics Δ.2, Δ.8, Z.1–3; Physics II.3; Posterior Analytics I.2, II.11,
II.16–17 (Ross / Hardie–Gaye / Mure translations, MIT) — and candidates were
derived from **what the definitions say** rather than from the Arabic terms.
Then the same protocol.

**What the definitions say.** Categories 5: primary substance is «that which
is neither predicable of a subject nor present in a subject; for instance,
the individual man or horse»; it is «individual», «has no contrary», «does not
admit of variation of degree», and «while remaining numerically one and the
same, is capable of admitting contrary qualities». Metaphysics Δ.8: «substance
has two senses, (A) ultimate substratum, which is no longer predicated of
anything else, and (B) that which, being a "this", is also separable — the
shape or form of each thing»; Z.3: the substratum is «that of which
everything else is predicated, while it is itself not predicated of anything
else». Physics II.3 / Δ.2: «cause» is (1) «that out of which a thing comes to
be and which persists» — the bronze of the statue; (2) «the form or the
archetype, i.e. the statement of the essence» — 2:1 for the octave; (3) «the
primary source of the change or coming to rest» — the adviser, the father,
«the maker a cause of the thing made and the change-producing of the
changing»; (4) «the end or "that for the sake of which"» — health of walking;
and «men do not think they know a thing till they have grasped the "why" of
it». Posterior Analytics II.16: the correlate of αἴτιον is **τὸ αἰτιατόν, «the
thing caused»** — a passive verbal adjective, which is what Arabic معلول
copies. Etymology: οὐσία = οὖσα (the participle *being*) + ‑ία, «beingness»,
calqued by Latin *essentia*; *substantia* is the calque of ὑπόστασις, «what
stands under»; αἰτία ← αἴτιος «responsible, culpable» — the cause is what is
answerable for a thing.

**What the definitions yield, through the engine.**

| candidate | for | carries | `/explain` | rules | corpus |
|---|---|---|---|---|---|
| **زیرایستا** *ziristā* | جوهر as substratum | Δ.8 (A) / Z.3 — *what stands under*; the shape of *substantia* | **true**, 2 | V-076 zir- + ایستادن; V-024 ‑ā | 0 |
| زیرایست *Zirist* | the same, as کارنام | | true, 1 | V-076 + V-049 | 0 |
| **باشنده** *bāšande* | جوهر as οὐσία's own calque | οὖσα → باشنده | true (V-022 ← باشیدن; two spurious parses) | V-022 | 8 / 8 / 4, 13th — in مولانا: *dweller* |
| هستی | the exact calque of οὐσία | | `Hasti` false; not a headword | — | 8,710 — Persian's *Sein*, occupied |
| **جنباننده** *jonbānande* | علت, the efficient cause | Physics II.3 (3), verbatim: «the change-producing of the changing» — the mover | **true**, 2 | V-022 ← جنباندن | **41 / 17 / 4**, 13th — مولانا pairs جنباننده with جنبنده: Physics VIII's argument, in Persian |
| **جنبانده** *jonbānde* | معلول, the moved | αἰτιατόν's shape: the passive participle | **true**, 1 | V-008 ← جنباندن | 3 / 3 / 3 |
| جنبیده *jonbide* | the same | | true, 2 | V-008 ← جنبیدن | 17 / 15 / 12 |
| جنبنده *jonbande* | the moving thing (مولانا's partner word) | | true | V-022 ← جنبیدن | 81 / 74 / 34 — **occupied**: a creature (جنبندگان) |
| جنبانندگی | علیت as *moving* | | true, 3 | V-022 + V-023 | 0 |
| چرایی | علت as «the why» | Physics II.3's opening | false — چرا absent | — | (L33 above) |
| زیرنهاد | ὑποκείμενον's calque | | **false** — نهاد is اسم معنی | L26 | 0 |
| آغازگاه | «whence the change first begins» | | **false** — آغاز is اسم معنی | L26 | 0 |
| پدیدآورنده | «the maker of the thing made» | | compound: **0 rows** — پدید is a برنام | L26 | 2 |
| خودایستا | Categories: «not in a subject» | | false — no compound route | | 0 |

**Two things this route shows, and both are worth having.** First, the
definitions reach one sense of each term and not the others: *what stands
under* but not *a this that is separable*; *the mover* but not matter, form
or end. That is exactly why the tradition chose non-definitional words —
*jawhar*, *ʿilla* — and it is the argument for keeping the lexical route
(گوهر; انگیزنده / انگیخته) first and offering these beside it. Second, the
Greek word for the effect is itself a passive participle, so the shape L33
recommends for the pair is not a Persian expedient but the shape of the
original. **And the same wall as before**: four definition-derived candidates
(زیرنهاد، آغازگاه، پدیدآورنده، خودایستا) die on L26 or the compound gap, not
on the rules.

**What we did meanwhile**: nothing. The page for the project lead carries the
section «از تعریف ارسطو» with the same table.
