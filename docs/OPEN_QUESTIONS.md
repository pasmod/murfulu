# Open questions

Things we need answered before or during planning. Move each one to
[DECISIONS.md](DECISIONS.md) once settled.

---

## Opened 2026-10-27 (the move to the VPS)

### S35. How much memory does a corpus build need, and where does it run now?

The previous host built v13 and v14 in a one-shot container capped at 7 GB
(ENGINEERING, "Building a corpus version"). Production moved on 2026-10-27 to
a 16 GB VPS that Sokhan shares: Sokhan needs ~7.5 GiB, murfulu's stack is
capped at 4.9 GB, so ~3 GB are left and 7 GB does not fit. What the build
actually peaked at was never recorded. Before v15: measure a build's peak
(`docker stats` or the cgroup's `memory.peak`) on the previous host, which still
holds everything a build needs, then either cap it to fit the VPS, run it
on the previous host and move the result with `deploy/server.sh corpus`, or stop
Sokhan's reclaimable page cache from being the margin. Unanswered until the
next corpus version is due.

---

## Opened 2026-08-24 (session 21)

### S33. A coinage free in the corpus is not a coinage that is free

The corpus is 19.5 million lines of classical poetry and every word this
project is asked to coin is modern. So `0 occurrences in 25,497,189 words`
answers *the poets did not write it* and not *the word is available*, and the
two read identically on the screen.

Measured on one case rather than argued: **دادمندی has 0 occurrences in the
corpus and is in current use meaning عدالت.** It was offered as a candidate
and withdrawn only because somebody looked outside the corpus by hand.

**The question is whether the app should say so.** Three options, in
increasing cost: word the zero properly wherever it is shown — «در پیکره نیامده
است» rather than anything that reads as *free* — which is a copy change and
should probably happen regardless; add a second, modern corpus and report the
two separately; or leave it to the caller and document it. The first is cheap
and the wording is currently doing harm on the build screen, where an
unattested form is what the screen is *for*.

### S34. The coining protocol has no home in the repository

Four coining runs have now used the same protocol — propose, verify every
proposal through `/explain`, `/generate`, `/compound` and `/search`, report
what could not be verified — and it exists only as prose in FINDINGS entries
and as instructions retyped into each run. The results keep being good and the
protocol keeps being re-derived.

Whether it should become a `tools/` script, a documented recipe, or the
coining prototype that PLAN 9.6 defers is the project lead's call. Noted here
because the cost of not deciding is now four repeats, not one.

---

## Opened 2026-08-20 (session 20)

### S31. Should the round trip be checked over the whole engine, not one table?

The glide table was one-directional for as long as the project has existed and
nothing caught it, because every test names its own words. What found it was a
person handing an output back in as an input. **455 of 793 one-step glide forms
over a 300-reading sample could not be taken apart** — the fault was wide, not
rare.

A check exists in principle: build *n* forms from *m* readings, feed each back
to `analysis.explain`, and require an account. Run over 300 readings it takes
about four minutes, which is not a unit test. **The question is where it
belongs** — a `tools/` measurement run per release like the productivity and
compounding ones, a slow marked test, or a CI job over a fixed sample. And
what it should do about the known-legitimate gap: the form cap
(`searched_partially`) means some forms genuinely cannot be reached backwards,
so the check has to count those apart rather than fail on them.

### S32. Nothing reverses a compound

`engine/compound.py` fills slot rules — گفت‌وگو, دستور — and `analysis.explain`
only ever removes affixes. So a compound the engine built is a word the
analysis screen cannot account for, in the same shape as the glide fault but
larger. Checked 2026-08-20: *Goftvagu* returns no account at all, and
*dastvar* returns only the suffix reading (N-080, دست + -var) — never the
compound the compound screen offers. Whether the decomposer should try to split a compound at all, given
that any two-word split is a guess until both halves are looked up and the
whole is rebuilt, is a design question and not a small one.

---

## Opened 2026-08-18 (session 19)

### S28. Should a question have a *resolved* state, separate from *answered*?

The project lead, on the questions screen: the linguist answers, and *"I as a
maintainer later can decide if I want to put them in resolved or not"*. The
store has four states — `open`, `blocked`, `answered`, `withdrawn`
(`db/models/rulings.py`) — and no fifth. The screen now counts and filters by
the four it has; a fifth needs a column value, a migration, an endpoint to set
it and a rule about who may. **Not built on a guess.**

### S29. The rules screen does not show the document's own condition

Every rule carries `input.condition_text` — V-001's is *Kārboné doé nāgozarā az
Goruhé yek (NKZ)* — and `api/rules.py` does not serve it, so the screen prints
our generated sentence («از کاربن دو…») and drops the qualification. Serving it
is small. The question is whether the row should show the transcription as
well as our Persian, which is a screen-design call.

### S30. A compound whose spelling is a homograph of a real word

دستور built from دست + ور carries «۹۷۰ سروده از ۱۱۸ سراینده» — the count of
*dastur*. `also_an_inflection` marks and sinks دلم; nothing marks this. The
affix side already has a homograph pass (`tools/flag_homograph_claims.py`).
Should the compound route run it too, and should such a row sink or only say so?

---

## Where this file stands, 2026-08-17

**Every engineering question the project lead had open is now answered.**
Fifteen were settled in one sweep — S1, S2, S3, S4, S5, S6, S8, S11, S13, S14,
S15, S16, S18, S19 and S21 — and each carries its answer above its original
entry, with the measurement it was decided on. S9, S10, S12, S17, S22, S23 and
S24 were already closed. The reasoning is in [DECISIONS.md](DECISIONS.md); the
measurements are in [FINDINGS.md](FINDINGS.md).

**Three have opened since and one is already closed.** **S25**, the licence on
the interface font, was answered the next day: the project lead has bought it.
**S26** asks whether the compound screen should show one row per word or one
per rule; what was wrong with it either way is fixed, and nothing waits on it.
**S27**, opened 2026-08-18, is that half the browser suite silently sits out on
a laptop because the dev server cannot reach the API.

**Two things came out of the sweep that nobody had asked about**, and both were
confident wrong answers rather than gaps:

* **`/explain` reported an unfinished search as a refusal.** The engine stops at
  20,000 forms per base and the analysis threw that flag away, so *we did not
  finish looking* and *this word cannot be built* read identically. At three
  steps **5.8% of empty answers** were the first, not the second.
* **The compounding rules reported `types_built: 0`** because a measurement tool
  written for them had never been run. A zero beside a rule that builds
  35 million forms is worse than no figure.

**What is still open is the linguist's**, and it is gathered in
[FOR_THE_LINGUIST.md](FOR_THE_LINGUIST.md): S7 (which stem group is NKZ) is the
only genuinely blocking item, S20's triage of 75 examples is the largest, and
L17, L18 and L19 were added by this sweep. Everything below the fold is kept for
the record.

---

## For the linguist — one ruling, nothing blocked

**S7. Which stem group is NKZ, and which is NKDZ?** V-001 and V-002 both make
a verb with `-āndan`, and the only thing separating them is the stem's group:
*Kārboné doé nāgozarā az Goruhé yek (NKZ)* against *…az Goruhé do (NKDZ)*.
The lexicon carries `stem_rule` and `stem_group` columns, so the test is a
line of code — but **which of karbon's numbered groups NKZ names is not
written down anywhere we hold**. Guessing it would silently mark half the
verbs as breaking a rule they may well keep, so `rules/input_conditions.yaml`
records the condition and refuses to test it. Every other rule with a
checkable condition is now checked.

## For the project lead — engineering

**S27. The dev server cannot reach the API, so tests skip and the run reads
green.** Vite proxies `/api` to `http://localhost:8010` and the API container
publishes no port — only Caddy does, behind the site password. So on a laptop
every Playwright test that needs real data calls `test.skip(!answer.ok())`.

**Corrected 2026-08-18, later the same day: it is not a handful of tests, it is
half the suite.** The first count here said *8 skipped*, which was the figure
with the bridge already up. Measured again with the bridge down — the normal
state of a laptop:

| | skipped | passed |
|---|---|---|
| bridge up | 8 | 106 |
| bridge down (normal) | **50** | 64 |

So **50 of 114 tests sit out** and the summary line still reads green. Bridging
for one session ran 4 that had been skipping in that run and **2 of them failed
for real** — one asserting on rows that had moved behind a folded group, one an
axe contrast violation introduced the same hour. Both would have reached the
deployed site.

One of the screens whose accessibility test skips is **questions**, which
carries a 15% `opacity` on an answered card. Whether axe passes it has never
actually been checked here.

The bridge used was a throwaway `socat` container on `murfulu_default`
forwarding host 8010 to `api:8000`; it was removed and nothing in the
repository depends on it. **The question is what the committed answer should
be** — publishing the API port in `docker-compose.yml` for development only, a
documented one-line bridge command, or leaving it and treating a skipped
layout test as a known blind spot. Publishing a port is the thing DEPLOY.md is
most careful about, so this is not a free choice.

**S26. Should two rules that write the same word stay two rows?** Raised by the
compound screen showing دلبر three times. Two of those are V-078 and V-079,
which join the same two parts and differ only in what they build — the doer and
the done-to — and `compounding.py` keeps both deliberately, because that is
information rather than noise. That decision is not reopened here.

What was done meanwhile is presentational and is enough on its own: the row now
shows the class it builds, so the two read as different words rather than as
the same word twice. **The question left is whether a reader would rather see
one row per form** with the rules listed inside it. That is a different claim —
*here is a word, and here are the two ways the grammar makes it* — and it
would fold the third row in as well, the one that is the same spelling read
*dalber*. Not built, because collapsing rows discards the ranking they carry
and the answer depends on who the screen is for. The evidence line is qualified
either way: the count is the spelling's, which is all the corpus was asked.

**S25. ANSWERED 2026-08-18 — the font is bought.** The project lead has paid
for Farhang and the question is closed. The six-digit code goes into the
comment at the top of `web/src/styles/farhang.css`, where the dots are, when it
is to hand. Original entry follows.

**S25. Farhang has no licence code, and the repository is going public.** The
interface is now set in Farhang2, from the Drive archive, on the project lead's
word. It is commercial software from **fontiran.com**, and its own
`FontLicense.txt` — shipped beside the files and now beside ours — asks for a
six-digit code, registered there, to be written into the CSS wherever a font
file is copied into a project and served. **Ours reads `(.....)`.** The terms
name a site that serves the fonts without registering an illegal distributor.

Two things to settle, and they are separate:

* **Register the licence.** Murfulu is a research app with one account and no
  revenue, so fontiran's non-commercial licence looks like the right one and it
  is free of charge — but it still has to be *issued*, and the code then goes
  into `web/src/styles/farhang.css` where the blank sits.
* **Decide whether the font files may go into a public repository.** Serving
  them and publishing them are not the same act, and CLAUDE.md says this
  repository will be made public. The licence forbids redistribution outright,
  and a public repo redistributes. If the answer is no, the files come out of
  git and go in at deploy time; that is a small change and it is much smaller
  now than after the repository is public.

Nothing is blocked meanwhile: the font is in place and the app runs.

**S24. ANSWERED 2026-08-16 — the same flex trap in two places.** A flex item
will not shrink below its own content unless told to: `.nav` never scrolled and
`.input` never narrowed, so four screens pushed the page sideways. Both now set
`min-width: 0`, and the suite runs at 320px where it reproduces. Found by making
the assertion name the element holding more than it shows — naming the widest
*rectangle* accused a bystander, because RTL overflow shifts every rect.
Original entry follows.

**S24. Five layout tests fail only in CI, and have since before anyone noticed.**
Found 2026-08-16 while fixing the build. The failing list is **byte-identical**
to the run of 2026-08-14, so none of it is new; it had simply been sitting
behind seven `test_repository` errors that were louder.

| | |
|---|---|
| `/`, `/build`, `/compound`, `/explain` at phone width | body overflows by **43px** |
| the skip link at phone width | not reached |

**They cannot be reproduced here**, and that is the whole difficulty. They pass
locally with the API up **and** with it stopped, which rules out the missing
backend — the first and most obvious explanation. The fonts were npm packages
at the time (`@fontsource-variable/vazirmatn` and `inter`), so CI had the same
faces we did.

What is left is something about the CI browser itself. The likeliest candidate
is the **scrollbar**: Chromium on Linux paints a classic one that takes width
out of `clientWidth`, where macOS overlays it and takes none — and this test
measures exactly `scrollWidth - clientWidth`. 43px is more than a scrollbar,
so that is a hypothesis and not an answer.

**Four of the nine were a real gap and are fixed**: the two compound tests
needed a live API and real data and did not skip without one, unlike the
thirty-nine other tests in the file that do.

**Question:** is the phone overflow worth chasing? It is only ever visible in
the error state, on a phone, with no backend — a real user with a dropped
connection. The cheap next step is a CI run that uploads Playwright's trace, so
the failing frame can be looked at instead of guessed at.

**S22. ANSWERED 2026-08-15 — lookup now matches every recorded reading.**
The project lead approved it the day it was found; the risk was measured first
(8 collisions in 8,218, all the same word spelled two ways) and all 7,106 are
now reachable. **A second fault was found by testing the fix**: SQLite's own
`lower()` is ASCII only, so matching case-blind in SQL left every reading
beginning with a long vowel — `Ābrov` among them — still unreachable. The
lower-casing is Python's. Original entry follows.

**S22. 7,106 readings the dictionary records cannot be looked up.** Found
2026-08-15 while sorting PLAN 9.3's piles. `Lexicon.by_latin` matches the
`phonemic` column only, and a genuinely different second reading lives in
`phonemic_variants`. کنار is **Kanār or Kenār**; asking for *Kenār* returns
nothing at all.

| | |
|---|---|
| readings in the snapshot | 44,788 |
| carrying a second reading | 7,181 |
| **whose second reading no Latin lookup finds** | **7,106** |

Question P (answered 2026-08-11) established that *generation* builds from
every reading, and `Reading.all_latin` carries them. **Lookup was never given
the same treatment.** So a user typing a reading karbon itself commits to gets
a 404, and `/explain` cannot reach a word through its second reading.

**Not fixed when found, deliberately.** It changes what every route returns for
7,181 words, so it wants the project lead's word and probably a corpus version
to be measured against — the same shape as the `rule_chain` change. It also
means PLAN 9.3's *the base is not in the lexicon* pile is an **upper bound**:
N-003's *kenār* is in that pile and the lexicon holds it as a variant.
**Question:** should `by_latin` match every recorded reading, and if so does
the case rule (*Gofte* against *gofte*) still hold for a variant, which the
snapshot stores lower-case?

**S23. ANSWERED 2026-08-15 — restrict the list to what our rules can build.**
The project lead chose this over writing a function-word list: "and" is not
built from anything, so it drops out by itself and no list needs maintaining.
4,519 words, each carrying the rules that form it; 99 short words left of
5,681. See UPSTREAM B2c. Original entry follows.

**S23. The cleaned gap list is still headed by function words.** PLAN 9.4 took
the inflections out — 48,039 of 392,120, exactly reproducing B2b — and what is
left is **not** sendable, for the reason B3 already gives. Measured on v9:

| | |
|---|---|
| **60 of the 100 biggest surviving gaps** | three characters or fewer |
| 32 single-letter spellings | **15.6%** of all kept occurrences |
| 441 two-character spellings | 26.6% |

و, ز, آن, او, چون, ای, ما, همه, هم, بی — the first content word is عشق, at
position 11. B3 recorded that function words are out of scope and agreed
*later, not now*. **This is what *later* costs**: the most useful thing we can
send upstream cannot be sent until either a function-word list exists or the
list is restricted to spellings our rules can build, which is B2's `proposed`
list and a different filter entirely. **Question:** which of the two, before
9.7 opens the pull requests?

**S21. ANSWERED 2026-08-17 — the flag is renamed, and evidence goes beside it.**
`explained` is now **`rebuilt`**, which is all the route can honestly claim: a
chain of real rules reproduces these letters from a dictionary entry. Nothing
was taught to judge meaning — refusing *Nāxodāgāhi* needs a ruling this project
does not make in code. Instead every account carries **the base's own corpus
evidence**, in one batched query, which is the one thing we already hold that
separates a parse a reader would accept from arithmetic. It does part of the job
and not all of it, and that is stated rather than hidden: *Hamzamāni*'s base
هم‌زمان has **1 document** and *Nāxodāgāhi*'s base ناخدا has **213** — an
ordinary word that simply is not the one anyone means. The screen now says the
rebuild is about the letters and not about the word.

**A second worked case, 2026-08-20: داستان.** It rebuilds as **دا + ستان**
(N-057), and دا is a headword with **111 documents by 25 poets** — an ordinary
count, so the evidence line warns a reader of nothing. Reported by the project
lead as *Dastān*, which is a different word: the engine builds دستان from دست,
and دستان is a headword in 1,639 documents. Worth keeping both, because the
pair is exactly how a Behnevis form gets read as the wrong Persian one.
Original entry follows.

**S21. `/explain` says `explained: true` for a parse that is nonsense.**
Found 2026-08-14 by the coining experiment. The route rebuilds forward and
keeps whatever reproduces the letters, which is what it says it does — and
what a caller reads is a flag that looks like a sense check.

| call | what comes back |
|---|---|
| `/explain?word=Nāxodāgāhi` | base **ناخدا** — a ship's captain — + N-068 + N-095, `explained: true` |
| `/explain?word=Hamzamāni` | base **`Zam`** + N-036/N-037 + N-015, `explained: true` |

Neither is wrong about the letters and both are useless about the word. The
model using the API said so itself and stopped trusting the flag.

**What it is not:** a bug in the rebuild. Refusing these would need a
judgement about meaning that this project does not make in code.
**Question:** does an account carry something that separates *this parses* from
*this is plausible* — the base's own frequency, whether the base is a headword
a reader would recognise, the semantic distance between base and result — or
does the flag get renamed so nobody reads it as more than it is? The second is
free and honest; the first is S6's machinery pointed at a new question.

**S20. The rule pack was going to be the test suite, and half of it never
became one.** `tests/test_golden_examples.py` states the intention in its own
docstring — *"Until the engine exists (PLAN 2.1) these check the shape of
every example… When the engine lands, `expected` becomes what it must
produce."* The engine landed in session 2. **The examples are still checked
for shape only**: that they parse, that a worked example's parts agree with
its rule, that the result looks like Behnevis.

Measured 2026-08-14 by the coining experiment, and **wanting re-measurement by
us before it is quoted**: of the first example of all 165 prefix and suffix
rules put through `/explain` at depth 3, **88 were explained by the rule that
lists them and 77 were not**.

**Some of that is certainly not a build fault.** N-004's example is `bexrad`
and the system builds `bexerad` from the lexicon's `Xerad` — a vowel
convention between the source grammar and karbon's phonemizer, not a wrong
join. Which is exactly why turning the examples into assertions is a
*question* rather than a chore: every failure has to be sorted into *the
engine is wrong*, *the pack's example is wrong*, and *the two spell the same
word differently*, and the third pile is the linguist's.

**ANSWERED 2026-08-14 for the second half; the triage is still open.** The 88
that pass are now asserted — `tests/example_baseline.json` lists them and a
test rebuilds each against the real snapshot — and the list may grow and must
never shrink. So every future engine change shows its effect on the grammar's
own examples without anyone having to settle 75 linguistic questions first.

Re-measured by us rather than taken from the run that found it, and the piles
are three rather than two:

| | | |
|---|---|---|
| explained by its own rule | **88** | 54.0% |
| not rebuilt at all | 61 | 37.4% |
| rebuilt, but by **another** rule | 14 | 8.6% |

That third pile is new and is the interesting one: the word rebuilds, just not
through the rule that claims it. `tools/check_examples.py` keeps them apart.

**What is still open is the triage**, and it is the linguist's more than
ours: each of the 75 has to be sorted into *the engine is wrong*, *the
example is wrong*, and *the two spell the same word differently*. Only the
first is a bug here.

**S19. ANSWERED 2026-08-17 — the field is `built_by`.** A field called
`rule_chain` whose contents are deliberately not a chain was the same trap in
the name that the old value was in the data. Nothing read it, so the rename was
free, and **no alias is kept** — an alias would preserve the trap. It takes
effect at the next corpus version; derivations-v10 still carries the old key.
The other two fields this entry names, `affixes` and `glide_rules`, turned out
to have been fixed with the value, and the entry had not caught up. Original
entry follows.

**S19. `rule_chain` named the first derivation only. HALF ANSWERED
2026-08-14: it is now the union.** The field is the set of rules that build
the word, in first-seen order, and **its order is no longer a chain** —
`paths` carries the ordered derivations and always did.

Settled rather than asked because the field turned out to have **no reader at
all**: `/search` queries `word_types`, the affix map is built from `paths`, and
the web build screen composes its own chain from `paths[0]`. So nothing could
break, and a filter written against it later would have been quietly 20%
short.

**It takes effect at the next corpus version.** derivations-v8 was built before
the change and still carries the old field; rebuilding a 1.6-million-record
index to correct a field nothing reads was not worth twenty minutes of compute.

**What is still open is the name.** A field called `rule_chain` whose contents
are not a chain is a trap of a different kind. `rule_ids` or `built_by` would
say what it holds. The rename is free at the next rebuild and is nobody's
decision but the project lead's.

**And two fields beside it have the identical defect**, unfixed and unmeasured:
`affixes` and `glide_rules` are also taken from the shortest path alone.

The measurement that started it:

**`rule_chain` names the first derivation only, so every count taken from
it understates the rule. Measured 2026-08-14.** A form the
engine reaches more than one way keeps all its paths — that has been settled
since session 4, and 439,078 forms depend on it — but the flat `rule_chain`
field beside them carries the **first path alone**.

| | |
|---|---|
| records in derivations-v7 | 1,704,021 |
| reached by more than one path | 437,202 |
| `rule_chain` smaller than the union of their paths | **342,511 — 20.1%** |
| of those, exactly equal to the first path | 342,511 — all |

دندانایی is reached five ways — V-024+V-025, V-024+V-030, V-026+V-027,
N-023+N-095, N-072+N-095 — and `rule_chain` names the first pair. So a filter
on it misses four rules that genuinely built the word. Found while measuring
the infix fault: the live index reported 57,826 forms for N-023 where the file
holds 57,856, and the 115,682 in the session-10 write-up is the `rule_chain`
figure rather than the true 115,712.

**What it costs is unmeasured and probably small**, because the one thing
known to read the field — the affix map — is built from `paths` and not from
it. What it costs *later* is the worry: any future "words this rule built"
query written against `rule_chain` will be quietly 20% short.

**Deliberately not fixed in v8.** Changing the index's shape in the same build
that removed 91,615 forms would have made "nothing else moved" untestable.
**Question:** does `rule_chain` become the union of every path — which makes it
mean *rules that built this word* — or does it stay the first path and get
renamed to say so? The second is cheaper and the first is what a reader
assumes.

**S16. ANSWERED 2026-08-17 — wait for L10, and the two engineering excuses are
gone.** The wall has not moved: five affixes still hand back one identical
meaning, so a model would choose between them on its own priors, which is the
exact failure the design exists to avoid. But both *engineering* reasons its
proposals failed are now dealt with — compounds reach a reader, and an
unfinished search says so rather than reporting a refusal.

**Chasing درافکندگی, the word this entry calls the engine's largest gap, found a
bug instead.** It is not a missing rule. The engine stops at 20,000 forms per
base; building forward from افکندن reaches **20,050 at three steps**, so the run
is truncated and never arrives. Every rule the chain needs exists and fires.
`analysis.explain` threw the engine's own truncation flag away, so an unfinished
search and a real refusal gave a reader the same sentence. `/explain` now serves
`settled`, and measured over 120 random readings **5.8% of empty answers at
three steps and 7.5% at four were unfinished searches, not refusals**. مولانا
remains a settled refusal, which is what the whole check exists for.

When the prototype is built it must call `/explain` on its own proposals and
read `settled` as well as `rebuilt`. Original entry follows.

**S16. A language model that coins words *through* Murfulu. Proposed
2026-08-13; the loop was run by hand and it works.** The idea is his: a model
alone does not build Persian words to the rules, but it is good at meaning —
so let it read the user's request, ask Murfulu for candidates, and judge what
comes back. **The division of labour is the right way round**: the model does
semantics, which it is good at, and never morphology, which it is not.

**No new routes are needed for a prototype.** The loop was walked with four
existing calls:

| step | call | what came back |
|---|---|---|
| which affixes make a place | `/affixes?tag=Jā` | five rules — `-ān`, `-dān`, `-stān`, `-kade`, `-gāh`, with an example each |
| build from a base | `/generate?word=نان&attest=true` | the five forms, correctly joined |
| what already exists | the same call | نمکدان **304 poems**; ناندان **0** |
| how a form was built | `paths`, `rule_chain` | every step, for the model to quote |

**That last row is the property that makes the feature worth having.** The
system can tell the model which of its candidates is *already a word* and
which is genuinely new, with a count behind it — which is exactly what a
coining tool needs and no model can know on its own.

**And there is one wall, which is L10 and nothing else.** Every one of the
five candidates comes back carrying the identical meaning:

```
نانان    Nānān     N-037   جایی که نان در آن است
ناندان   Nāndān    N-048   جایی که نان در آن است
نانستان  Nānstān   N-057   جایی که نان در آن است
نانکده   Nānkade   N-062   جایی که نان در آن است
نانگاه   Nāngāh    N-068   جایی که نان در آن است
```

A *-dān* is a container, a *-stān* is a land, a *-kade* is a house. **The
system cannot tell them apart and hands the model five identical
descriptions**, so the model would choose between them on its own priors —
which is the exact failure the design exists to avoid. **L10 stops being
background and becomes the blocking item** the moment this is built.

**Two lesser ones, both already recorded.** S8: 41.3% of unlinked attested
forms read as inflections, so a model handed a ranked list is handed noise
near the top. And a verb has no definition at all (0 of 1,752 مصدر), so a
model coining from a verb gets no meaning for its base either.

**One thing to check before designing:** کتاب is **not in the lexicon** —
14 of 15 everyday nouns are, and that one is not, which matters because the
model picks the base by meaning and may well pick one we do not hold. The
answer is UPSTREAM B2's gap list, not new code here.

**Tested 2026-08-14, as a controlled experiment.** Two agents, the same four
questions — the longest meaningful Persian word, three renderings each of
*Dasein* and *Geworfenheit*, and a word holding two contradictory words. One
had the API; the control had nothing but its own Persian and was forbidden
tools. Then every checkable claim in both answers was checked against Murfulu.

| | control | with the API |
|---|---|---|
| corpus figures quoted | none — none possible | **12, and 12 correct** |
| rule ids cited | none — none known | **19, all real and active** |
| bugs it found in our API | — | **3, all confirmed** |
| self-reported rule violations | — | **1, disclosed unprompted** |

**The difference is not fluency. Both answers read well.** The difference is
that one is checkable and the other is not. The control wrote "I believe this
is not lexicalized"; the API agent wrote "0 documents, and درافکنده is 38
documents across 17 authors, and the identical pattern is درماندگی at 92".
Every one of those numbers is exact.

**Three things it found that we did not know.** It went looking for permission
to join two contradictory words and found **کمابیش** — *less-ā-more* — at 34
documents and 21 authors, which is N-104 joining outright opposites and is not
in that rule's example list. It found **بودگی** attested in the 13th century,
where it had assumed "being-ness" was a modern coinage. And it settled on
`-gāh` for *Dasein* because **N-068 is the only rule in the pack tagged `Jā`
and `Zamān` at once** — place and time together, which is the shape of the
German *Da*.

**And it disclosed its own violation.** Its contradiction-word بودانابود
stretches N-104, whose `input_types` is `nam`, because نابود is filed
`barnam`. It said so unprompted, and noted that کمابیش stretches it the same
way — so the rule as written is narrower than the corpus it was drawn from.
**The control could not have known there was a rule to violate.**

**And then the proposals were put back through the engine, which is where the
enthusiasm should stop.** Every word both agents proposed was handed to
`/explain`. **Only 3 of the API agent's 8 rebuild.** Its top pick for
*Geworfenheit* — درافکندگی, confidence 85 — does not, and neither does its
longest word nor its contradiction-word. Two reasons, both real and neither
the model's fault:

* **No compound reaches a reader** — S18. Three of the four answers lean on
  slot or template rules, and those produce nothing by any route: the ten
  templates are implemented and **nothing calls them**, and the six slots are
  not implemented at all. The API meanwhile showed their examples and tags and
  said they were "generated on demand".
* **`/explain` starts only from a lexicon entry**, so a chain through a coined
  intermediate cannot begin. درافکندن is not a headword; فروافکندگی rebuilds
  only because `foru-` happens to apply to an existing noun instead.

**So the honest reading is narrower than it first looked.** What the API
reliably gave was **evidence** — corpus counts, real rule ids, attested
neighbours — and every bit of it checked out. What it did not give was a
guarantee that the assembled word is one the system can build, and the model
had no way to tell the difference. **A prototype must call `/explain` on its
own proposals before showing them**, which costs nothing and would have caught
five of eight.

**What the experiment does not show.** The system verifies that a chain of
real rules produces the form and that the parts are attested. It does **not**
verify that the result is good Persian, and neither agent's output is a
ruling. The corpus is classical poetry and cannot judge a modern or
philosophical word either way: all eight of the control's proposals are absent
from it, and that counts against neither.

**Question:** prototype it now against the wall, or wait for L10?

**S18. ANSWERED 2026-08-17 — the compounding rules are measured, so they stop
reporting zero.** `tools/measure_compounding.py` existed and had never been run
for v10, so 18 rules still said `types_built: 0` in `/rules` — a figure of zero
beside a rule that builds millions of forms. **16 of 18 are now measured** and
2 say honestly why they cannot be: V-078 builds 28,896,536 pairs with 26,361
attested; V-044 has the best rate in the pack at 4.0094%; N-104 would be
435,932,641 pairs. The screen half of this entry was already built
(`web/src/screens/compound/`).

**The last piece — سخن building nothing — is now L18 for the linguist**, with
the measurement: 1,949 readings are a kārnām and not a nām and every one is shut
out of every slot rule, while سخندان (199 documents), سخنور (178) and سخنگو
(121) are ordinary Persian. Original entry follows.

**S18. 16 compounding rules were in the pack and no compound had ever reached
a reader. ANSWERED 2026-08-14: `/compound` serves them.** The route is the
shape decided below — attested pairings ranked, the count of the rest beside
them, inflection-shaped rows marked rather than dropped, and the whole list one
`attested=false` away. Measured on دل's first reading: **4,652 compounds built,
220 attested (4.7%), 1,741 verbs offered.** دلبر leads at 2,920 poems; دلم
sinks to 162 of 220 carrying «دل + ضمیر پیوستهٔ اول مفرد».

**One thing the route does that this entry did not anticipate.** Being already
in the dictionary was going to sink a row too, and that was wrong: the
session-9 rule it borrowed is about **homographs**, and دلبر is not one — the
lexicon holds it and it *is* دل + بر. It leads the list and is marked
`already_a_word`, which is what a coiner wants to know.

**And one thing that is now visibly open.** سخن — the word this entry was
measured on — builds **nothing**, because it is filed اسم معنی → `karnam` while
the slot rules take a `nām`. The 3,071 figure below was produced by building
the word by hand and bypassing the category mapping, so **the route is
stricter than the measurement that justified it**. Whether اسم معنی is right
for سخن is already UPSTREAM A6.

What is still unbuilt: no screen shows any of this, and the productivity pass
still does not exercise the compounding rules, so they continue to report zero
in `/rules`.

The original, for the record:

**16 compounding rules are in the pack and no compound has ever reached a
reader — but only half of that is unbuilt.** Corrected 2026-08-14 after
looking rather than assuming, twice:

**The 10 templates are built.** `murfulu/engine/compound.py` fills them and
produces *Budonabud*, *Goftogu* and *Kešākeš* exactly as the source has them,
with the same-verb, different-verb and negated constraints all handled.
**Nothing calls it** — not the precompute, not `/generate`, nothing in
`tools/`. So the rules report zero built forms and read as unimplemented.

**The 6 slots are built now** (2026-08-14). `fill_slot` joins the two words
with nothing between them, which is what the source's dash means, and makes
*soxanguy*, *tondrow* and *Čašmdāšt* exactly as the grammar writes them.

**What is still open is where the output goes, and the numbers say why.**
Measured over five ordinary nouns:

| | |
|---|---|
| compounds one noun makes | **3,071** |
| of them the corpus has | **15 to 102** — 0.5% to 3.3% |

So this cannot join `/generate`, which already answers in megabytes at depth 2.
**And the attested ones are not what they look like.** سخن's best hits are
سخنم (478) and سخنش (350) — *my word*, *his word*, possessive forms, not
compounds. They appear because **میدن's present stem is a single letter, م**,
and seven verbs have one-letter present stems. Real compounds are in there —
سخندان (199), دلبر (2,920), کارگر (405), چشمداشت (32) — mixed with inflection.

**Which is S8 again, and the instrument for it already exists**: the
inflection analyser built at the start of this session reads سخنم as سخن plus
a possessive. So the route, when it is written, should return the attested
pairings ranked, **mark the ones that also read as an inflection** rather than
dropping them, and carry the count of everything built but unattested.

**Not written this session, deliberately.** A new public route is a shape
decision and this session is long; the engine half is done, tested against the
grammar's own examples, and the measurement above is what the route needs to
be designed against.

**And one of the ten was quietly wrong.** V-021's pattern read
`{a} + o + na + {b}` in Latin and `{a}ون{b}` in Persian — the ا of *na* was
missing, so it built *Budonabud* correctly and بودونبود wrongly. Fixed, with
a test that every pattern's two alphabets join with the same letters. **It was
invisible because nothing in the codebase builds a compound**, which is the
same reason the whole of S18 went unnoticed.

**What made this worth writing down is that our own data denied it.** The
productivity block gave `unmeasurable_reason: "compounding, which is generated
on demand and never precomputed"` — the intention, stated as fact. Corrected
2026-08-14 to say it is not built.

**Found by giving the API to a language model and asking for hard words.** It
built three of its four answers on V-016, V-078 and N-104, quoted their real
examples and tags, and produced words the engine cannot make. **Only 3 of its
8 proposals can be rebuilt by `/explain`**, and the two independent reasons
are both here: compounding is unimplemented, and `/explain` can only start
from a lexicon entry, so a chain through a coined intermediate — درافکندن is
not a headword — has nowhere to begin.

This is the largest hole the experiment found, and it was invisible to both
test suites because nothing asks the engine to make a compound.

**Do we have the rules for it? Yes, and more of the work is done than
anyone thought.**
Checked 2026-08-14, every one of the 16 against its source row:

| | |
|---|---|
| compounding rules with a source row | **16 of 16** |
| **templates** with a machine-readable `pattern` and typed `slots` | **10 of 10** |
| **slots** with a pattern | 0 of 6 — but see below |

The source states the join in words and the transcription already turned it
into data. V-021 — *Budonabud*, which is the contradiction-word question
almost verbatim — reads
`pattern: "{a} + o + na + {b}"`, `pattern_fa: "{a}ون{b}"`, with slot *b*
typed `karbon_yek`, constrained `same_verb`, and `negated: true`. The joining
element is **`o` in seven rules and `ā` in three**, and each says whether the
second element is *Hamān* (the same word) or *Digar* (a different one).

**The 6 slot rules have no pattern and need none.** Their whole shape is in
`affix` plus `input.types`: `Nām-` + `karbon_do` → *soxanguy*. One side is the
caller's own word, the other is any present stem — direct juxtaposition, no
joining element, and a **sum rather than a product** because one slot is
pinned. Those six are the cheap half.

**So what is missing is smaller than the engine.** The ten templates are
already implemented and correct; what they lack is a caller. Only the six
slots need building, and they are the simpler shape.

**And the route was hiding the specification.** `/rules` served neither
`pattern` nor `slots`, so a caller saw `kind: template` with an affix of `‒`
and nothing to say what the template was — which is exactly why the language
model hand-assembled its compounds. Served from 2026-08-14; null on the 179
affix rules, which is what they are.

**Question:** is 2.3 worth doing now? It is what a coining tool most wants —
Persian builds words by compounding more than by affixation — and S16 is
half-blind without it. **The six slot rules are the place to start**: they are
specified, they are a sum, and they cover the *soxanguy* / *delgir* shape that
is everywhere in the language.

**S17. `/rules/{id}` served less than `/rules` did. FIXED 2026-08-14.** The
detail route now carries `productivity`, `semantic` and the corpus version the
figures were measured on. Pinned by a test asserting the detail row is a
**superset** of the list row rather than by naming the fields, so a key added
to one cannot go missing from the other. A glide still carries neither: it
decides a letter at a join and builds no word, and a null there would read as
a measurement of zero.

The original, for the record:

**`/rules/{id}` serves less than `/rules` does.** The list carries a full
`productivity` block per rule — `types_built`, `types_attested`, `band`, the
corpus version it was measured on. The **detail** route carries none of it, so
a caller who asks about one rule gets less than one who asks about all 212 and
filters. Found by a language model given the API, which had to keep the whole
list cached and read productivity out of it.

A detail view holding less than the list view is backwards, and nothing says
so — the fields are simply absent, which reads as *not measured*. Not fixed:
it is a small change in `src/murfulu/api/rules.py` and the route's shape is a
decision about what a rule *is*, which is worth five minutes of somebody's
attention rather than mine at the end of a session.

**S15. ANSWERED 2026-08-17 — a deep form keeps the first-step score.** The
open half asked whether it should instead be scored on its own outer rule.
**No**, and the reason is now concrete rather than a worry: a base's vector is
the average of corpus lines using the word, so an unwritten intermediate —
*yāni* — can never have one, and producing one is FRACSS's job and is
unvalidated on this material, where 79.0% of attested pairs have a bound stem as
their base. It is also no longer needed: the realisation figure orders deep
answers, which is the job typicality was being asked to do and cannot — at three
steps 12,999 forms share 22 typicality values between them. Original entry
follows.

**S15. The semantic score is measured on the first step and shown on every
row. Labelled 2026-08-13; the weighting is open.** `semantic` carries
`typicality`, `rule_id` and `base`, and all three are about the **first** rule
in the chain. The build screen printed only the number, under «همانندی پایه با
پایه‌های همیشگی *این دستور*» — *this rule* — so on any form more than one step
deep the sentence named a rule the row is not built by and a base it is not
built on.

Measured on derivations-v7: **549,194 of 583,572 scored forms are two steps
deep — 94.1%.** Found by the project lead reading یان's screen, where
**twenty-three rows carried the identical 86%** and only the first of them was
about its own rule. یانیسار is N-098 then N-055 and was given N-098's number.

**The number was never wrong; the sentence was.** `generate.ts` has always
said "the first step's base" in its own type. This is the same failure as two
screens quoting different corpus versions in session 9b — a true figure under
a false label — and it is fixed the same way: **the figure now travels with
what it is about.** A row whose every chain ends on the rule the score names
keeps the original sentence; any other row reads «همانندی Yān با پایه‌های
همیشگی دستور N-098: ۸۶٪ — سنجیده بر گام نخست».

**And the figure itself was misleading, which is the half that mattered
more.** Asked what the sentence meant, the honest answer is *on its own, very
little*. The score is a cosine and on this corpus it never leaves the middle.
Measured over all 583,572 scored forms in derivations-v7:

| | |
|---|---|
| lowest anywhere | **0.554 — 55%** |
| highest anywhere | **0.914 — 91%** |
| median | **0.828 — 83%** |
| the middle **half** | 0.800–0.852 — 80%–85% |

**So 84% is the median.** Printed bare it reads as a good mark out of a
hundred and is the most ordinary word on the screen. Nothing said the scale
only runs 55–91.

**Fixed by the remedy the project already uses for rule productivity**, which
had the same problem and solved it the same way: a figure is shown with its
**band** of the measured distribution. `tools/measure_typicality_spread.py`
writes the cut points, `MURFULU_TYPICALITY_PATH` points at them, and the row
reads «۸۶٪ — زیاد در میان همهٔ واژه‌های سنجیده‌شده (میانه: ۸۳٪)». Five bands
rather than three: a tercile over a distribution this narrow puts nearly
everything in the middle. The bands are percentile slices, not equal slices of
the range, because the range is unevenly filled. **An absent artefact leaves
the figure alone** rather than giving it a position nobody measured.

**Re-measured on v8 (2026-08-14) and the spread did not move.** 27,713 scored
forms went with the infix rules — 583,572 → 555,859 — and lowest 0.5541,
median 0.8283 and highest 0.9144 are identical to four places, with the four
band boundaries moving by at most 0.0003. So no word changed band because its
neighbours left. `data/typicality-v8.json` is what the app now reads.

**What is still open.** Should a deeper form be scored on its **own** outer
rule instead? It would need a vector for the intermediate base — *yāni* is not
a lexicon word and has none — so it is a question about the semantic model
rather than about the screen, and it belongs with S6's weighting. Until then
a deep row carries a fact about its ancestry, correctly labelled, rather than
a fact about itself.

**S14. ANSWERED 2026-08-17 — it grows `retired_reason_fa`, authored beside the
ruling.** The rules screen is the canonical published reference and it is
Persian throughout, so a **بازنشسته** badge with nothing behind it told a reader
*that* a rule no longer applies and never why — which for N-090, the ezāfe filed
as word formation, is the whole of the interesting part. All five retirements
now carry a Persian reason in `rules/decisions.yaml`, built into the pack and
served on both routes. **An unwritten reason shows the badge alone**: the
interface may not invent Persian, so silence must not become a guessed sentence.
The Persian is ours and unconfirmed, per the working rule. Original entry
follows.

**S14. A retired rule cannot say why in Persian.** The pack now refuses a
retirement without a `retired_reason` — G-01, N-090 and N-099 have one — and
every one of them is written in **English**, for whoever reads the repository.
The interface is Persian throughout and the standing rule is that it may not
invent Persian: every user-facing string comes from the pack as `label_fa`,
`explanation_fa` or `gloss_fa`.
So the rules screen shows a **بازنشسته** badge and stops there. A reader is
told *that* a rule no longer applies and not *why*, which for N-090 is the
whole of the interesting part.
**Question:** does `retired_reason` grow a `retired_reason_fa` beside it,
written by whoever made the ruling — or is the badge enough, with the reason
living in the repository for the people who work on it? Nothing is blocked;
the reason is served on `/rules/{id}` either way.

**S13. ANSWERED — and the linguistic half is now L19.** The engineering half
was settled in session 10: a flagged reading sorts after a clean one, which is
an order and not a filter. Which reading of بلند is *right* is the linguist's,
and as of 2026-08-17 it is asked with its measurement — *Baland* (اسم ذات,
flagged, confidence 0.4) builds **2,335** words and *boland* (صفت, clean,
confidence 1.0) builds **498**, while the same snapshot spells سربلند as
*sarboland* with an **o** and files it clean. The dictionary contradicts itself.
Original entry follows.

**S13. Should a reading the dictionary flagged open the screen?** بلند has
two: `Baland`, filed as an اسم ذات and carrying `needs_review`, which builds
**2,408** words; and `boland`, filed as a صفت and clean, which builds **555**.
The readings come out in the lexicon's own order, so the flagged one is what
a reader sees first — and it is the one that disagrees with the same
snapshot's `sarboland`.
The flag is now shown (session 9b) and nothing is filtered or reordered on
it, deliberately: a flag is the dictionary saying *check this*, not a verdict,
and 31.5% of active rows carry one.
**Question:** does a flagged reading sort after a clean one where a spelling
has both, or is showing the flag enough? Reordering on it would be the first
place this project treats karbon's flag as a judgement rather than as a note,
which is why it was not done unasked.

**Answered 2026-08-13 (session 10): it sorts after.** The project lead asked
why the screen writes *Sarbalandi*, which is the same complaint a third time.
Readings are now ordered by the dictionary's own flag and then by its own
confidence, so بلند opens on `boland` and `SarBoland…` replaces
`SarBaland…`. **It is an order, not a filter** — both readings are returned,
both are built from, and the flagged one is one press away. Which reading of
بلند is *right* is still the linguist's and is still open.

**S12. A build result is a page nobody can scroll. FIXED 2026-08-13.**
Measured in a real browser at 375 px: رفتن at depth 2 rendered **180,547 px**
of page — 222 phone screens — and بلند **588,102 px**, 3,185 rows. Every form
the engine made was in the DOM. The screen already declined depth 3 because
the answer is 24.7 MB; depth 2 was past what a reader could use, and nothing
said so.

Each group now opens at twenty rows and carries the count of the rest on the
control that opens it. Measured after: بلند **39,513 px** and 226 rows, رفتن
**40,005 px** and 230. **The length is now set by how many word classes there
are rather than by how many words were built**, so it stops growing with the
answer — which is the property that matters, more than the figure.

**The third step is answered too, as of 2026-08-17.** Paging was the first
half — S1, answered 2026-08-14: `/generate` takes `limit`, `offset` and
`worded`. The second half was that a page of an *unranked* list is a random
handful, and at three steps only 50 of a verb's 17,717 forms are words the
corpus has. The route now ranks before it pages, on how often each rule in a
chain produces a real word, and the screen asks for the best thousand and says
how many of how many that is. See PLAN 9.13. Steps 1 and 2 still ask for
`limit=0`, because there the screen counts every form to say what each group
folds.

**S11. ANSWERED 2026-08-17 — yes, by looking it up.** Every reading is
analysed, not the first: کنار comes back as *Kanār*, *Kenār* and *Konār*, and
the dictionary commits to none of them. **Never transliterated** — reading
Persian script into Behnevis without diacritics measured 5.8% correct, and a
guess would put a wrong base under a real chain of rules. A spelling the lexicon
does not hold is still refused, and the message now gives *that* as the reason
rather than "this route takes Behnevis", which had stopped being true.

**The honest caveat, measured:** of 20 derived words a reader would plausibly
paste, the lexicon holds **9**. This halves the refusals and does not remove
them — the words `/explain` exists for are mostly not headwords. And دانشمند,
one of the two examples this entry names, *is* in the lexicon and still rebuilds
to zero accounts, which is the S20 triage seen from the reader's side. Original
entry follows.

**S11. Should `/explain` accept the Persian spelling?** The route reads the
Behnevis form only: `Goftār` is taken apart, گفتار is not, and نه دانشمند نه
گفتگو — both of them the rule pack's own examples — come back with anything.
The screen now says the script is the reason rather than repeating "most
words are simple", which was not the reason. The route could look the
spelling up and try each reading's Latin, the way `/generate` already does.
**Question:** is that the right shape, or is the analysis screen deliberately
the expert's screen and the Behnevis its input? Nothing is blocked; the
screen is honest either way now.

**S10. The rules screen offers a family with nothing in it. FIXED
2026-08-13.** The میانجی button filtered on `family=G` and `/rules` served
**0** of them, while **17 glide rules sat in `rules/glides.yaml`** and build
results named them — `ow->av`, G-10, G-11 — with nowhere to look one up.

They are served with their own shape rather than squeezed into the affix
envelope: a glide has no affix, no input class, no semantic tag and nothing
to measure, so nulls in those fields would have put blanks on screen exactly
where the affixes screen had its twelve empty chips. `kind: "glide"` plus
`left`, `right`, `result` — which is what `/rules/{id}` has always returned
for one — and the screen gives it its own row, `ā + e → āye`.

Two consequences worth knowing. The pack total on screen went **195 → 212**,
which is what the pack has always held; 195 was the count with the glides
silently dropped. And `web/src/api/generate.ts` still asks `/rules?family=G`
as a cheap way to fetch the word-class table — it worked *because* the answer
was empty, and now carries 17 rules it throws away. Harmless, and worth a
tidier route for the word classes one day.

**S9. `/health` said the API was well while every build 500'd. HALF FIXED
2026-08-14.** The second of the two candidate fixes is done: `/health` opens
the lexicon, counts a row, pings the cluster, names whichever half is down and
answers **503**. The container healthcheck already honoured the status. **The
first is still open** — whether the snapshot should be opened with
`immutable=1`, which is what the flag is for and which also says the snapshot
may not be swapped under a running container. Nothing is blocked; a dead
lexicon now reports itself.

The original, for the record:

**`/health` says the API is well while every build 500s.** The lexicon
snapshot is in SQLite **WAL** journal mode and `./data` is mounted
**read-only**, so a WAL reader cannot make the `-shm` file it needs. Any host
process that opens the snapshot read-write — one line of `sqlite3.connect`
with no `mode=ro` — leaves the container unable to open it again, and
`/generate` answers a bare 500 until the API restarts. Reproduced and
recovered by `docker compose restart api` during the session-9 walkthrough.
Two candidate fixes, both cheap, and they are not the same decision:
open the snapshot with `immutable=1`, which is what the flag is for and
which also says the snapshot may not be swapped under a running container;
or make `/health` read one row, so a dead lexicon stops being reported as a
healthy service. The second is worth doing whatever the first answer is.
**Question:** which, or both?

**S6. ANSWERED 2026-08-17 — all three, and not yet.** Parts 1 and 2 stand as
recommended: script-keyed public vectors, BGE-m3 (MIT). Part 3 asked whether it
is acceptable to build all three measures and let the expert feedback set decide
between them. **It is — but that set (8.3) does not exist**, and re-measured on
v10 only **65 of 195 rules have any attested pair and 23 have 200 or more**, so
a three-way comparison today would be decided on a tenth of the pack.

**And the constraint has tightened, which is the number that matters here.**
**79.0% of attested pairs have a bound verb stem as their base** — 13,270 of
16,787 — up from the 76.8% this entry quotes. That is the fact that separates
the three candidates, because FRACSS fits a matrix on base→derived vector pairs
and a bound stem has no distributional vector. Original entry follows.

**S6. Semantic scoring: which vectors, and which measure? Blocks 5.6, and
5.5 behind it.** Researched and measured 2026-08-12; the full working is in
[RESEARCH_SCORING.md](RESEARCH_SCORING.md). The question used to be "which
embeddings, trained on what". It is now three smaller questions, and the
first two have a recommendation attached.

**1. Persian-script vectors, or our own over Behnevis forms?**
[RULE_DISCOVERY.md](RULE_DISCOVERY.md) assumed we needed our own, because
public models are trained on Arabic script. Measured, that costs **6.2%** —
1,037 of the 16,714 linked corpus spellings have more than one reading, and
the engine composes the Persian spelling beside the Latin anyway. *Suggested:
start with a script-keyed public model and flag the 6.2%, exactly as the app
already does with مرد.* Training our own is a fallback, not a prerequisite.

**2. Which model?** Options with their licences are tabled in
RESEARCH_SCORING. *Suggested: **BGE-m3**, run over our own corpus.* The sister
poetry-search project already uses it on classical Persian couplets, it is
**MIT** licensed, and it is already downloaded — so it is the cheapest thing
to try and the only candidate with evidence behind it on **this** material.
It is a line-level model, so a word's vector has to be built by averaging its
occurrences rather than looked up.
The one decision that is not technical: **fastText's Persian vectors are
CC-BY-SA 3.0**, and share-alike travels to anything derived from them — which
touches PLAN 8.4. BGE-m3 (MIT), HPLT v3.0 (CC0) and Naab (MIT) do not have
that problem.

**3. Which measure? This is the one that is genuinely open.** A 2025 study on
Malay — an under-resourced language, off-the-shelf fastText — found the
**affix centroid** fitted human transparency judgements *better* than FRACSS.
It also needs no base vector, which matters here more than it did there:
**76.8% of our attested pairs have a bound verb stem as the base**. But the
centroid scores a word that already exists, and this project generates words
that do not. FRACSS predicts a vector for those; a third shape — comparing the
*base* against the centroid of bases the affix usually takes — would also
work and **is our extrapolation, not something anyone has published**.

**Question:** is it acceptable to build all three and let the expert feedback
set (8.3) decide between them? That is the honest answer, and it is the
project lead's to approve, because it means 5.6 lands after there is feedback
to fit against rather than before.

**What no choice here can fix:** only **63 of 195 rules** have a single
attested pair, and only **22** have 200 or more. A per-affix semantic model is
possible for a few dozen rules and for no more than that.

**S8. ANSWERED 2026-08-17 — an inflection no longer outranks a derivation.**
This entry says no condition over the fields we hold can fix the second half,
and that is right: the fix does not use those fields. It asks the **inflection
analyser** built in session 10 to *measure* the problem, which had never been
asked at request time.

Measured on رفتن at two steps, 660 forms: رفتی moves from **12 to 57**, نرفته
from 19 to 60, and رفتار from 13 to **10**, روش 16 → 13, رونده 21 → 14.
**Seven of the top twenty read as inflections before and none does now.**

**Both the clear and the shared cases are demoted**, deliberately. 95.6% of
inflection-shaped forms are spelled by a derivational rule too — independently
reproducing the 95.5% this entry measured on a different sample — so demoting
only the clear ones would have left رفتی above رفتار untouched, because *-ی* is
also N-095. The letters cannot settle which reading is meant and the row says
so, naming the rules. Marked and ranked down, never dropped. Original entry
follows.

**S8. Ranking puts how a match was *linked* above how much evidence there
is. FIXED 2026-08-13; what is left is the weighting.** `ranked()` on the
build screen sorted on the attestation level —
`reading` before `spelling` before `none` — and only breaks ties on the
document count. The level says whether the lexicon has a headword for that
exact spelling, which is a statement about the dictionary, not about the
word. So on گفتن the screen puts **گویه, in 6 poems, above گفت, in 19,839**.
Measured over the top twenty of every group of five builds — رفتن، گفتن،
دانستن، بلند، مهر: **64 of 4,977 pairs are inverted, 1.3%**, and they land
near the top because that is where the level boundary falls.
The discount is not baseless: a `spelling` match may be a homograph, which is
exactly what session 8 measured. So the order is now *written, unwritten,
never asked* → the document count → the ground under the chain → **then** the
level, as a tie-breaker; and the row says whose count it is, which it did not
before.

**What is still open is the weighting, and the re-test says it is urgent.**
A tie-breaker is the crudest possible use of the level: it discounts nothing
until two forms are otherwise equal. So the count now outranks everything, and
**رفتن's screen opens on روی** — `ravi`, 31,830 poems, which the corpus reads
as *Rui*, "face", a different word — above رفتار at 1,091 and روش at 912.
Behind it come رفتی and نرفته, which are inflected forms rather than new
words. Measured over the top twenty of the first group: **0 of رفتن's, 0 of
بلند's and 0 of مهر's matched on the reading**.

The row says «شمار برای این املاست», so nothing is claimed falsely. But saying
a number belongs to another word and then ranking on it is not a resting
place, and this is the first row of the flagship word rather than a subtlety
at the bottom of a list.

**Half of this is now built, on the project lead's word.** Where the lexicon
holds a reading for the spelling and none of them is the one we built — case
folded, so `Goft` and `goft` are one word — the count is evidence about a
different word and no longer ranks the form. It stays on screen with its
caveat; only the ranking stops using it. Narrow: 11 of رفتن's 500 forms, 9 of
مهر's, 1 of گفتن's. رفتن now reads رفت، رفتن، **رفتار، روش**.

**What is still open, and it is the harder half.** Where the lexicon knows
**no** reading for the spelling, nothing in the data separates رفتی — an
inflected form, "you went" — from گفتار, which is exactly the word we built.
Both are `unlinked`, and 16 of رفتن's top twenty are. So inflected forms still
rank on a count that may not be theirs, and no condition over the fields we
hold will fix it: it needs either a morphological analyser over the corpus or
the affix map extended to cover inflection.

**Measured 2026-08-13 (session 10), before designing anything.**
`tools/measure_inflection.py` and `tools/measure_built_inflection.py`.

| the corpus, all 409,916 spellings | spellings | share |
|---|---|---|
| the lexicon has a reading | 16,714 | 4.1% |
| a verb stem we hold | 1,082 | 0.3% |
| **reads as an inflection of one of those** | **48,039** | **11.7%** |
| unaccounted for | 344,081 | 83.9% |

But the corpus is the wrong denominator: only an **attested** form carries a
number and only an attested form is ranked on one. Against the 22,118
attested built forms in derivations-v5:

| | forms | inflection | share |
|---|---|---|---|
| every attested built form | 22,118 | 7,047 | 31.9% |
| of them, `unlinked` | 17,071 | **7,047** | **41.3%** |
| of them, the lexicon knows the spelling | 5,047 | 0 | 0.0% |

The last row is **true by construction**, not a discovery: a spelling the
lexicon holds is never called an inflection, and `unlinked` means it does not
hold it. What it does establish is that the whole of this sits in the half S8
already named. Those 7,047 forms carry **1,080,260 of the 2,589,413 documents
the unlinked half rests on — 41.7%.**

**And the finding that decides the design: 6,730 of the 7,047 — 95.5% — are
`shared`**, meaning a derivational rule in the pack writes the same letters.
آبادانی is the indefinite of آبادان *and* the noun "prosperity"; کشی is a
clitic form *and* a word; گسترده is a past participle *and* an adjective. **So
this cannot be closed by spelling.** A rule that demoted every inflection-
shaped form would demote 95.5% of them on a coin-flip.

**The instrument was checked against a control before any of that was
believed.** Every lexicon headword is a word by definition, so the share of
them the analyser reads as an inflection anyway is its own error rate:
**3,262 of 43,225 — 7.5%** — and it is very unevenly spread.

| pattern | corpus hits | known words it also claims |
|---|---|---|
| `‌های` / `های` plural | 1,591 | **0.0%** |
| `‌ها` plural | 1,079 | 0.3% |
| `شان` | 1,072 | 0.9% |
| `ها` plural | 1,483 | 1.1% |
| `تر` comparative | 696 | 4.1% |
| `ی` indefinite | 6,874 | 10.4% |
| `ان` plural | 2,966 | 13.9% |
| `ین` Arabic plural | 681 | 17.6% |
| `ا` vocative | 1,757 | 18.2% |
| `ون` Arabic plural | 482 | **20.2%** |

**So the patterns are not one thing and must not be treated as one.** The
ha-plurals are all but exact; the Arabic plurals and the vocative are noise —
*تافتون* is a bread, not a plural of تافت. **Nothing is built on this yet**:
what a ranking should do with a `clear` pattern at 0.3% and a `shared` one at
20% is the project lead's, and the weighting proper still belongs with S6.
**And the weighting proper is untouched.** A spelling match and a reading
match with the same count still sort alike. That number belongs with S6.

**S5. ANSWERED 2026-08-17 — the third option: a second appended row.** New
table `rule_proposal_decisions` (migration 0007), append-only behind a Postgres
trigger, which is the shape `expert_feedback` and `linguist_rulings` already
use. Option 2 was rejected because stamping the proposal `settled` would have
made `rule_proposals` the one authored table edited in place, in a schema that
protects the others with a trigger.

`store.undecided()` is what `tools/export_proposals.py` now applies, so a
refused proposal does not come back; `--all` is a deliberate override.
**Deciding twice is allowed** — the latest row wins, so a later accept genuinely
reopens a refusal, and both rows stay. New `tools/decide_proposals.py`. Original
entry follows.

**S5. How is a *refused* rule proposal recorded? Nothing is blocked.**
PLAN 8.1 works end to end: an expert proposes, `tools/export_proposals.py`
writes the change into the YAML, and `git diff rules/` is the review. Accepting
is committing; **refusing is `git checkout rules/`** — and that is where it is
incomplete. A refused proposal is still in the table, so the next export
applies it again, and the reviewer refuses it again. The loop does not
converge.

Three ways out, and picking one is a workflow decision rather than an
engineering default:
1. **Nothing** — the export lists every proposal it applied, and a reviewer
   reads the list. Cheap, and it stops working at about twenty proposals.
2. **A settled marker** on the row, written by a command when the reviewer
   commits or refuses. Simple, but the table stops being append-only.
3. **A second appended row** recording the decision, the way feedback records
   a verdict. Keeps the history whole and is the most work.
Today the export is honest about what it did — *applied*, *already in the
pack*, *the rule moved*, *no such rule* — so nothing is lost while this is
open. It only gets noisy.

**S4. ANSWERED 2026-08-17 — no, and it is now a decision rather than a gap.**
The structured context is the reusable half and is captured in full; an image is
not machine-readable at all.

**The export is what decides it, not the storage.** The feedback manifest
deliberately claims no licence, because those records are judgements experts
made about the language and were not given to us to hand on. A screenshot
compounds that in a way structured context cannot: it captures whatever else was
on the reviewer's screen, which nobody consented to and which no field of ours
describes. `screenshot_ref` stays as a nullable column, documented as never
written rather than left looking unmeasured. Original entry follows.

**S4. Is the optional screenshot worth its storage? Nothing is blocked.**
[REVIEW.md](REVIEW.md) offers a screenshot beside every piece of feedback and
says where it would live: "a mounted volume, not the database". The record
carries `screenshot_ref` for it. **No volume exists, nothing captures one, and
the widget built in 7.9 does not pretend to** — the structured context, which
REVIEW.md itself calls the important half, is captured in full.
Adding it costs a volume, an upload route, a size limit, and a decision about
what happens to the images when the feedback set is exported as a research
dataset (8.3). **Question:** is "what did he actually see" worth that, or is
the structured context enough? Nothing waits on the answer.

**S3. ANSWERED 2026-08-17 — the coined terms are authored data.**
`rules/word_classes.yaml` holds کارنام، برنام، کاربن دو and the rest, loaded by
`murfulu/rules/word_classes.py` and served from `/rules`; the build screen heads
its groups with the project's term and puts the traditional one in a tooltip. It
used to say اسم مصدر — the interface labelling its own output in the vocabulary
the project exists to replace.

**Eight terms are quoted from the linguist's own table. Four are ours**, read
off the source's Behnevis, and **the vocative gets none at all** — *Nedāyi* is
itself Arabic-derived, so writing ندایی into the column reserved for the
replacement would have hidden the gap; the API falls back and says it fell back.
All twelve Persian explanations are ours. Everything unconfirmed is marked and
is question **L17**. Original entry follows.

**S3. Where does the grammar glossary come from?** The interface has to explain
*kārnām* and *kārbon-e do* without a manual, so every technical term needs a
one-line Persian explanation and the traditional term beside it. Those exist
already, in `murfulu/rules/types.py` as `WORD_CLASSES` — and **no route exposes
them**. The `Term` component takes them as props and invents nothing, which is
right, but something has to supply them before the first screen shows a word
class.
**Half of this is now answered, and the remaining half is sharper.** `/rules`
serves the word-class table (task 7.4), so a screen can name a class in
Persian without inventing anything. But what it serves is the **traditional**
term — اسم مصدر for `karnam` — because that is what the transcription holds.

**The project's own coined terms are not in the data at all.** کارنام, کاربن
دو, برنام and the rest exist only in the design documents; `rules/types.py`
keys on the transliteration and stores the traditional name beside it. So the
build screen labels its groups اسم مصدر where FRONTEND.md says the primary
label should be کارنام with the traditional term in a tooltip.
**Question:** where do the coined Persian terms live, and who writes them
down? Transliterating `karandekarbahr` into Persian script is a linguistic
act, not a mechanical one, so nothing here has done it. One small authored
table — the same shape as `semantic_tags.yaml` — would close it.

## For the project lead — engineering, and both block PLAN 6.2

**S1. ANSWERED 2026-08-17 — a cache hit re-derives the presentation.**
Measured on derivations-v10: the three fields would add **245 bytes a record,
18.6%**, taking the index from 2.28 GB to 2.71 GB and needing a full rebuild to
land. Re-deriving them costs **0.02s at two steps and 0.48s at three**.

**Size is the smaller half of the reason.** The three fields are deterministic
functions of a **versioned** rule pack, so storing them freezes a presentation
against the pack that produced it — a `glide_alternatives` written under 0.1.0
and read under 0.2.0 is a true-looking figure under a false label. ARCHITECTURE
constraint 6 is met either way, which is what makes this a choice: the stored
path already carries the rule ids, the affixes and the glide ids. What is absent
is presentation detail, not derivation. Original entry follows.

**S1. What does a cached generation return?** Measured on the real lexicon:
رفتن gives 510 words at depth 2, **15,479 at depth 3 in 0.2 seconds**, and
22,952 at depth 4. The space saturates and building it is nearly free; what
costs is checking each form against the corpus and writing it.

The stored derivation keeps each path's rule ids, affixes and glide ids, but
**not** the base at each step, the *ow → av* stem form, or the glide
alternatives — three fields `/generate` shows today for every step. So a
cached answer is thinner than a fresh one.

**And the answer has to be paged, not only cached.** Measured through the
running API: رفتن at depth 2 is a **0.5 MB** response; at depth 3 it is
**39 MB** (24.7 MB when this was written, before 9.10 gave prefixed verbs
their stems). Paging is the same decision as caching — what a cached answer
*is* decides what a page of one looks like.

**The screen offers three steps as of 2026-08-17** and pages them, so this no
longer blocks a reader; it blocks only the *cache*. Every deep request still
rebuilds all 17,717 forms and discards all but a thousand, which is the cost
this task exists to remove and is now measurable: 1.3 seconds a request.

**And depth 2 alone is enough to kill a consumer, which stopped being
theoretical 2026-08-14.** A language model given the API called `/generate`
at depth 2 without filtering and stalled outright — the response never fit.
Measured across four ordinary words:

| word | depth 1 | depth 2 |
|---|---|---|
| رفتن | 58 KB | 1.3 MB |
| نان | 49 KB | 3.1 MB |
| بلند | 67 KB | 3.8 MB |
| مهر | 99 KB | **6.2 MB** |

**The browser survives this because the screen folds each group at twenty;
nothing protects anyone else.** A programmatic caller gets the lot, and the
route offers no way to ask for less — no page, no limit, no field projection.
So the answer to *what does a page look like* is now also the answer to
*how does anything but our own screen use this route*, and S16's prototype
needs it before it needs anything else.

**Question:** does the stored path grow those three fields, on all 1.7 million
documents, or does a cache hit re-derive the presentation in memory and use
the index only for the evidence? The second costs 0.2 seconds and stores
nothing extra; the first makes "served from cache" literally true.
ARCHITECTURE constraint 6 — *every generated word carries its derivation* —
argues for the first, and it is the project lead's call because it is paid for
in index size.

**S2. ANSWERED 2026-08-17 — it does not reach it at all.** Both answers this
entry offers damage something, so the cache goes elsewhere. The `derivations`
index is a **release artefact**: versioned, built as a batch, and compared
version against version by `tools/compare_versions.py`, where *nothing else
moved* is a property a release is checked against. A live write makes that
untestable and the index unreproducible — drift caused by whoever happened to
browse. The project has met this shape before, when three rulings were edited
into generated rule files and re-running the builder reverted all three without
a word. A live cache is its own index beside the release one, disposable by
design.

**The read half was already built** and this entry had not caught up:
`murfulu/search/attested.py` asks `word_types` in one batched query and fills
the same `Index` class the batch job fills, so the two cannot drift about what
counts as attested. Original entry follows.

**S2. How does a live result reach the `derivations` index without damaging
it?** The precompute merges across the whole lexicon: 439,078 words are built
more than one way, and each record carries every path and its sister forms.
A live run knows one source, so writing by the same id would replace a merged
record with a single-source one. Writing only what is absent keeps the index
intact but leaves the older forms unmarked, so the cache cannot find them
again on the next request.
Part of the same question: `scoring/attestation.py` is an **in-memory** index
built from a full link pass, which a live request does not have. Attesting a
live result needs a batched lookup against `word_types` — about eighty lines,
but it decides whether a live record carries evidence at all, and a stored
derivation with no evidence must never look like one with none found.

## For the linguist — nothing is blocked, but these need a ruling

Phase 0 and Phase 1 are complete. None of the following stops work; each is a
place where the source is unclear and nothing was guessed.

**R. What measured productivity should each authored `strength` mean?**
RULE_PACK.md defines three strengths — `obligatory`, `typical`, `occasional` —
and proposes the authored value as a prior with corpus P as the evidence.
Measured: **the source states a strength for 3 of the 195 rules** (V-010,
V-011, V-012, all *-ār*, all `typical`, because the source writes *bištar*).
So there is almost no prior to combine with.
Two questions, and the second blocks the composite score in 5.5.
1. Should the linguist author a strength for the remaining 192, or should the
   measure stand alone?
2. If both are kept, **what measured value does each strength correspond to?**
   The comparison currently splits the measured spread into terciles and maps
   `obligatory`/`typical`/`occasional` onto high/middle/low. The terciles come
   from the data; the mapping onto the three names does not, and it is a
   judgement rather than an engineering default.
Under that provisional mapping all three authored rules disagree with the
measurement: hedged as tendencies in the source, top third when measured.

**Q2. Two Persian spellings, one Behnevis reading — one word or two?**
The `derivations` record is keyed on the Latin form plus the output class, and
Behnevis is phonemic, so two Persian words that read the same way land on one
record. Measured in the first precompute run: **10,270 of 1,738,711 words**.
The pair that shows it plainly is خواستن (to want) and خاستن (to rise), both
*xāstan*, so everything built from them shares a reading.
Nothing is lost — `form_fa_variants` keeps the second spelling — but the app
has to show *something*, and which is a linguistic judgement.
**Question:** are two spellings with one reading one entry with two written
forms, or two entries the key cannot tell apart? If the second, the id needs
the Persian spelling in it, and ARCHITECTURE's dedup key changes.

**Q. Two transcription faults to send to the karbon maintainer.** Measured in
[LEXICON_ANALYSIS.md](LEXICON_ANALYSIS.md) §4b. **و read as `v`** where it is a
vowel (71 primary readings, 16 variants) and **ه read as `h`** where it is a
vowel (22 primaries, 12 variants) — the second one was not previously
recorded. Both are single mechanical patterns, so both should be cheap to fix
at source. **76 of the broken primaries carry no `needs_review` flag**, so
nothing downstream can tell they are suspect. Nothing is filtered on our side;
this is a request upstream, not a workaround here.

**O. Should function words and inflected forms be linked at all?** Linking
the corpus to the lexicon covers 45.7% of running text. Almost all of the
remainder is words a headword dictionary does not carry: و, ز, بر, آن, او,
چون, plus inflected verbs (بود, شد). **Question:** is a small hand-written
list of function words worth adding, or do we simply state that they are out
of scope? It does not affect generation — no rule applies to و — but it does
affect any figure we publish about coverage.

**N. Three gaps on the corpus, none blocking.** First, and newly measured:
**27 of the century table's 43 entries name a poet slug this corpus does not
use.** They date nothing, and an entry that matches nothing looks exactly like
one that works. That is why **فردوسی is undated** — 778 poems, the largest
poet in the corpus — the table writes `ferdowsi` and Ganjoor's own slug is
`ferdousi`. Rumi, Rudaki, Sanai and Naser Khosrow are in the same position.
Only **16 entries actually match**, and those are what the 26% figure rests
on.

Repairing them is **not** a mechanical rename, and nothing was guessed. Some
are plainly the same poet under another spelling — `ferdowsi` → `ferdousi`,
with فردوسی on both sides. Others are not: `kamal-khojandi` is nearest to
Ganjoor's `kamal`, which is **کمال‌الدین اسماعیل — a different poet**. A fuzzy
match would have dated one poet's work with another's century.
**Question:** should the table be re-keyed on the poet's Persian name, which
both sides carry and which cannot silently match the wrong person? A
candidate list with poem counts is one command away; confirming it is the
project lead's.
`centuries_without_a_poet()` reports the gap, and the ingest prints it.

Second, **the century table covers 56 of Ganjoor's 237 poets** as written, so
only 26% of the 133,148 poems can be dated. Century drives the dispersion chart and the "did this word survive?"
evidence, so the other 181 poets need dates from somewhere — the table is
hand-written and inherited from the earlier prototype.
Second, **Ganjoor's own terms are confirmed as of 2026-08-17, and the answer
is that they warrant nothing.** Their FAQ, asked whether the data are free of
copyright, answers «لزوماً خیر!» — not necessarily — stating that no legal
review has been made, that most of the content was typed from published books
whose own status was never established, and that free access must not be read
as a licence. Their *service* is GPL-3.0; the poetry is not covered by it.

The adapter said *"public-domain classical texts … (confirm terms)"* until that
day, and the first half was ours rather than theirs: the parenthesis was honest
about not knowing, the words in front of it asserted the very thing nobody had
checked. It now states Ganjoor's own answer. **The poems being classical and
their authors centuries dead is a different question** from whether this
compilation of them may be redistributed, and conflating the two is what made
the old wording feel safe. See NOTICE and PLAN 8.4.

**H. Is the prefix باژ or واژ?** Verb row 55, the only place it appears. The
source writes *bāž* with a *b*, giving باژ, and its example is *bāžgunidan*
("to turn upside down"). But the form usually written today is واژگون
(*vāžgun*) with a *v*. Both exist in older Persian. Being asked; باژ is in the
pack meanwhile, and V-055 is the only rule still flagged.

**M. Persian joining when a word ends in ه. BUILT 2026-08-13, unconfirmed — see FOR_THE_LINGUIST L7.** *taze* + *i* is *Tāzegi* in
Latin and تازگی in Persian: the ه drops and گ appears. The engine currently
writes تازهی. The Latin is right; only the Persian is wrong. Part of the same
unextracted Behnevis joining specification as item K.

**Measured 2026-08-13, and it is much more expensive than "only the Persian".**
**38,932 forms spell this join wrong.** Attestation looks a form up by its
Persian spelling, so a form spelled wrongly **cannot match the corpus and comes
back *never written***. At least **658** of them are real words the corpus has:
زندگی (4,571 occurrences), مژگان (3,977), زندگانی (3,489), درگاه (3,284),
بندگی (2,583), بارگاه (1,336), آزادگان (634). It is also why the best-ranked
*new* words for دانستن read as دانندهگی and داناگی.
So this is not cosmetic: it suppresses a whole class of real vocabulary from
the evidence, and it makes the top of the build screen look wrong at a glance.
**Built, in corpus v4.** `glides.join_fa` drops the ه, and also puts the گ in
the Persian at all — it was missing entirely, so *Zandegi* was written زندهی.
The joins spelled wrong went from 38,932 to 0; attested forms from 24,197 to
24,482, which is **1,609 gained and 1,324 false matches removed**. Marked
unconfirmed and registered as L7. **Item K — the ZWNJ inside a compound — is
untouched**, because it needs the joining specification this one did not.

**K. Persian joining inside a compound — ZWNJ.** The engine writes *Goftogu*
as گفتوگو, plain concatenation. The usual modern spelling is گفت‌وگو, with a
zero-width non-joiner. Same question for prefixed forms. This is the
Behnevis-joining item PLAN 1.3 already flagged as unextracted; it affects only
the Persian spelling, never the Latin, so nothing is blocked.

**L. Can an affix stack on itself? — answered by measurement for prefixes on
2026-08-15 and for suffixes on 2026-08-20. One narrower question is left.**

**Prefixes: no, and the corpus settled it rather than a ruling.** v9 builds
**4,968 words whose derivation adds one prefix twice, and not one of them is
attested** anywhere in 25,497,189 tokens. The 14 that appeared to be were
spelling collisions — ننوشت is *na-navešt*, a single negation on a stem
beginning with *n*, not *na-* twice. Settled the same way question J was: by
measuring, because the project does not guess a linguistic decision and
waiting is never the reason something stays wrong. A prefix may now be added
once per path, and the guard keys on the **affix**, not the rule id — V-059 and
V-060 are both *farāz-*.

**Suffixes: also no, and by the same measurement — 2026-08-20.** The reasoning
for leaving them out was that *andišidegi* + *-i* is a real pattern, which is
two **different** suffixes. What the engine actually built was *Golstānstān*,
*Golzārzār*, *Golkadekade*, *Golāā* and *goftee* — **35 of the 2,335 forms one
reading of گل makes at two steps**, and the same 35 shapes for درد. Raised by
the project lead.

Measured before anything changed, over 120 random readings: **2,725 of 161,774
forms at depth 2 add one suffix twice, 1,830 distinct spellings, and not one of
them is in the corpus** — against 25,497,189 tokens, with گلستان (3,518
documents) and دردمند (507) sent through the same query as controls to prove it
could find a word. The guard now covers suffixes, keyed on the affix for the
sharper of the two reasons: N-093 and N-095 are both *-i*, N-074 and N-077 are
both *-vār*, so a rule-id guard would have built *Goliyi* and *golvārvār*
anyway. Cost: the sample goes from 161,774 forms to 159,183, and every rule
example the engine could rebuild before it still rebuilds.

**Still open, and narrower.** The guard keys on the affix *string*, so it also
refuses two different suffixes that happen to be spelled alike — the *-i* of
nesbat followed by the *-i* that makes an abstract noun, which is the
*andišidegiyi* case. Nothing in the corpus supports it, but the corpus is
classical and that form is modern. **Question:** is a repeated *-i* ever right,
and if so, does the pack need the two *-i* rules told apart by something other
than their spelling? Also *-ā* on an infinitive (V-051) — the same shape, never
measured on its own.

**I. نهفتن has no present stem.** The stem document writes ؟ and karbon leaves
the verb out rather than guess. The lexicon may have it.

---

## Answered on 2026-08-11 (session 3, later)

**P. Lexicon rows with a second reading.** — **Answered: fixed. Both readings
are real and both are generated from.** The `phonemic_variants` column holds a
genuinely different second reading for **7,212 active rows** — آبرو is *Ābrav*
or *Ābrov*. The wrapper had been reading only `phonemic`, so the alternative
never reached the engine and a whole family of words could be built on a
reading the dictionary does not commit to.
`Reading.latin_variants` now carries them and `generation` builds from every
one. The stored variants are lower-case while the primary keeps its
capitalisation, so the primary's case is applied — case is meaning in Behnevis
and a variant is the same class of word. **No verb is affected**: stems live in
their own columns and carry no variants.

**J. What happens when a stem written *ow* meets something?** — **Answered by
measurement, then confirmed.** It is not a joining rule at all: a stem written
*row* **is** *rav* the moment anything follows it, vowel or consonant. The *ow*
spelling is only how the stem looks standing alone.

Evidence, taken from the lexicon snapshot: **not one of its 45,579 words
contains *ow* anywhere.** The sequence appears only in the six present stems
themselves (row, šow, dow, derow, šenow, šenāow). Every word built from them
uses *av* — 16 words begin *Ravān-*, 28 begin *ravā-*, 17 begin *šav-*, plus
*šenavidan* and *šenavāndan*. The consonant case is settled by **šenavgar**,
where *gar* follows and it is still *šenav*. And the project's own alphabet
table lists the vowels as ā a e o i u, with *ow* named separately as a sound
for words like *owj* and *ferdows*.

Recorded in `rules/decisions.yaml` as a `stem_finals` rule with that evidence.
G-15 and G-16 are retired as two instances of this one fact. Every result that
uses it records `ow->av` in its path, so nothing changes silently.

**G. Glide rule G-01 contradicts its own example.** — **Answered: G-01 is a
duplicate of G-03 and its example was misfiled.** G-01 is retired
(`active: false`, id kept, reason recorded) and its example
`ā + ande = Āyande` moved to G-04, the *ā + a* rule it actually demonstrates.
Recorded in `rules/decisions.yaml`.

**H1. The affix `-mānd`.** — **Answered: a typo.** Built as *-mand* (مند), as
its own example *dānešmand* and the neighbouring *-umand* / *-vand* rows show.
The source spelling is kept beside it as `affix_source`.

**H2. The prefix `pa-`.** — **Answered: پ is correct.** *pa-* + *did* →
*padid* (پدید).

**H3. Is `-bāž` a prefix or a suffix?** — **Answered: a prefix.** The source
writes it with a leading dash, but its own example *bāžgunidan* puts it at the
front. The dash was on the wrong side. Built as *bāž-*. Only the spelling
remains open — see H above.

---

## Answered on 2026-08-11 (session 3)

**A. Which source rows are the `D` family?** — **Answered: there is no D
family.** Kept below for the record. RULE_PACK.md promises D-001…D-004,
"the 4 rules that make a verb from a noun/adjective", in `verbalisers.yaml`.
The source document has no verbaliser table. Only **two** rows build a verb
from a noun or adjective — verb-table row 3 (`-idan`, Nām/Barnām →
intransitive infinitive) and row 4 (`-ānidan` / `-āndan`, Nām/Barnām →
transitive infinitive). Rows 1 and 2 also produce infinitives, but from a verb
stem, so they are causatives.

  - *Reading one:* D covers verb rows 1–4, so `V` starts at V-005.
  - *Reading two:* D covers rows 3–4 only, so D has two members, and rows 1–4
    also carry V ids.

  Ids are permanent, so this cannot be corrected later. **Not guessed.**

  **Searched, 2026-08-11:** all 19 documents in the Drive archive and the whole
  earlier prototype at `~/Code/mosaic/murfulu`. No verbaliser group exists
  anywhere. The concept document `Konzept/درآمد_پروژه.docx` states there are
  **two** such rules — `-idan` for the intransitive and `-āndan` for the
  transitive — which are exactly verb-table rows 3 and 4. The "4" is a
  miscount in RULE_PACK.md itself.

  **Recommendation: drop the D family.** Number all 81 verb-table rows
  `V-001` … `V-081` in document order, and tag rows 3 and 4 as noun-to-verb so
  they can still be shown together. This also matches the principle
  RULE_PACK.md already applies to compounding templates — a rule lives in the
  family of the table it comes from. Awaiting a yes.

**B. Are the `S` stem rules in scope for Phase 1?** — **Answered: yes, done.**
Extracted, assigned S-01 … S-09, and cross-checked against karbon. S-01…S-09 (infinitive →
kārbon-e do) are not in `Dasturhāye Vāžesāzi az Kārbonhā.docx`. SOURCES.md puts
stem rules 1–9 and their exception lists in the separate stem-rules file under
`Forschung/`. Extract them now, or leave `S` for its own task?

**C. Are the lower-case bracketed labels tags, or plain glosses?** 44 bracketed
strings in the rule tables. The capitalised ones (Jā, Zamān, Nesbat…) read as
the grammar's coined tag names; the lower-case ones (bālā, pāyin, darun, pas,
dobāre, bāz, suy…) read as ordinary words explaining what a prefix means. All
44 are currently kept as tags. Not blocking — it changes how the tag set is
presented, not whether the rules load.

