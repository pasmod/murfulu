# Frontend — draft design

**Status: draft.** 2026-08-11. React SPA, separate container, API-only backend.

## Screens

### 1. Search

The flexible query box from [SEARCH.md](SEARCH.md), plus facet panels for
population, category, source, century, frequency band.

Results are a table. Each row: Persian spelling · Latin · category · population
badges · counts · corpus version. Click a row → word detail.

This is the screen that does not exist anywhere today, so it is the one to get
right.

### 2. Word detail

Everything known about one word.

- all readings of the spelling (*mard* / *mord*) — never collapsed into one
- stems, category, confidence, which lexicon entry it came from
- statistics: total, distinct documents, distinct authors, first and last date
- **dispersion chart** — occurrences by century and by author. This is what
  separates "a real word" from "one poet's rhyme"
- citations: the actual lines, with author and poem, clickable through — six,
  one per author, so a rhyme repeated in one poem does not fill the list
- **every text of the spelling** («همهٔ شواهد», 2026-11-14), under the six:
  every text the corpus holds it in, each with every line holding it, paged
  and filtered by author — see *Every text of a spelling* below
- word family: other words sharing the stem
- **what can be built from this** → link into the Build screen

### 3. Build

The core feature. Input a word, a stem, a noun or an adjective.

Output is a table, grouped by result type (kārnām, nām, barnām, agent
participle…). Each row:

| column | content |
|---|---|
| form | Latin, correctly capitalized |
| Persian | script form |
| rule | `v-010: stem1 + -ār → kārnām`, clickable to the rule |
| meaning | composed from the semantic tag |
| level | one of three, with one sentence of reason — see below (2026-11-13) |
| evidence | attested *n×* in corpus v3, or «در پیکرهٔ v3 نیامده است» — behind «شواهد» |
| sisters | other words the same rule made that do exist |
| score | its parts, never one number — corpus evidence, whether the
chain rests on written ground, how often the chain's rules produce real
words, and how typical the base is for its rule — behind «شواهد» |

**Built 2026-08-17, and not as drafted.** Steps 1, 2 and 3 are offered as a
choice rather than as a *go deeper* button, because the third step is not more
of the same: one verb builds 17,717 forms there against 660 at two steps, and
only fifty of them are words the corpus has. So a deep answer is **ranked at
the route and then paged** — the screen asks for the best thousand and says how
many of how many it is showing. It takes about a second, and is *not* instant
after that: the cache is still task 6.2.

