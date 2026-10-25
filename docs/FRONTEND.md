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
- citations: the actual lines, with author and poem, clickable through
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
| evidence | attested *n×* in corpus v3, or "not found in corpus v3" |
| sisters | other words the same rule made that do exist |
| score | its parts, never one number — corpus evidence, whether the
chain rests on written ground, how often the chain's rules produce real
words, and how typical the base is for its rule |

**Built 2026-08-17, and not as drafted.** Steps 1, 2 and 3 are offered as a
choice rather than as a *go deeper* button, because the third step is not more
of the same: one verb builds 17,717 forms there against 660 at two steps, and
only fifty of them are words the corpus has. So a deep answer is **ranked at
the route and then paged** — the screen asks for the best thousand and says how
many of how many it is showing. It takes about a second, and is *not* instant
after that: the cache is still task 6.2.

Sorted by score, **never by depth**.

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

**Never say "does not exist".** Say "not found in corpus v3". Every count
carries its corpus version.

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