**D. Is `Mānand` the same tag as `Mānandi`, and `Nāi` the same as `Nāyi`?**
Kept separate for now; merging is a linguistic judgement.

**E. Who writes the gloss templates, and do they hang on the tag or the
rule?** Every semantic tag needs a Persian sentence like
`جایی که {stem} در آن است` to turn a generated form into a generated
*meaning*. 42 of 43 are `null` — the one exception is `Jā`, which
RULE_PACK.md already supplies. Authoring the rest is the linguist's, not the
engine's.

**Measured 2026-08-13 (session 10)**, after the project lead asked whether the
sources give the meanings at all, and said that a word we cannot give a
meaning to is not obviously worth building.

| | |
|---|---|
| active rules | 193 |
| of them naming a semantic tag | **103** |
| of them naming **no** tag at all | **90** |
| distinct tags | 43 |
| tags with a bare gloss word (`gloss_fa`) | **43 — all of them** |
| tags with a gloss *template* | **1** |
| built forms in v5 carrying a meaning | **70,370 of 1,704,021 — 4.1%** |
| **attested** built forms carrying a meaning | **407 of 22,118 — 1.8%** |

So a reader ranking a real word sees a meaning **once in fifty-four times**.

**And authoring 42 more templates on the tag would not fix it, which is the
part worth putting to him.** The template hangs on the *tag*, and one tag is
shared by rules that do not mean the same thing:

