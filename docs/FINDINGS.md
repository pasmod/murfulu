# Findings

Running record of what we have established. Newest session at the top.
Each entry: what we looked at, what we found, what it means for Murfulu.

---

## 2026-09-05 (session 25) — جوهر، علت، معلول: a loan that can return, and the case in a Behnevis query

Three terms through the protocol in one session, run by hand rather than by
agents. Candidates and evidence in
[L33](FOR_THE_LINGUIST.md#l33-جوهر-علت-معلول--a-word-persian-lent-and-can-take-back-and-a-pair-the-engine-builds-off-one-verb);
a rule gap in [L34](FOR_THE_LINGUIST.md#l34-a-suffix-the-document-does-not-have-کاربن-دو--ـند).
Six things for the record.

**جوهر is the first term whose answer is a loan-return.** Arabic *jawhar* is
Middle Persian *gōhr* «substance, essence, nature; jewel»; Dehkhoda writes
«معرب گوهرِ فارسی». So L30's rule fires — Persian has the word — with a
twist: the good word is the Arabic term itself in its native dress. Measured:
گوهر **11,466 / 8,236 / 210** against جوهر 4,526 / 2,692 / 168, and عطار uses
both in one couplet in one sense (جوهر عشق beside گوهر عشق). The poets kept the
Arabic in the technical compound: جوهر فرد 35 lines, گوهر فرد 3. Worth having
as a method: **before coining for an Arabic term, ask whether the Arabic is
Persian.**

**Coin off the verb worked a second time, and this time it gave a pair.**
انگیختن yields انگیزنده، انگیخته، برانگیخته، انگیزندگی، انگیزه، انگیزش, and
every one returns `rebuilt: true`. The point beyond L31: two terms that the
Arabic builds on one root (علّة / معلول) come out as the two participles of
one کارواژه — the فاعل / مفعول shape — and need no second decision.

**The count lied about چرایی, and reading 243 lines corrected it.** 297
occurrences; **221 of 243 lines are «چرا + یی», *why are you***; 22 are the
noun, nearly all in the pair چون و چرایی, and a فردوسی line that pairs چرایی
with چون is the cleanest. Session 23's rule again — and this time the reading
had to be done by pulling every line and grepping, because a phrase with «و»
in it cannot be searched on the `passages` index: «چون و چرایی» returns the
same 243 lines as «چرایی», and «چون و چرا» returns 0. Not diagnosed; the
session-23 lookups were `match_phrase` on `documents.text_fa`, and this one
used `passages.text`.

**شوند has the دساتیر profile without the دساتیر label.** Dehkhoda's entry
rests on برهان، انجمن‌آرا، آنندراج with no verse; the corpus has the string
2,940 times and the noun 0 times («به شوند», «شوندان»: 0); Kasravi revived it
in زبان پاک. And the engine cannot build it because the rule pack has no
[کاربن دو + ـند] rule, although روند، پیوند، گزند، خورند are that shape — 759
headwords end in ـند, 58 with a present stem in front, about ten of them
genuine. L34.

**The Behnevis case is part of an `/explain` query, and a run can trip on
it.** `Konande` is `rebuilt: false` and `konande` is true; `angizandegi`
false, `Angizandegi` true. A برنام or کاربهر is lowercase, a نام or کارنام
capitalised, and the reverse parse honours that. The first pass of this run
recorded angizande، konande، zāyande، šavande as unbuildable on that mistake;
the second pass, lowercase, rebuilt all four. Not a fault — the case is the
word class — but it belongs in the protocol's verification step, and it is
now in DECISIONS.

**Two lexicon gaps surfaced, both function words.** چرا — **14,869
occurrences, 9,897 documents, 228 authors** — is not a headword, so چرایی
cannot be built; neither is بر (the fruit) nor چون. B7. And پی is اسم معنی, so
`/compound?word=پی&partner=آمدن` returns 0 rows for both readings — L26
blocks پیامد exactly as it blocked دادبوم.

**Later the same day: the definitions were read, and they yield two engine-built pairs.** The project lead's own rendering comes from Aristotle's definitions, so Categories 5, Metaphysics Δ.2/Δ.8/Z.1–3, Physics II.3 and Posterior Analytics I.2/II.11/II.16–17 were read and candidates derived from the wording. The engine builds **زیرایستا** (V-076 + V-024 — the shape of *substantia*, «what stands under», Δ.8's first sense) and the pair **جنباننده / جنبانده** (V-022 / V-008 on جنباندن — Physics II.3's «the change-producing of the changing»), and the corpus has مولانا stating Physics VIII's argument with the very word, جنباننده beside جنبنده (41 / 17 / 4). Posterior Analytics II.16 also settles a method point: Greek's word for the effect, τὸ αἰτιατόν, is a passive participle, so the participle pair L33 recommends is the original's own shape, which Arabic معلول copied. **The definitions reach one sense per term** — substratum, mover — and four further candidates (زیرنهاد، آغازگاه، پدیدآورنده، خودایستا) died on L26 or the compound gap. Addendum in L33.

**Nothing was changed.**

---

## 2026-08-29 (session 24) — Windtelefon, and the first compound coined through the slot route

One word through the protocol: German *Windtelefon*, the Ōtsuchi wind phone.
Candidates in [L32](FOR_THE_LINGUIST.md#l32-windtelefon--the-wind-phone-and-a-compound-the-engine-builds-forward). Three things for the record.

**The recommendation is the first candidate in five runs built by the slot
rules.** بادگو comes out of `/compound?word=باد&partner=گفتن` under V-078/V-079
— the سخنگو rule — with no ruling needed: باد is اسم ذات → nām. Every previous
run's winner was an affix derivation (بانگا, شایش, بایش, ورزیدمان) or blocked
(دادبوم, L28). The slot route works when the front is a concrete noun; S32
still means the result cannot be independently re-parsed, and that is stated
in L32 rather than glossed over.

**بادگاه is a toilet.** Dehkhoda: «بیت‌الخلا و طهارت‌جای». The obvious
place-word for anything wind-related is dead, and it is exactly the kind of
thing a coining run proposes first. Recorded so it is never proposed again.

**The wind-as-messenger motif was measured, then read.** باد صبا in 1,231
documents, پیک صبا in 46 — and the verses carry the wind phone's exact
semantics: in ادیب صابر the morning wind carries a message to the friend, and
in a hemistich of مهستی گنجوی باد is at once the addressed wind and the
optative of blessing — the same بادِ دعا Persian says over the dead
(شاد باد: 119 documents). Per the session-23 rule, the lines were read, not
counted: the futility branch (بادپیما «بی‌فایده‌گوی و دروغ‌گوی», 13 documents)
was weighed against the messenger branch and the costs written down.

**Nothing was changed.**

---

## 2026-08-25 (session 23) — coin off the verb, and the forgeries a سره run walks into

Three agents, one each on **امکان، ضرورت، واقعیت**, in pure Persian. Candidates
and evidence in
[L31](FOR_THE_LINGUIST.md#l31-امکان-ضرورت-واقعیت--three-terms-and-the-first-set-the-engine-can-build).
Four things belong here, and the first changes how the next run should be
started.

### The first term set the engine builds — because it went in through a verb

**شایایی، بایایی، ناشایایی، کردمان all return `rebuilt: true`.** دادبوم could
not be built and مردم‌سالاری could not be built; these can, with no ruling on
L26 or L28 needed.

The reason is one line long. **L26 is a rule about what a noun is, and a مصدر
is neither a nām nor a kārnām**, so the V-rules take it without asking:

| base | filed | forms at one step |
|---|---|---|
| کار | اسم معنی → kārnām | **1** |
| توان | اسم معنی → kārnām | **2** |
| یارا | اسم معنی → kārnām | **1** |
| **شایستن / بایستن / کردن** | **مصدر** | **38 each** |

**So the method is: where a concept has a native verb, coin off the verb.**
The two previous runs failed because they reached for nouns — داد and مردم —
and نه because the engine lacks the machinery. This is worth having before the
next term is asked for.

### The tail-count method is right for compounds and wrong for derivations

L27, L29 and L30 all decided on tail counts. **That reasoning is sound for a
compound tail and unsound for a derivational one**, and the measurement is
flat:

| | a lexicon headword? |
|---|---|
| زندگی، دانش، کوشش، بینش، آفرینش، خستگی، رانندگی، کردار، هستی، کارگر | **none of them** |
| گفتمان، سازمان، زایمان | **none of them** |
| مرزبوم، سپهسالار، ساختمان، گلبن | **all of them** |

**karbon headwords compounds and does not headword regular deverbal
derivations.** دانش alone has 4,488 corpus occurrences and no entry. So a zero
on ـستگی, ـندگی or ـایی measures Dehkhoda's editorial policy, not Persian.

**L29's ـبوم and L30's ـسالار arguments are untouched** — both are compound
tails, and the entries counted there are real compounds. But the third run
would have reached the wrong answer by applying the method mechanically, and
the distinction is now written down.

### A سره run walks into eighteenth-century forgeries constantly

**132 lexicon entries mention دساتیر and 52 mention آذرکیوان.** Three separate
candidates in this session were killed by it, and each looked excellent first:

- **ناور** — صفت, «به معنی ممکن باشد که **برابر واجب** است», with **ناوران**
  for ممکنات: the exact modal pairing the امکان run wanted, 8 occurrences by 7
  authors. Both entries end «از لغات **ساختگی** دساتیر است».
- **کنشمندی** — rebuilds by one rule from کنشمند, glossed «خداوند کردار و
  **صاحب عمل**… یعنی کننده و فاعل», which is *being-in-act* almost word for
  word. «و این لغت **از دساتیر** است», and its synonym کنور is «از
  **برساخته‌های فرقهٔ آذرکیوان**».

The pattern to keep: **a gloss that lands exactly on a European philosophical
term is a reason to check the entry's provenance, not a reason to celebrate.**
The Dasātir was written to supply Persian with the vocabulary its authors
thought it should have had, which is the same thing a coining run does — so it
produces exactly the words a coining run is hoping to find.

### We could read the verses all along, and reading them changed the answer

Four coining runs have reported counts and each said, in its own words, that
it could not read a line of the corpus. **That was a fact about the runs and
not about the system.** The corpus is an Elasticsearch index named
`documents`; every record carries `text_fa` whole, and a `match_phrase` query
returns the verse with its author, title and century. `/search` queries
`word_types` and returns counts, which is what every run used.

Read at last, three lines moved the L31 recommendation:

**شایایی's only occurrence means *worthy*** — in بهار's «ای زن» it stands in
one row with **لایق**, and **درخور** follows in the next couplet. That is the
axiological sense the term was defined against.

**بایش's only real occurrence is a term of logic** — ادیب‌الممالک, glossing a
vocabulary in verse, sets **بایش against رانش as ایجاب against سلب**.

**بایا's only occurrence is a letter-riddle** — ابن یمین reverses its letters.
The word the recommendation rested on has no attested use.

So the ـش family was recommended over ـایی on the usage evidence, reversing
what the counts alone had suggested. **Two of عطار's three hits for بایش were
also false**, **با ایشان** matching as a phrase — which the counts could not
have shown either.

**The lesson is a method one and belongs in every future run:** a count says
how often a string appears and never what it meant. Where a candidate rests on
an attestation of one or two, the line must be read before the count is
quoted.

### A check outside the corpus moved the answer, and corrected one of our claims

A parallel run against modern Persian lexicography — the check S33 says every
candidate needs and the corpus cannot give — returned after the three agents
had reported. It changed one recommendation and corrected one assertion.

**ورزیدن, Greek ἔργον and German *wirken* are one Proto-Indo-European root,
\*werǵ-.** Persian ورز/ورزیدن ← Middle Persian *warz/warzīdan* ← Proto-Iranian
\*warj-; ἔργον ← \*wérǵom, whose cognate list names Avestan *varəzəm*; *wirken*
← Proto-Germanic \*wirkijaną. And ἐνέργεια is ἐν + ἔργον. **So a Persian term
for *Wirklichkeit* coined on ورز- repeats in Persian the move German made from
*wirken* — with the true Iranian cognate.** کردن cannot: کردن is *facere*,
where *wirken* is the verb Persian keeps separately as ورزیدن.

`/explain?word=Varzidmān` returns **`rebuilt: true`, one account, V-014 on
ورزیدن**, and it is 0 in the corpus with no lexicon entry — the same clean
shape as کردمان on the etymologically exact verb. Its cost is the
neighbourhood: **every ورز- headword in the lexicon is a farmer or an
athlete** — ورزکار «زارع. کشاورز», ورزگر «برزگر», ورزو the plough-ox — so on
its own tail it reads *the ploughing*. **ورزمان, the short form, was approved
by the Farhangestān in 1390 for ماساژ**, which is a candidate we had on the
list and would have offered.

**And there is already a rigorous pure-Persian system for these terms**:
Heidari Malayeri's astronomy dictionary has هسیا/هسیایی for real/reality (Old
Persian *hašya-*), **ژیروند/ژیروندی for actual/actuality**, توند/توندی for
potential/potentiality, and کاروژ for energy. L30's rule — where Persian has a
good word, report it rather than coin past it — applies. None of his stems is
in karbon: `/explain?word=Hasyāyi` returns `rebuilt: false`.

**The correction.** We asserted that Meister Eckhart coined *Wirklichkeit* to
render *actualitas*, itself Aristotle's ἐνέργεια. **Neither half is
established.** Pfeifer mentions neither Eckhart nor *actualitas*; Grimm gives
the Latin equivalents as *operatio, actus, efficacia, existentia* and names
nobody; the attribution is unfootnoted in German Wikipedia, and the one
scholarly source found hedges it himself. *Actualitas* is moreover not
Aristotelian — thirteenth-century theology, earliest in Albertus Magnus.
**What survives is the part the argument rests on**: Pfeifer has late Middle
High German *wirkelīcheit* meaning «Tätigkeit, Wirksamkeit, Aktivität», so
*Wirklichkeit* is built on *wirken* and first meant efficacy. Recorded because
it was asserted in this project's own docs before it was checked.

### کارایی means sower-hood, and that is the second word it has happened to

`/explain?word=Kārāyi` rebuilds under **9 accounts and every base is کشتن،
کاریدن، کاشتن** — *to sow*. کارگری does the same under 6. This is L27's
کارنده finding reproduced on two further words, and it is now three: the
engine cannot tell کار from کاشتن anywhere.

**Nothing was changed.** The two questions the set could not settle — ـایی
against ـش, and whether امتناع is ناشایایی or نابایایی — are on L31 for the
linguist.

---

## 2026-08-25 (session 22) — Demokratie, and a tail that says the opposite of its words

Second word through the coining protocol, straight after Rechtsstaat. The
candidates are in
[L30](FOR_THE_LINGUIST.md#l30-demokratie--the-persian-is-already-good-and-the-tail-under-it-says-the-opposite).
Three things are worth keeping here, and the first is a correction to how the
last session's result should be read.

### One wall, not two — and the difference is a lexicon category

`/explain?word=Mardomsālāri` returns `rebuilt: false`, exactly as every
Rechtsstaat candidate did. **The cause is not the same, and the distinction
matters for what to fix first.**

| | filed | one-step forms | walls between it and the word |
|---|---|---|---|
| داد | اسم معنی → kārnām | **1** | **L26 and L28** |
| **مردم** | **اسم ذات → nām** | **65** | **L28 only** |

Both halves of مردم‌سالار are already nām, so nothing about the category
mapping touches it. The only thing missing is the plain noun-plus-noun row:
N-104 puts its ā in and offers **مردماسالار**.

So **L28 alone would unlock Demokratie, and Rechtsstaat needs both rulings.**
Worth knowing when the two questions are put to the linguist, because they
have been carried as a pair since session 20 and they are not equally
expensive.

### Every ـسالار in the lexicon is «the chief of X», and the modern series reversed it

Counted over the 45,579 active entries: **ـسالار has 16 entries, 14 اسم مرکب**
— against ـشاهی 5, ـداری 3, and nothing at all on ـفرمانی، ـسروری، ـتوانی. The
tail is the right one. Its **relation** is the finding:

سپهسالار «سالار و رئیس لشکر»، دریاسالار «امیرالبحر»، ناوسالار «فرماندهٔ ناو»،
خوانسالار «رئیس میز پادشاهی»، گندسالار، سابقه‌سالار — and two where Dehkhoda
unpacks the compound in so many words: **بارسالار «سالار بار»** and
**نوبت‌سالار «سالار نوبت»**.

**All sixteen are the chief *of* the first noun, never the first noun ruling.**
Read by that rule مردم‌سالار is «سالار مردم» — a chief over the people, which
is what democracy is defined against.

**And the answer to it is the honest half of the finding.** The modern
ـسالاری words all reverse the relation — دیوان‌سالاری، شایسته‌سالاری،
نخبه‌سالاری، تک‌سالاری — and **not one of them is in the lexicon**. Modern
Persian gave the tail a new relation rather than misusing the old one, and
مردم‌سالاری is a member of that new series. Ruling against the reversal takes
the whole series down, not one word. Recorded on L30 with both sides visible.

### The engine built a candidate and the evidence killed it

`/explain?word=Mardomgāni` returns **`rebuilt: true`**, two accounts — N-067
(`-gāni`) and N-064 + N-095. It is the only candidate in the run the engine
derives with no ruling needed: the بانگا shape from L27, arrived at again.

**It was rejected, and on N-067's own example.** خدایگانی, the rule's worked
example, **is not a headword at all** — only خدایگان is, and karbon files that
as a **وام‌واژه**. The 16 entries ending in ـگانی are grape varieties and
tanned leather (کرنگانی، گوزگانی، کورگانی، کوزگانی، گوژگانی), coins, and six
compounds of زندگانی. **No word of government sits anywhere on that tail.**

This is the cleanest case the project has of a thing it keeps needing to say:
**the engine building a word is not the engine approving it.** S21 made that
point about meaning; this makes it about register. That N-067's example is not
a headword is a small separate fault, filed on L30.

**Two others were dropped on tails as well.** مردم‌شاهی — ـشاهی has 5 entries
and they are coins and a plant (چارشاهی، نیم‌شاهی، ارده‌شاهی، اورنگ‌شاهی).
مردم‌داری — occupied, a live word for affability, and in the corpus.

**Nothing was changed**, and the recommendation is to keep مردم‌سالاری. Unlike
Rechtsstaat this was never a gap; the work found a question under an existing
word rather than a missing one.

---

## 2026-08-24 (session 21) — Rechtsstaat, and the engine that builds its opposite

The project lead asked for Persian renderings of the German **Rechtsstaat**,
by the coining protocol: propose, then verify every proposal through the
running app. The candidates are in
[L29](FOR_THE_LINGUIST.md#l29-rechtsstaat--a-persian-word-for-it-and-the-two-rules-that-stop-us-building-one).
Three things the run established are worth keeping here.

### The engine derives *Unrechtsstaat* and refuses *Rechtsstaat*, on one mapping

```
/explain?word=Bidādstān   rebuilt: true   بیداد + -stān   N-057
/explain?word=Dādbum      rebuilt: false  no account
/explain?word=Dādšahr     rebuilt: false  no account
/explain?word=Dādkešvar   rebuilt: false  no account
```

**بیداد is filed اسم مرکب and داد is filed اسم معنی.** The first maps to a
nām, the second to a kārnām, and **80 active rules take a nām against the one
that takes a kārnām**. That
is the entire difference between the word for the lawless state, which builds,
and the word for the lawful one, which does not.

Measured on the base itself, with nothing else changed:

| داد classed as | one-step forms |
|---|---|
| kārnām, as karbon's category maps today | **1** — دادی |
| nām | **79** |

**The 79 are the vocabulary of the courts**: دادگاه، دادستان، دادگر، دادور،
دادبان، دادوند، دادمند، دادکده، دادگان. At depth 2 the same base gives 3,718
forms over 1,909 distinct spellings, among them دادمندی (N-071 + N-095) and
دادگری (N-063 + N-093). None of it is reachable from داد today.

This is **L26 seen on one word**, and it is the strongest instance of it we
have found: L26's own examples — دانشمند، امیدوار — are rules failing on their
illustrations, where this is a rule family failing on an entire register.

**The route was checked rather than assumed.** `/explain?word=Šahrvand`
returns `rebuilt: true` — شهروند, the modern word for *citizen*, is the
engine's own output from شهر by N-084 and N-105. The machinery works; the
category is what shuts it.

### The tails decide the head, and they decide against شهر

The obvious calque of *Rechtsstaat* is دادشهر — شهر in its Middle Persian
sense of *realm*, as in ایرانشهر. Counted over the 45,579 active entries, the
lexicon does not support it:

| tail | entries | what they are |
|---|---|---|
| ـستان | 249 | 159 اسم مرکب — the tail that names countries |
| **ـبوم** | **14** | 12 اسم مرکب, every one «[X]-land» |
| ـکشور | 4 | |
| **ـشهر** | **3** | کهنه‌شهر، هم‌شهر، بی‌شهر — all about the *city* |

**Dehkhoda glosses پاک‌بوم as «کشور پاک»** and مرزبوم as «سرحد مملکت», so a
ـبوم compound is read as a country in the dictionary's own words. In the
corpus the ـشهر compounds are town names — گلشهر، بوشهر، آبادشهر — while
ایرانشهر has 10 documents. So **دادبوم** is recommended over دادشهر, on the
project's own evidence rather than on taste.

### Persian already made the word once, and the modern language took it

karbon holds **two** readings of دادستان. The second is `Dādastān`, اسم مرکب,
glossed «مرکب از «داد» به معنی عدل و «ستان» از ادات اتصاف به مکان، یعنی محل
داد» — *the place of justice*, from the same two pieces, 14 occurrences by 9
authors in the 12th–13th centuries. Modern Persian then took دادستان for the
public prosecutor. Worth knowing before anybody proposes it again.

**One candidate was withdrawn on a check the corpus could not make.**
دادمندی was proposed for *Rechtsstaatlichkeit*; it is free in all 25,497,189
words, and it is nonetheless in use in modern Persian meaning عدالت. The
corpus is classical, so a coinage being free in it is not the same as the
coinage being free. Every candidate that survives should get the same second
check.

**Nothing was changed.** Both walls are existing questions — L26 for the
category, L28 for the plain noun-plus-noun compound — and the pack does not
invent rules.

---

## 2026-08-20 (session 20) — guyande, دانشمند, Golstānstān, and one long scroll

The project lead built four words on the engine — *guyande*, *Guyeš*,
*Dānāyi*, *āyande* — handed each straight back to the analysis screen, and got
*this word cannot be built* for all four. The forms are the engine's own
output. This is the *sāzāyi* rule broken at the one place it is supposed to
hold: **whatever is put together must come apart.**

### The glide table was never run backwards

Forward, `engine/glides.py` puts a *y* between two vowels that meet — گو + نده
= گوینده. Backwards, `engine/decompose.py` removed the affix **as a string**
and nothing else, so *guyande* minus *-ande* left *guy*, *āyande* minus
*-ande* left *āy*, *Dānāyi* minus *-i* left *dānāy*. None of those is in any
dictionary, none ever was, and the analysis stopped there.

The *row* → *rav* reversal worked all along, which is why the fault was
invisible: it comes from `stem_forms`, a different table, and the decomposer
had always reversed that one. The seventeen glide rules it had never touched.

### How much of the round trip was broken — measured

Every one-step form the engine builds with a glide in it, fed back to the
analysis:

| base | forms with a glide | not analysable, before |
|---|---|---|
| گفتن | 13 | 13 |
| آمدن | 6 | 6 |
| بودن | 13 | 13 |

Over a random sample of **300 of the snapshot's 44,788 readings** (seed 7,
`data/lexicon-20260808.sqlite`): **793 one-step forms carry a glide, and 455
of them — 57% — could not be taken apart.** After the fix, 0 of 793.

### The reversal comes from the table, not from a rule written in code

`glides.unapply` is `glides.apply` read backwards, off the same two shapes the
table already has: a result that spells the whole join (*uya* + *nde*) and one
that replaces the left vowel only (*av* + *eš*). It puts the rule's own left
vowel back and proposes the base. *Āyande* is the edge of it — the base is the
bare vowel **ā**, and nothing is left in front of it.

Nothing became less strict. A proposal is still only a guess until the word is
built forward again from a lexicon entry and reproduces the spelling exactly,
so no word that was refused before is accepted now for any reason other than
that the engine really can build it. *Mowlānā*, *Fanā* and *Zzzqi* are still
refused.

**Cost:** six analyses go from 0.40s to 0.61s. The decomposer offers more
proposals, and most of them die in the rebuild, which is what the rebuild is
for.

### The account now says where the letter came from

An analysis step carried `stem_form` and not `glide_id`, so the explain screen
would have shown «gu + -ande» with the *y* appearing from nowhere. The forward
path knows which glide fired; it is carried through to the screen, beside the
stem change and for the same reason.

### Four rules cannot build their own examples, and it is one word class

The project lead asked, later the same day, why *honarmand*, *omidvār*,
*dānešmand*, *Dānešgāh* and *soxangu* are all refused. They are, and it is one
cause: امید، هنر، سخن، کار are filed **اسم معنی**, which the source grammar's
prose makes a **kārnām**, and *-mand*, *-vār*, *-gāh*, *-var* and the slot
rules all declare their input as **nām**.

**The sharpest form of it is that the rules fail on their own examples.** N-071
carries *dānešmand*, N-068 carries *Dānešgāh*, N-074 carries *omidvār*, N-080
carries *dānešvar*, V-078 carries *soxanguy*. None of the five builds the word
it is illustrated by.

**And the engine contradicts itself inside one chain.** V-033 builds *Dāneš*
from دانستن and labels it a kārnām, so the engine makes دانش and then cannot
put *-mand* on it. Tested with nothing else changed: N-071 on *dāneš* as a nām
gives *dānešmand*; as a kārnām it is refused.

Measured on `lexicon-20260808`:

| | |
|---|---|
| active rules taking a nām | **80** |
| active rules taking a kārnām | **1** (N-098, the *-i*) |
| readings that are اسم معنی → kārnām | **1,949** |
| forms one of them builds at one step | median **1** |
| forms an اسم ذات → nām reading builds | median **65** |

**Fourteen of the 163 checked rule examples fail from this one mapping.**
Eleven are the checker's own "the base is held in another word class", and all
eleven are nām-wanted against اسم معنی-held. The other three — N-068, N-071,
N-080 — the checker files under *the base is not in the lexicon*, which is true
of دانش and **not the real reason**: the engine builds دانش itself, and the
form it builds is a kārnām. The checker only ever looks a base up; it does not
ask what the engine would call a base it built. Worth knowing before that
column is read as a diagnosis.

The words are ordinary Persian — امیدوار in 538 documents by 130 poets,
هنرمند 211 by 70, دانشمند 137 by 45, سخنگو 121 by 56 — and karbon holds all
four as صفت مرکب. The dictionary has the words; only the derivation is shut.

**Nothing was changed.** The mapping is grounded in the linguist's own prose,
so this went to him as [L26](FOR_THE_LINGUIST.md#l26-four-nominal-rules-cannot-build-their-own-examples) rather than into the rules —
the same restraint, and the same reason, as L18 in session 17. L18 is the
compounding half of one question; L26 is the affix half, and it is the half
with the stronger evidence.

### A suffix could be stacked on itself, and 1,830 spellings say it should not

The project lead built گل at depth two and read the list: **2,335 forms per
reading, and 35 of them put one suffix on twice** — *Golstānstān*,
*Golzārzār*, *Golčeče*, *Golbānbān*, *Golkadekade*, *Golāā*. درد gives the
same 35 shapes; گفتن gives *goftee* and *guyee*.

**The prefix half of this was settled on 2026-08-15 and the suffix half was
left out on purpose.** The module note said so: *suffixes are untouched —
andišidegi + -i is a real pattern*. That reasoning is about two **different**
suffixes, and nothing was checking the other case.

**Two shapes, and the second is why a rule-id guard would not have worked.**
Most are one rule twice — N-057 then N-057. But *Goliyi* is N-093 then N-095,
and *golvārvār* is N-074 then N-077: **different rules, one affix**. The prefix
guard already keyed on the affix for exactly this reason (V-059 and V-060 are
both *farāz-*), so the fix is the same guard widened rather than a new one.

**Measured before it was changed**, over 120 random readings at depth 2:

| | |
|---|---|
| forms built | 161,774 |
| forms adding one suffix twice | **2,725** (1.7%) |
| distinct spellings among them | **1,830** |
| of those in the corpus | **0** |

The zero was checked rather than assumed: گلستان (3,518 documents) and دردمند
(507) went through the same query as controls and both came back. After the
guard the same sample builds 159,183 forms and none of the 1,830.

**What it does not touch.** *Ravandegi* is *row* + *-ande* + *-gi* and is
untouched — two different suffixes still stack. A prefix and a suffix spelled
alike are still two affixes: *Nāgolnā* is N-022 in front and N-072 behind, and
it still builds, because whether ناگلنا is a word is a different question from
this one. Every rule example the engine could rebuild before still rebuilds —
the golden baseline is unchanged.

**Unconfirmed, and the narrow part is recorded.** The guard keys on the affix's
spelling, so the *-i* of nesbat followed by the *-i* that makes an abstract
noun is refused with everything else. That is the *andišidegiyi* case, it has
no corpus support, and the corpus is classical while the form is modern. It
stays question L.

### دستان is not داستان, and the real false friend is one letter away

Reported as a false analysis: *Dastān* accepted as *Dast* + *-ān*, read as دست
+ ان = **داستان**. It is not. The engine builds **دستان**, and the two are
different words with different Behnevis forms — `Dastān` is دستان, `Dāstān` is
داستان — each a headword of its own (دستان اسم ذات, داستان اسم معنی). دستان is
in 1,639 documents by 173 poets, and N-037 is the rule whose own examples are
بیابان and گیلان. Nothing was claimed that needs refusing.

**But the case the report describes is real, one letter over.** *Dāstān*
rebuilds as **دا + ستان** under N-057. دا is a headword and carries **111
documents by 25 poets** — an ordinary count, so the evidence line beside the
account (*«این پایه در ۱۱۱ سند آمده است»*) warns a reader of nothing. This is
the ناخداگاهی shape exactly, and it is why S21 renamed the flag to `rebuilt`
on 2026-08-17 rather than teaching the route to judge meaning.

**One of the refusals in the same report is an accident, not a judgement.**
*Bustān* is refused because the proposal بو is held as اسم معنی → kārnām and
N-057 wants a nām — the L26 fault, not a decision about the word. Tested: N-057
on *Bu* as a nām gives **بوستان**. So if L26 is ruled the way its evidence
points, بوستان starts rebuilding — and that one is very likely **right**, since
بوستان is بو + ستان in the ordinary account of it. Recorded on L26 so the
ruling is made with both sides of it visible.

**One signal was tested and rejected.** When a rebuilt word is itself a
headword, does the last rule's output class agree with the lexicon's own class?
It separates دستان (agrees) from داستان (does not). Measured over 300 sampled
headwords: 50 rebuild, 45 agree, **5 disagree** — and the five are mostly the
coarseness of the category mapping rather than bad parses (*Didār* is filed
اسم مرکب and is a kārnām, correctly). Not a usable filter; recorded so it is
not re-derived.

### Four things a walk through two screens found

The project lead read the search filters and the questions screen on 2026-08-20
and named four faults. None is deep and all four are the same kind: the screen
serving us rather than its reader.

**The filters looked like a form and were not one.** Every control sized
itself, so nothing lined up down the panel, and the native `select` drew its
own height and its own arrow beside inputs that had ours — three controls in a
row were three different objects. Measured after the rebuild: all four selects
176px wide and 44px tall on one line, every label flush at one edge, and at
375px nothing overflows.

**The answer box asked for three languages.** Persian, then Behnevis, then an
English rendering. The question stopped being shown three ways in session 16
for exactly this reason and the answer had kept all three.

**The evidence fold was English.** Imported from the repository's Markdown,
rendered as left-to-right prose in a right-to-left page with its `**` still in
it. The files beside it — the grammar document, the word list — are what a
question actually turns on.

**The state was invisible while paging.** One question on screen at a time is
new as of this session, and the thing a reader most needs while stepping
through is whether *this* one is answered. It was a small grey word, last in
the header row.

Also fixed while there: «پس گرفته شده» had no account on screen. The store has
kept `withdrawn_because` all along — L4 *«این یک پرسش نبود بلکه فهرستی از
پرسش‌های کوچک‌تر بود»*, L11 *«پاسخ داده شد»* — and the screen never printed it.

### What went live, and the one check that nearly read wrong

Deployed twice — after the glide work and again after the rest — with
`docker compose -f docker-compose.prod.yml up -d --build` against the stack
this machine runs behind the Cloudflare Tunnel. Checked on the running system
rather than in the tree:

| | |
|---|---|
| the wall, from outside | 401 on the site and 401 on `/api` |
| *guyande* on the live API | 2 accounts, glide G-06 |
| *Golstānstān*, *Golzārzār*, *Golāā*, *Goliyi* | gone; *Golstān* still built |
| the served CSS | no `select` chrome, the arrow drawn |
| the served JS | no English answer box, the pager, the withdrawn reason |

**And a check that looks like a failure and is not.** `curl http://localhost/`
against the running stack returns **200 with an empty body**, which reads as
the password wall being off. It is not: the Caddyfile's site is
`{$MURFULU_SITE_ADDRESS}`, a request with no matching Host matches no site, and
Caddy answers with nothing. The wall is only exercised by asking for the name
it is written under — `curl -H 'Host: murfulu.mosaic-hub.de'`, or the public
address, which is what DEPLOY §6 uses. Worth knowing before somebody checks
the quick way and believes the answer.

### The grammar's own vocabulary cannot be built by the grammar's own rules

The project lead asked for better Persian candidates for the Arabic grammar
terms — the coining experiment turned on our own vocabulary. Checking the
candidates the way that experiment checked its proposals found something
larger than the candidates.

**کارنام، کارواژه، جانام، چون‌واژه، پیش‌واژه are a nām joined straight to a
nām, and the pack has no rule for that shape.** The only two-noun row in the
nominal table is row 104, verbatim in `rules/source_rows.json` as
`Nām + ā + Nām` with *Sarāsar* for an example, and it puts an **ā** between the
halves. So asked for کار + نام the engine builds **کارانام**, and asked for
ordinary Persian it builds کتاباخانه, گلاآب, روزانامه, شبانم for کتابخانه,
گلاب, روزنامه, شبنم. Four hand-checked words, and the pattern behind them is
plausibly the most productive compound shape in the language.

Recorded as [L28](FOR_THE_LINGUIST.md) rather than fixed: the document does not
have the row, and the pack does not invent rules.

**And a measurement that must not be quoted.** Trying to size the pattern by
splitting the 4,000 commonest corpus spellings into two lexicon nouns reports
43 — and its top rows are پیوسته as پیو + سته, دیگران as دیگ + ران, داستان as
داس + تان. Unusable, for exactly the reason L18 records: short strings collide.
Written down so nobody derives it a second time and believes it.

**On the terms themselves**, three coining runs were made against the running
app — propose, then verify through `/explain`, `/generate`, `/compound` and
`/search`, the *Dasein* protocol. The candidates and their evidence are in
[L27](FOR_THE_LINGUIST.md). Four findings from the runs are worth keeping here:

**کارنده does not mean the doer.** `/explain` rebuilds it from **کشتن، کاریدن،
کاشتن** and by no route from کار, so «کارنده‌کاربهر», the term for the agent
participle, reads on this project's own engine as *the sower*. And **کاربهر
occurs 0 times in 25,497,189 words**; کاریده occurs once.

**The tail ـواژه is not a Persian compounding tail and ـبن is.** Entries whose
spelling ends in واژه: **two**, گواژه and بلواژه, neither a compound of واژه.
Entries ending in بن: **45**, most of them اسم مرکب — گلبن (971 documents, 145
poets), خاربن, سروبن, رزبن, خرمابن, کاج‌بن. Four of the linguist's terms sit on
the first tail.

**The vocative has a rule already, and it hands us the one buildable term.**
N-032 makes a **ندایی** from a nām with *-ā*, and its own examples are خوشا
(1,161 documents) and دردا (487). Put بانگ — karbon's own entry glosses it with
نداء, 3,306 documents by 205 poets — through that rule and the running app
answers `rebuilt: true, settled: true`, one account, N-032. **بانگا is the only
word in the whole experiment the engine derives with no ruling needed**, and it
is free in the corpus. ناما was proposed first and withdrawn: نام is filed
اسم معنی → kārnām so N-032 refuses it, and `/explain` accounts for ناما by
نامیدن instead.

**پیش‌واژه collides inside our own pack.** N-084's worked example is
`Pišvand`, and پیشوند is the settled modern word for *prefix*.

**None of the candidates appears anywhere in the corpus**, checked against all
409,916 spellings; of the existing terms only برنام (15 documents) and جانام
(1) are attested at all.

### Flaschenhals, and the wall two independent runs hit

The project lead asked for Persian candidates for the German *Flaschenhals*.
Two runs against the running app, one on the geometry and one on the function.

**Persian already has the word: گلوگاه** — a karbon headword, 23 documents by
13 poets, and گلو + `-gāh` under N-068, which is the same shape every candidate
below uses. Neither run beat it on attestation and both said so.

**What the runs found that a person would not have.** تنگ has **three** lexicon
readings, and one of them — `Tong` — is glossed «کوزهٔ سرتنگ گردن کوتاه»: *a
narrow-necked flask*. So تنگ is at once the Persian for *narrow* and for
*bottle*, and **تنگگاه** is a Flaschenhals twice over on the same letters. It
builds: `/explain?word=Tonggāh` → `rebuilt: true`, تنگ + `-gāh`.

The other candidates that build, all verified through `/explain`: **نایگاه**
(نای, the hollow tube, 1,074 documents), **گردنگاه**, **گیرگاه**, **ماندگاه**,
**بندگاه**, **بندشگاه**, **بستگاه**, **روزنگاه**, **گدارگاه**. None is in the
corpus. The function angle's best is ماندگاه — *the place where everything is
left waiting* — which is the one candidate that fits a process rather than a
pipe.

**And both runs hit the same wall, which turned out to be a live fault.**
Neither could get گلوگاه to analyse from its Persian spelling. The cause is
karbon's transliteration: **457 of the 463 entries ending in ـگاه are written
`-gāe`** while the rule pack's affix is `-gāh`, so `/explain?word=Golugāe`
returns `rebuilt: false` and `Golugāh` returns `rebuilt: true`. Widening it:
**777 of the 803 readings ending in ـاه** are written `-āe` — شاه is `Šāe`, ماه
is `Māe`, راه is `Rae`.

**It is not only a reading problem; we are building wrong Persian with it.**
`glides.join_fa` decides whether a final ه is the silent one by reading the
Latin — deliberately, because بنده + گی is بندگی while شاه + گان is شاهگان, and
the Persian alone cannot tell them apart. The docstring names شاه as the case
it handles. It handles it only if the Latin is right, and for these 777 it is
not: building from شاه gives **شاگان، شاگین، شاگیدن**. Sampled over 40 of the
779 affected readings, **550 of 1,935 one-step forms — 28% — lose the ه**.

Filed as [UPSTREAM A9](UPSTREAM.md), **and guarded on our side the same day**:
a ه standing after ا is never the silent one, whatever the Latin says, because
a silent ه writes a short *e* and a short vowel cannot follow a long ā. The
same 40-reading sample now loses the ه **0 times in 1,935 forms**. The reading
is untouched — `Šāe` is still what karbon hands us and what the screens show —
so this is our orthography changing, not karbon's value being worked around,
and `/explain?word=گلوگاه` still fails until the value is fixed. Nothing
outside ـاه was touched: کوه is *kuh* and میوه is *mive*, both written وه.

**One more category fault, in passing.** تنگنا cannot be rebuilt either:
N-072 (`-nā`, *Derāznā*) and N-033 (`-ā`, *Pahnā*) both want a **barnām**, and
تنگ is filed اسم ذات → nām on all three of its readings. So the whole
درازنا/پهنا/تنگنا paradigm is shut to the words it is for. The same shape as
L26, on a different rule family.

### A ruling from two days ago had two places it had not reached

`--measure` was set to the page width on 2026-08-18 because paragraphs were
breaking at 734px inside a 1248px page. Two screens still carried a cap of
their own — the questions screen at `60ch`, the word screen's definition at
`62ch` — and the questions screen is where it showed worst, because its
paragraphs are the longest text in the app and its card is the full width of
the page. Both caps removed; nothing in the app now breaks a line before the
page does.

**The same screen was also a single scroll of sixteen questions**, each one
several paragraphs plus files, evidence and an answer box. It is one question
at a time now, with next and previous and its place in the set, and the open
question is named in the address so a single question can be linked to.

---

## 2026-08-18 (session 19) — دستور, and what a compound row never showed

The project lead read the compound screen for دست and asked one question of a
row — *where does this word come from?* — which the screen could not answer.
Working it out found a data fault, a wording fault and a missing check.

### دستور is offered as دست + ور, and ور is a verb stem in karbon

`دست + ور ← کارنده‌کاربهر V-078`. The ور is not the suffix **-var**: it is the
**present stem of وشتن**, which karbon derives with its stem rule 8 and stores
at `confidence 1.0, needs_review 0` (`data/lexicon-20260808.sqlite`, id 1916,
`وشتن / وشت / ور`). The engine is behaving exactly as V-078 says — a noun in
front, any کاربن دو behind — so nothing here is a bug in Murfulu.

**The pack already holds the reading a Persian speaker would give.** N-080 is
*نام + -var → برنام* with the example *dānešvar*, and دستور on that route is
دست + the possessing suffix, not a verb compound. The compound screen only
runs compounding rules, so a reader sees the verb-stem reading alone.

### How often a stem can be read as a suffix — measured

Every verb stem in the snapshot against every suffix spelling in the pack:
**25 of 3,232 verbs have a present stem spelled exactly like a suffix**
(مان ×5, کار ×3, آسا ×2, دان ×2, ستان ×2, ش ×2, تر ×2, and one each for
چه، زار، گار، گر، وار، ور …). Each of those makes every noun compound built on
it also readable as noun + suffix. This is the compound-screen twin of the
homograph pass that already runs over affix claims.

### The evidence line vouches for a different word

The row prints «املای «دستور» در ۹۷۰ سروده از ۱۱۸ سراینده آمده است» — true, and
about *dastur*, the vizier and the order, which is not the coined *dastvar*.
The screen has a mechanism for exactly this — `also_an_inflection`, which marks
and sinks دلم — and it fires only for inflections. A homograph in the lexicon
passes as support.

### What the rules screen shows is ours, not the document's

Every rule carries `source: {table, row}` into `rules/source_rows.json`, which
is a verbatim transcription naming the .docx and its sha256 — so the rules are
the document's. **The Persian sentence under each one is not.** It is generated
from the row's structured fields, and V-001 shows what that loses: the source
row reads *Kārboné doé nāgozarā az Goruhé yek (NKZ)* → *Nābesudkārvāžeé
gozarā*, and the screen says «از کاربن دو با پسوند -āndan نابسودکارواژه ساخته
می‌شود» — no intransitive, no group one, no transitive. The full string is in
the pack as `input.condition_text`; `api/rules.py` does not serve it.

### کار builds nothing, and that is L18 arriving on a screen

کار is filed **اسم معنی** → کارنام, and every slot rule takes a **نام** in
front, so it is shut out of all six. **1,949 readings are in that position**
(measured for L18 on 2026-08-17). Nothing is broken; the screen simply had no
way to say it, and answered with «۰ ترکیب». The mismatch is now data on the
route — `word_classes` against `slot_wants`.

### The compound screen was showing 2% of its own answer

`/compound` defaults to `attested=true` and the screen never sent anything
else, so دل's 4,543 unwritten compounds — the coinages this project exists to
produce — were unreachable from the interface. Asked by the project lead on
2026-08-18: *do we only show words in the corpus?* We did.

### A shadowed loop variable, caught before it shipped

`_from_slots` computed the front classes into `wanted` and the function's own
inner loop is `for wanted in rule.input_types`, so every successful reading
reported its front slot as `karbon_do`. Found by running دست and کار against
the real snapshot rather than by a test, which is the argument for running the
real thing.

### The 212 on the rules screen

81 verb-table rules + 105 nominal + 9 stem + 17 glide = **212**. It is every
rule of every family, which is what «۲۱۲ دستور» should mean, and the family
buttons narrow it.

---

## 2026-08-18 (session 18, after) — what «۴۳۲ بن» actually counts

The project lead asked what the semantic sentence meant, and walking it through
the Feynman steps caught a wrong claim in our own Persian.

### The stems were not found in the corpus. The rule's output was.

The sentence read «بن‌هایی که در پیکره یافته‌ایم» — *stems we found in the
corpus*. What the artefact counts is **attested pairs**: a stem enters a rule's
count only when the word **that rule built from it** was written. The corpus
vouches for the pairing, not for the stem. Corrected the same day; it had
shipped.

### What a "meaning" is here, exactly

Worth writing down, because the sentence names a *مرکزِ معنایی* and nothing
said what one is:

- a stem's vector is the mean of **BGE-m3 embeddings of up to six corpus lines
  containing it** — the word as the poets used it, not as a dictionary defines
  it. 1,024 numbers.
- a rule's centre is the mean of its attested bases' vectors.
- **a rule needs at least ten attested pairs to get one, and only 59 rules
  clear that bar.** Every other rule shows nothing here at all.

So the figure rests on up to six lines of verse per word, and the phrase
*centre of meaning* is an average of averages. That is not an argument against
it — the pilot scored 93% against 33% chance — but it is the thing a reader is
being asked to trust, and the screen should not make it sound firmer than it
is.

### What is still unexplained on screen

**«مرکزِ معنایی» is ours and undefined.** A reader is shown the phrase and no
account of what it is. The list beside it does most of the work — five stems
with their figures, and the base placed among them — but the phrase itself is
jargon this project invented and has not explained. For FOR_THE_LINGUIST, and
for a plainer wording.

---

## 2026-08-18 (session 18, after) — دل is six words, and the app shows the wrong one

The compound screen ships with **دل** as its example. The project lead asked
why its Behnevis reads **Dal**. Because the lexicon holds **six** entries for
that spelling:

| vowelized | Behnevis | class | what it means |
|---|---|---|---|
| دَل | Dal | اسم ذات | a fir tree, in Hamadan |
| دَل | Dal | اسم ذات | a female dog, Gonabad dialect |
| دَل | Dal | اسم ذات | «sea» in Hindi |
| دُل | Dol | اسم ذات | knots in the intestines after illness |
| دَل | dal | صفت | full, brimming |
| **دِل** | **Del** | **اسم ذات** | **قلب و فؤاد — the heart** |

`/compound` returns them **Dal, Dol, Del, dal** and the screen shows the first,
so the app labels *heart* as a Hamadani fir tree — on its own worked example,
the first thing a new reader is shown.

**Nothing is wrong with the phonemization.** All six are correct readings of
those letters. What is missing is an **order**: the readings arrive in what
looks like lexicon-entry order and nothing puts the common word first.

**And the corpus can settle it.** دل as *Del* will be everywhere in the poetry
and *Dal* essentially nowhere. The evidence needed to rank these is already
computed for built words; it is simply not applied to a word's own readings.
Same family as بلند, where the flagged reading builds the longer list — but
worse, because there both readings are plausible and here a dialect word
outranks one of the commonest nouns in Persian.

### Capitalisation is meaning, and the box is right to be strict

Typing `del` finds nothing, and that is **correct**: a capital marks a name in
Behnevis, and the lexicon proves the distinction carries — `Dal` is three nouns
and `dal` is an adjective meaning *full*. `del` lower-case does not exist at
all. What the screen does wrong is only to say nothing: the reader gets silence
where «did you mean Del?» would cost one line. Left unbuilt on the project
lead's word.

---

## 2026-08-18 (session 18, last) — four rules, one sentence, and no way to tell them apart

The project lead opened the derivation of **وارفتنی**, saw «۴ راه» and then
twelve rules, and asked what it meant. Both halves of the confusion were the
screen's.

### It was four routes of three steps, shown as one list of twelve

Every route is the same three steps — `raft` + `vā-` → vāraft, + `-an` →
vāraftan, + `-i` → Vāraftani. Steps two and three are **identical in all four**:
V-006 then N-098, four times over. Only the first step changes.

They rendered as four `<ol>`s inside one grey panel separated by a gap, with
nothing numbering them. Twelve rows, no boundary, and a count above that
matched nothing a reader could see.

### The one field that told them apart was not sent to the screen

V-070, V-071, V-072 and V-073 all attach the same `vā-` to the same stem and
carry a **word for word identical `explanation_fa`**, because that sentence
describes the mechanics and the mechanics are what they share. What separates
them is the sense the prefix carries, and it is in the rule pack already:

| rule | tag | gloss |
|---|---|---|
| V-070 | `pas` | **پس** — back, behind |
| V-071 | `dobare` | **دوباره** — again |
| V-072 | `baz` | **باز** — open, back again |
| V-073 | `axsij` | **آخشیج** — opposite, counter- |

`Step` carried `rule_id`, `affix`, `applied_to`, the explanation and the glide.
It did not carry the tag. So the screen printed the same sentence four times
and the reader was asked to infer a difference that had been dropped in
transit.

**What it means for Murfulu.** «۴ راه» does not mean four mechanisms; it means
**four senses the word could carry**, which is worth far more than it was being
shown as. It is also the same shape as the compound screen's S26 — several
rules that write identical letters and differ only in what they mean. If the
linguist would rather these were one rule with four senses, that is a data
question and this display would follow it rather than block it.

**A guard earned its keep.** `test_no_route_holds_logic` asserts the string
`yaml` appears nowhere in `api/`, and it failed on a code *comment* naming the
tag file. `api/` is wiring; even a comment pointing at a data file is a hint
that logic is drifting there. Reworded, not suppressed.

---

## 2026-08-18 (session 18, later) — the build screen had categories nobody could use

### 660 words in 8 classes, and every class open at once

رفتن at depth 2 answers with **660 words in 8 word classes**, and it does that
for **each of its two readings** — raftan and roftan. The screen grouped them
correctly and then opened every group at twenty rows, so what a reader got was
sixteen headings buried in a scroll of rows.

Measured in the browser at 1280px, on the real answer:

| | page height |
|---|---|
| every group open — what the screen did | **47,802px** (290 rows) |
| classes only, folded | **2,209px** |

**21.6 times shorter**, or 53 screens of scrolling down to 2.5. The categories
were already there and already correct; they were simply not the thing the
reader was given first.

### The explanation could not stay a tooltip

The class heading is now the control that opens the group, and the heading used
to be a `Term` — which is a **button**. A button inside a button is invalid
HTML and the inner one cannot be reached by keyboard, so the explanation had to
leave the tooltip and be written out. That turned out to be the better place
for it anyway: the folded list is exactly where a reader decides whether
کارنام is what they want, which is the same reasoning the navigation's gloss
was settled on a day earlier.

### Two things only real data caught

The Playwright suite skips its data-dependent tests when the API is
unreachable, and the dev server cannot reach the API — it proxies to port 8010
and the API container publishes nothing. Bridging the two for the session ran
**4 tests that had been skipping**, and 2 of them were real:

- the build tests asserted on rows that are now behind a closed group;
- **axe found a contrast violation this session introduced** — a 15% `opacity`
  on top of `--ink-faint` to set the traditional term back. The token is
  already at the contrast floor, so anything layered on it goes under. Set a
  term back with order and spacing, never by fading an ink token.

**What it means for Murfulu.** A skipped test reads exactly like a passing one
in the summary line. Anything that depends on the API is unverified on a
laptop unless the bridge is up, and that is worth remembering before believing
a green run.

---

## 2026-08-18 (session 18) — `ch` is a digit, and Persian is not

The project lead walked the running app again. Four faults, and one of them is
a measurement worth keeping.

### The line measure was calibrated to the wrong glyph

`--measure: 68ch` capped every paragraph. `ch` is defined as the width of the
digit **zero**, and Farhang2 does not draw a Persian letter anything like a
digit. Measured on the running app at 18px:

| | width |
|---|---|
| `1ch` — the digit zero | 10.81px |
| the letter «ا» | 3.47px |
| an average Persian character, over a real sentence | 5.91px |

So `ch` is **1.83×** a Persian character, and `68ch` never meant sixty-eight of
them. It resolved to 734px, which holds about **124** Persian characters — past
any measure anyone would choose on purpose, and still 41% short of the 1248px
page it sat in. It was achieving neither thing: not a readable line length, and
not a full one.

**What it looked like.** The word screen's definition carried its own
`max-width: 62ch` inside a wrapping flex row, so a Dehkhoda gloss broke onto a
second line with two thirds of the first still empty. That is what the project
lead saw and named: *do not add a line break when there is enough space in the
line; the whole app has this issue.*

**What it means for Murfulu.** Any width written in `ch` is wrong here by a
factor of nearly two, and there is no CSS unit calibrated to a Persian
character. Until there is a reason to pick a real measure, the page's own
maximum is the honest bound and `--measure` is now `var(--page-max)`. If a
measure is ever wanted back, 5.91px per character at 18px is the number to
divide by — not `ch`.

### The search screen was teaching the same four queries twice

The four example chips under the box — `*nā`, `type:karnam`, `count:1`,
`stem2:gu` — are every one of them already a row inside راهنمای نحو, which
session 17 built to hold all fourteen forms. Adding the folded reference made
the unfolded chips a duplicate, and nobody noticed at the time. They also read
as buttons offering an action rather than as help, which is what got them
raised. Folding them in cost nothing: the reference already ran each one on a
click, and the input's placeholder still shows a working query on the empty
screen.

### The corpus screen named its source in Latin

Under a heading reading **سرچشمه** it printed `ganjoor`. The identifier is
correct for `source:ganjoor` in the search box and wrong for a reader on a
Persian page; the two are different jobs and one string was doing both. Same
shape as the licence fault found on 2026-08-17 and fixed the same way — a fact
about the source, filled in by source id for reports written before the field
existed, so it does not wait on a re-ingest.

---

## 2026-08-17 (session 17, later) — a walk through the app, and four faults it found

The project lead went through the running app screen by screen. Every finding
was the same finding in a different place: **the app names things and does not
say what they are.** [FRONTEND.md](FRONTEND.md) has required the opposite since
the shell was built — *the interface has to explain itself without a manual* —
and it had been honoured for the grammar terms and almost nowhere else.

### The search screen taught four of its fourteen operators

The chips under the box are real queries and clicking one runs it, which is the
right teaching device. But there are four of them, and the language has
**fourteen** forms: `stem1:`, `stem2:`, `rule:`, `affix:`, `tag:`, `in:`,
`author:`, `source:`, `count:>10`, `century:10-13`, `bar*`, `*raft*`, `/regex/`
and the Persian-script case were named in `docs/SEARCH.md` and nowhere a reader
could see. The facet panel does teach the syntax — it writes the query it stands
for — but it only appears *after* a search has worked, so it cannot help anyone
who does not know how to start.

### Two bugs in the facet panel, and the second was the worse one

Found while reading that code rather than by any test.

**`category:` was not a field the parser had.** The panel had written
`category:<value>` since it was built and `query.py`'s `FIELDS` had `type` and
no `category`, so every click on a value under «گونه در واژه‌نامهٔ کاربن»
replaced a working search with *this query was not read*. The facet counts
`lexicon_category`, which is a real field and a different one from `word_class`,
so the fix was to add it rather than to rename anything.

**And the values are two words.** Dehkhoda's categories are «اسم ذات»، «اسم
معنی». `query.py` splits with `shlex`, so an unquoted space ended the term:
`category:اسم ذات` parsed as *category is اسم* **and** *the word is ذات*. It
did not fail. It answered a different question and looked right doing it, which
is why it outlived the bug beside it.

**Neither could have been caught by the tests as they stood**: the screen's
tests mock the API, and the parser is in Python, so a query the interface writes
had never once been given to the thing that reads it. That gap is now
`tests/test_search_syntax_contract.py`, which reads `syntax.ts` and asserts the
parser accepts every field and every reference row it offers — and the reverse,
that no parseable field is unreachable from the app. `stem1` and `tag` were
both, so *which affixes mean 'place'?* — the question in the proposal that
started the project — could not be asked from the interface at all.

### The English the reader still saw

Two places, and both were prose rather than identifiers:

| where | what |
|---|---|
| corpus screen, پروانهٔ استفاده | *classical poetry compiled by Ganjoor; Ganjoor states its data are not necessarily free of copyright and warrants nothing* |
| search screen, when a query fails | *poem: is not a searchable field*, and four more like it |

The second is the one a reader meets by mistyping. `QueryError` now carries a
**code** and the parts of the fault, the API sends those, and the screen writes
the Persian; the English stays in `said` for the log and the network tab. The
first is now `licence_fa` on the adapter, falling back to the English where a
source has not written one — a sentence about copyright in the wrong language
beats no sentence. Ganjoor's own answer is «لزوماً خیر!», so the Persian is
nearer the source than the English was.

### A tooltip that a phone could not open, in the component whose job is explaining

Found by writing a test for the new ⓘ and watching it fail. **A press is three
events** — pointer enter, focus, then click — and both `Term` and the new `Info`
opened on the first two and *toggled* on the third, so the tooltip opened and
shut inside one tap. With a mouse the hover hides it; on a phone there is no
hover, so tapping a grammar term explained nothing. `Term` has had this since it
was written. Both now open on click and close on leave, blur or Escape.

### دلبر three times is not a duplicate

The compound screen showed دلبر from V-078, دلبر from V-079 and دلبر read
*dalber*, all with the same ۲٬۹۲۰ سروده / ۱۹۱ سراینده.

Nothing there is wrong and two things are badly said. V-078 and V-079 join a
*nām* to a *kārbon-e do* and differ in **one** thing — one makes the doer, the
other the done-to — which `compounding.py` keeps on purpose and the screen
reduced to two rule ids that mean nothing to a reader. The word class was on
every row already and was not shown. And the count is looked up **by spelling**
(`_asked` keys on `pairing.fa`), which is all the corpus can answer, the corpus
having no vowels — so printing it bare on each reading made one word's evidence
read as three findings. Both are now said on the row.

---

## 2026-08-17 (session 17) — the interface face, and the one thing Farhang cannot set

### Farhang2 has the Persian in full and none of the Behnevis diacritics

The project lead asked for Farhang as the app's font. It is in the Drive
archive at `Assets/Fonts/Farhang2Pro`, version **2.100**, nine static weights
plus a variable file, in `.ttf`, `.woff` and `.woff2`.

Its character map was read rather than eyeballed, and the answer splits cleanly
in two:

| | |
|---|---|
| Persian block, ZWNJ, Persian digits ۰–۹ | **complete** |
| ASCII Latin `a–z A–Z 0–9` | **complete** |
| `ā ē ī ō ū š ž č ğ` and their capitals | **none of the eighteen** |

So Farhang can take the interface and cannot take the data. A Behnevis form set
in it would break apart mid-word — `k` and `r` from Farhang, `ā` from whatever
the browser reached for next — which is precisely the confusion
[FRONTEND.md](FRONTEND.md) gives the Latin forms their own face to prevent.
**Inter keeps the Latin islands**, and now also stands second in the Persian
stack, so a stray `ā` outside an island lands on a face we chose. Measured in
the browser afterwards: a Behnevis string in the body stack renders at Inter's
width, not the system font's.

### Farhang is proprietary, and it is paid for

`FontLicense.txt` and `licenses.pdf` ship beside the files. The fonts are
commercial software from **fontiran.com** (designer Moslem Ebrahimi); the terms
ask for the licence file to be kept next to the fonts and for the six-digit
code to be written into the CSS, and both are done — the file is in
`web/src/styles/fonts/`, and the comment at the top of `farhang.css` holds the
place for the code.

**Raised on 2026-08-17 as S25 and answered on 2026-08-18: the project lead has
bought the font.** Recorded here because the question — a proprietary face,
served from a host, in a repository due to go public — is the kind that gets
asked again by whoever reads this next, and the answer should be findable
rather than re-derived.

### What it cost to swap

Three weights ship — 400, 500 and 700, the only ones `tokens.css` names — at
**88 KB of `.woff2` in total**, against Vazirmatn's five subsets. Vazirmatn is
uninstalled; the layout suite passes at 375 px and 1280 px with no new overflow,
so Farhang's metrics fit the layout Vazirmatn's were tuned against.

---

## 2026-08-17 (session 16, later) — deploying, and three things that only fail in production

### The deploy runbook's first command could not run

`docs/DEPLOY.md` moves the corpus to a server as a snapshot rather than an
ingest, because re-ingesting needs the Ganjoor dump and hours of compute. Its
first command fails: **neither compose file set `path.repo`**, and Elasticsearch
refuses to register any `fs` repository while that setting is empty.

The runbook had been written the same morning and never executed. Proved end to
end after fixing it — **v11 snapshot: 72 seconds, 2.8 GB, four of four shards**
— and the volume needs `chown` once, because Docker creates it as root and
Elasticsearch runs as uid 1000. Both are in the runbook now instead of being
discovered.

### Docker Compose eats a `$` in a `.env` value, and the failure looks like success

The bcrypt hash for the site password is `$2a$14$…`. Compose interpolates
variables **inside `.env` values**, so `$TrQo7…` was read as a variable name and
expanded to nothing: the container received `$2a$14` and no more.

**`docker compose config` does not reveal it** — it prints its own escaped form,
`$$2a$$14`, which looks plausible either way. What revealed it was asking the
container what it actually had:

```
docker compose run --rm caddy sh -c 'echo "$MURFULU_SITE_PASSWORD_HASH" | wc -c'
```

61 characters after escaping each `$` as `$$`. The general rule: **verify a
secret at the process that consumes it, not at the tool that passes it along.**

### There is no server, and there never was

`murfulu.mosaic-hub.de` had no DNS record and no host to point at. The sibling
app on the same domain — `sokhan` — turns out to run from a workstation through
a Cloudflare Tunnel, in fifteen lines of shell. Following that removed the
question rather than answering it.

Two of this repo's assumptions were quietly unsafe in that shape. Caddy asked
Let's Encrypt for a certificate it could never validate, because Cloudflare has
already terminated TLS. And Caddy published on `0.0.0.0`, which on a laptop
offers the corpus to everything on the same wifi as well as to `cloudflared` —
a password wall in front of an address that should not have been listening.

### And the wall was checked from outside, which is the only place it counts

401 with no credentials, 401 with a wrong password, 401 with a wrong user, and
401 on `/api` — all through Cloudflare's edge, not the loopback. Elasticsearch,
which the development stack publishes on 9200, refuses the connection entirely.

**One thing could not be checked and should not have been**: that the *right*
password gives 200. Only the person who chose it can do that, which is the same
reason the hash had to be produced on their side.

---

## 2026-08-17 (session 16) — clearing the open questions, and the two wrong answers it found

Fifteen open engineering questions were settled in one pass. The decisions and
their reasons are in [DECISIONS.md](DECISIONS.md); what follows is what was
*learned*, which is a shorter list and mostly not what the questions were about.

### `/explain` reported an unfinished search as a refusal

**The largest thing found, and nobody had asked about it.** Chasing why
درافکندگی does not rebuild — the case the coining experiment named as the
engine's largest gap — the answer turned out not to be a missing rule at all.

`MAX_FORMS = 20_000` in `engine/generate.py`. Building forward from افکندن
reaches **20,050 forms at three steps**, so the run is truncated and never
arrives at *Darafkandegi*. Every rule the chain needs exists and fires:
`darafkande` is built, it is a `karidekarbahr`, and V-082 takes exactly that
class.

**The engine had always reported this** — `Generation.truncated` — and
`analysis.explain` threw it away. So an unfinished search and an exhausted one
gave a reader the identical sentence. Measured over 120 random lexicon readings:

| depth | rebuilt | settled "no" | search ran out of room |
|---|---|---|---|
| 2 | 15.3% | 84.7% | **0%** |
| 3 | 19.2% | 75.0% | **5.8%** |
| 4 | 19.2% | 73.3% | **7.5%** |

At the depth the coining experiment used, **about one "cannot be built" in
seventeen was not a refusal at all**. مولانا — the case the whole *sāzāyi* check
exists for — is still a settled refusal, checked.

**The lesson is the one this project keeps relearning**: a confident wrong
answer is worse than a slow one, and *not established* is a third answer that
has to survive to the screen. The same shape as a bare 500 behind a healthy
`/health`, and as a stored `false` where nothing was measured.

### A tool that measures something is not the same as a measurement

Eighteen compounding rules reported `types_built: 0` in `/rules`. The tool that
measures them — `tools/measure_compounding.py` — had been written, tested and
documented, and **never run for v10**. A figure of zero beside a rule that
builds 35 million forms is worse than no figure, which is the argument the tool's
own docstring makes.

Run now: **16 of 18 measured**, 2 refusing to guess.

| rule | pairs built | attested | rate |
|---|---|---|---|
| V-016 | 35,369,026 | 3,632 | 0.0103% |
| V-078, V-079 | 28,896,536 | 26,361 | 0.0912% |
| V-080, V-081 | 18,749,048 | 7,931 | 0.0423% |
| **V-044** | 1,696 | 68 | **4.0094%** |
| V-021 | 1,696 | 0 | 0% |
| N-104 | — | — | *20,879 nouns against itself is 435,932,641 pairs* |
| V-031 | — | — | *one side is a derived class, not a word the lexicon holds* |

### An inflection outranking a derivation was fixable, and the instrument was already here

S8's second half said no condition over the fields we hold could separate رفتی —
"you went" — from گفتار. That is true, and it is why the fix does not use those
fields: it asks the **inflection analyser**, built in session 10 to *measure* the
problem and never asked at request time.

Measured on رفتن at two steps, 660 forms:

| form | before | now |
|---|---|---|
| رفتی — 1,565 poems | 12 | **57** |
| نرفته | 19 | **60** |
| رفتار | 13 | **10** |
| روش | 16 | **13** |
| رونده | 21 | **14** |

**Seven of the top twenty read as inflections before; none does now.** 45 of the
660 forms read as one, and **95.6% of those share their letters with a
derivational rule** — independently reproducing the 95.5% measured in session 10
on a different sample. That is why both the clear and the shared cases are
demoted, and why the row says which kind it is rather than pretending the
letters decide.

### The semantic constraint has tightened, re-measured on v10

`tools/count_semantic_pairs.py` over 1,852,066 records:

| | v10 | previously quoted |
|---|---|---|
| rules with any attested pair | **65** of 195 | 63 |
| rules with ≥ 200 pairs | **23** | 22 |
| **pairs whose base is a bound stem** | **79.0%** (13,270 of 16,787) | 76.8% |

Bases by class: karbon_do 8,790 · karbon_yek 4,480 · barnam 2,962 · karnam 555.
Best supplied: V-049 with 1,106 pairs, V-007 and V-020 with 761, V-033 with 635.

**79% is the number that decides between the three candidate measures**, because
FRACSS fits a matrix on base→derived vector pairs and a bound stem has no
distributional vector at all.

### Accepting the Persian spelling buys less than it looks like

`/explain` now looks a Persian spelling up rather than refusing it — and
**every** reading, so کنار comes back as *Kanār*, *Kenār* and *Konār*. But the
words this route exists for are mostly not headwords. Of 20 derived words a
reader would plausibly paste, the lexicon holds **9**:

* held: دانشمند آزادگان نمکدان گلستان میکده درگاه خردمند سخندان دلبر
* not: گفتار روش زندگی گفتگو دانایی رفتار رونده بندگی روشنگاه کارگر چشمداشت

So it halves the refusals and does not remove them. **And دانشمند, one of the two
words the question named, is in the lexicon and still rebuilds to zero
accounts** — which is the S20 triage seen from the reader's side.

### The base's own corpus count separates one bad parse and not the other

The evidence now served beside each account of a word:

| word | base | the corpus |
|---|---|---|
| `Hamzamāni` | هم‌زمان | **1 document** |
| `Nāxodāgāhi` | ناخدا | **213 documents** |

It sinks *Hamzamāni* and says nothing useful about *Nāxodāgāhi*, whose base is a
perfectly ordinary word that is simply not the one anyone means. **Evidence, not
a verdict**, and the screen says so. Nothing here judges meaning.

### A machine id that disagrees with its own source

The word class `jonvaze` is written *Čonvāže* everywhere in the source grammar —
a **j** where the source has a **č**. It is a leftover of the Latin convention
this project used before the one DECISIONS settled on (š ž č j ˈ).

**The id stays.** It is written into `rules/nominals.yaml`, `rules/verb_stems.yaml`,
the engine and every stored derivation, and an id is permanent. The Behnevis is
now carried beside it in `rules/word_classes.yaml`, so a reader can see the
disagreement instead of inheriting it.

### Renaming an API field takes the screen down against a stale container

Found by testing: renaming `explained` to `rebuilt` made the explain screen
answer *no way to build this was found* for every word, because the running API
was one build behind. That is a confident wrong answer produced by a rename
meant to stop confident wrong answers.

The client now **derives** the flag from the accounts when the field is absent,
rather than reading the old name — deriving keeps the meaning, an alias would
have kept the trap. Same class of failure as the `word_classes` incident, and
worth remembering as a general rule: **a renamed field needs a client that can
answer without it, not a server that answers twice.**

### What the storage question actually cost

For S1, measured rather than argued: storing the three presentation fields on
every record costs **245 bytes, 18.6%** — 2.28 GB to 2.71 GB — against **0.02s at
two steps and 0.48s at three** to re-derive them. The size settled it less than
the staleness did: those fields are functions of a *versioned* rule pack, and a
stored one is a true-looking figure under a false label the moment the pack moves.

---

## 2026-08-17 (session 15d) — the licence, and the part of it that was actual work

### The corpus screen was asserting the thing nobody had checked

`GanjoorCorpus.licence` returned *"public-domain classical texts, compiled by
Ganjoor (confirm terms)"*, and that string is on the corpus screen under
«پروانهٔ استفاده». **The parenthesis was honest and the words in front of it
were not.** "Confirm terms" admits to not knowing; "public-domain classical
texts" asserts the answer anyway, and a reader stops at the first clause.

What made it feel safe is a real distinction applied to the wrong question: the
*poems* are classical and their authors are centuries dead. Whether **this
compilation of them** may be redistributed is a different question, and it is
the one Ganjoor answers «لزوماً خیر!» to.

It now returns Ganjoor's own answer. The v10 report was rebuilt to carry it —
**not hand-edited**, because it is a generated file and this project has been
bitten by that before. The ingest refuses to overwrite an existing index, which
is the guard doing its job, so the two v10 indices were dropped and rebuilt and
the aliases re-released; dropping an index takes its aliases with it, which is
worth knowing before doing it on anything that matters. All five report figures
came back identical.



**Apache-2.0**, chosen by the project lead. PLAN 8.4 had been blocked on it
since Phase 8 and is closed.

**Picking it took a sentence. The work was the boundary.** A licence file in a
repository is read as covering the repository, and three things travel with
this one that are not ours to give:

| | why not |
|---|---|
| Ganjoor's poetry | they decline to warrant it — see the entry below |
| karbon's lexicon | mounted read-only; karbon's question |
| the expert feedback set | judgements about the language, not software |

`NOTICE` says so for each, and the README carries the same table, because the
failure mode is not somebody reading the licence and getting it wrong — it is
somebody not reading anything and assuming.

**The third one was the near miss.** `tools/export_feedback.py` writes a
manifest beside the records, and while 8.4 was open it said *not yet decided*
with a test asserting no licence name appeared anywhere in it. Closing 8.4
would have made that sentence false, and the obvious repair — deleting it — is
exactly what would have handed the records on by inheritance. **A guard written
to stop us guessing a licence turned into a guard against inheriting one:**
every line in the manifest that names Apache must also say *not*.

**The copyright holder is a project, not a person**, because this repository is
going public and names no individuals — the same rule that keeps roles rather
than names in the docs. It cost nothing to honour and would have been awkward
to undo later.

---

## 2026-08-17 (session 15c) — v10 is out, and Ganjoor says its own data is not copyright-free

### The rebuild, and 3,563 words that were not reachable before

v10 is 9.10's first corpus. The comparison against v9, all five report figures
unmoved because the text has not changed:

| | v9 | v10 | |
|---|---|---|---|
| records | 1,612,406 | 1,852,066 | +239,660 |
| paths | 2,251,023 | 2,796,936 | +545,913 |
| **attested** | **21,134** | **24,697** | **+3,563** |

**The rules that moved are exactly the ones 9.10 unlocked**, which is the check
that matters more than the totals: V-070 to V-076 — the *vā-*, *var-* and
*zir-* prefixes that make a verb out of a past stem — gained **+53,840 records
each**, and V-063 to V-066 between +21,392 and +28,424. Nothing else came close.

**One rule went down, and the drop is the guard working.** V-069 lost 1,739.
V-069 is *vā-* on an infinitive and V-070 to V-073 are *vā-* on a past stem;
the repeated-prefix guard keys on the **affix**, not the rule id, so a branch
that has already taken *vā-* one way cannot take it the other. That is the rule
that stopped *farāzfarāzfarāz-*, doing the same job for *vāvā-*. A dozen other
V-05x rules lost 14 records each for the same reason.

Cost, against the 1.40 predicted: the file went 1.81 GB → 2.13 GB and the
index 1.61 M → 1.85 M records. **Lower than predicted, and the reason is
deduplication** — 1.40 was forms *generated*, and many of the new ones collide
with words already reachable another way. What they add is paths, +545,913 of
them, which is the same word carrying more accounts of itself.

### And the rebuild put the rules screen's own finding out of business

The rules screen exists to show where the grammar's stated strength and the
measured productivity disagree. The source states a strength for **three** rules
— V-010, V-011, V-012, all *typical* — and on v9 all three measured **high**, so
the screen led with the disagreement.

On v10 all three measure **middle**, and agree.

**Not because the evidence improved.** 9.10 gave V-010 8,658 outputs where it
had 3,464, so the same attested count is a smaller share: its realisation fell
from 3.06% to 0.78%. The bands are terciles of all measured rules, and the
tercile boundary fell with it — 1.52% to 0.89%. The rule did not move relative
to its peers on `potential_p` at all: 14th percentile in both. **The agreement
is arithmetic, not corroboration**, and reading it as the grammar being
vindicated would be wrong.

**Two browser tests failed on it, and one of them was passing by accident.**
The layout test asserted the disagreement heading exists — now conditional on
the corpus actually holding a disagreement, because that is a fact about the
data and not about the screen. The accessibility test asked for `/rules?family=G`
and clicked the first *details* button: a glide row has nothing to expand, so
the button it found was in the disagreement section above the list, which
renders affix rules whatever family is chosen. When the disagreement went, an
accessibility check went with it silently. It asks for an affix family now.

### Ganjoor's own answer about its terms, and it is not the one on the tin

The corpus report has said *"public-domain classical texts, compiled by Ganjoor
(confirm terms)"* since v1. Confirmed 2026-08-17, and the parenthesis was right
to be there.

Ganjoor's English introduction says the content "has been made available as a
public domain and open source database". **Its own FAQ says the opposite.**
Question 21 — *آیا داده‌های گنجور از لحاظ حق تألیف آزاد محسوب می‌شوند؟*, are
Ganjoor's data copyright-free — is answered **«لزوماً خیر!»**, *not
necessarily*. The site states it has run no legal review; that most of the
content was typed from published books whose own status was never established;
that editing and compilation can attract rights of their own; and that a reader
**may not infer from free access that a work is out of copyright**, the
responsibility being their own.

**So the answer to "what are Ganjoor's terms" is that Ganjoor declines to say.**
That is a usable answer and better than the assumption: it means the corpus
cannot be republished on the strength of somebody else's licence, and the
password in front of the deployment is not caution but the actual requirement.
The *code* is separable — `GanjoorService`, their own service, is GPL-3.0 — but
the poetry is not covered by it.

---

## 2026-08-17 (session 15b) — the meaning score cannot judge a coined word, and that is not a fault in it

**Three steps are offered on the build screen now** (9.13), and getting there
went through two wrong answers before a right one. The wrong answers are the
finding.

### What was withheld, and why the stated reason was not the real one

The screen capped at two steps, and the note said why: a three-step answer was
24.7 MB. But the route has paged since 6.2, and a page is 275 KB in half a
second. **The size had stopped being the blocker and nobody had gone back to
check.** The real blocker was different and larger: *a page of an unranked list
is a random handful*, and at three steps only **50 of 17,717** words are ones
the corpus has. The ordering is the whole feature.

### Two filters proposed, and both would have hidden the word we built it for

First *show only the words the corpus has* — which hides every new word, and
the project exists to make new words. Then *show only the words whose every
step is written* — which also marks **بازگوینده False, and the corpus contains
it**. A test that hides a word we can prove is real cannot be used to hide
anything.

**The code already said so**, in the ranking's own comment: *sunk, never
hidden — an absent word can still be good Persian the poets never needed.* The
measure was built to push words down and was being proposed as a way to remove
them. The rule is **rank, never filter**, and it was already written down.

### Why the semantic score cannot do this job, measured

A base's vector is the mean of BGE-m3 embeddings of **up to six corpus lines
using the word** — meaning-in-use, which is exactly why the pilot reached 93%
against 33% for chance. A word nobody has written has no lines.

| | |
|---|---|
| bases with a vector | 2,245 |
| rules with a centre | 57 |
| deep words whose **first** step's base has a vector | 17,679 of 17,679 |
| deep words whose **last** step's base has a vector | **2** of 17,679 |

So typicality is measured on the first step alone, deliberately, and **12,999
of a verb's 17,717 forms share 22 values between them**, in ties two thousand
deep. Reordering it above grounding moved *hamandišande* by sixteen places out
of 17,717. **It is not failing; it is staying quiet where it has nothing to go
on**, which is what this project asks every measure to do. Filed as 9.14.

### What could speak, and it was already measured

**How often each rule's output turns out to be a real word.** It is about the
*rules* rather than the words they made, so a coined intermediate costs it
nothing:

| chain | rule 1 | rule 2 | rule 3 |
|---|---|---|---|
| هماندیشنده | **27.8%** | 0.04% | **21.8%** |
| هماندیشیدبانگانه | 0.12% | 0.22% | 0.02% |

*hamandišande* moves from **10,551 of 17,717 to 676**; *vāguyande* from 9,590
to 994. Summarised by the **median**, because on the weakest link the two
chains are within 2× of each other and on the median they are 180× apart — one
weak rule inside a strong chain is ordinary, *ham-* and *-ande* being in the
same word.

**The measurement was run on two verbs before it was believed**, which is the
only reason this third answer stood: the first two were stated before being
checked, and both were wrong.

### And the page size is a measurement too

The band worth reading is the attested words plus the new ones whose every step
is written — **542** for اندیشیدن, **843** for گفتن, **2,183** for رفتن. Six
hundred covered one of three; a thousand covers two, at 2.0 MB and 1.3s against
the 3.94 MB this screen already asks for at two steps. رفتن's band still runs
past it, and the screen says so rather than hiding it.

---

## 2026-08-17 (session 15) — 9.10 was filed as costing thirteen times, and costs 1.4

**Two things done: the prefixed verb finally has its stems (9.10), and the five
questions whose evidence was a paragraph rather than a file now carry the file.**
The theme is the same in both halves — **a number nobody re-ran is a guess**,
and every one of them moved when it was run.

### 9.10 — the estimate was for a different fix

*ham-* on *andišidan* built *hamandišidan* and nothing could be built from it,
because a verb is entered through its two stems and a verb the engine builds has
none. **The fix is one sentence: a prefix is transparent, so a prefixed verb's
stems are the stems underneath with the prefix in front.** *hamandišidan* has
*hamandišid* and *hamandiš*, and *hamandišande* falls straight out.

It could not be done in the engine alone. A present stem is irregular and is
read from the lexicon — nothing derives *andiš* from *andišid* — so the pair is
handed in from `generation.py`, which is the only place that knows it.

**Restricted to prefixes on purpose.** Five rules build an infinitive with a
*suffix* — V-001 to V-005 and V-051, *tars* giving *tarsidan* — and a coined
verb's present stem is written nowhere. Guessing one would be inventing a stem,
so those stay dead ends. That restriction is the whole cost story:

| | filed | measured |
|---|---|---|
| multiplication | ×13 | **×1.40** |
| derivations file | 1.9 GB → ~25 GB | 1.9 GB → **~2.7 GB** |

Measured on 40 real verbs from the snapshot, at depth 2 and depth 3 alike. **The
×13 was an estimate for giving *every* built verb its stems** — which cannot be
implemented at all without a ruling on those present stems. So 9.10 was filed as
a corpus-scale decision and is a bug fix.

**The evidence it is right is a word anybody would recognise**: *bāzguyande*,
بازگوینده, one who retells. Unreachable by any route until now.

**One trap, found by the test failing.** V-005 turns *andišid* into
*andišidan*, which is not a new verb — it is the verb written out in full, and
S-01 states the converse. Treated as new, its stems came back unknown and the
prefix a step later had nothing to land on. Treated as unchanged but re-entered,
the whole family generates twice. It has to be *the same verb, not re-entered*,
which is two lines and neither of them obvious.

### The five questions whose evidence was a sentence

Each of L5, L7, L8, L9 and L12 rested on a measurement described in prose, with
either nothing attached or a hand-typed sample of four rows. **All five were
re-run, and four reproduce their own figures exactly** — which is the argument
for keeping old indices alive:

| | what the question claims | what re-running gives |
|---|---|---|
| **L5** | 3,613 doubted claims | 3,613 |
| **L8** | 28,148 forms, 2,252 attested, largest *Dideé* at 33,599 | all three, exactly |
| **L9** | 0 of 45,579 readings, 0 of 20,263 compounds, 8,116 markers | all three, exactly |
| **L12** | 8 occurrences, 4 poets | 8, and the four are named |

`derivations-v4` is still in Elasticsearch, which is the only reason L8 could be
reproduced rather than re-measured — the two rules it is about have been retired
since, so a fresh run would have built nothing.

**L7 is the one that could not be reproduced, and that is worth more than if it
had.** Its "before" state — the join written *bandehgi* rather than *bandegi* —
exists in no index; v4 already has the fix. So both spellings were rebuilt from
the rule and both put to the corpus, which turned up something the original
measurement did not say: **the rule creates collisions as well as removing
them.** دیه + گر gives دیگر, which occurs 22,212 times and is a different word
entirely. A file that only counted the words gained would have hidden that. It
is now in front of him, in the same column as the gains.

---

## 2026-08-16 (session 14) — one name, and the two places it was not a name

**L11 is settled: karbon's dictionary is «واژه‌نامهٔ کاربن».** The project
lead's call — it is named after the library that holds it. Built the same day
and withdrawn from the question store, which leaves **thirteen open for the
linguist**. What the change turned up is worth more than the name.

### «فرهنگ» was doing three jobs, and only two of them were the same job

The question had been recorded as two: a **label** beside «پیکره» and
«ساخته‌شده», and **prose**. Reading all twenty occurrences found a third, once,
in the gap list: «و فرهنگِ سرواژه‌ها هرگز آنها را در بر نمی‌گرفت» — *and a
dictionary of headwords was never going to list them*. That is not karbon's
dictionary, it is **any** dictionary of headwords, and it is the sentence that
stops a reader taking the 4.1% coverage figure for a quality score.

Renaming it with the rest would have changed the claim: *karbon's dictionary
never lists grammar words* is a much smaller and more accusatory statement than
the one that was there. It stayed «فرهنگ», with a comment beside it saying why.
**A find-and-replace over a name is a find-and-replace over an argument**, and
the twentieth occurrence is where that shows.

### The name is in one file now, and the tests import it

`web/src/text/lexicon.ts` holds the string, the three population labels, and
the four phrases that were already written out twice — «خوانشی در … نیست» and
«از …:» each appeared on two screens, and `POPULATION_LABEL` existed twice in
full, in `WordRow.tsx` and in `Facets.tsx`, which is the drift this prevents.
The Vitest and Playwright suites import the same constants rather than
asserting the Persian, so the next rename is one edit and not a negotiation
with the tests.

### And a collision recorded rather than worked around

**«کاربن» is already the project's term for a verb stem** — کاربن یک، کاربن دو,
in the rule labels the app shows on the same screens. So «واژه‌نامهٔ کاربن» can
be read for a moment as *the dictionary of stems*. It is the library's real
name and the project lead chose it knowing this; it is written down in
DECISIONS and beside the constant, for the linguist to raise or not.

### The 320px suite grew a screen, because the name is three times longer

«واژه‌نامهٔ کاربن» is 15 characters where «فرهنگ» was 5, and it lands in a
heading and in a two-column definition list on `/corpus` — a screen the 320px
suite did not cover, because that suite was written for the four screens with a
text input. Added; it passes. Last session's lesson was that 375px is not
narrow enough, and **the way to keep a lesson is to extend the test the moment
something makes it relevant again**, not when it next breaks.

---

## 2026-08-16 (session 13) — the build was red for two days, and the reason was three things stacked

**Nobody was looking, and that is the finding.** CI had been failing since
2026-08-14. It was three separate faults on top of each other, and the top one
was loud enough that the two underneath it were invisible.

### The one that hid the others

`tests/test_repository.py` errored — not failed, **errored** — on every run.
Its own guard, whose entire job is to skip when git is unavailable, could not
survive a container without git: `check=False` suppresses a non-zero exit, but
a binary that is not on PATH raises `FileNotFoundError` before there is an exit
code to read. The API image has no git.

Seven red tests saying nothing about the repository, for two days. **And a real
failure did hide behind them**: a web typecheck break went up the next day and
the red build looked like the same red build.

### The one that was ours, and the lesson

The typecheck break was verified with the wrong command. `npx tsc --noEmit`
passed while the project's own `npm run typecheck` — which is `tsc -b` — failed,
because build mode reads the project references and sees the test files. In the
same session `ruff check` passed while `ruff format --check` had eight files to
reformat.

**Run `make check-all`. Not a piece of it by hand.** Written into ENGINEERING.

### The one that was a real bug, twice, in the same shape

Four screens pushed the page sideways at phone width. Green on macOS, 43px past
the edge on CI's Linux Chromium, every run.

**A flex item will not shrink below its own content unless it is told to.**

- `.nav` set `overflow-x: auto` so the links would scroll instead of wrapping.
  It never scrolled: as a flex item of `.masthead` its `min-width: auto` kept it
  at content width, so it grew and shoved the page — the one thing the rule
  existed to prevent.
- `.input` is `flex: 1` in a flex row, and an `<input>`'s intrinsic content is
  about twenty characters, so the search box held that width on `/`, `/build`,
  `/compound` and `/explain` — **exactly the four screens that have one**.

It only showed where the default face renders a little wider than it does here.
**The layout suite runs at 375px and that was not narrow enough**; at 320px it
reproduces, the row holding 351px of content in 288px of space. There is now a
test at 320px.

### How it was found, which is the transferable part

By making the failure describe itself, over three rounds.

| round | what the failure said | what it was worth |
|---|---|---|
| 1 | `Expected <= 1, Received 43` | true, unactionable |
| 2 | the widest rectangle past the edge | **wrong** — accused an innocent `li` |
| 3 | the element whose content is wider than itself | `div._row` holds 351px in 288px |

**Round 2 is the interesting one.** In an RTL document that already overflows,
every bounding rect is shifted by the scroll offset, so "past the right edge"
names bystanders — and a fix aimed at the bystander changed nothing. The
question a layout test should ask is not *what sticks out* but *what holds more
than it shows while not being a scroll container*.

### And the questions were rewritten, on the project lead's reading

**One version, in Persian.** The English and Behnevis renderings are gone: a
question shown three ways is three things to keep in step, and two of them were
for us. Each question now runs 1,100–2,100 characters in several paragraphs —
context, measurement, what we did and why, then the question — with every term
explained where it is used and none of the project's own vocabulary used
without saying what it means.

**Seventeen files attached across fourteen questions**, both source documents
as `.docx` and the measurements as CSV. The bytes are held in the row and not
as a path, because a path is a promise about one machine and breaks silently at
the moment somebody is answering.

**Two faults found by using it.** A Persian filename in an HTTP header is a
500, because headers are latin-1 — RFC 5987's `filename*` carries it
percent-encoded. And the screen poured a four-paragraph question into a single
`<p>`, so the paragraph breaks vanished and it came out as a wall. Persian body
text is set justified, does not hyphenate, and wants a measure counted in
something other than `ch` — which is the width of the Latin zero.

---

## 2026-08-15 (session 12) — the loop queue: v9 released, and the pack's own examples became evidence

**Ran PLAN phase 9, tasks 9.1 to 9.5.** 9.1 was finishing a build the last
session had left unreleased; the rest was using the system and fixing what
using it exposed. The theme of the session is that **three separate faults
were found by re-running a tool rather than by reading code**, and the fix in
each case was to make the tool's own output the test.

### 9.1 — v9 is live

The derivations, the corpus report, the productivity file and the typicality
spread had all been built at 22:08 the night before and never released. The
aliases still pointed at v8.

**The comparison before releasing found nothing moved**, which is what it is
for: all five release figures identical, and no rule's output count changed.

| | v8 | v9 |
|---|---|---|
| documents | 133,148 | same |
| tokens | 25,497,189 | same |
| spellings | 409,916 | same |
| spellings_linked | 16,714 | same |
| documents_without_century | 98,627 | same |

**The affixes fix is in v9 and was verified from the data, not from the git
log** — the precompute takes six minutes and its run overlapped the commit, so
the file was checked directly: in the first 400,000 records, **10,289 carry an
`affixes` set strictly larger than their first path's**, and v8 carries **0**.
دندانایی's record now names all seven rules from all four paths, and its
`affixes` is the union `-ā, -i, -nā` instead of one route's.

**The compounding pass had not been re-run** and its figures are not carried
forward: v9's productivity file was the pre-compounding size. Re-run, all
sixteen rules land on the same figures as v8, so nothing moved there either.

### 9.2 — four faults, and one the rebuild uncovered

**A prefix was being stacked on itself, and the corpus settled it.** Cycle
detection keys on (form, rule), and *farāz-* on *andišidan* gives a different
form, so depth 4 built *farāzfarāzfarāzandišidan*. OPEN_QUESTIONS L had asked
whether a prefix may stack and the project's rule is never to guess — so it
was **measured instead**, the way question J was: v9 builds **4,968 words
whose path adds one prefix twice, and not one is attested** in 25,497,189
tokens. The 14 apparent hits are spelling collisions — ننوشت is *na-navešt*,
one negation on a stem beginning with *n*. The guard keys on the **affix**,
not the rule id, because V-059 and V-060 are both *farāz-* and a rule-id guard
would let one follow the other.

**V-052 is a prefix, and correcting it in the obvious place was wrong.** The
source writes `-andar` with the dash on the wrong side, as it did for `-bāž`,
and its example *andarāmadan* puts it in front. But correcting the affix table
moved **N-038 as well**, whose example *Mādarandar* (stepmother) puts the same
letters on the end and is right to. The source itself distinguishes them:
`-andar (darun)` on the verb table, `-andar (nātani)` on the nominal one. **One
spelling, two affixes**, so the ruling is per rule.

**na- and nā- attach to a stem, not to the infinitive.** V-063 to V-066 all
write `attaches_to: Nābesudkārvāže` and are otherwise identical — no tag tells
them apart. Their examples do, and they split two and two:

| | example | base | which stem |
|---|---|---|---|
| V-063 | nasuz | suz | present, of suxtan |
| V-064 | nadid | did | past, of didan |
| V-065 | nāšenās | šenās | present, of šenāxtan |
| V-066 | nāšāyest | šāyest | past, of šāyestan |

Read as the infinitive the engine kept the whole infinitive and called the
result an adjective — *nāhamandišidan*, barnām, which is not a word. This also
explains why the source carries a **pair** for each prefix, which had looked
like duplication.

**The two farāz- rules are not a duplicate, and the recorded fault overstated
it.** It was filed as *identical strings come back twice under two rule ids*.
They do not: deduplication keys on (Latin, word class) and keeps every path,
so the reader gets one word naming both rules. That is the honest answer while
the pack cannot tell *boland* from *bepiš* — L10 again. Pinned with a test.

**A derived infinitive is still never re-stemmed, and the reason it was not
fixed is a number.** V-062 builds *hamandišidan* and nothing can be built from
it, because the system enters a verb through its two stems and a derived
infinitive has none. The fix is to give a prefixed verb its prefixed stems,
and it **multiplies the generation by 13** — one verb goes from 24,027 forms
at depth 3 to ~312,000, and the 1.9 GB derivations file to roughly 25 GB. That
is a corpus-scale decision, not a bug fix. Left filed with the measurement.

### The one nobody was looking for: the rule pack is generated, and three rulings were not

Rebuilding the pack to correct V-052 **silently reverted three earlier
decisions**, because they had been edited straight into the generated files:
N-090 (the ezāfe) and N-099 (the indefinite enclitic) came back **active**,
and V-021's Persian pattern lost its negation again. The builder's own
`JOINER_FA` still said `na → ن` while the committed file had been hand-fixed
to `نا`.

**This is the same failure as a pipeline that is reproducible in principle and
not in practice.** Nothing errors; the next person to run the tool undoes a
decision and is not told. `rules/decisions.yaml` already existed for exactly
this and was only being applied to glides and stem forms. It now covers
verb and nominal rules too, and `tests/test_rule_pack_build.py` asserts the
committed pack **is** what the builder writes.

### 9.3 — running the rules forward turned 75 open questions into 4 answers

`tools/check_examples.py` reported *75 examples do not rebuild* and nothing
more, so every one of them read as though the engine might be at fault. Its
own docstring had promised to record what the engine built from the same base
and never did. **That is the whole of 9.3**, and it changes what the number
means:

| | |
|---|---|
| the base is not in the lexicon | **22** — UPSTREAM B2 |
| the two spell the same word differently | **21** — the linguist's, L13 |
| the lexicon has the base in another word class | **15** — the category map, PLAN 3.2 |
| the example does not use the affix its rule declares | **5** |
| **the engine builds a different word** | **0** |

**It was 7 before the session ended.** V-070 to V-076 take a past stem and say
they produce an infinitive — *goft* gives *vāgoftan* — and the prefix alone
left *vāgoft*, a stem wearing the label of an infinitive. All **seventeen**
examples those seven rules carry end in *-an*, and stem rule S-01 states the
converse: taking *-an* off any infinitive leaves kārbon-e yek.

**Examples explained by their own rule went 88 → 100 of 163**, in two steps:
the V-052 and na- rulings were worth five (and N-022 improved with them), the
infinitive ending another seven. **The rulings were made without looking at
the examples**, so this is the pack checking them rather than agreeing.

**Two things had to be got right before the piles meant anything.** Stripping
a prefix leaves a lower-case letter where the lexicon holds a capital — *kenār*
against *Kenār* — so case is tried before anything else. And a consonant
skeleton is a weak match on a short base: *div* finds *Dāv*, a different word.
A spelling disagreement is now claimed **only when the rule goes on to build
the expected word bar its vowels**, which is evidence rather than resemblance.

### And a fault in our own lookup, found while sorting those piles

**7,106 readings the dictionary records cannot be looked up.** `by_latin`
matches the `phonemic` column only, and a second reading lives in
`phonemic_variants`. کنار is *Kanār* **or** *Kenār*; asking for *Kenār*
returns nothing. Of 44,788 readings, 7,181 carry a second reading and
**7,106 of those second readings no Latin lookup can find**.

Question P established that generation builds from every reading. **Lookup was
never given the same treatment**, so a user typing a reading karbon itself
records gets a 404. Not fixed here: it changes what every route returns, and
that is the project lead's call. It also means the *base is not in the
lexicon* pile above is an **upper bound** — some of those bases are held under
a variant spelling.

### And then three decisions, taken and built the same day

**The gap list is restricted to what our rules can build (S23).** Chosen over a
function-word list, and it is the better answer for a reason beyond the count:
nothing has to be maintained. و is not built from anything, so the ~100 function
words B3 names drop out on their own. **344,081 becomes 4,519**, short words
fall from 5,681 to 99, and every row carries the rules and affixes that form it.
The head of the list is ناله, اندیشه, خنده, **زندگی**, پادشاه — and زندگی
("life"), پادشاه ("king"), اندیشه and خنده were each checked by hand and are
genuinely absent from the lexicon. The cost is stated: a borrowed word has no
Persian derivation, so کتاب is missing from this list too.

**Lookup now matches every reading the dictionary records (S22).** Approved the
day it was found. All 7,106 are reachable; the risk was measured before the
change, not after — 8 collisions in 8,218, and all eight are the same word
spelled two ways.

**And the fix had the same fault inside it.** The first attempt matched
case-blind in SQL, and **SQLite's `lower()` is ASCII only**: it leaves *Ā*
alone, so `Ābrov` never matched the stored `ābrov` and every reading beginning
with a long vowel stayed unreachable. Caught by testing the repair against the
example that had motivated it. The lower-casing is Python's.

**The linguist answers in the app, and the app is the record.** Separate from
expert review, on the project lead's word. Two tables hold the questions and the
rulings, the rulings are append-only behind a Postgres trigger, and
`docs/FOR_THE_LINGUIST.md` becomes an export. All 15 questions were seeded out
of it.

**A third role was built for it and removed the next day, and that is the
finding.** The case for splitting *ruling* from *grading* is sound on paper —
a verdict is evidence, a ruling is authority, and with one role any expert can
overwrite a ruling. It still did not survive one question from the project lead:
**the expert is the linguist**. A distinction that is true but names the same
person twice is a distinction that costs a role, a permission check, a migration
and a paragraph of explanation and buys nothing. Removed before anything was
committed, so the migration does not touch `users` at all.

**karbon's maintainer gets no role either, and the reason is not symmetry.**
They never sign in: feedback about the lexicon is tagged `owner: karbon` on the
way in and leaves as an export, to be opened as an issue on their own tracker.
karbon has a repository where an answer belongs next to the code it is about.
**The linguist has neither** — which is the whole and only reason the app grew a
place for him to answer.

**What seeding deliberately could not do.** The document is English and he works
in Persian. Translating each question automatically on the way in would have
made our English the original — the exact failure the change exists to fix — so
every seeded question carries the English title, is marked ⚠, and counted at the
top of the export. **Which is why the document has not been switched over yet**:
until the Persian is written the export is a worse file than the one it would
replace, and swapping it now would have been the change on paper rather than in
fact.

### 9.4 and 9.5

**The gap list cleans to 344,081 from 392,120**, reproducing B2b's figures
exactly — 48,039 inflections out, 11.7%. `tools/clean_gap_list.py` drops a row
only where the pattern that recognised it has been measured, on karbon's own
headwords, to be wrong rarely enough to act on; the ceiling is a flag and the
tool prints what other ceilings would have cost. **It is still not sendable**,
and the reason is B3 rather than inflection: **60 of the 100 biggest surviving
gaps are three characters or fewer** — و, ز, آن, او, چون — and single letters
alone carry 15.6% of the kept occurrences.

**`/compound` pages.** It took a `limit` and no `offset`, so everything past
the limit was unreachable by any request; it now carries the same three fields
as `/generate` and walks all 4,652 pairings of مرد without a gap or a repeat.

---

## 2026-08-14 (session 11) — corpus v8 is live, the wrong forms are gone, and comparing two versions found a second silent failure

**The session was track A**, and it was execution rather than design: build v8,
get the infix forms out, and show that nothing else moved. It did both, and
the comparison it needed turned up something nobody was looking for.

### What went, exactly

`session-10-semantic-label` was merged into main first (15 commits,
fast-forward, `make check` green before and after), so the engine that built
v8 is the one that no longer applies `infix`.

| derivations | v7 | v8 | moved |
|---|---|---|---|
| records | 1,704,021 | 1,612,406 | **−91,615** |
| paths behind them | 2,371,799 | 2,251,023 | −120,776 |
| attested built forms | 22,118 | 21,134 | −984 |

**112,502 records were touched and 91,615 of them disappeared.** The other
20,887 are forms the engine still builds another way and which lost only their
infix path — they stay, with one fewer derivation. *rāyānnāknā* — رایانناکنا,
دل + نا on the wrong end — is gone, and the app answers 404 for it.

**The two rules now build nothing**: N-020 and N-023 each fell from 57,856
forms to 0, and each carries `unmeasurable_reason: "compounding by infix: not
built (PLAN 2.3)"` instead of a middle band. Both figures are served and both
were checked on the running API.

**The docs' 115,682 was measured off `rule_chain` and the true figure is
115,712** — 57,856 + 57,856 rather than 57,856 + 57,826. Why, below.

### And nothing else moved, which is a measurement rather than an impression

Every record in v7 was matched against v8 by id and its set of paths compared —
`tools/compare_versions.py --attributable-to N-020 N-023`, which is repeatable
from the two `.jsonl` files and prints exactly this:

| | |
|---|---|
| unchanged | 1,591,519 |
| gone, **every** path an infix path | 91,615 |
| gone for any other reason | **0** |
| kept, lost only infix paths | 20,887 |
| kept, lost a path that was not infix | **0** |
| gained a path, or newly appeared | **0** |

The five release figures are identical across the two corpus reports —
133,148 documents, 25,497,189 tokens, 409,916 spellings, 16,714 linked, 98,627
undated — which is what a rebuild on unchanged text should give.

**The semantic spread did not move either**, which was not obvious in advance:
27,713 scored forms went and the distribution stayed where it was. Lowest
0.5541, median 0.8283 and highest 0.9144 are identical to four places, and the
four band boundaries moved by at most 0.0003. So the removed forms were spread
through the distribution like everything else, and no word's band changed
because its neighbours left.

### One rule other than the two changed band, and it is a correction

**N-033 fell from `high` to `middle`.** Its attested output went 401 → 342 and
its built types 27,361 → 24,153, because part of what it was credited with was
built on top of an infix step — a real word standing on a form the engine
should never have made. Twenty-seven other rules lost forms the same way and
none of them changed band.

**A rule's productivity is measured over the whole chain, so a wrong rule pays
its neighbours.** This is the part of the fault that was invisible while only
N-020 and N-023 were being looked at.

### The second failure, which the comparison found and nothing else would have

**`word_types-v6` and `word_types-v7` carry zero rule claims.** Counted on the
field itself:

| version | corpus word types traced to a rule |
|---|---|
| v4 | 1,415 |
| v6 | **0** |
| v7 | **0** |
| v8 | 1,435 |

Both were built without `--affix-map` and both were released. **It does not
fail** — the index builds, the app starts, every screen renders — and the only
symptom is that `rule:` search answers nothing, so a rule that formed a hundred
corpus words looks exactly like one that formed none. On v8, `rule:N-088`
returns 75 word types; on v7 it returned nothing, and had since v6.

**The cause is in our own documentation.** ENGINEERING listed the ingest
*before* the precompute, and the ingest takes the precompute's affix map — so
anybody following the written procedure had nothing to pass. The order is now
right, the whole v8 run is written down step by step, and `run_ingest.py` says
out loud when no map was given, exactly as it already did for the century
table.

**This is the third instance of one shape**: an optional input that is silently
absent, a build that succeeds, and one feature quietly dark. Centuries in v6,
the affix map in v6 and v7, and — differently — `infix` in `SUPPORTED` with no
branch to implement it. The remedy each time was the same and it is not more
tests: **put the new version beside the old one and read the difference.**
`tools/compare_versions.py` now does that, and reproduces the v6 century
failure from its own fixtures.

### `rule_chain` carries the first path alone

Found while measuring the fault, and worth its own line because it silently
understates every count taken from it:

| | |
|---|---|
| records reached more than one way | 437,202 |
| records whose `rule_chain` is smaller than their paths | **342,511 — 20.1%** |
| of those, `rule_chain` is exactly the first path | 342,511 — all of them |

دندانایی is reached five ways — V-024+V-025, V-024+V-030, V-026+V-027,
N-023+N-095 and N-072+N-095 — and `rule_chain` names the first pair only. So
a filter on `rule_chain` misses four rules that genuinely built the word, and
that is why the index reported 57,826 forms for N-023 where the file has
57,856.

**Deliberately not changed in v8.** Fixing it would have altered the index's
shape in the same build that removed the infix forms, and then "nothing else
moved" could not have been tested. Recorded as **S19**.

### The repository was carrying SQLite's scratch files

Noticed while checking which files under `data/` are committed, and it is the
paperwork half of S9.

`data/*.sqlite` is ignored, correctly — the snapshot is 29 MB and comes from
karbon. But **`lexicon-20260808.sqlite-shm` (32 KB) and
`lexicon-20260808.sqlite-wal` (0 bytes) were tracked**, and had been for
months. They are SQLite's own sidecars: the write-ahead log and the
shared-memory index that goes with it. They mean nothing without the database
beside them, so **a fresh clone got a stale write-ahead log next to a database
it did not have.**

**It was an accident, not a workaround, and that was worth checking before
removing them.** A committed `-shm` would be one way to let a read-only
container open a WAL database it cannot create the sidecar for — which is
exactly the bind S9 describes. It is not what happened: the two files were
added by `git add -A` inside three commits about entirely different things
(*Generate from a real Persian word, end to end*, *Keep and generate from the
second reading the lexicon records*, *Check generated words against the corpus
at three levels of evidence*), and they were added, dropped and re-added as
processes opened and closed the database. Nothing in the codebase reads either
one; the only mentions anywhere are the prose in S9 and this file.

Untracked with `git rm --cached`, which leaves both on disk, and `data/*.sqlite-*`
now ignores them along with any `-journal`. The running API still answers
`/generate` afterwards, checked rather than assumed.

**What this does not fix is S9 itself.** The snapshot is still in WAL mode,
`./data` is still mounted read-only, and a read-only reader still cannot create
a `-shm` it does not find. What changed is that the repository no longer ships
one and no longer pretends to.

### Four routes, and what building them found

Built after the corpus work, on the project lead's pick of the four items that
need no linguistic ruling. Each is its own commit and each was called on the
running app after a container rebuild.

**Compounding reaches a reader for the first time (S18).** Sixteen rules have
licensed it since the transcription and nothing had ever called them.
`/compound` joins the caller's word to every verb stem — a **sum** over 1,741
verbs rather than a product over the dictionary — and answers with the
attested pairings ranked and the count of the rest beside them.

| دل, first reading | |
|---|---|
| compounds built | **4,652** |
| the corpus has | **220** — 4.7% |
| verbs offered | 1,741 |

The list opens on دلبر (2,920 poems), دلدار (1,722), دلکش (672), دلستان (450)
— which are the words the session-10 measurement named, now produced by the
system rather than by hand.

**Two faults the live data caught that the fixture could not.** The corpus
answers for *every* spelling it is asked about and says `none` where it has
nothing, so filtering on "an answer came back" counted all 4,652 as attested —
the first run reported 5,223 of 5,223. And two verbs sharing a stem spelling
each produced an identical row. Both now have a test.

**And one design correction, made against the data rather than in advance.**
The first version sank any pairing the dictionary already holds, on the
session-9 rule that a count belonging to another word may not rank a form.
That rule is about **homographs** — روی read as *Rui* — and دلبر is not one:
the dictionary holds it and it *is* دل + بر, the same word by both routes. It
now leads the list and carries `already_a_word`, which is what a coiner wants
to know. **Only an inflection reading sinks a row**: دلم has 12,947 documents,
is دل plus a possessive, and sits at **162 of 220** with the reason on it.

**سخن builds nothing, and that is the mapping rather than a bug.** It is filed
اسم معنی → `karnam`, and the slot rules take a `nām`. The session-10 figure of
3,071 compounds for one noun was measured by constructing the word by hand and
bypassing the category mapping, so **the route is stricter than the
measurement that justified it**. Which is right is a question about اسم معنی,
and it is already open as UPSTREAM A6.

**`/generate` is usable from outside (S1).** It had no page, no limit and no
projection, and بلند at depth 2 is 2,856 forms and 3.94 MB. `limit` defaults
to 200 a reading, `offset` walks them, `limit=0` returns the lot — and the
default answer is now **450 KB against 3.65 MB**. Every reading says its
total, what came back, from where, and whether more remain, so a count can
never shrink with the page and look like a small answer.

`worded=false` drops each step's Persian label and explanation and keeps the
derivation: **43% of the bytes**, because 8,731 steps repeat sentences that
belong to the rule. The derivation itself is never optional — that is settled
from the *sāzāyi* incident — so what a caller may drop is the wording alone.
The build screen asks for `limit=0` deliberately: it groups by word class and
must count every form to say what each group folds.

**`/rules/{id}` no longer serves less than `/rules` (S17).** The detail route
carried the pack's description and none of the measurement, so a rule that
deliberately builds nothing looked exactly like one nobody had measured — this
session's own N-020 read that way. Pinned by a test asserting the detail is a
**superset** of the list row, so a field added to one cannot go missing from
the other.

**`/health` reads a row (half of S9).** It returned a hardcoded `ok`, which is
why it reported a well service through a walkthrough in which every build
answered 500. It now opens the lexicon, counts, pings the cluster, names
whichever half is down and answers 503. The container healthcheck already
honoured the status. The other half of S9 — opening the snapshot `immutable=1`
— is untouched.

### The coining experiment, run a third time — and the walls it hit are new ones

Re-run once the compounding route existed, with the same four questions as
session 10 so the numbers compare: the longest meaningful word, three
renderings each of *Dasein* and *Geworfenheit*, and a word holding two
contradictory words. The protocol added one rule: **verify every proposal**,
through `/explain` for an affix word and `/compound?word=&partner=` for a
compound.

| | first run | second | **third** |
|---|---|---|---|
| proposals the system could reproduce | 3 of 8 | 6 of 8 | **12 of 12** |

**And the rate is the least interesting number in the table**, because the
model itself said why: for the seven compounds, "verified" means *the same
builder produced the form a second time*. `/explain` still takes no compound
and no Persian script, so half the words have no independent parse. It
reported that unprompted, which is the behaviour that makes the experiment
worth running at all.

**Every checkable claim it made was checked and every one was exact.**
افکندگی at 35 occurrences, 34 documents, 19 authors, 12th–18th century;
90 of 195 non-glide rules carrying no semantic tag; V-052 filed `kind:
suffix` with a prefix for its example. No invented numbers.

### Three faults in the route built this morning, all found by using it

Each was reproduced by hand before being touched, and each now has a test.

**Naming a partner lost the templates.** `/compound?word=بودن` gave
*Budonabud*; `?word=بودن&partner=بودن` gave **nothing**. The two words were
being joined as plain words and a template needs whole verbs.

**The four two-verb rules could not fire at all.** V-017, V-019, V-043 and
V-047 join two *different* verbs — *Zadoxord*, *Xordoxāb*, *Suzogodāz*,
*Rixtopāš* — and every route offered a partner as a plain word, so nothing
ever reached them. `زادن + مردن` now builds **زادومرد** (V-017) and زادومیر
(V-019, V-047), which is the word the model asked for and could not get.

**A template named the wrong half.** V-021's second slot is the same verb's
**past** stem, negated; the route reported the present stem for every
template, so *دیدونادید* was published as دید joined to **بین**. The engine
knew and was never asked: `parts_used` now says which word filled each slot,
and the route quotes it.

### And a promise in our own test suite that was never kept

`tests/test_golden_examples.py` says in its own docstring: *"Until the engine
exists (PLAN 2.1) these check the **shape** of every example… When the engine
lands, `expected` becomes what it must produce."* **The engine landed and that
never happened.** The examples are still checked for shape alone.

The model measured the gap: it put the first example of all 165 prefix and
suffix rules through `/explain` at depth 3 and **88 came back explained by the
rule that lists them, 77 did not**. Some of that is a vowel convention rather
than a build fault — N-004's `bexrad` fails while the system builds `bexerad`
from the lexicon's `Xerad` — which is exactly why it is a question and not a
bug list. Recorded as **S20**; the figure wants re-measuring by us before it
is quoted anywhere.

### The wall is still L10, and it is now the only one

The model could not ask what any of it *means*. `meaning_fa` is null on every
form it built; `definition_fa` is null on the entries it started from; and
**all three compounding rules its answers rest on — V-016, V-021, N-104 —
carry no semantic tag at all**. Its own words for it: *«`Jābud` is a guess
about the rule's semantics, dressed as a build.»*

**And form-only verification produces confident nonsense**, which is the
sharpest thing the run found. `/explain?word=Nāxodāgāhi` returns
`explained: true` with the base **ناخدا** — a ship's captain — plus N-068 and
N-095. `/explain?word=Hamzamāni` returns base `Zam`. The route is doing what
it says it does, and a caller that reads `explained: true` as *this word means
what you think* will be wrong. Recorded as **S21**.

### The four loose ends, closed

**The compounding rules have figures for the first time.** They reported zero
for as long as they existed, and the main pass could never have measured them:
it counts what the precompute built, and a slot rule's output is a product —
20,879 nouns against 1,696 verbs. A second bounded pass measures them and
writes into the same file.

| | built | attested | rate |
|---|---|---|---|
| V-078 / V-079 — *Nām-* + present stem | 28,896,536 | **26,361** | 0.091% |
| V-016 — *Nām-* + past stem | 35,369,026 | 3,632 | 0.010% |
| V-080 / V-081 — *Čonvāže-* + present stem | 18,749,048 | 7,931 | 0.042% |
| V-044 — *kešākeš* | **1,696** | 68 | **4.009%** |
| V-021 — *bud-o-nabud* | 1,696 | **0** | 0.000% |

**V-044 is the most productive rule in the pack by realisation rate and the
smallest by output**, which is the shape every measure in this project keeps
finding: the big producers are the least confirmed. And **V-021 has no corpus
support at all** — a result, not a gap. The poems write بود و نابود as two
words, so a joined spelling is not there to find.

**Compounds are on a screen.** The list opens at twenty and says what it
folds, the three counts sit above it, and a row that also reads as an
inflection carries the reason. دل's four readings each fold 80 rows. The
Persian on the screen is written here rather than taken from the pack — as on
the other six screens — and wants a native reading.

**The lexicon opens `immutable=1`**, which closes S9, with a fallback to
`mode=ro` whenever a non-empty `-wal` says the promise would be false.

**`rule_chain` is now the union of every path.** Settled rather than asked,
because the field turned out to have no reader at all: `/search` queries
`word_types`, the affix map reads `paths`, and the build screen composes its
own chain. It takes effect at the next corpus version — rebuilding 1.6 million
records to correct a field nothing reads was not worth the compute.

### And the examples, re-measured by us

The run's 88 of 165 was close and the shape was different. On 163 active
prefix and suffix rules at depth 3, against the real snapshot:

| | | |
|---|---|---|
| explained by its own rule | **88** | 54.0% |
| not rebuilt at all | 61 | 37.4% |
| rebuilt, but by **another** rule | **14** | 8.6% |

That third pile is the one worth having and the run did not separate it: the
word rebuilds, just not through the rule that claims it. The 88 are now
pinned by a test and may grow but never shrink.

### What was not touched

The word-formation rules, the ranking on the build screen, and the pack faults
the run surfaced — V-052 filed as a suffix, prefix stacking unbounded, a
derived infinitive never re-stemmed. Each is a rule question rather than a code
one. The compound screen was checked by the browser tests at 375 px and at
desktop width and **not looked at by eye**: the preview tool was unavailable. `data/corpus_report-v8.json`, `data/typicality-v8.json`
and `data/rule_productivity-v8.json` are the artefacts the app now points at;
v4, v5, v6 and v7 indices are all still queryable and none was dropped, which
stays a deliberate act somebody performs.

---

## 2026-08-13 (session 10) — measured the inflection half of S8, and it does not fall to a rule

**The session was track B: measure before designing.** Two rulings arrived
from the project lead mid-session and a third question opened; all four are
below, with the numbers each rests on.

### How much of the corpus is inflection, and of what

The instrument reads a corpus spelling against what the lexicon holds and
reports which inflectional pattern would produce it —
`src/murfulu/corpus/inflection.py`, run by `tools/measure_inflection.py`.
It decides nothing: a spelling the lexicon already holds is **never** called
an inflection, and a pattern whose letters a derivational rule in the pack
also writes is reported `shared` and counted apart.

All 409,916 distinct spellings, against 43,225 headwords, 1,705 past stems
and 1,387 present stems:

| | spellings | share | occurrences | share |
|---|---|---|---|---|
| the lexicon has a reading | 16,714 | 4.1% | 11,644,767 | **45.7%** |
| a verb stem we hold | 1,082 | 0.3% | 1,491,886 | 5.9% |
| inflection, no rule writes it | 28,038 | 6.8% | 1,673,185 | 6.6% |
| inflection, a rule writes it too | 20,001 | 4.9% | 1,538,017 | 6.0% |
| unaccounted for | 344,081 | **83.9%** | 9,149,334 | 35.9% |

**The first row is the one to hold on to.** We hold a reading for 4.1% of the
corpus's spellings and those 4.1% are 45.7% of everything ever written. The
long tail is real and it is mostly not ours.

### But the corpus is the wrong denominator, and the right one is worse

Only an **attested** form carries a number, and only an attested form is
ranked on one. Against derivations-v5's 22,118 attested built forms
(`tools/measure_built_inflection.py`):

| | forms | reads as inflection | share |
|---|---|---|---|
| every attested built form | 22,118 | 7,047 | 31.9% |
| of them, `unlinked` | 17,071 | **7,047** | **41.3%** |
| of them, the lexicon knows the spelling | 5,047 | 0 | 0.0% |

**The last row is true by construction and is not a finding** — a spelling the
lexicon holds is never called an inflection, and `unlinked` means it does not
hold it. Stated because a 0.0% that looks like a result and is really a
definition is exactly the kind of number this project keeps catching.

What it does establish: the whole of the problem sits in the half S8 named,
and those 7,047 forms carry **1,080,260 of the 2,589,413 documents the
unlinked half rests on — 41.7%**.

### And then the finding that decides the design

**6,730 of the 7,047 — 95.5% — are `shared`.** A derivational rule in the pack
writes the same letters. آبادانی is the indefinite of آبادان *and* the noun
"prosperity"; کشی is a clitic form *and* a word; گسترده is a past participle
*and* an adjective; ریختنی is an infinitive plus -i, which is word formation.

**So S8's remaining half does not fall to a rule over spellings.** A condition
that demoted every inflection-shaped form would demote 95.5% of them on a
coin-flip, and the 4.5% left is not worth a mechanism. This is now a question
about *which* patterns, not *whether*.

### The control, which is why any of the above is usable

Every lexicon headword is a word by definition. So the share of them the
analyser reads as an inflection anyway is its own error rate, measured with no
judgement about Persian in it: **3,262 of 43,225 — 7.5%** — and it is very
unevenly spread.

| pattern | corpus hits | known words it also claims |
|---|---|---|
| `‌های` / `های` plural | 1,591 | **0.0%** |
| `‌ها` plural | 1,079 | 0.3% |
| `شان` possessive | 1,072 | 0.9% |
| `ها` plural | 1,483 | 1.1% |
| `تر` comparative | 696 | 4.1% |
| `ی` indefinite | 6,874 | 10.4% |
| `ان` plural | 2,966 | 13.9% |
| `ین` Arabic plural | 681 | 17.6% |
| `ا` vocative | 1,757 | 18.2% |
| `ون` Arabic plural | 482 | **20.2%** |

**The patterns are not one thing.** The ha-plurals are all but exact. The
Arabic plurals and the vocative are noise — reading the sample by eye,
*تافتون* is a bread and not a plural of تافت, and *کتمت* is Arabic. **The
sample is what caught that**, before the number was written anywhere: the
first run printed thirty analyses and four of them were wrong in the same way.

**Nothing was built on any of this.** What a ranking should do with a pattern
at 0.3% and one at 20.2% is the project lead's, and the weighting proper is
still S6's.

### Reading it back: why سربلندی kept coming out wrong

Asked a third time why the screen writes *Sarbalandi*, and the answer was
neither of the two things already fixed.

بلند has two readings and **they were coming out in the lexicon's row order**,
which is arbitrary:

| reading | class | the dictionary's own flag | confidence |
|---|---|---|---|
| `Baland` | اسم ذات | **`needs_review`** | 0.4 |
| `boland` | صفت | clean | 1.0 |

The flagged one is written first, so the screen opened on it — and the same
snapshot spells سربلند `sarboland`, so it contradicted itself on one screen.
Readings now sort on the dictionary's own flag, then on its own confidence.
Confirmed through the running API: بلند opens on `boland`, and the sar- forms
read `SarBolandā`, `SarBolande` where they read `SarBaland…` before.

**It is an order and not a filter.** Both readings are returned, both are
built from — `Baland` still builds its 65 forms at depth 1 against `boland`'s
22 — and the flagged one is one press away. Which reading is *right* is still
the linguist's. This answers S13.

### Two rulings from the project lead, both unconfirmed by the linguist

**The ezāfe and the indefinite -i stay retired (L8).** He has not put it to the
linguist and does not want it holding anything up: he expects the same answer,
that these are not word-formation rules. They may earn a place for another
purpose; not for building a new word.

**A prefix keeps the base's capital (L9) — session 9b is reversed.** سربلند is
*SarBaland* again. His reason is that the capital is doing work for the
reader: it says the part inside is a noun, which is what a capital does in
Behnevis everywhere else, and the source keeps it in *Došnām* (N-010). Still
one line either way, and the source's other examples are flat.

**Neither has been ruled on.** Both are recorded in FOR_THE_LINGUIST as a
position rather than as an absence, which is the difference from yesterday.

### A built word almost never says what it means

He asked whether the sources even give us the meanings, and said the sensible
thing is to build the words we can give a meaning to. Measured:

| | |
|---|---|
| active rules | 193 |
| naming a semantic tag | 103 |
| naming **no** tag at all | **90** |
| tags with a gloss word | **43 of 43** |
| tags with a gloss **template** | **1 of 43** |
| built forms in v5 carrying a meaning | 70,370 of 1,704,021 — **4.1%** |
| **attested** built forms carrying a meaning | 407 of 22,118 — **1.8%** |

So the sources give half of it: every tag has a gloss *word*, and one tag has
the *sentence*.

**And authoring the other 42 sentences would not fix it**, which is the part
worth the linguist's time rather than his labour. A template hangs on the
**tag**, and a tag is shared by rules that do not mean the same thing:
`Nesbat` covers **19** rules, `Mānand` 12, `Dāštan` 11, `Jā` five. The index
shows the cost of the one template that exists — **آبادانیدگان،
آبادانیدهدان، آبادانیدهستان، آبادانیدهکده and آبادانیدگاه all carry the
identical sentence «جایی که آبادانیده در آن است»**. Five affixes, one meaning,
when نمکدان is a container and گلستان is a land and میکده is a house.

**And N-068 (-gāh) is tagged `Jā` and `Zamān` at once**, so a word that may be
a time is told it is a place. Three rules in the whole pack name two tags and
the first template met wins.

Put to the linguist as **L10**: does the sentence belong to the tag — 43,
coarse — or to the rule — 193, exact? And are the 90 untagged rules missing a
tag, or do they carry no meaning a template could state?

### The experiment run again, and the worst fault of the session

The same four questions, the same routes, after three changes: `/explain`
refuses Persian script instead of answering nothing, `/rules` serves a
compounding rule's `pattern` and `slots`, and V-021's Persian is fixed. One
protocol change too — **the model was told to call `/explain` on its own
proposals and report honestly whether each rebuilds**.

| | first run | second |
|---|---|---|
| proposals the engine can rebuild | **3 of 8** | **6 of 8** |

And the two failures were reported rather than dropped, which is what makes
the output usable at all.

**Two process notes, because both were nearly repeats of earlier mistakes.**
The api container had never been rebuilt after the `pattern`/`slots` commit,
so the first relaunch was testing the old API — caught after one message,
stopped, rebuilt, verified, relaunched. And the run before that **stalled
outright** on an unfiltered `/generate` at depth 2; the second prompt carries
a hard rule about filtering, so it is not a byte-identical rerun.

### `infix` was in the engine's supported set with no branch for it

**The worst thing found today, and it was found by using the system rather
than testing it.** N-020 and N-023 are `kind: infix`. The engine's `apply`
has a branch for `none` and one for `prefix`, and everything else falls to
the suffix case — so both rules put their affix on the **end**.

| | |
|---|---|
| the source writes | `-nā-`, a dash on **both** sides |
| its own example | **دل + نا + چسب** — *delnāčasb* |
| the engine built | **چسبنا** — *časbnā* |
| types built, each rule | **27,361** |
| forms in the live index | **115,682** |
| how they were reported | band **middle**, as though measured |

**An infix sits between two words**, so it needs a second word exactly as a
slot does: these are compounding rules wearing another name, and they belong
with PLAN 2.3. `infix` is out of `SUPPORTED` — they build nothing now, which
is this project's rule everywhere else, and 115,682 wrong forms leave at the
next corpus version.

**Nothing caught this.** Both suites pass with the bug in place; the rules
screen showed the two at middle-band productivity; the precompute counted
them. The only thing that found it was somebody trying to make a word with a
rule that had a dash on both sides of its affix.

### And `/explain` was answering a typo with a dead end

*budmān* returned nothing and *Budmān* returned a clean account. **Case is
meaning in Behnevis** — the two are different words and must never be merged —
but an empty answer is indistinguishable from *this word cannot be built*, and
the model recorded about ten false negatives before working it out. The answer
now carries `built_in_another_case`, filled only where nothing rebuilt the word
as written.

### And one fault found by looking at the stack rather than the app

`docker compose ps` had **`web` unhealthy** and had had for two hours, while
the site answered 200 on every request. The healthcheck asks for
`http://localhost/`; inside that image `localhost` resolves to **`::1` alone**
and nginx's `listen 80` binds IPv4, so it was refused every ten seconds — a
failing streak of **702** by the time anyone read it. `wget http://127.0.0.1/`
from inside the same container succeeds.

**It is not only a wrong word in a status column.** `web` is a `depends_on`
target with `condition: service_healthy`, so anything added downstream of it
would never have started, and the cause would have looked like the new service.
And it is the exact mirror of the trap already in the notes — `/health` going
on saying 200 while every request failed. **A health signal that is wrong in
either direction is not a health signal**, and this one had been wrong since
the container was written.

### برنا: we had the pronunciation and threw it away

The project lead read `barnā` on the search screen and said it sounds like
*bornā* in the poems. **The lexicon holds both.** برنا is `barnā` with
`bornā` listed as a variant, clean, at confidence 1.0 — no flag, no doubt.

**7,181 of 44,788 readings — 16.0% — carry a second pronunciation**, and no
screen anywhere showed one. `/generate` had been sending `latin_variants` all
along and `web/src/api/generate.ts` even declared the field; nothing rendered
it. The build screen shows it now. The search screen and the word page could
not: `word_types` had **no field for a variant at all**, so that half needs a
new corpus version.

**This is the third time the same shape has been caught in two days** — the
`needs_review` flag (read, stored, not served), the retired rule's reason
(written in the pack, dropped on load), and now the variant. Each was data
that existed, travelled most of the way, and died one step from the screen.

### And so: what else of karbon's do we not use?

Asked for by the project lead — *make sure this does not happen again*. Built
as `tools/audit_lexicon_use.py` rather than answered once, because a column
added upstream is unused by default and the next snapshot will have the same
problem otherwise.

**12 of karbon's 27 columns reach nothing of ours.** The full table is in
UPSTREAM B5. What matters here is that two of them bear on questions already
open, and one bears on a ruling made an hour earlier.

**`definition_preview`, 96.1% full — Dehkhoda's own definition.** The project
lead had just asked whether we have meanings at all, and the answer measured
then was 1.8% of attested built forms. That was the right answer about *built*
words and it missed this: we can say what a **base** word means for 43,816 of
45,579 rows. Different thing, and it may be the more useful one.

**`stem_group`, and it narrows L2.** L2 has been open since session 3: which
of karbon's numbered groups are NKZ and NKDZ? The column was there the whole
time. Groups hold **1,547, 10 and 168** verbs. Group 2 holding ten of them
means the NKZ/NKDZ split is almost certainly not groups 1 and 2 — which does
not answer L2 but does stop a guess being made in the wrong direction.

**`notes`, and it finds something karbon's own flag misses.** karbon marks
**335 rows `[v7:badbracket]`** — it knows the Dehkhoda bracket it read was not
diacritics. Those brackets hold `دریای چین`, `هری`, `مرا`: definitions and
place names where a harakat belongs. **60 of the 335 carry no `needs_review`
flag**, one of them served at confidence 1.0. Recorded as UPSTREAM A2c, which
is A2's complaint with a second, independent signal attached.

### And a measurement that argues against a ruling made an hour earlier

The same audit answered a question nobody had put to karbon: **does it ever
write a capital inside a word?**

| | |
|---|---|
| readings with a capital after the first letter | **0 of 45,579** |
| **compounds** with one | **0 of 20,263** |

*Ābādbum*, *Ābādjāi*, *Ābāngān* — flat inside, capital at the front only. And
**8,116 rows carry karbon's marker `[v7:rule12-cap]`**, so this is a deliberate
capitalisation rule and not an artefact: karbon capitalises the front alone.

**Nothing was changed on the strength of it.** The project lead ruled that a
prefix keeps the base's capital and that is what is built. But he said to
change it if the answer came back otherwise, and this is the strongest
evidence either way that anyone has produced — twenty thousand compounds from
a lexicon built on the linguist's own rules. It is in L9 for him to weigh.
A compound is not a prefixed form, which is the honest caveat and is stated
there too.

### And the reader found one more, by reading a screen we had not

Handed two lines off the build screen — «همانندی پایه با پایه‌های همیشگی این
دستور: ۸۴٪» and «یانچی» — with no complaint attached. Building from یان shows
what he was looking at: **twenty-three rows, every one of them carrying the
identical 86%.**

| row | built by | the score names |
|---|---|---|
| یانی | N-098 | N-098, base *Yān* ✓ |
| نایانی | N-098 → **N-021** | N-098, base *Yān* |
| یانییانه | N-098 → **N-040** | N-098, base *Yān* |
| یانیتر | N-098 → **N-045** | N-098, base *Yān* |
| یانیسار | N-098 → **N-055** | N-098, base *Yān* |

The score is measured on the chain's **first** rule. The sentence said *this
rule*. So on every row but the first it named a rule the row is not built by
and a base it is not built on.

**549,194 of 583,572 scored forms are two steps deep — 94.1%**, so this was
almost every scored row in the index rather than an edge.

**The number was never wrong and the API never lied**: `generate.ts` says "the
first step's base" in its own type, and `semantic.rule_id` and `semantic.base`
were being served all along and thrown away by the screen — the third instance
of that exact shape this session, after the reading flag and برنا's second
pronunciation.

**Fixed the way this project fixes it: the figure travels with what it is
about.** A row whose every chain ends on the rule the score names keeps the
original sentence. Any other row reads «همانندی Yān با پایه‌های همیشگی دستور
N-098: ۸۶٪ — سنجیده بر گام نخست». Checked in a real browser on یان: one row
with the plain sentence, twenty-two naming their rule.

Whether a deeper form should instead be scored on its **own** outer rule is a
question about the semantic model, not the screen — *yāni* is not a lexicon
word and has no vector — and is registered as **S15**.

### And then he asked what the number meant, which was the better question

The honest answer is *on its own, very little*, and measuring it says why.
The score is a cosine and on this corpus it never leaves the middle:

| across all 583,572 scored forms | |
|---|---|
| lowest anywhere | **55%** |
| highest anywhere | **91%** |
| median | **83%** |
| the middle **half** | 80% – 85% |

**So the 84% he read is the median** — the most ordinary word on the screen,
printed in a way that reads as a good mark out of a hundred. Nothing on the
screen said the scale only runs from 55 to 91, so there was no way to know.

**This project had already solved this once and not noticed.** Rule
productivity does not print a raw figure either; it prints the band of the
measured distribution, and `run_productivity.py`'s own comment says why — the
band "can only be worked out where the whole distribution is". The semantic
score had the identical problem and none of the remedy.

`tools/measure_typicality_spread.py` now measures the cut points and the row
reads «۸۶٪ — زیاد در میان همهٔ واژه‌های سنجیده‌شده (میانه: ۸۳٪)».

**Five bands, not three**, because a tercile over a distribution this narrow
puts nearly everything in the middle and says nothing. **Cut on percentiles,
not on the range**, because the range is unevenly filled and equal slices of
it would not be equal slices of anything real:

| band | from | to | share of words |
|---|---|---|---|
| کمترین | 55.4% | 76.3% | 10% |
| کم | 76.3% | 80.7% | 20% |
| میانه | 80.7% | 84.7% | 40% |
| زیاد | 84.7% | 87.0% | 20% |
| بیشترین | 87.0% | 91.4% | 10% |

**An absent artefact leaves the figure alone.** A position nobody measured is
worse than no position, and a machine that has never run the tool must not
invent one.

**And the compose file had to be told.** The variable was in `.env` and the
file was mounted, and the API still saw nothing: `docker-compose.yml` lists
each `MURFULU_*` explicitly rather than passing the environment through, so a
new one is invisible until it is added there. Caught by reading the API's
answer rather than by trusting the restart.

### Two things the reader raised at the end, neither of them acted on

**The dead badge.** The search row can print three populations — پیکره,
فرهنگ, ساخته‌شده — and the index carries **two**: 411,165 rows are `corpus`,
17,963 are also `lexicon`, and **nothing is `generated`**. So «ساخته‌شده» is
label text that no row can ever reach; built words live in `derivations` and
come to a reader through the build screen. Left alone pending a word from the
project lead — it is either wiring or a deletion, and which one is his call.

**«فرهنگ» is the wrong word.** Raised by the project lead reading the same
screen. It ordinarily means *culture* and means *dictionary* only in فرهنگ
لغت. **15 occurrences across 8 screens**, of which two are the badge and its
facet and the rest is prose that has to agree with them — one decision, not
fifteen. Not changed: naming in Persian for the project's own terminology is
the linguist's, and coining one here would put a term in front of readers with
nobody behind it. Registered as **L11**.

He is content to leave the coverage gap itself — 4.1% of spellings, 45.7% of
the writing — because the lexicon is going to grow.

### Rebuilding it, and the version that had to be thrown away

Both rulings and both new columns need a new corpus version to take effect, so
one was built. It took two attempts and the first failure is the more useful
finding.

**v6 was built with every poem undated, and nothing looked wrong.**
`MURFULU_GANJOOR_CENTURIES` was not set. The tool does not fail on that — it
prints one line, `centuries none loaded`, and carries on. Every word came out
with a null `first_century`, a null `last_century` and an empty
`counts_by_century`, so the century chart on the word screen would have been
blank and no other number moved.

| | v4 | v6 | v7 |
|---|---|---|---|
| documents | 133,148 | 133,148 | 133,148 |
| tokens | 25,497,189 | 25,497,189 | 25,497,189 |
| spellings | 409,916 | 409,916 | 409,916 |
| spellings linked | 16,714 | 16,714 | 16,714 |
| **documents undated** | **98,627** | **133,148** | **98,627** |

**Four of the five numbers were identical, which is exactly why it nearly went
out.** It was caught by comparing the new report against v4's line by line,
not by looking at the app — and it was released to the live aliases before
that comparison was made.

**And v6 was not the first time.** Checking whether the fix had worked meant
counting dated rows in every version, which turned up something older:

| | attested forms | of them dated |
|---|---|---|
| derivations-v4 | 24,482 | **14,279** |
| **derivations-v5** — live since session 9b | 22,118 | **0** |
| derivations-v6 | 22,118 | 0 |
| derivations-v7 | 22,118 | **12,975** |

**The version the app has been serving since session 9b has had every built
word undated**, and the same variable is why. It survived session 9b's own
re-test — fifteen routes twice, eight journeys — because **no screen shows a
built form's century**. `Evidence.tsx` prints the count, the poems and the
poets, and not the dates. So the data was lost and there was nothing to see.

That is the honest shape of it: no reader was shown a wrong number, and
anything built on those fields later — a *when was this first written*
question, the research export in 8.3 — would have been silently empty.
`word_types` was unaffected, which is why the word screen's century chart
went on working and looked like proof that the dates were fine.

**This is the third variable in two days that a rebuild needs and the
repository did not name.** `MURFULU_GANJOOR_PATH` was missing until session
9b; the precompute's own flags were never written down (fixed earlier today);
and now the centuries file. Each one is invisible because the pipeline
succeeds without it. `.env.example` now carries it with what it costs, and
ENGINEERING carries the five numbers to check a finished version against
before it is released.

**And one thing found by doing it.** `run_precompute.py --elasticsearch`
**moves the `derivations` alias with no way to say otherwise** — `run_ingest`
has `--no-release` and the precompute has no equivalent, so a new derivations
version goes live the moment it is written. Recorded in ENGINEERING; not
fixed, because it is somebody's next small task in that file rather than this
session's.

### What the rebuild actually changed

**Not the capitals.** v5 was already built by session 9b's lowering version,
and the ruling settled on lowering again, so v5 and the new version agree:
**0 forms with a capital after the first letter** in both. The reversal that
lived for one afternoon was never built into an index. Worth saying plainly
because "takes effect on the next corpus version" was true of it and it then
took effect as no change at all.

**Not the attestation, either.** 1,704,021 words written and 22,118 attested,
identical to v5 — the retired clitics were already out of v5, and the capital
is Latin, while attestation matches on the Persian spelling.

**What did change is the two columns**, which is what the version was for:
`latin_variants` on 2,650 rows and `definition_fa` on 17,471, and all three
indices on one version for the first time since session 9b split them.

**And the centuries came back**, which was not what the version was for.
12,975 of the 22,118 attested built forms are dated again, against **0** in
the version that had been live all day.

**Checked in a real browser rather than only asserted.** برنا's word page at
375 px and 1280 px shows *bornā* beside *barnā*, «از فرهنگ» with the
definition under it, and nothing scrolling sideways. The test skips itself if
the corpus version being served predates the fields, so it says *not
applicable* rather than passing vacuously on an old index — and it was checked
that it is running rather than skipping: 95 browser tests where there were 93,
with the same 3 skips as before.

### What was left alone, and why

**The 344,081 unaccounted spellings were not chased.** They are 83.9% of the
corpus and 35.9% of its writing, and they are proper names, Arabic, dialect
and words the lexicon does not have. Nothing in S8 needs them.

**No new corpus version was built.** Both rulings — the retired clitics and
the restored capital — take effect on the next one, and building it for two
one-line changes that may both move again is not worth 1.7 million rows.
v5 stays live and v4 stays on disk.

**The app was not swept again.** The fifteen routes and eight journeys have
passed four times; the one thing driven here was the reading order, and it was
checked through the running API rather than asserted on.

---

## 2026-08-13 (session 9b) — the six fixes, and what the reader found that we did not

Session 9a is below and is the survey. This is what was done about it, in the
order the project lead asked for. **Everything here is unconfirmed where a
ruling is missing, and every one of them is one line to undo.**

| # | done | takes effect |
|---|---|---|
| 1 | N-090 and N-099 no longer generate | next corpus version |
| 2 | a prefix drops the base's capital | next corpus version |
| 3 | build results rank on evidence, not on link level | at once |
| 4 | a spelling-only match says whose count it is | at once |
| 5 | a letter from another alphabet is repaired on read | next corpus version |
| 6 | the lexicon's `needs_review` reaches the screen | at once |
| 7 | the affix screen's twelve blank chips | at once |
| 8 | a retired rule must say why, and the route serves it | at once |
| 9 | the 17 glide rules are served; the میانجی button works | at once |
| 10 | a build group opens at twenty and says what it folds | at once |

### The twelve blank chips, and the hole behind them

The affixes screen showed twelve identical `‒` chips. Split by what a rule
actually is: **19 of the 81 untagged entries are not affixation** — 10
compounding templates, 6 slots, 3 zero-derivations.

**The dash is not a rendering bug.** The source writes a dash because a
template joins two words with *nothing* between them. So they are not dropped
either — hiding them would leave a reader believing the inventory is affixes
only, which is the same mistake the screen already exists to avoid. They now
sit under their own heading with their rule id and their example, which is the
one readable thing about a rule whose affix is nothing: V-018 *Goftogu*,
V-017 *Zadoxord*, V-078 *soxanguy*, N-104 *Sarāsar*. **62 affixes and 19
rules, counted apart**, so neither number is inflated by the other.

### And behind that, a rule could be switched off with nobody told

Checking that N-090 was still readable after being retired turned up
something worse than the chips.

**`Rule` had no `retired_reason` field at all.** The reasons written into the
YAML beside `active: false` were being dropped on load, and — unlike the glide
loader, which has refused a reasonless retirement since G-01 — nothing
required one. **A rule could be switched off in the pack and stop building
words with nothing anywhere saying so.** Ids are permanent and a retired rule
is still served, so the reason is the only thing that separates a ruling from
a rule somebody disabled.

The route had the second half of it: `/rules/{id}` served `retired_reason`
only from the glide branch, so a retired affix rule showed as inactive with a
blank beside it.

Field, loader refusal and route now match what glides have had all along, with
a loader test beside the other malformed-rule cases. **This was invisible until
the first affix rule was retired**, which is a fair description of how the
hole survived: nothing had ever exercised it.

### The third re-test: the sweep had stopped telling us anything

Three passes of the same fifteen routes and eight journeys had all come back
clean, which is the point at which a test stops being a test. This pass drove
**the interactions behind a click** instead — the derivation expander, the
copy button, a facet, the details expander, the affix filter, the Back button,
a missing word, the keyboard, and an expert verdict end to end.

Fourteen checks, twelve clean, **two real faults, both invisible to a sweep
that only loads pages.**

**Both boxes were showing a query the screen was no longer answering.** Each
seeded its draft from the address once and never again, so any route change
that did not come from the box left the two disagreeing.

| screen | what a reader does | address | box |
|---|---|---|---|
| search | clicks the مولانا facet | `*nā author:مولانا` | **`*nā`** |
| analysis | presses Back | `word=Ravandegi` | **`Goftār`** |

The first defeats the reason facets exist. `Facets.tsx` states it: *a facet
writes the query it stands for and the box shows it, so the reader learns the
syntax by using the interface.* The narrowing worked and the teaching never
happened. The second is worse — the screen answered about one word and named
another.

**And the fix taught something about the framework.** Adjusting the state
during the render is React's shorter answer for a prop-derived draft, and it
**does not survive here**: the router navigates inside a transition, and a
render-time adjustment made during one can be discarded when the transition
replays. The browser test failed every run on that version and passes on the
effect. Not reasoned — measured, after the render-time version passed in
jsdom and failed in a real browser.

**The test needed the same care as the code.** Waiting on the box or the
address let Back fire inside the same frame as the push, and the router then
committed the push *after* the pop and settled on the wrong entry. Two runs
in three failed. Waiting for the screen to have finished answering — which is
what a reader would do — makes it five for five. Worth stating plainly: **the
first version of that test was measuring a race no reader can run.**

**Two more of the fourteen were my own assertions, not the app.** رفت's
derivation says «خودِ کاربن یک کارنام است» rather than «ساخته می‌شود», because
V-007 and V-020 are zero-derivations; and the address percent-encodes
`author:`. Recorded because a wrong assertion that goes unexamined is how a
fixture starts lying.

### The second full re-test: clean, and one stale number

Whole stack rebuilt again, all fifteen routes at both widths, all eight
journeys walked. **No console error, no failed request, nothing scrolling
sideways, every journey passing.** رفتن reads رفت، رفتن، رفتار، روش; the
founding question answers in one filter; گفتار's chart still adds to its
total (1,166 + 3,647 = 4,813); every family button narrows to its real count
(81, 105, 17, 9).

**One thing it caught.** The rules screen showed N-090 marked **بازنشسته**
and, beside it, **14,074 words built and 1,983 of them written**. Those were
v4 numbers, measured before the rule was retired. The screen labelled them v4
and the build screen labelled its evidence v5, so **both sentences were true
and the pair was misleading** — which is the failure mode this project keeps
finding, and the reason it insists a version travels with every count.

`tools/run_productivity.py` re-run over the v5 precompute: N-090 and N-099
now measure 0 built and 0 attested, every other rule is unchanged, and the
rules screen says *سنجیده بر پیکرهٔ v5* like the build screen. Nothing about
this was visible to either suite: both numbers were correctly labelled, and
no test asks whether two screens are talking about the same corpus.

### The full re-test: the ranking fix moved the problem, it did not solve it

Whole stack rebuilt from scratch — both images, the real nginx container on
5173 rather than a dev server — and every screen walked at 375 px and 1280 px.
**No console error, no failed request, nothing scrolling sideways on any of
the fifteen routes at either width.** But reading the flagship word says
something the tests do not.

**رفتن now opens on روی.**

| | before session 9 | after |
|---|---|---|
| 1 | رفتن — the echo | **روی** `ravi` — 54,649 times, *read as Rui* |
| 2 | رواندن — 1 poem | **رفتی** `rafti` — "you went" |
| 3 | فرورفتن — 10 poems | **نرفته** `narafte` — "not gone" |

روی is *Ruy*, "face" — a different word, and 31,830 of the corpus's poems
have it. رفتی and نرفته are **inflected forms**, not new words. Meanwhile
رفتار (1,091 poems) and روش (912), the two outputs the plan names as رفتن's
flagship, sit below them.

Measured over the top twenty of the first group of five builds:

| word | matched on the reading | no lexicon reading | corpus reads it another way |
|---|---|---|---|
| رفتن | **0** | 16 | 1 |
| گفتن | 2 | 6 | 3 |
| دانستن | 1 | 13 | 2 |
| بلند | 0 | 6 | 0 |
| مهر | 0 | 15 | 5 |

**This is the ranking change, and it is honest to call it half a fix.** Before,
the link level outranked everything, so گویه — 6 poems — sat above گفت —
19,839. Now the document count outranks everything, and a spelling match with
31,830 documents beats a reading match with any number at all. گفتن reads
better than it did; رفتن reads worse.

The row says so — every one of them carries «شمار برای این املاست» — so
nothing is claimed falsely. But **saying a number belongs to another word and
then ranking on it is not a resting place.** This is exactly the weighting
OPEN_QUESTIONS S8 left open, and the re-test is what makes the cost of leaving
it open visible: it is not a subtlety at the bottom of a list, it is the first
row of the flagship word.

**Built, on the project lead's word.** Where the lexicon holds a reading for
the spelling and none of them is the one we built, the count is evidence about
a different word and no longer ranks the form — it stays on screen with the
caveat it already carried; only the ranking stops using it.

**Case is folded first, and that is the whole of why it is safe.** گفت is
`Goft` to us and `goft` in the lexicon: one word in two classes, not two
words. A case-sensitive comparison would have sunk the commonest word the
screen has.

Narrow by design — **11 of رفتن's 500 forms, 9 of مهر's, 1 of گفتن's** — and
the result:

| | before | after |
|---|---|---|
| رفتن | روی، رفتی، نرفته | **رفت، رفتن، رفتار، روش** |
| گفتن | گفت، گو، گفتار | unchanged |
| بلند | بلندی، سربلندی | unchanged |
| مهر | مهربان، مهره، مهرگان | **مهربان، مهربانان، مهرگانی** |

**And the test fixture was caught lying by it.** The shared stand-in said the
corpus reads گفت as *goftār*, which under the new rule correctly sinks it —
so a test written to prove گفت ranks first started failing. The fixture said
something the data does not, which is how session 8's family-filter bug
survived too.

**What is still open is the harder half, and no condition fixes it.** Where
the lexicon knows *no* reading for a spelling, nothing we hold separates رفتی
— "you went", an inflected form — from گفتار, which is exactly the word we
built. Both are `unlinked`, and **16 of رفتن's top twenty are**. That needs a
morphological analyser over the corpus, or the affix map extended to
inflection. Recorded in S8.

### The rules screen was the long page the build screen used to be. Fixed

42,840 px at 375 px wide — 52 phone screens — because all 212 rules rendered
at once. Same shape as the build screen, same answer: the list opens at
twenty with the count of the rest on the control that opens it, and one press
gives the whole 42,840 back.

| | before | after |
|---|---|---|
| the whole pack | 42,840 px | **5,372 px**, «۱۹۲ دستور دیگر» |
| the verb family | — | 5,372 px, 61 folded |
| the glide family | — | 4,771 px, nothing to fold — seventeen fit |

**It folds again when a family button is pressed.** Otherwise a reader who
opened the pack and then narrowed would get a long page for a reason they did
not choose.

**And the first version of its test counted the navigation**, which is a list
too — 26 rows where 20 were expected. Scoped to the rules list. Worth the
note: `getAllByRole("listitem")` on a page with a nav is almost never what it
looks like.

### The last two, and the same mistake underneath both

**The میانجی button.** 17 glide rules sat in the pack and `/rules` served none
of them, so the one family with a button had no members and every build result
naming `G-10` linked nowhere. They are served now — with **their own shape**,
not squeezed into the affix envelope. A glide has no affix, no input class, no
tag and nothing to measure, so nulls in those fields would have put blanks
exactly where the affixes screen had its twelve empty chips. Same mistake,
caught the second time. The pack total on screen goes **195 → 212**, which is
what the pack has always held.

**The page nobody could scroll.** Each group now opens at twenty rows and
carries the count of the rest on the control that opens it.

| | before | after |
|---|---|---|
| بلند | 588,102 px, 3,185 rows | **39,513 px**, 226 rows |
| رفتن | 180,547 px, 1,026 rows | **40,005 px**, 230 rows |

**The figure matters less than the property**: the page length is now set by
how many word classes there are, not by how many words were built, so it stops
growing with the answer. Nothing is hidden — the control says «۱٬۱۶۲ واژهٔ
دیگر در این گروه» and one press shows them.

**And one thing found by doing it, not fixed.** Every `retired_reason` in the
pack is written in **English**, for whoever reads the repository. The
interface is Persian and may not invent Persian, so the rules screen shows a
**بازنشسته** badge and stops — a reader is told *that* N-090 no longer applies
and not *why*, which is the whole of the interesting part. Registered as S14.

### Rebuilt as derivations v5, and re-tested in the browser

`derivations` now serves **v5**; `documents` and `word_types` stay on v4,
because the corpus text did not change — only what we build from it. The
corpus screen already models the three separately, so it says so. **v4 was
not touched** and is still on disk and queryable.

| | v4 | v5 |
|---|---|---|
| words written | 1,738,928 | **1,704,021** |
| forms built by N-090 / N-099 | 28,148 | **0** |
| forms carrying a Greek letter | 2,582 | **0** |
| forms with a capital inside the word | **281,522** | **0** |
| attested | 24,482 | 22,118 |
| rules with an attested output | 158 | 156 |

The 281,522 confirms the 16.2% estimate taken from a 5,000-form sample.
**Attested falls by 2,364**, and 2,252 of those are the clitic forms that
were counting the base word's occurrences. That number going *down* is the
fix working.

**What the flagship screen looks like now.** Same word, same screen, before
and after:

| | before | after |
|---|---|---|
| 1 | بلندِ — 7,353 times, 217 poets | **بلندی** — 1,147 times, 160 poets |
| 2 | بلندِِ — 7,353 times, 217 poets | **سربلندی** — 162 times, 56 poets |
| 3 | بلندِی — 1,147 times | بلنده — 3 times |
| 4 | بلندی — 1,147 times | بابلند |

and on گفتن, گفت — 19,839 poems — is first, where گویه — 6 poems — used to be
second and گفت third.

Every spelling-level row now carries **«شمار برای این املاست»**, and the
reading heading carries **«فرهنگ این خوانش را بازبینی‌نشده نشان کرده است»**
where the dictionary flagged it.

**One thing the re-test settled and one it did not.** *sarbalandi* is now
spelled the way Behnevis spells it. Whether it should be *sarbolandi* is still
open, and now visibly so: بلند's flagged `Baland` reading builds 2,408 words
and its clean `boland` reading builds 555, so the flagged one opens the screen
and `Bolandi` is on the second. The screen no longer hides which is which.
**Whether a flagged reading should open a screen at all is S13.**

### The reader found the thing the survey missed

Asked why *SarBalandí* was wrong, the project lead said it should be
*sarbolandi* — and was right about a **third** fault the survey had not seen.

بلند has **two** readings in the snapshot:

| reading | class | the lexicon's own flag |
|---|---|---|
| `Baland` | اسم ذات | **`needs_review = 1`** |
| `boland` | صفت | clean |

The build screen opens on `Baland`, builds **2,612** words from it against
`boland`'s 567, and never mentions the flag. The same snapshot spells سربلند
**`sarboland`**, so it contradicts our output on its own.

**The flag was being read and thrown away.** `murfulu/lexicon` carries it,
the search ingest stores it, and `/generate` did not serve it. **14,361 of
45,579 active rows — 31.5% — carry it.** It is now served and shown under the
reading. Nothing is filtered or reordered on it: a flag is the dictionary
saying *check this*, and which reading of بلند is right is L1's kind of
question, not ours.

So `SarBalandí` had three faults, not one, and only the second was in the
survey: the wrong reading, the inner capital, and the `í` from the indefinite
rule.

### The phonemizer question, measured rather than argued

The project lead asked whether karbon can Latinise any word, not only the
words it holds — which would let the corpus be searched in Latin and stop
بلندِ inheriting بلند's count.

**karbon does have a phonemizer**, six versions of it, and the earlier answer
here that we only know 4.1% of the corpus was wrong about the reason. But its
signature is `phonemize_v6(headword, bracket_raw, is_noun)`, and `bracket_raw`
is Dehkhoda's own diacritics — «فَ رْ وَ دَ». A poem in Ganjoor has none.

Run without them, over 2,000 lexicon headwords whose true reading we hold:

| | correct |
|---|---|
| with Dehkhoda's diacritics (karbon's own golden set) | **89.2%** |
| without them | **5.8%** — 17.4% ignoring case |

It emits consonant skeletons: بلند → `blnd`, سپردن → `sprdn`, دانشمند →
`dānšmnd`. **Marking that "unconfirmed" would not rescue it** — `blnd` is not
a low-confidence reading, it is not a reading. Whether karbon has an
unbracketed resolver is a question for its maintainer; the code read here has
none.

### Retiring two rules is cheap; the ezāfe was never the root either

Worth stating plainly, because it was nearly missed: **stopping the false
counts and stopping the false words are two different jobs.** Latinising the
corpus would have fixed the first and left بلندِ in the list with a zero
beside it. Retiring the rules fixes the second. Only item 4 — saying whose
count a spelling match carries — addresses the first, and it addresses it by
telling the truth rather than by getting a better number.

### A rebuild could not be reproduced from the repository

`MURFULU_GANJOOR_PATH` was not in `.env.example`. It is a host path that only
the batch tools read and no container gets, which is presumably why nobody
wrote it down. The precompute stopped on it, and the dump had to be hunted
across the disk — two candidates turned up, both with 133,159 poems, and
neither was named anywhere in the repo. Now documented, pointing at the corpus
report so a candidate can be checked before a rebuild is trusted.

---

## 2026-08-13 (session 9) — used it as a writer would, and it is not good yet

**Not a test run.** Both suites are green and neither says whether the app is
any good. Every screen was driven in a real browser at 375 px and at 1280 px,
in Persian, and the screenshots were looked at rather than asserted on. The
eight journeys in USER_JOURNEYS were walked as a person, not as a script.

**What the app does well is worth stating first**, because most of what
follows is faults. The founding question is answerable: filter وندها on «جا»
and five affixes come back with an example each. The two-group split on
`*nā` works — four formed with the affix, forty-six merely ending in those
letters. A word page's numbers agree with themselves: گفتار's chart adds to
1,166, its undated remainder to 3,647, and the total to 4,813, with the gap
named on screen. Its six citations all contain the word. The corpus screen
says what the app does not know, in the reader's language, without being
asked. Feedback works end to end, and a linguistic verdict about the app
itself is refused as designed.

### The top of the build screen is not word formation

**Worst first, and it is the first thing a reader sees.** Build from بلند,
an ordinary adjective, and four of the top five results are بلند with a
grammatical clitic stuck on it:

| rank | form | Persian | what the screen claims |
|---|---|---|---|
| 1 | *Balandé* | بلندِ | 7,353 times, 5,625 poems, 217 poets |
| 2 | *Balandéé* | بلندِِ | 7,353 times, 5,625 poems, 217 poets |
| 3 | *Balandéí* | بلندِی | 1,147 times, 1,059 poems |
| 4 | *Balandí* | بلندی | 1,147 times, 1,059 poems |

Two rules do this: **N-090**, the ezāfe, whose own example is *Ketābé u* —
کتابِ او — and **N-099**, the indefinite *-i*, whose example is *Ketābí*.
Both are enclitics. The engine runs them like suffixes, on every noun, and
lets them stack on each other and on themselves.

**And they invent evidence.** The corpus has no kasre in it, so بلندِ is
looked up as بلند and inherits everything بلند was ever credited with.
Measured over the whole v4 index:

| | |
|---|---|
| forms built with N-090 or N-099 | **28,148** |
| of those, marked attested | **2,252** |
| share of every attested form in the index | **9.2%** |
| the largest | *Dideé* (دیدهِ) — 33,599 occurrences, 22,740 poems |

Nearly one attested word in ten is a base word wearing a clitic and carrying
the base's own count. Nothing was changed: retiring a rule is a ruling and
the ids are permanent. Registered as **FOR_THE_LINGUIST L8** with the
measurement.

### A capital in the middle of a word, on one form in six

سربلندی comes out as **SarBalandí**, بی‌مهری as **BiMehri**. A prefix rule
joins its affix without touching the base's capital.

Measured on a random 5,000 of the 1.74 million forms: **808, 16.2%**, carry a
capital after the first position — *DošKohbale*, *barFāxmān*, *hamLamāze*.
On بلند it is 1,064 of 2,612.

The source is not consistent — *Namakdān*, *soxanguy* and *xodaparast* are
flat, *Došnām* is not — so nothing was guessed. **FOR_THE_LINGUIST L9**.

### Ranking sorts on how a match was linked, not on how much evidence there is

On گفتن the screen puts **گویه, written in 6 poems, above گفت, written in
19,839**. `ranked()` orders on the attestation *level* first — `reading`
before `spelling` — and only breaks ties on the document count. The level
says whether the lexicon holds a headword for that exact spelling, which is a
fact about the dictionary rather than about the word.

Measured across the top twenty of every group of five builds: **64 of 4,977
pairs inverted, 1.3%** — small in count, and they fall where the level
boundary is, which is near the top. Same cause on رفتن: رواندن, one poem, one
poet, sits second, above فرورفتن, ten poems, eight poets.

The discount is not baseless — a `spelling` match may be the homograph
session 8 measured — so this is a scoring decision, not a bug. **S8**.

### The analysis screen answered a Persian word with a reason that was not the reason

`/explain` reads the Behnevis and nothing else. **Fixed, in the screen.**

| typed | answered |
|---|---|
| گفتار | راهی پیدا نشد |
| **Goftār** | six accounts |
| دانشمند, گفتگو | راهی پیدا نشد — and both are the rule pack's own examples |

Every other screen takes Persian, the interface is Persian throughout, and
this one said *this does not mean the word is wrong; most words are simple or
loanwords*. True in general and false here. The screen now names the script
when the input carries Persian letters, and the label asks for the Behnevis
before anything is typed. Whether the route should accept Persian is **S11**.

### The feedback panel would not let go of the key form

Found by leaving feedback the way a new reviewer would. The panel re-raised
itself with the subject it already held, React saw the same object and
skipped the render, and the effect that identifies the caller never ran
again. **The key form stayed on screen after the key was kept**, and the only
way past it was to close the panel and open it again — on the first thing
every new reviewer does. **Fixed**, with a test.

### A shell that reads the lexicon can take the API down

Reproduced by accident during this session, and it is not the documented
`MURFULU_LEXICON_PATH` trap. The snapshot is in **WAL** journal mode and
`./data` is mounted **read-only**, so a WAL reader cannot create the `-shm`
file it needs. One host-side `sqlite3.connect(path)` without `mode=ro` and
every `/generate` answers a bare 500 until the API is restarted.

**`/health` kept answering 200 and `docker compose ps` kept saying healthy**
through all of it. That is the part worth fixing whatever else is decided:
a dead lexicon should not be reported as a well service. **S9**.

### Eleven lexicon rows carry a letter from another alphabet

سپردن's present stem is written **`sepοr`** — with a Greek omicron. Ten more
rows hold an omicron, a Greek capital alpha, a *ú*, or an Arabic **ه** inside
a Latin field. Because a stem is copied into everything built on it,
**2,592 forms in the index carry one**, and none of them can be typed,
searched or matched — while looking, on screen, exactly like a correct form.
A one-character replacement upstream clears all of it. **UPSTREAM A5**, with
the full table.

### Smaller, in the order a reader meets them

**A build result is 588,102 px tall.** بلند at depth 2 renders 3,185 rows on
a 375 px screen — 724 screens of page. رفتن renders 180,547 px. The screen
declines depth 3 because the answer would be 24.7 MB; depth 2 is already past
what anyone can scroll, and nothing says so. **S12**.

**The وندها screen shows twelve blank chips.** The *affixes the source gives
no meaning for* list renders `affix` straight, and **18 of the 81 have no
Persian affix at all** — twelve are compounding templates (V-017 *Zadoxord*,
V-018 *Goftogu*), zero-derivations (V-020 *Sāxt*) or slot rules (`Nām-`,
`Čonvāže-`). They are not affixes, they render as a bare `‒`, and they carry
no rule id or example a reader could follow. The same list also stays at full
length when the meaning filter is narrowed to one: search «جا» and the answer
is one card followed by 81 unrelated chips.

**The میانجی family button is always empty.** `/rules` serves 105 N, 81 V and
9 S rules and **none of the 17 glide rules**, which build results name by id.
**S10**.

**`stem2:gu` is one of four example chips on the home screen and returns one
word** — گفتن itself. The chip reads *ساخته‌شده بر بن «gu»*, "formed on the
stem gu", and what it actually asks is *which lexicon entry has gu as its
present stem*. A reader clicking it expects گو، گویا، گوینده.

**`type:karnam`, another of the four, returns را second.** The lexicon files
را — the object marker — as اسم معنی, which murfulu maps to کارنام. So do گر
(*if*), مرا, خوش and پنج, among the twenty commonest. Reported to karbon as a
question rather than a fault: **UPSTREAM A6**.

**One spelling, two readings, the same number under both.** رفتن as *raftan*
and رفتن as *roftan* each get a page claiming 3,886 occurrences in 3,202
poems. The page says the readings do not merge and then gives both the same
count. That is item **Q2** seen from the reader's side.

**The floating بازخورد button covers content on every screen**, including
links — the rule link on the last *-gāh* row of the جا card, the رونوشت
button on the third build row. It is fixed to the corner and the pages carry
no room for it.

**A task number was on screen.** The build screen's *no third step yet* note
ended with «کار ۶.۲». **Fixed.**

### Already known, and here is whether they are worse than stated

**The echo at the top of a build is worse than "cluttered".** رفتن returns
رفتن first, as recorded — but on دانستن the first row is **دانه**, credited
with 5,122 occurrences. Those are occurrences of دانه, "grain". The rule is
*dān* + *-e* and the spelling collides. Same shape as the ezāfe fault: a form
whose evidence belongs to a different word.

**Near-identical rows are not only about capitalisation.** *Balandé* and
*Balandéé* both render as بلندِ on screen, with identical numbers — the same
word twice, and neither is a word.

**S3 is visible everywhere and reads as inconsistency, not as a gap.** The
search chip says **کارنام‌ها** and the rows under it say **اسم معنی**; the
build screen's groups say **مصدر** and **اسم**. A reader is given two
vocabularies and no indication that they are the same thing.

**ZWNJ (item K) is untouched, as recorded**, and V-018 *Goftogu* is one of
the twelve blank chips above, so the screen does not show گفتوگو at all
there.

---

## 2026-08-13 (session 8) — the corpus reads every word now

**Five tasks, and two corpus versions.** v2 replaces the analyser that was
eating the commonest words in the language; v3 carries an affix map a semantic
check has been through. All three aliases serve v3.

| built | measured |
|---|---|
| an analyser that keeps every word (v2) | رفت: **0 poems → 10,636** |
| a homograph detector over every claim | **3,613 of 16,627 doubted, 21.7%** |
| grounding and typicality written into the index | 279,106 grounded, 595,135 scored, +13 MB |
| a rule's semantic centre on the rules screen | 57 of 195 rules have one |
| the pilot over all 57 centroid rules | **25.4%** strict, **53.9%** on unique affixes |

**Three faults found by running rather than reading**, none of them by a test
that already existed: the zero-width non-joiner half of the stopword hole,
which the original diagnosis had not named; a detector that flagged 100% of
claims and had to be thrown away; and a family filter on the rules screen that
had never worked because the API did not send the field it filters on.

### The join is fixed, and the missing letter was worse than the extra one

Corpus version **v4**. `glides.join_fa` drops the base's silent ه when a گ
follows, and — the part that was not in the diagnosis — **puts the گ in the
Persian at all.**

Two glide rules insert a *g* in the Latin, G-09 (*taze + i = Tāzegi*) and G-10
(*morde + ān = Mordegān*), and the Persian side knew only about *y*. So
*Zandegi* was written **زندهی**: no گ anywhere. The module already guarded
this exact drift for *y* — گوش against گویش — and nobody had asked about *g*.

**Silent is decided by the Latin, never by the letter.** شاه ends in ه too and
its ه is a consonant, because *šāh* ends in *h*. Reading it off the Latin is
exact where guessing from the Persian would not be.

| | v3 | v4 |
|---|---|---|
| joins spelled wrong | 38,932 | **0** |
| attested forms | 24,197 | **24,482** |
| rules with an attested output | 156 | **158** |

**The net +285 hides what actually happened: 1,609 gained and 1,324 lost, and
both are corrections.**

| | |
|---|---|
| gained | زندگی (4,571 occurrences), مژگان (3,977), زندگانی (3,489), بندگی (2,583) |
| lost | *Šaegi*, which was spelled **شاهی** and matched شاهی, "kingship" |

The losses are false matches going away. With no گ in the Persian, *Šaegi*
came out as شاهی — a real word, and a different one — so the corpus confirmed
a derivation that had never been built. **A missing letter does not only fail
to match; it matches the wrong thing.** That is worse than the extra ه, and it
was invisible until the two were fixed together.

About 11,000 forms still spell هگ and that is correct: their base ends in a
**consonant** ه — آگاه, آجه, دوازده — which the Latin says by ending in *h*.

**Unconfirmed**, per the working rule: the orthography is standard and the
grammar's own examples assume it, but the Behnevis joining specification is
still unextracted. Registered as FOR_THE_LINGUIST L7.

### A shell that can run the batch tools cannot start the containers

`docker compose` substitutes from the environment before it reads `.env`, so a
shell with `MURFULU_LEXICON_PATH` exported for the batch tools hands the
container a **host** path, and `/generate` answers 500 with the snapshot
missing. The batch tools need the host paths and the container needs its own;
the same variable name means one shell cannot do both. Start the containers
from a clean shell, or `env -u`.

### Asked whether the words are any good, and the answer is: the Behnevis is,
### the Persian spelling is not

Nobody had looked at the output as a writer would. Doing that on رفتن، گفتن
and دانستن found three things, in order of how much they cost.

**The Behnevis forms are right and the Persian spellings are systematically
wrong.** *Dānandegi* is correct; the engine writes it **دانندهگی** where
Persian is **دانندگی**. A base ending in ه loses it before a suffix in گ, and
the engine does not know that. **38,932 forms spell that join wrong.**

**And the misspelling hides real words**, which is the part nobody had costed.
Attestation looks a form up by its Persian spelling, so a form spelled wrongly
cannot match the corpus and comes back *never written*. **At least 650 of them
are common Persian words:**

| we write | the corpus has | times |
|---|---|---|
| زندهگی | **زندگی** | 4,571 |
| مژهگان | **مژگان** | 3,977 |
| زندهگانی | **زندگانی** | 3,489 |
| درهگاه | **درگاه** | 3,284 |
| بندهگی | **بندگی** | 2,583 |
| بارهگاه | **بارگاه** | 1,336 |
| آزادهگان | **آزادگان** | 634 |

This is OPEN_QUESTIONS item M, recorded since session 2 as a spelling question
and never measured. It is not a minor one: it is the reason the *best-ranked
new words* — دانندهگی، داناگی، گویاگی — look wrong at a glance, and it
suppresses attestation for a whole class of real vocabulary.

**A first measurement of this was wrong and is worth recording as a method
note.** Stripping ه before any of گ، ی، ا matched 5,459 corpus words and looked
like a much bigger finding. Most were coincidences — *مرها* → *مرا*, *کهار* →
*کار* — which the top of the list showed immediately. Restricting the test to
the join the Latin actually spells (`eg` against `هگ`) gives 658, and those
survive reading.

**The top of a result list is cluttered by the word you asked about.** رفتن
returns رفتن; گفتن returns گو; دانستن returns دان. Those come from the
zero-affix and *-an* rules already counted as `echo_share` in task 5.3, and
they rank top because they are the best-attested outputs of the run. A writer
asking what can be built from دانستن does not want دان first.

**One form, several rows.** رفتار appears three times in رفتن's list, differing
only in the capitalisation of the Behnevis. That is correct in the data — the
key is the reading and the word class — and wrong on a screen.

### Do the scores predict a real word? Grounding does; typicality barely does

Measured over the whole v3 precompute, and neither signal sees the form's own
attestation:

| two-step words | attested |
|---|---|
| built on a form the corpus has | **10,004 of 189,174 — 5.29%** |
| built on a form nobody wrote | 1,099 of 1,459,822 — **0.08%** |

**A word standing on written ground is about seventy times more likely to be a
word.** That is the strongest ranking signal in the system and it justifies
session 7's grounding work on its own.

Semantic typicality separates the same two groups by **0.8394 against 0.8198** —
real, and small, exactly as the pilot's overlapping distributions predicted. It
earns its place as the **last** tie-breaker and nothing more.

### The rules screen's family filter had never worked

Found by opening `/rules?family=V` in a browser to check the new semantic line,
and getting three rules instead of eighty-one. The screen filters on
`rule.family`; **`/rules` never sent that field**. Every family button on the
screen emptied the list.

Nothing caught it because both halves were individually right. The route's own
`?family=` filter works and is tested. The component test supplies a fixture
with `family` in it — a fixture that had drifted from what the API returns —
so the screen filtered correctly against data it never receives. The layout
tests opened `/rules` and never a family.

The field is derivable from the id and is now served, with a test on each side:
the route's, that every rule carries it; and a layout test, that a family
button narrows the list rather than emptying it.

### The 93% was three rules. On all 57 it is 25%, and the reason is legible

The go/no-go pilot ran on a board of three well-separated rules. Run over
**every rule with a centroid** — 57 rules, 2,025 attested words, at most 40 per
rule — leave-one-out accuracy is **25.4% against 1.8% chance**, and **64.0%**
counting a rule with the same affix as right.

**The strict number is the wrong one to quote, and the run says why.** 35 of
the 57 rules **share their affix with another rule on the board**: V-070 to
V-073 are all *vā-*, V-005 and V-006 are both *-an*. Those 35 score 105 of
1,266 strictly and up to 90% on the same-affix score. Nothing in a word's
meaning separates *-an* the infinitive from *-an* the noun — the **output
class** does, the grammar states it, and no vector was ever asked.

**On the 22 rules with an affix of their own it is 53.9%.** That is the figure
to carry forward, and the spread inside it is the useful part: *nā-*, *-ande*,
*-tar* and *-gar* score 80–88% and each do one thing to one kind of base;
*-nā*, *-na-*, *-nā-* and *-ā* score 0–15%, are short, and collide with each
other and with Arabic endings — the same collision that makes the affix
backfill refuse *Fanā*.

So the method works where the affix is a real distinction in the corpus, and
the honest way to state the 93% is that it was measured where it works.

### A rule's semantic centre is now something a reader can disagree with

The centroids scored words and appeared nowhere. On the rules screen each rule
now shows the size of its centre and the bases nearest it: V-001 (*-āndan*)
is *the average of 50 written bases*, of which the nearest are رو، جه، رس، خو،
دم، گرد، گیر، ست — verbs of motion and holding, which is what an *-āndan*
causative is made from.

**The artefact could not answer the question as it stood.** It carries one
pooled table of base vectors and a centroid per rule, so nothing downstream
could tell *which* bases a given rule's centre was built from. The batch job
knows, so it writes the eight nearest ones; the component ranks nothing and
computes no cosine. **57 of 195 rules have a centre**, and a rule without one
says so rather than showing a blank, which would read as *nothing typical*.

### The index now carries what only the build screen could see

`base_attested` and the semantic typicality were computed per request and
stored nowhere, so `/search` and the rules screen could not use either. Both
are written by the precompute now, in a new run over corpus v3.

| | |
|---|---|
| run time | **34.8 s** for 1,738,928 words |
| index | **444.1 MB** at rest against 431.4 MB for v1 — the two fields cost about 13 MB |
| stand on written ground | 279,106 |
| carry a semantic part | 595,135, from the 57 rules with a centroid |

**The first size reading was wrong, and how it was wrong is worth keeping.**
Asked right after the write, Elasticsearch reported 518.5 MB; at rest, after
the segments merged, it is 444.1 MB. A figure read from an index that is still
settling overstates it by a sixth and looks exactly like a real one — the same
class of trap as the `cardinality` estimate in task 7.8.

**A stored derivation keeps less than a live one, and that shaped both.** The
grounding question is about the forms *between* the base and the word, and a
stored path records the base of its **last** step only — which at two steps is
exactly the one intermediate, and at three is not enough. So the batch version
has a third answer: a path too deep to read comes back **not established**,
never *false*, because a stored false would say the corpus was asked and
answered no. At depth 2, which is what the run does, nothing came back
unsettled. The semantic part is asked of the **first** step, whose base a
stored path does not keep either, so the run carries it while merging and
drops it afterwards.

**Grounding cannot be answered as each word is built.** Written ground is the
whole run's attested forms, so it takes a second pass after the last lookup —
the same shape as the sister forms, and for the same reason.

### A homograph detector, and the detector we had to throw away first

The pilot found the sister lists of *-dān* and *-stān* contaminated by
plural-ان homographs and dropped the two rules rather than measure round it.
Measured properly now — full working in
[RESEARCH_SCORING.md](RESEARCH_SCORING.md), per-rule table in
`build/homograph-report-v3.md`.

**The obvious method was built and it does not work, which is the finding.**
Score a claim by the cosine of the word to its rule's centroid and cut low:
claims sit at 0.811 against their own rule and 0.780 against every other one,
sd 0.05 apiece. The distributions overlap almost entirely and the first run
flagged **100% of claims**. A line-averaged encoder puts every Persian verse
vector in roughly the same place; the absolute cosine is mostly that shared
component.

**So the statistic is a rank, and then the cut costs nothing to justify.** For
each claim: what share of the candidates it has nothing to do with fit the word
better. Under the null that is uniform, so the null density is exactly 1 and
the cut is the first bin where the claim density falls to it. Checked, not
assumed — a null built by pairing every word with every rule that never claimed
it has a median of 0.495.

**And one check was not enough, for a reason worth keeping.** A rule whose
claims are *mostly* homographs has a centroid **made of** them. *-dān* has 14
claims and eleven of them occur once; شاهدان sits comfortably inside that
centroid, and the rule-fit check doubted nothing at all in either *-dān* or
*-stān*. The second check compares a word with **the word it was built from**,
per claim, so no amount of contamination in a rule can hide anything from it:

| doubted | claimed as | what it is |
|---|---|---|
| **شاهدان** | شاه + *-dān* | the plural of شاهد, a witness — 84% of other bases fit it better |
| **لهستان** | له + *-stān* | Poland |
| **مردمان** | مرد + *-mān* | the plural of مردم |
| **کرنا** | کر + *-nā* | a trumpet |

**3,613 of 16,627 checkable claims doubted — 21.7% — across 108 of 120 rules.**
The affix map falls from 1,573 corpus word types traced to a rule to **1,397**.

**Nothing is deleted, and that is a decision rather than caution.** A doubted
sister is ranked last and still attached; a doubted claim is held out of
`word_types.rule_ids` — an assertion, the thing that puts a word in the search
screen's *formed with this affix* group — and recorded in the map's
`contested` list. A cosine is evidence about a claim, not a ruling on it.

**The limit is the rare words, and it is the wrong way round.** A claim needs
two corpus lines to average, so the words that fill a small rule's list —
occurring once in a thousand years of poetry — are exactly the ones that cannot
be checked. *-dān* keeps twelve of them.

### The stopword hole is closed, and it was two faults, not one

Session 7 recorded that Lucene's stock `persian` analyzer drops رفت، گفت، شد،
بود, so `/word` showed a count with no line under it. Fixed as **corpus
version v2**; v1 was never touched and is still queryable, which is how the
before-and-after could be measured with one query against each:

| `match_phrase` on `text_fa` for رفت | poems |
|---|---|
| `documents-v1`, stock `persian` | **0** |
| `documents-v2`, `persian_every_word` | **10,636** |

**Building it found a second fault the diagnosis had not named.** The stock
analyzer also runs a character filter mapping the zero-width non-joiner to a
space, so می‌رود is two tokens and گفت‌وگو is three — while
`corpus/wordtypes.py` counts each of those as **one** word. Left in, it would
have kept a whole class of compound out of reach of the very citation lookup
this change exists for: the counting and the search would have disagreed about
what a word is. Dropping the filter makes the tokeniser keep the ZWNJ inside
the token, which is what the counting does.

So `persian_every_word` is the stock chain minus a stopword filter and minus a
character filter, keeping lower-casing, digit folding and the two
normalisations. Those last fold ي ك ة and strip harakat — the same folding
`normalise` does, in the opposite direction. Direction does not matter, because
the text and the query pass through the same analyser; what matters is that
only one of them ever changes.

**A stopword list is a relevance device.** It belongs in a search engine
ranking news articles, where بود carries no information. In a corpus assembled
to measure which words were ever written, every word is evidence, and the
default cost us the citations for the four most quotable words in the language.

## 2026-08-12/13 (session 7) — semantics live, and what runs under a word

**The semantic-scoring question moved from research to running code.** The
direction was set in conversation with the project lead: embeddings are
wanted for plausibility, nothing is trained, the model is the one the sister
search project already runs, and where we disagree with upstream we build our
own version now and register it for later.

| built | state |
|---|---|
| conditions the grammar states on a base (12 rules) | read, recorded per result, never refusing |
| lexicon overrides (2 stems + رُفتن) | applied on read, snapshot-keyed, unconfirmed |
| `docs/FOR_THE_LINGUIST.md` | the linguist's questions in one file |
| ground-under-the-chain ranking | live; رفتن's 231 airborne forms sink |
| semantic pilot | **93% against 33% chance** — go |
| typicality per form (57 rules) | live in `/generate` and the build screen |

**Five faults found by running, not reading:** the ES Persian analyzer's
stopword list (رفت finds nothing; citations empty for common words —
registered, unfixed), plural-ان homographs contaminating the -dān/-stān
sister lists, a prose row masquerading as a verse line (158 GiB attention
buffer), a harakat mismatch caught by the override safety check on its first
day, and the sisters of small rules being too thin to test.

The findings below carry the detail, newest first.

## 2026-08-12 (session 6) — the last of the frontend, and the round trips

**Six tasks: 7.8, 7.9, 7.10, 8.1, 8.2, 8.3.** Every unblocked task in the plan
is now done. Phase 7 is complete — all seven screens, feedback on every one of
them, WCAG 2.1 AA checked two ways — and Phase 8 has its three round trips
built: rule proposals out to a git diff, the pack mirrored for karbon, the
feedback set out as a dataset.

| | |
|---|---|
| Python tests | 2,562 |
| frontend tests | 140 component, 83 layout and accessibility |
| corpus coverage | 4.1% of spellings, **45.7%** of running text |
| poems that can be dated | 34,521 of 133,148 — **26%** |
| unmatched spellings | 393,202, exportable |

**What remains is blocked, all of it.** 5.5 and 5.6 on semantic scoring, 6.2
on questions S1 and S2, 8.4 on the licence. Four new questions were recorded
rather than guessed at: S4 (screenshots), S5 (how a refused proposal is
recorded), and the two that were already there.

**Five faults found by running things rather than by reading them**, and none
of them by a test that already existed: a whole screen missing from git, an
input border at 1.26:1, a scrolling table no keyboard could reach, a rule-pack
loader nothing ever called, and a verdict the schema allowed about the app
itself. Each is written up below.

### The Persian analyzer eats the commonest words, and citations with them

Found while building the semantic artefact. The `documents` index analyses
text with Lucene's stock **Persian analyzer, whose stopword list includes
رفت، گفت، شد** and the other most frequent verb forms. A phrase query for رفت
returns **zero hits** in a corpus that contains it millions of times.

Two consequences, one already handled, one registered:

- the semantic batch tool now reads the Ganjoor source directly and matches
  whole tokens — which is also more honest about what a line contains
- **`/word`'s citations are empty for exactly those words**: the counts are
  right, they come from `word_types`, but the quoted lines are fetched through
  the analysed field. A reader sees "written 143,873 times" and no line to
  check it against. The fix is a `text_fa.raw`-style subfield or a custom
  analyzer without the stopword list, in a new corpus version — not done yet.

### Built on something written, or built on air — now a ranking signal

The project lead confirmed the direction: rank, never hide. Measured first on
رفتن — of its 510 words, **231 are built on an intermediate form nobody ever
wrote**; three unwritten step-one forms (*Raftbān*, *Ravāk*, *ravnāk*) carry
over 150 step-two words between them. A form's own attestation cannot see
that: *DošRaftbān* and a genuinely promising unattested form both read *none*.

`murfulu/scoring/grounding.py`, surfaced by `/generate` as `base_attested` and
used by the build screen's ranking. The shape of the answer matters more than
the arithmetic:

- **one grounded route is enough** — a form reachable through *Raftār* and
  through *Raftbān* is grounded, because the first route is real
- **the starting base never counts against a form** — it is the dictionary's
  stem, and judging it would judge the dictionary
- **null is "not checked", never "no"** — a request with attestation off sinks
  nothing
- the sunk rows say why, in the project's wording: the intermediate was *not
  found in this corpus* — never "does not exist", because absence from a
  thousand years of poetry is not a verdict (*pišrafte* is fine Persian and
  absent from it)

On the live stack: the 231 now sit at the bottom of رفتن's list with the
sentence under each, and the 279 whose every step is written sit above them.

### Where we differ from the lexicon, we now hold our own value — without forking

The project lead settled the working rule: karbon v1 is finished, it is
completed from here by issues and pull requests, and **waiting for it is never
the reason something stays wrong here**. Two files carry the two directions —
UPSTREAM.md for what goes to karbon, and the new
[FOR_THE_LINGUIST.md](FOR_THE_LINGUIST.md) for what only the linguist can
settle, gathered for one conversation.

The machinery is `rules/lexicon_overrides.yaml` plus
`murfulu/lexicon/overrides.py`: values applied as readings are read, never
written to the snapshot. What keeps it from becoming a fork, in order of how
much damage each prevents:

- **an override is refused when its recorded old value no longer matches** —
  that means karbon changed it, possibly the very correction being waited on,
  and applying anyway would overwrite it silently. This check caught its first
  error within the hour: mine (آزر against آزُر, a missing harakat).
- **an override applies only to the snapshot it was measured against**, which
  also keeps it away from every fixture-based test.
- everything is `confirmed: false` until the linguist rules, because karbon
  was built from his own rules and hand-checked — a difference may well be his
  later correction, not an error.

The occasion was the 39 irregular verbs: **33 of 36 match the lexicon
exactly**; آزردن and گسیختن differ in one stem; and **رُفتن (to sweep) has no
entry at all** — stripped of harakat it is the same string as رفتن (to go), so
a lookup silently returned the wrong verb. It is now a second reading of the
spelling, flagged, the same shape as مرد being *mard* and *mord*.

### The grammar says more than the engine was listening to

Asked whether everything the source defines is actually honoured. Audited it,
and the answer is *mostly, with one real gap*.

| | |
|---|---|
| rules stating a condition on their base | 186 of 195 |
| conditions that are the word class again — **already honoured** by `input_types` | 164 |
| conditions saying something more — **nothing read them** | **12** |

The twelve are now read. `rules/input_conditions.yaml` is an authored table —
twelve lines of Persian-Latin prose do not want a parser — and each entry
quotes the source verbatim, with a test that fails if the quote ever drifts
from the pack.

Two things it deliberately does **not** do.

**It never refuses to build a word.** V-010 says its stem *mostly* ends in
``-t`` or ``-d`` — **bištar**, a tendency. Turning a tendency into a filter
would state something stronger than the grammar does, and whether a failed
condition should stop a rule is the linguist's ruling. The condition is
recorded on the result and the word is still built.

**It does not guess what it cannot test.** V-001 and V-002 turn on the stem's
*group* — NKZ against NKDZ — and which of karbon's numbered groups those name
is written down nowhere we hold. Both are recorded and neither is tested; the
answer comes back as *not established*, which is a third value and never the
same as *failed*. OPEN_QUESTIONS S7.

**Measured on رفتن, and smaller than it sounds.** Of the 510 words, **483 have
no condition to check at all**. Of the 27 that do:

| | in the corpus |
|---|---|
| condition met | 6 of 11 — **55%** |
| condition broken | 2 of 16 — **12%** |

So the signal is real and worth having — a word that breaks its rule's own
condition is about a quarter as likely to have ever been written — but it
touches 5% of the output. It is not the thing that cleans up the result list.
Building on a base nobody ever wrote is, and that is 231 of the same 510.

Also unread, and worth a later look: `affix_variants` and `strength`. The 39
stem exceptions belong to karbon — we take stems from the lexicon rather than
deriving them — but that should be confirmed with the maintainer, not assumed.

### The semantic-scoring blocker was three questions, and two of them are now measured

Asked to look for embeddings, and the useful answer turned out not to be a
model name. Full working in [RESEARCH_SCORING.md](RESEARCH_SCORING.md);
`tools/count_semantic_pairs.py` reproduces the numbers.

**How much material does the data actually hold?** This decides feasibility
before any model does. On the v1 precompute, counting single-step derivations
only:

| | |
|---|---|
| rules with any attested base→derived pair | **63 of 195** |
| rules with ≥ 200 pairs | 22 |
| rules with ≥ 50 pairs | 47 |
| ≥ 50 pairs on **confirmed readings** alone | **7** |

So a per-affix semantic model is possible for a few dozen rules and for no
more. 132 rules have nothing to learn from, and no embedding choice invents a
pair.

**Do we need vectors over our own Latin forms?** RULE_DISCOVERY assumed yes,
because public Persian models are trained on Arabic script. Measured, the
assumption costs **6.2%**: 1,037 of the 16,714 linked corpus spellings have
more than one reading, and the engine composes the Persian spelling beside
the Latin anyway. A public model keyed on the spelling is usable, and the
ambiguous 6.2% gets flagged the way مرد already is. That turns a prerequisite
into a fallback.

**Is a bound stem a base a vector can exist for?** Three quarters of our pairs
— **12,341 of 16,069, 76.8%** — are built on a *kārbon*, which is a bound
form. But **1,753 of 1,930 stem forms (90.8%) do occur as corpus word types**,
because in Persian the past stem is also the third-person past and the present
stem is the imperative. Free-word bases occur at 92.4%: barely different. The
caveat that remains is what the vector *means*, and that 593 of those stems
occur fewer than ten times.

**What is left is which measure, and that is a real question.** A 2025 study
of Malay — an under-resourced language, off-the-shelf fastText 300d — found
the **affix centroid** fitted human transparency judgements *better* than
FRACSS, and it needs no base vector at all. Given the 76.8% above, that is a
larger advantage here than it was there. But a centroid scores a word that
already exists, and this project generates words that do not. Three shapes are
now on the table rather than one, and OPEN_QUESTIONS S6 asks whether to build
all three and let the feedback set choose.

**Two traps written down before anyone starts.** fastText's Persian vectors
are **CC-BY-SA 3.0** and share-alike travels to anything derived from them,
which touches the still-open licence question. And fastText composes a
plausible vector for *any* unseen string from its character n-grams, including
the affix we just attached — so scoring a generated word against a looked-up
vector of that word would measure the spelling and call it meaning.

### The figures a screen shows must be counted where they can be counted

Task 7.8. The corpus screen needs sizes and coverage, and the obvious way to
get them is to ask Elasticsearch. **Measured against the real index first, and
it is wrong twice over — both times in a way that looks right.**

| asked of the index | answer | truth |
|---|---|---|
| distinct spellings (`cardinality`) | 409,500 | **409,916** |
| words of running text (`sum` of `total_count`) | 29,288,852 | **25,497,189** |

The first is off because `cardinality` is an estimate and its precision
threshold caps at 40,000; the second because `word_types` holds one document
per **reading**, so every spelling the lexicon reads two ways is counted twice.
Neither error announces itself: 409,500 is close enough to pass for exact.

So the numbers are written by the batch job and read by the app, exactly as
the rule productivity is. `tools/run_ingest.py --report-out` writes
`data/corpus_report-<version>.json`; `murfulu/corpus/report.py` reads it back;
`/corpus` serves it beside the live alias state. **Nothing on the screen is
computed per request.** The pass that produced these figures held the corpus
in memory and counted it, and it reproduces task 4.5's measurements exactly:
16,714 of 409,916 spellings and 11,644,767 of 25,497,189 words.

`--report-only` runs the counting and the linking and touches no index, which
is how a version already in service gets described without being rebuilt.

**A report describing another corpus version is labelled, not passed off as
current.** Every count in this system is true for one version and no other.

### Three quarters of the corpus cannot be dated, and now it says so

**98,627 of 133,148 poems carry no century** — 74.1%. The dispersion chart on
the word screen, the thing that separates a real word from one poet's rhyme,
rests on the remaining quarter. That was recorded in OPEN_QUESTIONS N and
visible nowhere in the app; it is now a section of the corpus screen, with the
27 century-table entries that name a poet this corpus does not have.

### The unmatched pile is 393,202 spellings, and it is a deliverable

Shown on the screen, biggest first, with the sentence that stops it being
read as a fault list: the largest entries are و (1.1 million), ز, بر, آن, او —
grammar words a dictionary of headwords was never going to carry. The whole
list leaves the system as a file (`--unlinked-out`, 8.2 MB), because no screen
shows 393,202 rows.

### Exporting the feedback found a rule the schema never had

Task 8.3. The set leaves as JSON Lines plus a manifest that says what is in it
and what is not: no account names — the author is a stable pseudonym, which is
all inter-rater agreement needs — no screenshots, and **no licence**, because
PLAN 8.4 is open and a guess in a file that leaves the project is worse than
the gap.

Looking at the real records showed two of them grading **the app**. *Is this
app good, possible or wrong* is not a question, and REVIEW.md's own table
already mapped the app to a bug report. The schema had disagreed with that
document since it was written, and nobody noticed until the widget was used
and then the export read the rows back. The widget refuses it and now the
store does too. The two rows stay, because the table is append-only — which is
the right outcome: the record of what the system once allowed is itself worth
keeping.

### A mirror is only real if you can tell when it is stale

Task 8.2. DECISIONS settled *one master, one mirror* for the rule pack, and
that is an agreement rather than a mechanism — two editable copies become two
rule sets within a month whatever anyone agreed.

So the mirror is defined as narrowly as it can be: **byte-identical, plus a
manifest**. Copying rather than transforming makes "is the copy current?" a
comparison either repository can run, without loading anything or agreeing on
a schema. A transformed export would need its own version, its own tests, and
a way to tell a transformation bug from a stale copy.

One detail decides whether the check gets used or ignored: **a new commit here
must not make karbon's copy stale.** The manifest names the commit it came
from, which is worth keeping, but the *content* decides — otherwise every
commit would report the mirror as out of date and within a week nobody would
look at it.

**No pull request was opened and the command cannot open one.** A test asserts
that neither file contains the means. It was run against a scratch directory,
not against the karbon checkout, which is under review.

### The round trip works, and it rests on a byte-for-byte round trip

Task 8.1. An expert proposes a change in the app, a command writes it into the
YAML, and `git diff rules/` is the review. Accepting is committing; refusing
is `git checkout rules/`.

**That only works because the pack round-trips through PyYAML byte for byte**
— measured on all four tables — so an applied proposal shows up as the one
line it changed:

```
-  strength: typical
+  strength: obligatory
```

If loading and dumping reformatted anything, every review would be a two
thousand line diff and nobody would read one. A test pins it.

**Three of the four outcomes are reasons not to write.** A proposal is applied
only when the rule still says what the proposal was written against; if it
says something else, somebody changed it since and applying now would silently
revert them. That is the whole reason a proposal stores the old value.

**Running it against the containers found a gap nobody had noticed.**
`murfulu/db/rulesync.py` was written with task 6.0 and **nothing outside the
tests ever called it** — no command, no startup hook. The live `rules` table
was empty, and the first real proposal failed on the foreign key pointing at
it. `tools/sync_rules.py` now exists. The same class of thing as the ingest
report: a module that works, tested, wired to nothing.

### A whole screen was missing from the repository, and nothing noticed

Found while committing 7.10. `.gitignore` carried `build/` for the batch job's
output — the derivation dump, the affix map, the sister forms. **A pattern
with no leading slash matches at every depth**, so it also matched
`web/src/screens/build/`, and the build screen — nine files, the whole of task
7.4 — had never been committed.

Nothing caught it because everything that runs here runs against the working
tree: the tests passed, the container built, the screen worked, the layout
tests drove it against the real API. Only a fresh clone would have failed.

The pattern is anchored (`/build/`) and the nine files are in. A test now
fails if any file under a source tree is ignored — and it was checked by
putting the old pattern back and watching it fail, rather than by assuming it
would.

### Accessibility, measured twice, because one measurement misses

Task 7.10. The palette is checked with WCAG's own formula, and the pages are
audited with axe. Neither finds what the other does: **a page can pass an
audit simply by not happening to put two colours together on the day it ran**,
and a palette check cannot see a scrolling box nothing can focus.

Four real failures, none of which anyone had noticed by looking:

| | measured | AA asks |
|---|---|---|
| `--ink-faint` on white | 4.19:1 | 4.5:1 |
| `--ink-faint` on the sunk ground | 3.91:1 | 4.5:1 |
| `--line`, the border of every input | **1.26:1** | 3:1 |
| the unmatched-pile table | not focusable | keyboard operable |

The first two are body text — every count, every caption, every "what this
does not cover" line. The third is the only thing on screen saying where to
type, and it now has a token of its own: `--line-strong` for the edge of a
control, `--line` for a rule that merely separates. The fourth means the rows
past the fold existed for a mouse only.

**The check itself was the fifth fault.** It tested two grounds and the app
paints three: the tinted panel behind a finding is darker than the sunk grey,
and the darkened `--ink-faint` still sat at 4.24:1 on it. axe found it on the
page; the palette check should have found it first, and now enumerates every
ground rather than a list somebody remembered to write.

32 audit checks pass across all seven screens at both widths, including the
parts behind a click.

### Asking who is calling before the note is written, not after

Task 7.9. The rule *only an expert may grade a generated word* is enforced in
the store and over HTTP, and the widget has to agree with it **before** a
reviewer writes anything: the alternative is a careful note in Persian lost to
a 403. So one route was added — `/me`, in `murfulu/api/accounts.py` — which
reports the role and nothing else. It answers *who am I*, never *who else is
there*.

The button is in the shell rather than on a screen, as FRONTEND.md requires.
What is being judged comes from one of two places: a screen declares its own
subject, or a row hands over its own. Both matter — a record naming `/build`
instead of *Raftorow* is nearly useless when the screen showed 510 words.

**Running it surfaced a case none of the design documents stated.** The corner
button on a screen that declares no subject is about the app, and *is this app
good, possible or wrong* is not a question. A linguistic verdict about the app
is now refused with the reason on screen; REVIEW.md's own table already mapped
the app to a bug report, and nobody had noticed the two disagreed.

**The optional screenshot is not captured**, and the widget says nothing that
implies otherwise. It needs the mounted volume `screenshot_ref` points into
and no such volume exists — OPEN_QUESTIONS S4. The structured context, which
REVIEW.md calls the important half, is captured in full.

### A Latin form may not break; an identifier may

The layout test caught 85 px of horizontal overflow at 375 px, from a single
element: `lexicon-20260808:45e05ff66c37`, 264 px wide, inside `Latin`, which
sets `white-space: nowrap`. That rule is right — a Behnevis form split across
two lines is two different words — but a snapshot id is an address, not a
form. The screen passes a class that allows it to wrap. **A component test
could not have found this**; jsdom has no layout engine.

---

## 2026-08-12 (session 5) — the authored store

**Ten tasks: 6.0, 6.1, 6.3, and 7.1 through 7.7.** Postgres, the API's last
route, roles, and seven of the ten frontend tasks. The app now runs end to
end — search, word, build, affixes, explain, rules — against 133,148 poems and
1.7 million precomputed words.

| | |
|---|---|
| Python tests | 2,486 |
| frontend tests | 91 component, 37 layout |
| corpus ingested | 133,148 poems, 411,166 word types |
| derivation space | 1,738,711 words, 29 s, 2.0 GB |
| of those, ever written | 24,161 — 1.4%, a first rough measurement |

**Open questions, in the order they cost most:** S1 and S2 block 6.2 and
nothing else. S3 changes which Persian term labels a word class, and blocks
nothing. N leaves most of the corpus undated. 5.5 and 5.6 are unchanged.

Still unblocked and untouched: 7.8, 7.9, 7.10, 8.1, 8.2, 8.3. Postgres
exists — eight tables, two Alembic migrations, built inside the `db` container
— and with it the last of the eight API routes, the roles that guard them, and
a React shell in front of the lot. **Task 6.2 is blocked**, on two questions
the measurements below make precise.

### The scoring argument, on a screen

Task 7.7, with the whole pipeline re-run here to feed it: the precompute
(**1,738,711 words, 29 s, 2.0 GB**) and the productivity roll-up, both
reproducing the session-4 figures exactly.

**The source states a strength for 3 of 195 rules, and all three disagree with
the measurement.** V-010, V-011 and V-012 — all *-ār*, all written as
*typical* — land in the **top** band when measured, where *typical* would put
them in the middle. The screen leads with that, because it is the finding the
project's scoring argument rests on, not an error to be tidied away.

**A rule measured at zero and a rule nobody could measure are not the same
thing**, and the screen draws them differently. 29 of 195 could not be
exercised at all, each carrying its reason.

**A third test made the clean-machine assumption.** It asserted that no
`derivations` alias existed — true only where a precompute had never run, and
false the moment one had. It now asserts what it meant: that writing an index
does not move the alias. Three of these have surfaced this session, all found
by running the real pipeline rather than by reading the tests.

### The sāzāyi check did not exist, and building it took four measurements

Task 7.6. Nothing in the system ran the engine backwards. Each attempt was
measured against the same eight known words before the next was written:

| | |
|---|---|
| naive stripping | **1 of 8** |
| + looking stems up, not only headwords | 4 of 8 |
| + trying both capitalisations | 6 of 8 |
| + stripping recursively | **7 of 8** |

Every step was a real fault, and none would have been found by reasoning:

- **Half the words the grammar builds are built on a stem**, and a stem is a
  column on the verb row, not an entry of its own. `by_latin` could never find
  *raft*. `Lexicon.by_stem` had to exist.
- **Capitalisation belongs to the result, not to the base.** The engine
  computes it from the output word class, so stripping *-ār* off *Raftār*
  leaves *Raft* and the entry is *raft*.
- **One level of stripping is not enough.** *Ravandegi* strips to *ravande*,
  which is in no dictionary because it is itself built.

**The round trip is the whole design.** Every account is rebuilt forward and
only what reproduces the word survives, so **مولانا is refused** — stripping
*-nā* leaves a word the dictionary knows, and a decomposer that stopped there
would announce an Arabic name as a Persian derivation. That is the same fault
the affix backfill made in task 6.4, caught the same way.

**14% of 200 real corpus words get an account, at 12 ms each.** Not a
shortfall: most words are simple or borrowed, and a checker that explained 90%
would be inventing. *Raveš* comes back with two accounts — *raftan* and
*ravidan* — and the screen chooses neither, because that is a question about
meaning.

### The question the project started from, answered in one look

Task 7.5. *Which affix carries the meaning «جا»?* — **five**: *-ān*, *-dān*,
*-stān*, *-kade*, *-gāh*, each with the examples the source grammar gives.
That question, and the fact that answering it meant opening a grammar book, is
why this project exists.

**43% of the affix inventory has no meaning recorded.** Measured on the pack:
**81 of 189 affixes carry no semantic tag at all**. They are shown in a
section of their own that says the source is silent about them — not hidden,
which would suggest the inventory is complete, and not mixed in, which would
suggest they had been checked and found meaningless.

That number also sizes a job already on the list: the gloss templates the
linguist has to author (OPEN_QUESTIONS E) sit on 43 tags, and 81 affixes are
not attached to any of them.

### The build screen: possible and attested words, one at a time

Task 7.4. رفتن gives **510 words**; **2 are confirmed at reading level and 61
at spelling level**. The precompute's 1.4% — a first rough measurement, not a
result (2026-08-12 below) — is now something a reader can see one word at a time.

**Generated forms carry evidence now.** That took the read half of what 6.2
needs: a batched lookup against `word_types` that fills the *same* attestation
index the batch job uses. A second implementation of "is this word attested"
would have drifted from the first, and the two would have disagreed about the
same word.

**Four states, never merged.** *Not checked* — the corpus was not asked — is
not *not found*. And *not found* always names the corpus version, because
that is the only thing the sentence is true of.

**Going deeper is refused, and the number is why.** رفتن at depth 2 is a
0.5 MB answer. At depth 3 it is **24.7 MB** — 15,479 words, each carrying its
derivation. The screen says so instead of offering a control that would hang
the browser. This sharpens 6.2: the answer has to be **paged**, not only
cached, and those are the same decision.

**A live layout test caught a real fragility.** The client read a field
straight through and took the whole build screen down with a
`Cannot read properties of undefined` the moment the running container was one
version behind the code. Component tests could not see it because they stub
the API with the shape the code expects.

### The word screen, and a chart that admits what it cannot show

Task 7.3. *Ravšanā* is written 22 times in 21 poems by 14 poets — and only
**2 of those occurrences can be dated**. The chart says so under the bars
rather than drawing two and letting them stand for twenty-two. A century
inside the span with no occurrences is drawn as a gap, because the hole is
itself the evidence, and a word with nothing dated gets no chart and a
sentence explaining why.

**Citations are one line per poet.** Thirty occurrences in one poem is a
rhyme; one each in thirty poets is a word. Elasticsearch collapses on the
author, so the four lines shown for *Ravšanā* are four different voices —
Ferdowsi, Shafiei Kadkani, Akhavan Sales and the Farāmarznāma poet — rather
than four hits from whoever wrote most.

The line is found with the **same folding the counting used**. Looked up any
other way, a citation would sometimes fail to find the word in the very poem
its count came from.

### فردوسی was undated, and so were 26 other poets, because of a spelling

Found while building the word-detail screen: the dispersion chart for
*Ravšanā* showed two centuries out of twenty-one poems, and the citation from
Ferdowsi carried no date at all.

**27 of the century table's 43 entries name a poet slug this corpus does not
use.** They date nothing, and an entry that matches nothing looks exactly like
one that works. The table writes `ferdowsi`; Ganjoor's own slug is `ferdousi`.
Rumi, Rudaki, Sanai and Naser Khosrow are in the same position. **Only 16
entries match**, and the 26% coverage figure recorded last session rests
entirely on those.

**It was not repaired, because repairing it is not mechanical.** `ferdowsi` →
`ferdousi` is plainly the same poet, فردوسی on both sides. But `kamal-khojandi`
is nearest to Ganjoor's `kamal`, which is **کمال‌الدین اسماعیل, a different
poet** — a fuzzy match would have dated one poet's work with another's
century. The question is recorded as OPEN_QUESTIONS N.

What changed is that the gap is now **visible**: `centuries_without_a_poet()`
reports it and the ingest prints it. Before, a table entry that matched
nothing was silent.

### The test suite was destroying the corpus, silently

Found by building the search screen against real data. Running `make check` on
a machine with a live cluster **deleted every `documents-*`, `word_types-*`
and `derivations-*` index** and left the aliases pointing at nothing: 133,148
poems and 411,166 word types, ninety seconds and four gigabytes to rebuild,
gone every time the tests ran. Nothing failed. `/search` simply answered "index
has not been built".

Two faults of the same shape, both now fixed and both verified by ingesting,
running the suite, and checking that the corpus and the aliases are exactly as
they were:

- **The index tests cleaned by wildcard**, so they deleted indices they had
  never created. They now use version names of their own and refuse to delete
  anything without that prefix.
- **Three live fixtures moved the aliases the app serves from** — which is the
  point, they test the real route — but did not put them back. An alias is now
  saved before and restored afterwards, however the test leaves it.

Also found: **the ingest was silently producing an undated corpus.** Without
`MURFULU_GANJOOR_CENTURIES` every poem is undated, every word gets a null first
and last century, and the dispersion chart — the thing that separates a real
word from one poet's rhyme — has nothing to draw. Nothing said so. It does now.

### The search screen, on the real corpus

Task 7.2. Built against 133,148 poems, with `*nā` returning its 57 real hits
through the whole stack.

**The two-group split is the screen.** *Tonoknā*, formed with the affix, and
*Fanā*, an Arabic loan where those letters are not a suffix at all, are not the
same answer. The first group is empty today, because filling it needs the affix
map from 6.4 to have been run for this corpus version — so the screen says *we
have not worked out which of these were formed this way*, never *none were*.
Two different claims, not merged.

**Facets count the whole result set, not the page.** That meant adding
aggregations to `/search`. Counting the returned page would have given a
figure that changes with the page size and looks exactly like a real one —
the same trap as the 10,000-hit cap in task 4.7.

A facet **writes its term into the query box** rather than filtering behind the
scenes. One way to express a search, and the reader learns the syntax by using
the interface.

**A query is syntax, so it is shown left to right.** With `dir="auto"` the same
query in two scripts — `*nā` and `*نا` — puts the asterisk on opposite sides,
and one of them gets copied wrongly.

### The app has a front door now

Task 7.1, all but its last clause. `web/` is a Vite + React + TypeScript app,
36 tests, and `docker compose up` serves it beside the API with deep links and
the `/api` proxy both working against the live containers.

Three things the shell settles, each because getting it wrong later is
expensive:

- **The design system is tokens, and a test enforces it.** A stylesheet that
  names an undefined token does not fail — the browser drops the declaration
  and the element renders wrong — so the check has to live in the test suite.
  A second test rejects any colour written outside the token file.
- **Logical properties only.** No `left` or `right` in any stylesheet, enforced.
  A right-to-left layout built by mirroring a left-to-right one breaks the
  first time a component is nested inside another.
- **The Latin island is a component, not a habit.** Persian and a Behnevis form
  share a table cell, and `dir` alone is not enough — without
  `unicode-bidi: isolate` the punctuation around the form reorders. It also
  refuses to lower-case: *Porsidan* and *porsidan* differ by nothing else.

Numerals go through `Intl`, not a digit table. Persian has its own thousands
separator, and every corpus figure in this project is past a thousand.

**375 px turned out to be worth testing rather than looking at.** jsdom has no
layout engine, so the component tests could say the navigation was present and
nothing more. Playwright now loads every screen at phone and desktop width and
checks what a reader would hit: nothing pushing the page sideways, every
navigation link at least 44 px, the last one reachable, the layout genuinely
right-to-left.

**It found two bugs on the first run**, both invisible to the 36 component
tests:

- **The skip link sat half above the top edge when focused.** A negative `top`
  plus a percentage transform, and the arithmetic did not land. A keyboard
  user's very first stop was half off screen.
- **The navigation was cut off flat at the edge.** Six items do not fit in
  375 px, so the row scrolls — but a word sliced in half reads as a clipping
  bug rather than as an invitation to scroll. It fades now.

And a third thing, about testing rather than the app: **the first version of
the skip-link test passed while the bug was there.** It asked whether the
element intersected the viewport at all, which half of it did. It now checks
the whole box.

**A gap the shell found:** the interface has to explain *kārnām* and
*kārbon-e do* without a manual, and those explanations exist in
`murfulu/rules/types.py` while **no route exposes them**. The `Term` component
takes them as props and invents nothing, which is right; something still has to
supply them. OPEN_QUESTIONS S3.

### The document contradicted itself about the derivation cache

ARCHITECTURE lists a `derivations` **table** under Postgres and, forty lines
later, says every live result is cached in the `derivations` **index**. Both
cannot be built without one of them being dead weight that quietly disagrees
with the other.

It is settled by the document's own rule of thumb — *if losing it means
re-running a batch job, it goes in Elasticsearch; if losing it means losing
human work, it goes in Postgres*. A cache is rebuildable by definition. The
index already exists, already holds 1.7 million words, and is what task 6.2
writes to. **No Postgres table was created for it**, and the contradiction is
recorded in ARCHITECTURE rather than left for the next reader to trip over.

### Append-only is now a trigger rather than a sentence in a document

REVIEW.md says *append-only* twice. Feedback is the one thing in this system
that no pipeline can recreate, and it is the evaluation set the four scoring
weights will be fitted against, so an accidental `UPDATE` in a console is a
real loss and not a hypothetical one.

The migration installs a Postgres trigger that raises on every UPDATE and
DELETE against `expert_feedback`. A test issues both and asserts both are
refused. Nothing in the application layer can turn it off.

### Three rules from REVIEW.md are enforced instead of described

- **A linguistic verdict may only come from an expert.** The store refuses it
  for the `user` role, with a message naming the role. Task 6.3 still has to
  do the HTTP half — deciding *who is calling* — but the rule itself no longer
  depends on the route remembering it.
- **A graded verdict and the `linguistic` category imply each other.** One
  check constraint, both directions: a bug report cannot carry a verdict, and
  a linguistic judgement cannot go ungraded. Free-text notes cannot be
  aggregated; that is the whole reason the verdict exists.
- **Feedback about karbon's data marks itself.** `lexicon_entry` and
  `stem_derivation` are set to `owner: karbon` on write, so the export is one
  query rather than a rule repeated at every call site.

### `/feedback` closed the last gap in the API

Task 6.1 is finished: **all eight routes the plan names are up**, OpenAPI
renders them, and **2,471 tests pass inside the container** against the real
Postgres and the real Elasticsearch, nothing skipped.

There is deliberately **no route that edits or withdraws a record**, and a
test asserts it. A trigger that refuses UPDATE would be pointless next to an
HTTP surface that offered one.

**The route authenticates nobody**, and that is written into its docstring
rather than left to be discovered. The caller names an account and it is
looked up; a disabled account is refused. Task 6.3 supplies the missing half.
Until then the app runs only on the project lead's machine, which is what
ARCHITECTURE already specifies.

### Roles are now enforced by the token, not by the request body

Task 6.3. Verified against the running containers: **401** with no token,
**403** for an account with the `user` role, **201** for the same verdict from
an expert. `/feedback` no longer accepts an author field at all — the body
cannot choose an author, so it cannot choose the wrong one.

**Tokens rather than passwords**, because the app is API-first and local: a
token is issued once, pasted in, and revoked when it is done with, and nothing
has to hold a password, reset one or expire a session. Only the SHA-256 is
stored, with no stretcher — a token is 256 bits of operating-system
randomness, so stretching would cost without adding safety. That reasoning is
written beside the code, because it stops holding the moment a human-chosen
secret is stored.

Nothing that carries a record is ever deleted: a token is **revoked**, an
account is **disabled**. Feedback is append-only and names its author, so a
credential that vanished would leave records pointing at nothing.

### Live generation is not slow, and that changes what a cache is for

Task 6.2 is **blocked**, and the measurement is why. رفتن gives 510 words at
depth 2, **15,479 at depth 3 in 0.2 seconds**, and 22,952 at depth 4 — the
space saturates, and building it is nearly free. What costs is checking each
form against the corpus and writing it.

So a cache that avoids re-generating saves almost nothing. Two questions have
to be answered before one is built, both recorded in OPEN_QUESTIONS as S1 and
S2, because both change stored data: what a cached answer returns, given the
stored path drops three of the fields `/generate` shows per step; and how a
live result reaches an index whose records were merged across the whole
lexicon without replacing them with single-source ones.

### The rules table had to be the loaded rule, not the sketched one

The sketch has `input_type`, `semantic_tag`, `example` — singular. The rule
pack has had plurals since Phase 1: a rule takes several input types, carries
several tags and gives several examples, and templates carry a pattern and
typed slots on top. Storing the singular version would have lost data on the
way in. The table now mirrors `Rule` field for field and the real pack loads
into it — **195 rules and 17 glide rules**.

The loader **never deletes**. A rule id is permanent and a retired rule keeps
its row with `active` false, so an id in the database that the pack no longer
mentions is a fault to look at, not a row to tidy away. It is reported.

## 2026-08-11 (session 4) — Phase 5: the derivation space, measured

**Six tasks finished: 4.7, 5.2, 5.3, 5.4, 6.4 and most of 6.1. 2,440 tests
pass, in Docker as well as on the host.** The system now builds every word its own
grammar allows, checks each one against a thousand years of poetry, and serves
the result over HTTP.

| | |
|---|---|
| words the rules allow, two steps deep | 1,738,711 |
| of those, ever written down | 24,161 — 1.4%, a first rough measurement |
| with a reading the lexicon confirms | 1,824 |
| rules with a measured productivity | 166 of 195 |
| rules with at least one attested output | 156 |
| one full run | 61 seconds, 2.0 GB |
| corpus ingested into the search index | 133,148 poems, 411,166 word types, 41s |
| spellings written exactly once | 222,859 |
| corpus words traced to the rule that formed them | 1,573 |
| words in use we can derive but not confirm | 10,877 |

Three gaps were found by building rather than by reading. Two are closed:
the ingest now fills `documents` and `word_types` (4.7), and the affix pass
now says which rule formed which corpus word (6.4). One remains: **there is no
Postgres layer at all**, which is why `/feedback` does not exist (6.0).

## 2026-08-11 (session 4) — the detail

### The affix split works, and the first version of it was wrong

`*nā` now returns 57 hits split into **5 formed with the affix and 52 that
merely end in those letters**. The five are *Derāznā*, *Farāxnā*, *Karnā*,
*Ruhinā*, *Yāninā* — all rare, all by N-072. The 52 include *Fanā* at 4,315
occurrences, an Arabic loan where *-nā* is not an affix at all.

**The rule for who may claim a word had to be tightened against real data.**
The first version claimed any spelling the corpus has and the lexicon lacks,
reasoning that گفتار is plainly *goft* + *-ār* and the dictionary merely does
not list it. Run against Ganjoor, that attached *-nā* to **مولانا، نخلنا،
لقینا and eighty more Arabic phrases** ending in the possessive نا.

An unlinked spelling means the lexicon knows *nothing* about the word,
including whether it is Persian at all. So only a **confirmed reading** may
claim: 1,573 word types. The 10,877 unconfirmed ones are kept as proposals,
never asserted — and that list, each entry carrying the rule that would form
it, is the strongest version yet of the request in UPSTREAM B2.

This is the project's own principle turning up again: a wrong output that
looks plausible is worse than one that is obviously broken. *Mowlānā* tagged
as *mowlā* + *-nā* would have looked entirely reasonable.

### The lexicon reads پهن as `pen` and پهنا as `Pahnā`

Found while asking why *Pahnā* — a real word, 141 occurrences in 126 poems —
was not credited to the rule that forms it. Because we build it from the base,
and the base is read `pen`, so we produce *Penā*.

The lexicon contradicts itself here: پهنا is `Pahnā`, پهنه is `Pahane`,
پهناور is `pahnāvar`, and the base they are all built on is `pen`, with no
`needs_review` flag. **2,437 bases show that shape, 1,964 of them unflagged.**

Not all 2,437 are faults — the sample mixes the known ه-as-`h` fault with
ordinary vowel reduction inside compounds — but the consequence is the same in
every case: a derivation built from the base cannot match the corpus form of
the derived word. Recorded as UPSTREAM A3.

### The search works on real data now, and `*nā` proves why the split matters

Nothing was writing `documents` or `word_types` into Elasticsearch. The whole
corpus now goes in: **133,148 poems and 411,166 word types in 41 seconds.**

More word types than spellings — 411,166 against 409,916 — because a spelling
with two readings is two documents. مرد the man and مرد the dead carry the same
evidence and are not merged.

The first real `*nā` search returns **57 hits**, and they are exactly the
mixture SEARCH.md predicted:

| formed with *-nā* | merely ends in those letters |
|---|---|
| Pahnā (پهنا), Ravšanā (روشنا), barnā, Mānā | Fanā (فنا, 4,315), Bonā (بنا), Minā (مینا), āšnā |

The right-hand column is mostly Arabic loans where *-nā* is not an affix at
all. A reader studying the affix gets four useful words and eight misleading
ones in one undifferentiated list — which is the founding complaint restated,
and why the two-group split is worth its own task (6.4).

### A search that reported 10,000 hits whatever the answer was

Elasticsearch stops counting matches at 10,000 by default and reports that as
the total. Several of these searches exist *to produce a count* — the hapax
query above all — so the number is the answer, not a footnote.

Asked exactly: **222,859 spellings occur exactly once**, not 10,000. A
twenty-two-fold error, and it looked like a plausible round number.

### The HTTP surface, and two things it refused to pretend

Seven of the eight routes are built. Two decisions in it are worth keeping.

**`/search` takes no index parameter.** The obvious API is *search this index*,
and it would have been wrong: every field the query language names —
`stem1`, `type`, `rule`, `author`, `count` — is a `word_types` field. Pointed
at `derivations`, whose fields are called `form_latin` and `output_type`, the
same query matches nothing and looks exactly like a query that found nothing.
The route searches `word_types` and says so.

**The two-group result split has nothing to split on yet.** SEARCH.md divides
hits into *formed with this affix* and *merely ends in these letters*, and the
first needs `word_types.affixes`. The mapping declares that field and **no
pipeline fills it**, so today every hit lands in the second group. That is the
honest answer — we do not know how those words were formed — and the missing
pipeline is now PLAN task 6.4 rather than a silent hole.

**`/feedback` is not built.** Feedback is append-only in Postgres, and there is
no Postgres layer at all: no models, no alembic, no migrations. The plan never
scheduled one, so it is now task 6.0. Inventing a different store to make the
route exist would have contradicted both ARCHITECTURE and REVIEW.

### Sister forms say more than a score does

The evidence to put beside a word nobody has written is the list of words the
**same rule** did make. For V-010, *-ār* on the past stem, the real corpus
gives 52, and the first six are:

| | | evidence | poems | poets |
|---|---|---|---|---|
| Didār | دیدار | confirmed reading | 4,434 | 212 |
| Bordār | بردار | confirmed reading | 1,618 | 190 |
| Kaftār | کفتار | confirmed reading | 67 | 37 |
| Goftār | گفتار | spelling only | 3,461 | 189 |
| Gereftār | گرفتار | spelling only | 2,061 | 194 |
| Kardār | کردار | spelling only | 2,023 | 161 |

The ordering is deliberate and is **not** by frequency. *Goftār* occurs 4,813
times and still sits below *Kaftār*, which occurs 75, because the lexicon
confirms how *Kaftār* is read and has no entry for *Goftār* at all. A confirmed
reading is stronger evidence than a common spelling — and the words that fall
to the second group are the same list UPSTREAM B2 wants to send to karbon.

Second in the ordering is **how many documents**, not how many occurrences.
Thirty hits in one poem is a rhyme.

### The stored record was losing four fields

Found by making the round trip a test rather than assuming it. A derivation
written out and read back came home missing the first and last century, the
`spelling_unlinked` flag and the other readings of its spelling.

Each of those does real work. Without the centuries a stored word cannot draw
its own dispersion chart, which is the whole "did this word survive?" question.
Without the unlinked flag a **gap in the dictionary looks exactly like a
homograph collision** — the distinction this project made a point of, undone
silently at the storage layer.

All four are stored now. The general lesson: a `as_document` / `from_document`
pair that is not pinned by a test will drift, and every pass downstream then
measures something slightly different without anything failing.

### The grammar states a strength for 3 of its 195 rules

RULE_PACK.md's open problem — authored strength versus measured productivity —
turns out to be almost entirely one-sided. `strength` is set only where the
source writes *bištar*, "mostly". That is **three rows**: V-010, V-011 and
V-012, all of them *-ār*.

So the plan's test "list the rules whose measured value disagrees with the
authored strength" has three candidates, and **all three disagree**: the source
hedges them as tendencies, and the measurement puts them in the top third of
the pack.

The hybrid RULE_PACK.md proposes — authored strength as the prior, corpus P as
the evidence — has almost no prior to work with. Either the linguist authors
strengths, or the measure stands alone. Recorded as OPEN_QUESTIONS item R.

### Five rules score at the top because they return their own input

The first productivity ranking put V-049 first at a realisation rate of 0.77 —
seven times the next affix. V-049 is a `kind: none` rule: the present stem
written as a noun, *Parhiz*, *Tarāš*. **The output is the same string as the
input**, which was already a word in the corpus before any rule ran.

The same thing happens through a second route: *-an* rebuilds the very
infinitive the generation started from, so V-005 and V-006 sit at an echo share
of 0.96.

`echo_share` now counts it. Five rules are affected, and the honest top of the
list is *-eš* (V-033, 0.44), *-e* (V-034/035/036, 0.42), *-ān* (V-029, 0.35)
and *-ande* (V-022, 0.22) — all with an echo share of zero.

The general lesson is worth keeping: **a measure of productivity that counts
attestation will always reward a rule that produces something already
attested.** Any later scoring has to exclude a form identical to its own base.

### Baayen's P is too small to rank anything here

Measured over 156 rules: **median P = 0.0069**, and 0.0002 over confirmed
readings only. The reason is structural rather than a fault — P is hapaxes over
tokens, and the attested output of a rule is dominated by a few very frequent
words, so the ratio collapses.

The realisation rate carries the signal instead: attested built forms over all
built forms, which is Monakhov's simulate-and-check measure and the one this
pipeline was shaped for. Both are stored; the P is kept because the literature
expects it, not because it discriminates here.

Only **70 rules have a P over confirmed readings**, against 156 over any
attestation. The gap is the lexicon's missing headwords again (UPSTREAM B2).

### How much of what the grammar allows is attested — a first rough measurement

The first precompute run applied every rule to every fully-reviewed lexicon
entry, two steps deep, and asked the corpus about each result.

| | |
|---|---|
| input | 5,208 readings — verbs, adjectives, abstract nouns |
| forms built | 1,849,284 |
| words after merging | 1,738,711 |
| attested at reading level | **1,824** |
| attested at spelling level | 22,337 |
| run time | 28s generating, 61s end to end |
| output | 1.62 GB, peak 4.2 GB memory |

**24,161 of 1,738,711 — 1.4%, as a first rough measurement and not a result**
(the project lead, 2026-10-19). The rules are not yet confirmed by the
linguist (a rule strength is stated for 3 of 195), most of the attestation is
at spelling level and may be homographs, the lexicon has changed since this
run, and the corpus is poetry only. What the run shows is that the gap between
what the rules permit and what was written can be measured; how large it is
for Persian stays open until the rules and the data are complete.

The two figures are kept apart for the reason FINDINGS already records:
`reading` means the lexicon confirms how the word is read, `spelling` means the
letters occur but no reading confirms them. رفتار sits in the second group at
1,206 occurrences — the word is obviously real, the dictionary just does not
list it (UPSTREAM B2).

### 29 rules produced nothing, and each for a stated reason

Of 195 active rules, 166 fired. The other 29 are not a productivity of zero;
they are rules this pass could not exercise:

| how many | which | why |
|---|---|---|
| 9 | S-01 … S-09 | stem rules: infinitive → stem, a different operation |
| 16 | 10 templates, 6 slot rules | compounding, which ARCHITECTURE deliberately never precomputes — the candidate space is a product, not a sum |
| 4 | N-009, N-013, N-017, N-091 | need a pronoun or a preposition, and the lexicon pool holds neither |

**Task 5.3 has to report these as unmeasured, not as unproductive.** A rule
with no output has no Baayen P, and printing 0.0 would read as a finding when
it is an absence.

### The estimate of the derivation space was wrong in both directions

LEXICON_ANALYSIS §6 estimated ~508,000 forms by multiplying rows by rules.
Measured: **177,000 at one step and 1,849,284 at two.** Step 1 was
over-estimated, because most rules do not fit a given entry; step 2 was never
estimated, and it is eleven times larger.

The categories also differ far more than an average suggests. A verb gives 34
forms at one step; an **abstract noun gives one**, because اسم معنی maps to
`karnam` and **exactly one rule in the whole pack takes a kārnām**. The 82
rules that take a `nām` belong to اسم ذات, which is 64% reviewed and outside
the first run by design.

### Merging one form across the whole lexicon, not one entry

`engine/dedupe.py` groups forms within a single generation. The precompute has
to group across all 5,208 entries, because the document id is the form plus its
output class. Writing per entry and letting Elasticsearch key on that id would
have looked correct and silently thrown away every derivation but the last —
**439,078 of the 1.7 million words are built more than one way.**

Each stored path records the lexicon entry it started from, and the merge is
keyed on the **whole path, not on the rule chain**. That distinction was worth
95,021 paths: that many forms are reached by the *same rule* from two different
lexicon entries, and keying on the chain alone dropped the second while the
record still claimed a single source. Caught by measuring the merge rather than
trusting it.

### 10,270 words where two Persian spellings share one reading

The document id is the Latin form, and Behnevis is phonemic — so two Persian
words that read the same way arrive at the same record. خواستن and خاستن are
the classic pair.

**Both spellings are kept.** `form_fa_variants` carries the second rather than
letting the first silently win, and the mapping gained a field for it. Whether
they are one word or two is a linguistic ruling, not something to settle by
picking a dedup key — OPEN_QUESTIONS item Q.

### A live cluster caught what the tests could not

The document carried `generated_at: ""` for a run with no timestamp. Every unit
test passed; Elasticsearch refused the write — an empty string is not a date.
The field is now omitted rather than blanked, and a run with no timestamp has a
test of its own. Worth repeating: `dynamic: strict` mappings are only actually
checked against a real cluster.

## 2026-08-11 (session 3) — Phases 0–4 built, Phase 5 started

**26 of the plan's tasks are done; 2,327 tests pass.** Foundations, the rule
pack, the engine, the lexicon, the corpus and search all work end to end:
a Persian word goes in and derived words come out, each carrying its
derivation, and each can be checked against a thousand years of poetry.

Measured this session, on real data rather than fixtures:

| | |
|---|---|
| rules in the pack | 212, of which 2 still flagged |
| words from رفتن at two steps | 510 |
| Ganjoor documents | 133,148 poems, 25,497,189 words |
| distinct spellings | 409,916 |
| corpus text we can read | 45.7% |

Everything that could not be read from a source is flagged, never guessed.
Items belonging to karbon rather than here are collected in
[UPSTREAM.md](UPSTREAM.md).

### The session's findings, newest first

### "Attested" and "in the dictionary" are not the same question

Running attestation on the real corpus showed that گفتار (4,813 occurrences,
3,461 poems, 189 poets), رفتار and روش all come back at level `spelling`, not
`reading` — because **the lexicon has no entry for any of them**. They are
obviously real words; the dictionary simply does not list them.

So `spelling` covers two situations that must not be shown the same way:

- the corpus reads this spelling as a **different word** (مرد is *mard* or
  *mord*, not whatever we built) — genuine doubt about our form
- the corpus has the spelling but **no reading exists to compare against** —
  a gap in the dictionary, not a doubt about the word

`spelling_unlinked` separates them. The count of unlinked-but-frequent
spellings is also a direct measure of what the lexicon is missing.

### The lexicon separates homographs better than we were using

Checked after a prompt to look at karbon. مرد is **two entries that differ in
three ways at once**:

| | reading | class | written |
|---|---|---|---|
| a man | *Mard* | اسم ذات | capital |
| he died | *mord* | صفت, past stem of مردن | lower case |

So it is not "one spelling, two sounds". It is two different **kinds of word**,
and the word class is what the rules key on — which matters more than the
sound. Of the 1,805 repeated spellings: 1,324 differ in reading, 466 differ in
class, and 459 are the same in both, which is the dictionary listing one word
in several senses.

**What nothing anywhere resolves** is which of the two a given line of poetry
means. karbon's "ambiguity" work is a different problem — whether a medial و
is *o*, *u* or *ow*, and verb transitivity — not homograph selection in
running text. No document in the archive addresses it either.

### 7,212 lexicon rows carry a second reading — now used, previously dropped

The `phonemic_variants` column is not a copy of `phonemic`. **7,212 active
rows hold a genuinely different second reading** of the same word — آبرو is
*Ābrav* or *Ābrov*, آب‌آشنا is *ābāšnā* or *ābāšenā*.

The wrapper read only `phonemic`, so every one of those alternatives was
silently dropped and generation could build a whole family of words on a
reading the dictionary does not commit to. **Fixed the same session**:
`Reading.latin_variants` carries them and generation builds from each.

Two details worth keeping. The stored variants are always lower-case while the
primary keeps its capitalisation, so the primary's case is applied to each —
case is meaning in Behnevis, and a variant is the same class of word. And **no
verb has a variant**: stems live in their own columns, so nothing about verb
generation changes.

Some variants are visibly broken transcriptions — آبخوست lists *ābxvst*, no
vowel between v and s, which is the و-read-as-v fault LEXICON_ANALYSIS §4
already measured. They are carried as the lexicon has them, not silently
filtered.

### The Persian was silently drifting away from the Latin

Found while gathering examples for a question to the linguist. When a glide
rule fired, the Latin got the *y* and the Persian did not:

| Latin | Persian was | should be |
|---|---|---|
| Dānāyi | دانای | **دانایی** |
| Guyeš | گوش | **گویش** |

The second one is the dangerous shape: گوش is a **real Persian word** meaning
"ear". A wrong output that is also a real word is far worse than one that is
obviously broken, because nothing looks wrong.

Fixed: when a glide rule's result contains the glide consonant, the Persian
join takes ی too. Three tests pin it.

**Still wrong, and now recorded as such:** glides whose result adds a *g*
rather than a *y* — *taze + i* is *Tāzegi* / تازگی, but the Persian comes out
تازهی. The ه has to drop first. That is the Behnevis joining rule PLAN 1.3
already flags as unextracted from the specification.

### A stem written *ow* is *av* the moment anything follows it

The engine's first run produced *rowān* where the grammar's own example says
**ravān**. The glide table has rows for *ow + a* and *ow + e* and nothing else,
so *ow + ā* fell through.

Rather than add rows, the lexicon was measured. **Not one of its 45,579 words
contains *ow* anywhere.** The sequence exists only in the six present stems —
row, šow, dow, derow, šenow, šenāow — and never survives into a finished word.
Everything built from them is *av*: 16 words begin *Ravān-*, 28 begin *ravā-*,
17 begin *šav-*, and the infinitives are *šenavidan* and *šenavāndan*.

**šenavgar** settles the consonant case: *gar* is not a vowel, and the stem is
still *šenav*.

So this was never a vowel-joining rule. The stem's working form is *rav*; *ow*
is how it is written standing alone, which is exactly how a stem appears in a
list of stems. The project's own alphabet table agrees — it lists the vowels as
ā a e o i u and names *ow* separately, as a sound for *owj* and *ferdows*.

One line in `rules/decisions.yaml` replaced two glide rules and fixed every
affected word at once. G-15 and G-16 are retired as two instances of it.

### The glide table contradicts itself on one row — read before task 2.2

The glide table's columns are *left vowel*, *right vowel*, *result*, *example*.
Most rows are consistent:

```
ā | a | āya | ā + am = āyam        ✓
ā | e | āye | Pā + e = Pāye        ✓
```

**G-01 is not:**

```
ā | e | āye | ā + ande = Āyande
```

Its example joins `ā` with `ande`, whose vowel is *a*, not *e*, and yields
`āya`, not `āye`. So G-01 either has the wrong example or the wrong vowel
columns — and it duplicates G-03, which states the same left/right/result with
an example that does fit. Whoever implements PLAN 2.2 must not quietly pick
one: it needs the linguist. Recorded in OPEN_QUESTIONS.

### karbon has the stem rules, but not the word-formation rules

Checked after a prompt to look there. The answer splits in two:

**The stem rules are in karbon, in full.** `src/karbon/morphology/rules.py`
implements all nine, with the exception lists, **and with Latin forms** — which
the source document does not give. Its `docs/phonemic_bible.md` is a
transcription of the same stem-rules document.

**The ~200 word-formation rules are not in karbon.** Grepping the whole
repository for the grammar's vocabulary (kārnām, barnām, Goftār) returns one
hit, in a generated report. karbon converts script to Latin and extracts stems;
it does not derive words. So the rule pack built here is not duplicating
anything.

**Cross-check result: the transcriptions agree.** Of the 39 exception verbs,
karbon has 38 and every shared entry matches, apart from diacritics. Two
differences worth recording:

- **karbon strips short vowels**, this transcription keeps them (رِشتن، سُفتن،
  گُزیدن، رُفتن), because the source writes them. Any match between the two —
  or between either and the lexicon — must strip diacritics first, or four
  verbs silently fail to line up.
- **karbon omits نهفتن entirely**, the verb whose present stem the document
  writes as ؟. It declined to guess too.

karbon's readings for the other two unresolved rows are now recorded in
`rules/stem_exception_resolutions.yaml` **with attribution** — گشادن → گشاد /
گشا via rule 4, and افراشتن → افراشت / افروز, taking افروختن as a separate
infinitive. They are a second reading of the same document, not a new source,
so each carries `read_by: karbon` and the original wording stays visible.

### The rule pack exists: 212 rules

81 verb rules, 105 nominal rules, 17 glide rules, 9 stem rules. Built by
`tools/build_rule_pack.py` from the two raw transcriptions plus two authored
tables, so it can be rebuilt and re-checked rather than being a hand edit.

**Six rules are flagged, and nothing else was guessed.** Three affix spellings
(`-bāž`, `pa-`, and `-mānd` — where the source writes *-mānd* but its own
example *dānešmand* says *-mand*) and the three stem exceptions the document
leaves open.

The Persian label and explanation on each rule are **composed** from the
grammar's own type names, not written freehand. For V-010 that reproduces the
text already in RULE_PACK.md word for word, which is a useful check that the
composition matches what the linguist expects to read.

### A parser that failed silently

The first version of the input parser matched the longest word-class name a
cell started with. For a compounding row — *"Kārboné yek + o + Kārboné do az
Hamānkārvāže"* — it matched `Kārboné yek`, ignored the rest, and produced a
rule with **one** slot instead of two. No error, no flag: a broken rule that
looked exactly like a working one.

Fixed by parsing compounds as templates and reporting every fragment that does
not resolve. The lesson is in the module docstring: a silently dropped slot is
worse than a flagged one.

All nine compounding rules now come out with both slots and the constraints
RULE_PACK.md documents — V-017 *Zadoxord* (different verb), V-018 *Goftogu*
(same verb), V-044 *Kešākeš* (same stem), V-021 *Budonabud* (negated).

### One source typo worth knowing about

Verb row 10 gives its example as *Gotār*. It should be *Goftār* — the *f* is
missing. Transcribed as written, because PLAN task 1.5 turns every example into
a test and that is exactly where a mistranscription should surface.

## 2026-08-11 (session 3, earlier) — Phase 0

Built the skeleton, the tooling, the Docker stack, the transcription of the
source grammar, the id register, the semantic tag set, the lexicon wrapper, the
category mapping, the corpus adapter interface and the Elasticsearch mappings.
133 tests, `make check` green, and the suite also passes inside the built image
(6 of them skip there — they need a live cluster).

### There is an earlier prototype at `~/Code/mosaic/murfulu`

Found on the second pass, when the whole machine was searched rather than just
the Drive archive. Dated April–May 2026: a working pipeline, a FastAPI backend,
a React frontend, Postgres with alembic migrations, and Ganjoor / Wikisource /
Miras fetchers. Not the same repository as this one.

What it holds that matters:

- **The nine stem rules**, seeded from the same stem-rules document, as
  `…-stem-1` … `…-stem-9`. Written in Arabic script, not Latin.
- **19 hand-picked derivation rules**, not the 81 from the grammar document.
  Someone typed in a working subset to get the prototype running.
- Corpus fetchers for Ganjoor, Wikisource and Miras — worth reading before
  writing PLAN task 4.2.

Its rule ids contain a person's name, so none of them can be reused here.

**It contains no verbaliser group.** Neither does any of the 19 documents in
the Drive archive. The claim that there are four rules making a verb from a
noun appears in exactly one place — our own planning note — and is a miscount.
The concept document states plainly that there are **two**: `-idan` for the
intransitive (*rowšanidan*, to become bright) and `-āndan` for the transitive
(*rowšanāndan*, to make bright). Those are verb-table rows 3 and 4.

### The source document holds two rule tables, not three

`Dasturhāye Vāžesāzi az Kārbonhā.docx` has eight tables. Three matter:

| Table | Rows | What |
|---|---|---|
| verb-stem rules | 82 (81 with content) | numbered 1–81; row 77 is blank |
| nominal rules | 110 (105 with content) | numbered 1–104, plus 5 blank pad rows |
| glide rules | 17 | numbered 2–17 — the header row is numbered "1" |

The other five are the conjugation table, the traditional-grammar terminology
mapping, the personal endings and the possessive endings.

**There is no verbaliser table.** RULE_PACK.md assumed one, with four rules. It
does not exist, and only two rows in the whole document make a verb from a noun
or adjective. This is what blocks the `D` family — see OPEN_QUESTIONS.

**Each rule table has exactly one row the author forgot to number.** Verb table:
`-gi` on a kāridekārbahr ending in `-e` → Zadegi, sitting after row 8. Nominal
table: `-vand (Nesbat)` → Damāvand, after row 84. Both are real rules. Under the
append-never-insert rule they become V-082 and N-105.

**Verb row 77 is completely empty.** V-077 is reserved and can never be used.

### The terminology table is the authority for the category mapping

Table 2 maps traditional grammar to the project's terms directly: اسم → نام,
صفت → برنام, مصدر → نابِسودکارواژه, اسم مصدر → کارنام, قید → چون‌واژه, ضمیر →
جانام, حرف اضافه → پیش‌واژه. The prose adds that اسم معنی is a **kārnām**
(these nouns come from a doing) and that اسم ذات is a **nākārnām** (they do
not). That settled six of the nine lexicon categories without guessing.

`nākārnām` is *not* in the rules' type vocabulary and no rule matches on it, so
اسم ذات maps to `nam` for rule purposes. Worth knowing the finer term exists.

### Two numbers in LEXICON_ANALYSIS.md were wrong

- **پی has 7 senses, not 4.** The four counted were soft-deleted `Pi` rows.
  Live: *Pey* ×7 and a separate reading *Pay* ×1. The reading split was right;
  only the count was off.
- **1,752 verb rows are 1,742 distinct readings.** Ten verbs are listed twice
  with the same spelling and the same Latin. The generation input pool is 1,742.

Both corrected in LEXICON_ANALYSIS.md. The cause of the first is worth
repeating: **6,238 of the 51,817 rows are soft-deleted**, and a query that
forgets `deleted_at IS NULL` silently resurrects retracted readings.

### 44 bracketed semantic labels, and a capitalisation pattern

Every bracketed string in the affix column, counted: 44 distinct, 43 after
merging kenār/Kenār. The capitalised ones (Jā, Zamān, Mānand, Nesbat, Dāštan…)
look like the grammar's coined tag names; the lower-case ones (bālā, pāyin,
darun, pas, dobāre…) look like plain-language glosses of what a prefix means.
That reading is not confirmed, so all 44 are kept as tags and the question is
recorded.

`Nesbat` (19 rules) and `Mānand` (12) and `Dāštan` (11) carry most of the mass;
26 of the 43 tags are used by a single rule.

## 2026-08-11 (session 2) — Architecture defined

Worked from the feature set down to data structures, then stress-tested the
design by walking user journeys. Full detail in the linked docs; this entry
records what changed and why.

### Settled

Frontend is a **React SPA**; backend is API-only. karbon is **imported as a
library**, not called over HTTP. Rule pack is **YAML in git, loaded into
Postgres**. **Postgres** for authored data, **Elasticsearch** for anything a
batch job can rebuild. Deployment is **local**, private repo
(`github.com/pasmod/murfulu`).

### The correction that mattered most

An early draft claimed we would need a Latin → Persian converter to check
attestation. Wrong. Corpus words acquire a Latin form during the *link*
pipeline step by matching a lexicon entry, so attestation is a Latin-side
lookup against `word_types`.

Persian spelling is still needed for display, but it is **composed, not
converted**: we build words by joining stem + affix, so we build both spellings
in parallel. Stem's Persian comes from the lexicon, affix's from the rule pack.

The residue is real though: the linguist's Behnevis joining rules (ZWNJ, joined
prefixes, glide *y* → ی) still have to be extracted.

### What the رفتن walkthrough exposed

Tracing one verb end to end surfaced three things the design was missing:

- **Glide rules are load-bearing, not decoration.** رفتن's stem 2 is *row*, so
  nearly every output triggers one (*row* + *eš* → *Raveš*, not *Roweš*).
- **Attestation has three levels**, not two: matched reading, spelling-only,
  not found. Without the middle one, homograph collisions read as confirmation.
- **A precompute job is needed.** Sister forms and rule productivity both
  require knowing which attested words each rule produced, which corpus text
  cannot tell us. Applying every rule to every applicable lexicon entry and
  checking attestation gives Baayen P, sister forms and fast lookup in one pass
  — and is exactly Monakhov's simulate-and-check method.

### What the user journeys exposed

Six journeys, ten gaps — see [USER_JOURNEYS.md](USER_JOURNEYS.md). Three
changed the design:

- **Compounding was missing entirely.** The concept document names هم‌نهی as
  one of the two main Persian word-formation processes and the NGI abstract
  promises generation "by combining words"; we had designed only affixation.
  The flagship *Lichtung* → *Rowšantonoknā* example needs it. Now in scope,
  limited to the combinations the source grammar license.
- **No way to search by meaning.** This is the founding complaint — a
  writer wanting to use *-gān* has to open a grammar book. Now a first-class
  dimension, plus a browse-affixes-by-meaning screen.
- **String suffix search is not affix search.** `*nā` also returns *Banā*.
  Results now split into confirmed derivations and mere string matches.

### Scope additions

**Feedback covers everything**, not just generated words — rules, glosses,
statistics, lexicon entries, and plain bugs. Categories differ, permissions
differ, and feedback on karbon-owned data is exported rather than dropped.
Crucially it doubles as the **evaluation set**: karbon's reviewed entries
validate transcriptions of existing words and contain no generated words at
all, so they cannot tune our scoring weights. Graded feedback can.

**Rule discovery** is a planned track (the concept document's "third class" of
rules). Established method is Soricut & Och 2015 — group candidate pairs by
string transformation, then validate by semantic offset consistency. Reuses the
embeddings built for scoring. Not v1. See
[RULE_DISCOVERY.md](RULE_DISCOVERY.md).

### Ownership

Rule changes split: stem rules, exceptions and phonemics are karbon's and move
by pull request; derivational rules, glides, semantic tags and compounding are
ours. karbon's roadmap claims affix rules for itself, which will collide with
our rule pack — needs raising with the karbon maintainer early. See
[OWNERSHIP.md](OWNERSHIP.md).

---

## 2026-08-11 — Reading the project archive and the karbon repo

### Sources read

Everything in the shared Drive folder `Projekte/Morphology` (29 files) plus the
cloned repo `github.com/kp-multiverse/karbon`. Index of the archive is in
[SOURCES.md](SOURCES.md).

### What the project is

A word-making machine for Persian. Input a verb (or a noun or adjective), output
the whole family of words the language can form from it, each with the rule that
produced it and a score.

**The users are not everyday speakers.** They are writers, translators and
thinkers who want Persian to make fine distinctions. This is stated explicitly
and repeatedly in the concept documents, and it settles a lot of design
arguments: a generated word does not have to catch on, it has to be correctly
formed and precisely defined.

The two problems being solved:

1. **Persian became analytic.** Naser Khosrow and Beyhaqi wrote *barresidan*; we
   say *barresi kardan*. You cannot derive new words from a compound verb, so
   the language lost productive capacity.
2. **You cannot search Persian by suffix.** No dictionary or site lets you ask
   "which words end in *-nā*?". So the real range of meaning of an affix is
   unknown even to specialists.

The worked example the team keeps returning to: Heidegger's *Lichtung* should
not be translated *rowšangāh* but *Rowšantonoknā* — and to build that you first
need the noun *tonoknā* from the adjective *tonok*. That word does not exist
yet. Murfulu is what produces it.

### the project's grammar terms

the linguist has replaced the traditional Arabic-derived grammar vocabulary with a pure
Persian one. The code and the API should use his terms, because his rule tables
are written in them.

| Traditional | the linguist | English |
|---|---|---|
| فعل | کارواژه (kārvāže) | verb |
| بن ماضی | کاربن یک (kārbon-e yek) | past stem / stem 1 |
| بن مضارع | کاربن دو (kārbon-e do) | present stem / stem 2 |
| مصدر | نابِسودکارواژه | infinitive |
| اسم مصدر / حاصل مصدر / … | کارنام (kārnām) | action noun (all the old sub-types collapse into this one) |
| اسم | نام (nām) | noun |
| صفت | برنام (barnām) | adjective |
| صفت فاعلی | کارنده‌کاربهر | agent participle |
| صفت مفعولی | کاریده‌کاربهر | patient participle |
| صرف | واژه‌گردانی | morphology / inflection |
| نحو | واژه‌چینی | syntax |
| جمله | واژه‌چین | sentence |

"Kārbon" — verb stem — is where the repo name **karbon** comes from.

### The rule material we already have

`Dasturhāye Vāžesāzi az Kārbonhā.docx` is the core asset. It contains:

- **Stem rules 1–9** — strip `-an` for stem 1; then eight rules keyed on how
  stem 1 ends (`-id`, `-d`, `-st`, `-ād`, `-xt`, `-ud`, `-št`, `-ft`) derive
  stem 2, each with an explicit exception list.
- **~81 affix rules from the two stems** — e.g. stem 1 + `-ār` → kārnām
  (*Goftār*), stem 2 + `-ande` → agent participle (*ravande*), stem 2 + `-eš` →
  kārnām (*Pazireš*), stem 1 + `o` + stem 1 → kārnām (*Zadoxord*), plus ~25
  verbal prefixes (*bar-*, *farā-*, *foru-*, *vā-*, *var-*, *andar-*…).
- **~104 affix rules from nouns / adjectives / pronouns / adverbs** — e.g.
  adjective + `-nā` → noun (*tonok* → *Tonoknā*), noun + `-gāh`, `-stān`,
  `-vand`, `-gin`, and so on. Many carry a semantic tag in brackets
  (Mānand = similarity, Jā = place, Dāštan = having, Nesbat = relation), which
  is what lets the system state the *meaning* of a generated word, not just its
  form.
- **17 glide rules** — when two vowels meet, insert `y`: `ā + i → āyi`
  (*dānā* + *i* → *Dānāyi*), `u + e → uye`, `e + i → egi`, `ow + a → av`
  (*row* + *am* → *ravam*).

Roughly 200 rules total, already tabulated. This is the rule pack.

### Behnevis, and why Latin

the linguist's phonemic Latin script. It encodes distinctions the Arabic script hides:
*do* (2) vs *dow* (stem of "run"); *Ketābi* (bookish) vs *Ketābí* (a book);
*Gofte* vs *Gofteé*. Nouns get a capital first letter, so a word used as a noun
is visibly different from the same word used as an adjective.

**This is why we work in Latin.** The affix rules are phonological — they key on
final vowels and consonants and they insert glides. In Arabic script the short
vowels are simply not written, so the rules cannot be applied reliably. In
Behnevis they can be applied deterministically.

Note: there are **two Latin conventions** in the archive. The `درآمد_پروژه`
document uses the linguist's own set (`ش` → `c`, `ج` → `dj`, `ء` → `v`). The later
`قواعد_مصدر` document (14 May 2026) switches to the linguistics-site
convention (`ش` → `š`, `ژ` → `ž`, `چ` → `č`, `ج` → `j`, `ء` → `ˈ`) so the data
can be matched against outside sources. **The later one is what karbon
implements.** Use that.

### What karbon gives us

Repo `kp-multiverse/karbon`, pip name `karbon-nlp`, version 1.1.0, CC0.

| Piece | State |
|---|---|
| Vājnevisi phonemics engine (Persian → Latin), ruleset **V.7** | Working. `karbon.phonemize(headword, bracket)` → vowelized, phonemic, variants, confidence, needs_review |
| Curated Dehkhoda lexicon: **45,579 active entries** with phonemics, category, transitivity | Exists — **but not in the repo** (see gap below) |
| Stem derivation, rules 1–9 + exception lists | Working — `karbon.morphology.derive_stems()`, taken verbatim from the phonemic rule set |
| OOV resolver for words not in the lexicon: suffix stripping, compound splitting, each result labelled with source + confidence | Working — `karbon.Phonemizer` |
| hazm wrapper (tokenize, POS, lemma) as optional extra | Working, optional |
| Workshop web app where an expert reviews entries | Runs on the karbon maintainer's server, behind auth |

Lexicon composition: اسم ذات 14,391 · صفت مرکب 12,131 · اسم مرکب 8,132 ·
وام‌واژه 5,347 · اسم معنی 1,991 · مصدر 1,752 · صفت 1,528 · صفت-اسم 296.
14,361 rows still flagged `needs_review=1`.

**Karbon does not generate words.** None of the ~200 affix rules above are
implemented anywhere in it. That is the whole of Murfulu's job.

Checked directly (`src/karbon/resolve.py:207`): karbon's entire affix inventory
is **eight suffixes** — هایی، ترین، های، گان، ها، تر، ان، ی. Those are
inflectional (plural, comparative), not derivational, and they are used in the
**strip** direction only, to peel a word down to something the lexicon
recognises so it can be phonemized. There is no build direction anywhere.

So of the material in `Dasturhāye Vāžesāzi`, karbon covers the stem rules (1–9
plus exceptions) and nothing else. The ~200 derivational rules, the 17 glide
rules and the semantic tags are still only a Word table.

### The gap that blocks us

`data/lexicon.sqlite` is gitignored. The cloned repo has the engine code and an
empty `src/karbon/data/` folder. Without that file we can phonemize word by
word but cannot look anything up, cannot check whether a generated word already
exists, and cannot count corpus attestation.

The DB is a mounted Docker volume on the karbon maintainer's server. `scripts/release.py`
builds a frozen snapshot from it. **We need either that snapshot or read access
to the live DB.**

### What this means for Murfulu

The division of labour is clean:

```
Persian word  ──karbon──►  Latin + stem 1 + stem 2  ──murfulu──►  word family
```

Murfulu's core loop is: take a stem and its category, find every rule whose
input side matches, apply it (with the glide rules), and emit the result with
its derivation path, its composed meaning, and a score.

Three things the documents insist on, which are really requirements:

1. **Every output must show its structure.** the linguist caught an AI inventing
   *sāzāyi* by treating `-āyi` as a suffix when it is actually the present stem
   of *āmadan*. A generated word that cannot state its own derivation is a bug.
2. **The meaning must be composed, not guessed.** The bracketed semantic tags on
   the affixes exist precisely so the system can say *what* the new word means.
3. **Attested vs. new must be marked.** Ganjoor (203 poets, 119,061 poems, open
   API at `api.ganjoor.net`) is the intended check for whether a form already
   exists in classical Persian.

### Funding context

NGI Zero Commons Fund, €48,000, 12 months, 4 milestones, deadline 1 June 2026.
Application is written and near-final. Requires everything to be open source.
The proposal promises: an open Persian corpus, a curated rule base, a reusable
Python library (`morphology-core`), a small German rule pack to prove the engine
is language-agnostic, an open spec of Behnevis, and an accessible RTL web
interface. EXIST is the fallback; a spreadsheet ranks 39 other programmes.

The proposal points reviewers at `github.com/pasmod/stemma`. The actual code is
at `kp-multiverse/karbon`. Those need to be reconciled before submission.