Sorted by **level first, then by score** within a level, **never by depth**
(the project lead's choice of 2026-11-13). The API decides the level and ranks
on it, because a deep answer is paged there; the screen sorts one and two
steps the same way.

**The level (2026-11-13).** Each row shows the word, one of three levels —
آشنا (familiar: under this reading in at least ten poems), خوش‌ساخت
(well-formed: no rule on the chain in the lowest third), کم‌پشتوانه (weakly
backed: some rule there) — as a name with three bars and an ⓘ, and one
sentence of reason under the word: the poems and poets for a familiar word,
otherwise what the corpus says and the record of the chain's weakest rule. A
line above the list says what the three mean and that the corpus is classical
poetry. «شواهد» opens three fields — پیکره، دستور، معنا — of up to three dots
each, and a press on a field gives its figures with the corpus version. The
names and thresholds are **unconfirmed** until the linguist rules (L36). The
corpus version is said once above the list and beside every count behind the
button, not in each row's sentence (DECISIONS 2026-11-13).

**The verses (2026-11-14).** Under the «پیکره» field's figures stand the
lines they were counted from: when the field opens, three texts by three
authors — one voice each, as the six citations — each with author — work —
title and every line holding the word (three, then the rest on a press), the
word underlined, each line with «در متن ←». Above them, where there are more,
one button «نشان دادن همهٔ شواهد», with no number beside the figures' own,
opens the word page's own list in place — the author filter, ten texts to a
page, its count and its sentence — and, open, reads «بستن همهٔ شواهد». A note says the lines are the spelling's, not one reading's. A word
the corpus does not have, and the letters of a function word, list nothing
(DECISIONS 2026-11-14).

One row per word. Where more than one rule chain produced the same form, the
paths are nested under it — that is information, not noise.

Controls: filter by output type, hide/show unattested forms.

Each row expands to show the full derivation path when it took more than one
step (*gu* → *guyā* → *Guyāyi*).

Copy button per form — translators will paste these into their own text.

### 4. Explain

The reverse. Paste a word, get its structure: stem, affixes, which rules could
have produced it, confidence. This is the *sāzāyi* check — it says "this is two
present stems joined, not a suffix" instead of inventing a suffix.

### 5. Affixes by meaning

The ~35 semantic tags, each with its gloss, the affixes that carry it, and
example words. Answers "which suffix means *place*?" — the question that
started the project.

Entry point for the translator journey: arrive with a meaning, leave with an
affix.

### 6. Rules

Browse the ~200 rules. Per rule: the affix, input and output type, semantic
tag, the linguist's examples, his `strength` value, and the measured productivity from
the corpus.

Where `strength` and measured productivity disagree, flag it. That disagreement
is a finding, not an error.

the expert's screen. Editing comes later; reading comes first.

### 7. Corpus

Sources, versions, sizes, ingest dates, licences. Plus coverage: how many
corpus word types matched a lexicon entry, and the unmatched pile.

The unmatched list is a deliverable in itself — words in classical Persian that
Dehkhoda's entries do not cover.

## Feedback, everywhere

Any element can be commented on — a generated word, a rule, a chart, a lexicon
entry, or the app itself. Category is chosen first (linguistic / data / bug)
and the form adapts. Structured context is captured automatically; a screenshot
is optional. See [REVIEW.md](REVIEW.md).

This is a UI-wide affordance, not a screen. It has to be present on every view
from the start, because retrofitting it means touching every component.

## Novel words as input

If the user types a word that is not in the lexicon but *is* derivable, the
answer is "not a recorded word, but well-formed: derivable from خرد by rule 3"
— not an error. Search and Build both need this path.

## Design principles

Minimal, in the Apple sense: nothing on screen that is not doing work.

**Space over lines.** Separate things with whitespace, not borders and boxes.
The data is dense — Persian, Latin, counts, rules, scores — so the layout must
be calm or it becomes unreadable.

**One accent colour.** Everything else is greys and the text colour. Colour
means something: attested vs not, high score vs low. It is never decoration.

**Typography carries the hierarchy.** Size and weight, not rules and shading.
Persian and Latin need a matched pair of fonts — Farhang2 sets the interface
and pairs with a neutral Latin face. The Latin forms are data, so they get a
face that makes `š ž č ā` unambiguous, and it has to be a second face: Farhang2
does not have those four characters, or the other fourteen like them.

**Progressive disclosure.** Show the answer. Put the derivation path, the glide
rule, the score breakdown and the citations behind an expander. A translator
wants the word; the expert wants the machinery. Same screen, different depth.

**One clear action per screen.** Search has a search box. Build has an input
and a result list. No screen asks the user to make three decisions at once.

**No spinners where we can avoid them.** Steps 1–2 are precomputed, so results
appear immediately. The third step is built on request — about a second — and
nothing is cached yet, so it waits every time. See task 6.2.

## Mobile and responsive

Mobile is not an afterthought. Translators and writers work on phones.

- **Design mobile first**, then widen. The reverse always produces a cramped
  phone layout.
- **Tables become cards on narrow screens.** The Build result table has six
  columns; on a phone each row becomes a card with the word large and the rest
  stacked beneath.
- **Touch targets at least 44×44 px**, per Apple's guideline. The feedback
  button and the expanders are the ones that get this wrong.
- **Test at 375 px wide** as the standard small case.
- Breakpoints only where the layout actually breaks, not at fixed device sizes.

## The app must teach

Users will not know what *kārnām* or *kārbon-e do* means. The interface has to
explain itself without a manual.

- every technical term has a tooltip with a one-line Persian explanation and
  the traditional term (`Term`, and its Persian comes from the rule pack)
- **every label the interface invented for itself explains itself too** —
  a small ⓘ beside it (`Info`, and its Persian is the interface's own). The
  test is whether a reader can tell two things apart from their names: «املای
  جداگانه» beside «واژه‌گونه» failed it, and so did the eight menu items
- **a tooltip must open on a press**, not only on hover. A phone has no hover,
  and both tooltip components opened and shut inside one tap until 2026-08-17
- the menu says what each screen does, not only what it is called
- empty states explain what to do, with a working example ready to click
  (رفتن on the Build screen)
- the first result carries a short "what am I looking at" line
- error states say what to do next, never just what failed — **in Persian**.
  Where the fault is found by the engine, the API names it with a code and the
  screen writes the sentence; the engine's own English never reaches a reader
- a language the app expects the reader to type is documented *in the app*.
  The search box carries a builder that writes the syntax and a reference that
  lists all of it, because `docs/SEARCH.md` is not shipped and is in English

## Accessibility

WCAG 2.1 AA, promised in the funding application and cheaper to build in than
to retrofit. Real keyboard navigation, real focus states, contrast checked, and
screen-reader labels in Persian.

**Done (PLAN 7.10), and checked two ways.** The palette is computed against
every ground the app paints — three of them, not two — with WCAG's own
formula; the pages are audited with axe on every screen at both widths and on
the parts behind a click. Neither replaces the other: a page can pass an audit
by not happening to put two colours together, and a palette cannot tell you a
scrolling box has nothing to focus. Both found real failures on their first
run.

Two tokens came out of it. `--line-strong` is the **edge of a control** and is
held to 3:1; `--line` merely separates and is not. Confusing the two is how
every input in the app came to have a 1.26:1 border.

## Language

**The interface is in Farsi.** All labels, all rule explanations, all composed
meanings. The engine works in Latin internally; the user never sees English.

Consequence: every user-facing string comes from the rule pack
(`label_fa`, `explanation_fa`, `gloss_fa`), not from code. The engine cannot
invent Farsi text.

**Terminology:** the project's grammar terms are primary — کاربن یک، کاربن دو، کارنام، برنام،
کارنده‌کاربهر. Traditional terms (بن ماضی، بن مضارع، اسم مصدر، صفت، صفت فاعلی)
appear as a tooltip, because that is what most users were taught.

## Rules for the whole UI

**Always show both scripts.** Persian and Latin, side by side, everywhere. The
project's whole argument is that the Latin makes distinctions the script hides;
showing only one defeats it.

**Mixed direction is the hard part.** Persian is RTL, Latin is LTR, and they sit
in the same table row. Every cell needs an explicit `dir` and bidi isolation, or
punctuation and numbers jump to the wrong side. Budget real time for this; it
is the most common way Persian interfaces break.

**Never lowercase Latin.** Capitalization carries grammar in Behnevis.

**Never say "does not exist".** Say "not found in corpus v3" — on the build
screen «در پیکرهٔ v3 نیامده است», *does not occur in corpus v3*, since
2026-11-13 (S33). Every count carries its corpus version; the one exception is
the sentence under each built word, whose list states the version once above
it (DECISIONS 2026-11-13).

**A count is said in texts and authors, never in poems and poets** (since
2026-11-13): «در ۲٬۱۱۸ متن از ۱۶۰ نویسنده». The corpus holds prose — 82,499
paragraphs of it in Ganjoor alone — and will hold other books. Unconfirmed
until the linguist rules (FOR_THE_LINGUIST L37); the words live in the screens
that show a count, not in one shared file, because each sentence is its own.

**Show the score's parts.** Rule, corpus, semantics, composite — visible and
separate. A single opaque number is exactly what the project is arguing
against.

Nice-to-have that follows from this: **weight sliders** on the Build screen, so
the linguist can reweight the components and watch the ranking change. The NGI
application promises the scoring is tunable and explainable; sliders make that
literally true.

**Accessibility: WCAG 2.1 AA**, promised in the funding application. Cheaper to
build in than to retrofit.

## Settled when the shell was built (2026-08-12, PLAN 7.1)

- **Vite + React + TypeScript**, `tsc` in strict mode to match the Python
  side's `mypy --strict`. Vitest and Testing Library for the tests.
- **Fonts are self-hosted** — Farhang2 for Persian, from the Drive archive and
  committed under `src/styles/fonts/`; Inter for the Latin forms, from npm.
  Nothing is fetched from a font CDN: the app is behind a password, and a CDN
  would leak every visit and break offline. Farhang2 was Vazirmatn until
  2026-08-17; it is commercial software, bought and licensed (DECISIONS,
  2026-08-18).
- **Plain CSS with custom properties**, no framework. The tokens are the design
  system, and a test fails if a stylesheet names a token nobody defined or
  writes a colour that is not one.
- **Logical properties only** — `inset-inline-start`, `border-block-end`, never
  `left` or `right`. A test enforces it. A right-to-left layout built by
  mirroring a left-to-right one breaks the first time a component is nested.
- **No hamburger menu.** Six items fit in a scrolling row at 375 px, and hiding
  the navigation would make the app harder to learn.
- **The screens are one list** (`web/src/shell/screens.ts`) feeding the
  navigation, the router and the page title, so a screen cannot appear in the
  menu with nothing behind it.
- **Every Persian string about the grammar is passed in, never written in a
  component.** `Term` takes the term, the explanation and the traditional name
  as props. Where those come from is the open question below.
- **The app always calls `/api` on its own origin.** The dev server proxies it;
  nginx proxies it in the container. The address of the API is deployment, not
  code.
- **375 px is a test, not a look.** Playwright loads every screen at phone and
  desktop width and checks the things jsdom cannot see: nothing pushing the
  page sideways, touch targets at 44 px, the navigation reachable, the layout
  actually right-to-left. It caught two bugs on its first run.

## Settled when the interface was tidied (2026-11-12 and 2026-11-13)

- **A control is taken, not written.** `styles/controls.module.css` has the
  field, the primary and the secondary button and the chip, each in every
  state: at rest, under the pointer, pressed, chosen, switched off. A screen's
  stylesheet takes one with `composes` and adds only where it sits. It must not
  restate what the shared class sets; a control that has to look different is a
  new class there.
- **Chosen is the accent's wash and the accent's edge**, everywhere, and is
  said by `aria-pressed` as well as by the look.
- **Under the pointer is asked of a pointer** — `:hover` sits inside
  `@media (hover: hover)`, because a touch leaves it stuck.
- **A screen's frame and its three "no answer" states are shared** —
  `styles/page.module.css`: the line under the heading, *something went wrong*
  (a box with a caution edge, never one faint line), and *wait*
  (`text/Waiting.tsx`: one sentence, a status message, which the component
  holds back 300ms so that a short wait is silent for every reader).
- **A breakpoint is where the content stops fitting, measured.** The menu has
  nine items now; the masthead is one row from 80rem and the fade stays below
  64rem. A list that shares its row with a side column is laid out by a
  container query, not a media query.
- **Nine items still need no hamburger**: the row scrolls, fades, and keeps the
  current screen's link in view.
- **A section is a white card on a grey page** (2026-11-13, the project lead's
  choice). This replaces *space over lines* above for sections; inside a card
  that principle still holds — rows are parted by a hairline and by space, and
  a grey tile inside a card is the only box within a box. On a phone a card
  runs edge to edge.
- **The menu stays at the top of the window**; below 80rem only its row of
  links does. `scroll-padding` keeps whatever is scrolled to out from under it.
- **A list row puts its buttons at the end of its first line** and sets its
  parts side by side where the window has room. It does not hide content to get
  shorter.
- **The small print is 13px and 15px**, not 12px and 14px.

## Every search box suggests (2026-11-14)

Asked for by the project lead: *the search fields all should support auto
suggest*. Seven boxes do — the word search, build, compound, take apart, the
meanings, the word bank and the reading screen — and all of them through one
component, `suggest/Suggest.tsx`, so they behave alike:

- **The ARIA combobox with a list.** The box keeps the focus; ↓ and ↑ move
  through the suggestions and wrap at the ends; Enter takes the marked one;
  Escape closes the list (and, once shut, is the search box's own *clear*).
  **Enter with nothing marked submits what was typed**, exactly as before:
  a suggestion is never taken unasked — so typing on, or moving the caret
  with ← →, unmarks it, and an input method's Enter is left to the method.
- **Asked for after a 150ms pause**, and an older request is aborted when the
  letters move on, so an answer for «د» never lands under «دلب».
- **Only typing opens the list.** A value written in from the address, the
  query builder or an example button does not; nor does leaving the box and
  coming back.
- **Taking a suggestion does what the screen's search does with it**: the
  bank asks for that word alone (`exact`), in the whole bank; build, compound
  and take apart run at once; the word search finishes only the last term,
  and only while the caret is at the end, and runs; the reading screen lists
  a group's texts or opens a text.
- **What is suggested** comes from `/suggest/words` (the bank, in the script
  typed: a Persian spelling with its readings, or a Latin reading with its
  spellings; build and compound only offer words the rules build from) and
  `/suggest/texts` (authors, works and sections whose own name holds every
  word typed, then single texts). The meanings box filters the 42 meanings the
  screen already has, and replaced the browser's `datalist`.
- **On a phone** the list is as wide as the box, scrolls inside itself, and
  each suggestion is a 44px touch target; pressing one keeps the focus in the
  box, so the keyboard stays up. `tests/suggest.spec.ts` checks it at 375px.

## Open

Settled: **Persian digits (۱۲۳)** throughout. **All seven screens** are built,
not a subset.

❓ **Where does the grammar glossary come from?** Every technical term needs a
one-line Persian explanation and its traditional name. Those exist in
`murfulu/rules/types.py` as `WORD_CLASSES`, and no route exposes them. The
`Term` component takes them as props and invents nothing; something has to
supply them before the first screen shows a word class.

❓ How much of the derivation detail (glide rule, exception note, rule number)
is shown by default versus behind an expander?

## The questions screen (`/questions`, 2026-08-16)

**The one screen written for a single reader.** Everything else here serves
anyone looking at Persian word formation; this serves the linguist, and the
whole reason it exists is that his answers had nowhere to live but an English
Markdown file in a repository he does not open.

So it inverts the usual balance. **The Persian is the question**, first and
largest; the English is a gloss under it, smaller and set left-to-right. Where a
question has no Persian yet — all fifteen seeded out of the document — the
screen says so rather than showing him English as though it were the question.

**The evidence travels with the question.** A question about 21 words cannot be
answered without the 21 words, and sending him to the repository to find them is
the thing the screen replaces. It sits behind a disclosure so a list of fifteen
questions stays a list.

**Refusal comes before the writing, not after.** The list says whether this
account may rule, so a reader is told plainly instead of composing a ruling and
losing it to a 403.

## The reading screen (`/texts`, 2026-11-13)

**Any text of the corpus, word by word, in Persian script and in Behnevis.**
The linguist's wish (IDEAS 12), widened by the project lead to any text, not
only poetry, because the corpus will take prose and other books. Built as
**direction A** of three drafts, the one the project lead chose: each Persian
word stands over its Behnevis in a block, and the blocks run right to left and
wrap like text. A couplet's halves stand side by side from 48rem and one under
the other below it, the second set in from the line's start as a printed divan
sets it; prose flows as paragraphs. The cost, stated in the drafts: a text
takes about twice the height, and a ghazal reads less like a poem.

**Opening a text.** One box takes author, work, section or title together,
and every word typed must be in the text's heading (`documents.heading`,
corpus v17 on); equal matches keep the source's order, so «حافظ» lists the
divan as printed. Every citation on a word's page has «در متن ←», which opens
the text at that unit with the word underlined and the unit washed in the
accent, scrolled so that the word itself is in view — a paragraph of prose
can be taller than the window. Everything is in the address (`?q=`, `?text=&unit=&word=`, `?start=`
for a long text's next 200 units, `?view=marked`).

**The source line** is author · work · sections · title, then the corpus
version and the source's name. Author and work are links to their lists.

**Every reading, equally; none proposed** (the project lead's choice). A
spelling the bank reads several ways shows all its readings, one under
another, the same size, in alphabetical order, with a dotted rule under them;
the panel says the bank reads it *n* ways and that which one this line needs
is not said. The drafts' placeholder rule had put *dall* under دل.

**One reading per word, coloured by how sure it is** (since 2026-11-14,
direction A, when `MURFULU_BEHNEVIS_PATH` names a model): the word's `auto`
reading under it, a green line (sure), amber dots (mid) or a red dashed box
(unsure); the legend shows the three with their edges, which come from the
API. The panel opens with «در این سطر»: the reading, its estimate, the
readings to pick (native radio buttons drawn as buttons: one tab stop, arrow
keys move the pick; the picked one filled with a check mark) and a field to type one — each clears the other — then a line
saying what will be saved and what becomes of it, and «ثبت «…»». A saved
reading stands under its word with a check mark on an accent wash
(`data-level="mine"`), asked for again on every visit (DECISIONS 2026-11-14,
*a pick is plain to see*). `levels.ts` names the levels.

**A reading the word's own harakat rule out is paler** (since 2026-11-14, the
project lead's choice): under «تُرکِ», *Tarak* and *Tark* in `--ink-faint`,
*tork* as before. The API names them (`against` on the word); the legend
explains pale readings only on a page that has one, the button's label names
them, and the panel says «اعرابِ متن با آن نمی‌خواند» beside each. Never
hidden: an edition's signs are sometimes wrong. The rule: `search/harakat.py`.

**«؟» for a word the bank does not read, never "not a word".** The panel says
the bank has no reading for the spelling and links to the bank's search for
it. The inflection analyser's guesses are not shown: they are wrong too often
(جنت as جن + ت, بخارا as a vocative of بخار). About four words in ten of a
classical text are «؟» today (UPSTREAM B9).

**The panel**, opened by a press under the unit and the unit's full width: the
word as written and its counted spelling where they differ; every reading with
its other pronunciations, the linguist's group names and the dictionary's
definition (two lines); the spelling's corpus count with the version — the
letters' count, whichever word they are, said so for a function word; and the
way into the bank: «این واژه در بانک واژه ←» opens `/bank?q=…&exact=1`, the
word itself and not the three hundred words holding its letters.

**«این خوانش نادرست است»**, under each reading, marks that one reading wrong
for the linguist's review. It asks once more, with an optional note, because
the mark cannot be taken back: it is an append-only record in the feedback
store (`category: linguistic`, `verdict: wrong`, `target_type: lexicon_entry`,
the word type's id as target, the text and unit in `context`), owned by karbon
and exported to it. A marked reading says so in the panel — the panel asks the store
for every mark on its spelling, however old. **The marks are reviewed on the
screen itself** — the list under the opener, or `?view=marked`, fifty at a
time with the total: the word as written, the reading struck through, the
text, the note and a way back to the line.

**A note is the source's own words** — in a tazkira, the next poet's name —
shown in small type under «یادداشت سرچشمه», never split into words and never
numbered, because it was never counted.

**Unconfirmed**: the control's wording, «؟», the kind labels (بیت، مصراع، نثر،
یادداشت سرچشمه) and the sentences of the legend and the panel are ours until
the linguist rules (FOR_THE_LINGUIST L39).

## Every text of a spelling (the word page, 2026-11-14)

**All of the evidence, under the six voices.** The six citations stay one line
per author. Below them a card «همهٔ شواهد» says, with the corpus version, how
many texts and named authors hold the spelling — and how many lines, for a
list of at most 1,000 texts — that
the lines are evidence for the spelling and not for one of its readings, and
opens on a press («نشان دادن همهٔ شواهد») to every text, twenty to a page:
author — work — title — century (n lines), then every line holding the
spelling, the word underlined in the accent as the reading screen marks it,
each line with the citations' «در متن ←». A text with more than six such lines
shows six and the rest on a press. A select chooses one author, most texts
first, each with their count. Everything is in the address: `?all=1`,
`author=`, `unnamed=1` (texts with no author), `page=` from 1.

**Order**: authors by how many of the texts are theirs, ties by name; within
an author Ganjoor's own order (`documents.order`, the order the reading screen
lists them in). The same on every reload, and paged by number.

**Two counts, one sentence.** The list is the search index's and the word's
figures are the counting's; they differ by a few texts (FINDINGS 2026-11-14),
and where they do the list says so once: «این فهرست … متن دارد و شمارش بالا …،
چون جست‌وجوی متن‌ها چند حرف را که شمارش جدا می‌شمارد یکی می‌گیرد، مانند آ و ا
یا ۀ و ه، و چند واژه را جور دیگری از هم جدا می‌کند.» A text the index found
only through such a letter says «این متن واژه را تنها با املایی نزدیک دارد که
شمارش جدا می‌شمارد.» and marks the word as written there; its «در متن ←» names that spelling, so
the reading screen marks it too.

**A line count beside a Persian numeral is in brackets**, «(۱ سطر)», never
after a middle dot: «۱ · سطر» reads as ten lines, the dot being a Persian zero.

**Unconfirmed**: the sentences are ours, in the reading screen's tone.