| tag | rules | their affixes |
|---|---|---|
| `Nesbat` | **19** | -āne, -či, -sār, -ak, -gar, -gān, -gāne, -vār, -vāre, -gi, -i, -in, -ine, -vand, be- |
| `Mānand` | 12 | -āsā, -gin, -āne, -dis, -sār, -sān, -ak, -vār, -vāre |
| `Dāštan` | 11 | bā-, be-, -mand, -nāk, -vār, -var, -ur, -umand, -vand |
| `Jā` | 5 | **-ān, -dān, -stān, -kade, -gāh** |

The one template that exists is `Jā`'s, and the index shows what that costs:
*آبادانیدگان*, *آبادانیدهدان*, *آبادانیدهستان*, *آبادانیدهکده* and
*آبادانیدگاه* all carry the identical sentence «جایی که آبادانیده در آن
است». **Five affixes, one meaning.** نمکدان is a container, گلستان is a land,
میکده is a house — the tag they share is too coarse to write one sentence for.
And **N-068 (-gāh) is tagged `Jā` *and* `Zamān`**, so a word that may be a time
is given a place: it is one of only 3 rules in the pack naming two tags, and
the first template it meets wins.

**Question, in two parts.** Does the gloss sentence belong to the tag — 43
sentences, coarse, and five affixes share one — or to the rule — 193
sentences, exact, and four times the authoring? And for the 90 rules with no
tag at all: is a tag missing, or do those rules have no meaning a template
could carry?

**F. Three lexicon categories are unmapped** (PLAN 3.2): وام‌واژه (5,347 rows —
"loanword" says origin, not class: classify in a second pass, or default to
`nam`?), صفت-اسم (296 rows — one class or both? mapping to both roughly doubles
what they generate), and the 11 rows with no category at all.

## In flight

1. **The lexicon.** ~~Not in the repo.~~ **Landed.** `data/lexicon-20260808.sqlite`,
   45,579 active rows, recovered from karbon's git history and now read through
   `murfulu/lexicon/`. Still worth asking the karbon maintainer for a fresher
   snapshot; the path is configuration, so swapping it needs no code change.

## Needs a decision soon

2. **Where do the rules live?** The ~200 rules are currently a Word table.
   Machine-readable format — YAML? JSON? A SQLite table the linguist can edit through
   the workshop UI? The NGI proposal promises rules "editable by a linguist
   without programming", which points away from hardcoding them in Python.

3. **How does Murfulu talk to karbon?** Import `karbon-nlp` as a dependency, or
   call it over HTTP? Import is simpler; it also means Murfulu inherits the
   lexicon-file problem.

4. **Repo naming.** The NGI application says `github.com/pasmod/stemma`; the code
   is `kp-multiverse/karbon`; this project is `murfulu`; the library the proposal
   promises is `morphology-core`. Four names for three things. Pick the public
   story before submission.

5. **Which Latin convention is canonical?** Confirmed: the later one
   (`š ž č j ˈ`), matching karbon. Worth writing down formally so it does not
   get re-litigated.

## Resolved 2026-08-11 (second pass)

- Depth: no linguistic cap; hard stop at 5, precompute 1–2, deeper live.
- Live results are cached; the cache becomes the precompute.
- Deduplicate by `form_latin` + `output_type`, keep alternative paths.
- Persian digits. All seven screens.
- Rules live in both repos: one master here, mirrored to karbon by PR.

## Resolved 2026-08-11

- Frontend stack, karbon integration, rule-pack format, database → DECISIONS.md
- Latin → Persian: not needed. Compose both spellings during derivation.
- Verb inventory (1,752 vs 6,000+): not a blocker; assume the rules generalise.
- Review: Murfulu builds its own, with roles and expert feedback → REVIEW.md
- Deployment: local, private repo.

## Needs a conversation with the team

10. **Rule ownership long-term.** karbon's roadmap claims affix rules for
    itself. We are building them here. Raise with the karbon maintainer before the rule
    pack is large. See OWNERSHIP.md.

11. **Where does the linguist work?** He already reviews in karbon's workshop. Murfulu
    adds a second review surface. Make sure he is not asked to use two tools
    without knowing which is for what.

12. **Licence check.** karbon is marked CC0 but derives from Dehkhoda. NGI
    requires open outputs and verifies claims. Confirm before it goes in an
    application.

## Still open in the design

13. **Size of the derivation space.** Measure before building the precompute
    job: how many forms do steps 1–2 actually produce over 45,000 lexicon
    entries? This decides whether the batch job is hours or days.

14. **How much derivation detail** shows by default versus behind an expander.

15. **Behnevis joining rules** — ZWNJ placement, when a prefix is written
    joined, where the glide *y* surfaces as ی. Needed to render generated words
    in Persian script. Not yet extracted from the Behnevis specification.

## Research / later

6. **Scoring.** The proposal describes a four-part score (rule / corpus /
   semantic / composite). What is the corpus, and what produces the semantic
   part for a word no model has ever seen?

7. **Prefix mining from Old and Middle Persian.** the linguist's 5 May message asks for
   *bar-*, *farā-*, *foru-*, *farāz-* and friends to be extracted from Avestan
   and Middle Persian dictionaries to widen the verb inventory. Separate track.

8. **Verb inventory.** the expert wants 6,000–7,000 verbs, converted from existing
   software rather than typed by hand. karbon's lexicon has 1,752 مصدر. Where
   does the rest come from?

9. **Corpus.** The proposal promises a multi-source open Persian corpus. The
   research note in the archive already maps the options (Ganjoor, Naab,
   HPLT, FineWeb-2, MADLAD-400). Not started.
