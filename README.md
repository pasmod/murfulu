# Murfulu

[![check](https://github.com/pasmod/murfulu/actions/workflows/check.yml/badge.svg)](https://github.com/pasmod/murfulu/actions/workflows/check.yml)

Murfulu is an engine for word formation that is not tied to one language. A
language's rules go in as data: its stems and affixes, how they join, and what
kind of word each step makes. The engine applies them, builds the words the
rules allow, and shows for each word the steps that built it. Give it the
rules of another language, and the same engine builds that language's words.

Someone who knows the German verb *lesen*, "to read", understands *lesbar*
and *Lesbarkeit* the first time they see them. Nobody had to teach them those
two words. They know the stem *les-*, they know what the suffixes *-bar* and
*-keit* do, and they put the pieces together. Most languages build words this
way, and their speakers carry the same kind of knowledge.

Murfulu writes that knowledge down as rules. Each rule says what a suffix or
prefix attaches to, how the pieces join, and what kind of word comes out. The
rules are data, not code: the rules change from language to language, the
engine stays.

## One pattern, three languages

| | German | English | Persian | Persian in Latin letters |
|---|---|---|---|---|
| the verb | lesen | to read | خواندَن | *xāndan* |
| it can be read | lesbar | readable | خوانا | *xānā* |
| how well it can be read | Lesbarkeit | readability | خوانایی | *xānāyi* |

Each language uses its own pieces: German *-bar* and *-keit*, English *-able*
and *-ity*, Persian *-ā* and *-i*. The build is the same. A stem, one suffix
that makes an adjective, and a second suffix that turns the adjective into a
noun. That shared build is what Murfulu describes: one way to write the rules
down, and one engine that applies them, whatever the language.

The pieces do not always just line up. English writes *readabil-* before
*-ity*. Persian puts a *y* between two vowels, so *xānā* and *-i* become
*xānāyi*. And Persian builds on the verb's stem, not on the whole verb:
*xāndan*, "to read", has the stem خوان *xān*, and *-ā* goes on that. These
details are part of the rules too.

A dictionary lists the words someone has already written down. Rules also
cover the words nobody has listed. The Persian *-ā* and *-i* that make
*xānā* and *xānāyi* also make دانا *dānā* and دانایی *dānāyi*, "knowing" and
"wisdom", and تَوانا *tavānā* and تَوانایی *tavānāyi*, "able" and "ability".
Given a Persian stem, Murfulu builds the words its rules allow, each with the
steps that built it. Some of those words are in every dictionary. Some
are words Persian could have formed and never used. Many are forms nobody
would say. The rules say what is possible, a corpus of real texts shows what
has been used, and a person judges the rest.

## What works today, and what does not

**Persian is the first language, and it works today.** Its rule pack,
version 0.2.0, holds 250 rules transcribed from the linguist's grammar of
Persian word formation. They run on a word bank of 58,983 Persian words from
karbon, a companion library, and every word the engine builds is looked up in
a corpus of classical Persian poetry. A web prototype in Persian lets the
linguist review the rules and what they build.

**German is planned as the second language.** Its rule pack does not exist
yet; it is how we will show that the engine carries over. **English appears
here only to illustrate**: there is no English rule pack.

**What does not work yet.** Persian came first, and parts of the code still
assume it. The rule format names Persian word classes, and the engine writes
every word in Persian script beside its Latin form, with joins only Persian
needs. Moving those into the rule pack, so that the engine assumes nothing
about a language, is the next step, together with an open description of the
rule format and a checker that tests a rule pack. The engine also builds many
forms that nobody would say. The corpus holds poetry only, so a modern word can be well
formed and still be missing from it. And some of the linguist's rulings are
still open; where we had to choose without one, the choice is marked as
unconfirmed.

## Why it is fundamental

Every tool that reads, writes, speaks or searches a language meets words it
has never seen: rare words, new words, words built on the spot. No dictionary
lists them all. Rules that say how words are built can take such a word apart
and put new ones together, and that one piece of knowledge serves many tools
at once. Murfulu keeps it in one place, as data, so that each tool does not
have to learn it again for each language.

Most of what follows is not built yet. The examples are Persian, the first
language; where the Persian prototype has a first version, the text says so.

**Reading aloud.** Persian writes its long vowels as letters and leaves the
short ones out. So کشنده can be کُشَنده *košande*, "deadly", or کِشَنده
*kešande*, "pulling". A speech synthesizer has to pick one, and a wrong pick
changes the meaning. Murfulu knows where both come from: the suffix *-ande*,
"the one that does it", on the stem *koš* of کُشتَن *koštan*, "to kill", or on
the stem *keš* of کِشیدَن *kešidan*, "to pull". So it can propose the readings
the grammar allows. It does not choose between them; the sentence around the
word does, or a model that reads the sentence. This matters most for rare and
new words: a dictionary does not list them, and a model has seen them seldom
or never. Murfulu is not a better vowel-adder than a large language model: in
a first test of our own, a language model read more words right than the
prototype's own reader did. What Murfulu adds is the list of readings the
grammar allows. The prototype has a reading screen that shows a Persian text
with a Latin reading under every word.

**Spelling.** A spell checker that knows the rules can accept a well-formed
word it has never seen, instead of marking every new word as an error. In
Persian it can also place the half-space, the zero-width non-joiner that
keeps two parts of a word apart without a full space, as in هَم‌خوانی
*hamxāni*, "agreement". Whether one belongs depends on where one part ends
and the next begins, and that is what the rules know.

**Search by word family.** A search for *xāndan* could also find خوانَنده
*xānande*, "reader" or "singer", خوانِش *xāneš*, "reading", and *xānāyi*,
because each carries the stem *xān*. A search that only cuts off letters would
also find خوان *xān*, "a laid table", a different word with the same letters.

**New terms.** When a field needs a word its language does not have yet, the
rules can propose candidates built from the language's own pieces, each with
its meaning spelled out from those pieces. The prototype has a first version.
Asked for a Persian word for the German *Windtelefon*, a phone booth where
people speak to the dead through the wind, it built بادگو *bādgu*,
"wind-speaker", with the rule that makes سُخَنگو *soxangu*, "spokesperson".
It is a candidate for the linguist, not a decision. The most obvious
candidate, بادگاه *bādgāh*, "wind-place", turned out to be an old word for a
toilet. The rules cannot know that; the dictionary does, and someone has to
read it. Carrying a term from one language into another works the same way:
split it into its pieces, give each piece a meaning, and look for words with
the same build on the other side.

**Other scripts.** Persian is written in Arabic script in Iran and
Afghanistan, in Cyrillic in Tajikistan, and often in Latin letters. Moving
between them needs the vowels that Arabic script leaves out and the borders
between the parts of a word. karbon already turns Persian script into
Behnevis, the linguist's Latin script. Tajik Cyrillic is not built.

**Learning.** A learner can see a new word as pieces they already know rather
than one more word to memorise. Children learning Persian abroad could put
pieces together and see whether Persian would accept the result.

## Try it

**The engine, in a few minutes.** The rule pack is in the repository, so the
engine runs without the lexicon, the corpus or Docker. After the three install
lines under *Running it*:

```python
from murfulu.engine import Word, apply_all, deduplicate
from murfulu.rules.pack import load

pack = load()  # the Persian rule pack in rules/
stems = [
    Word(latin="angiz", fa="انگیز", word_class="karbon_do"),    # present stem
    Word(latin="angixt", fa="انگیخت", word_class="karbon_yek"),  # past stem
]
words = deduplicate([form for stem in stems for form in apply_all(pack, stem)])
print(len(words))  # 36
for word in words[:5]:
    print(word.shortest_path[-1].rule_id, word.latin, word.fa)
```

The two stems of انگیختن *angixtan*, "to stir, to rouse", give 36 words in
one step. Four of them:

| Built from | Rule | Word |
|---|---|---|
| present stem *angiz* | V-022, suffix *-ande* | *angizande* انگیزنده |
| present stem *angiz* | V-033, suffix *-eš* | *Angizeš* انگیزش |
| present stem *angiz* | V-034, suffix *-e* | *Angize* انگیزه |
| past stem *angixt* | V-008, suffix *-e* | *angixte* انگیخته |

Each result keeps its derivation path: the rule, the base it was applied to,
and the join between them. The lexicon and the corpus add the rest, meaning
and attestation. The capitals are Behnevis: like German, it writes nouns with
a capital letter.

**The running prototype** is in Persian and behind a password. The password is
there because of the corpus, not the code: the site shows Ganjoor's poetry
verse by verse, and that corpus may not be passed on (see *Licence*).
Reviewers get access on request from the project lead. Without it,
[WALKTHROUGH_RAFTAN.md](docs/WALKTHROUGH_RAFTAN.md) follows one verb through
the whole system step by step, from input to presentation.

## How it works inside

- **Three inputs per language:** a rule pack ([`rules/`](rules)), a lexicon,
  and a corpus. The core reads nothing else.
- **The rule pack** is YAML, built by a script from a transcription of the
  linguist's grammar: 241 rules that build words and 9 that find a verb's
  stems, 223 of them in use, plus 17 rules for how two pieces join. The
  schema is in [RULE_PACK.md](docs/RULE_PACK.md).
- **Persian is handled in Latin script.** Arabic script leaves out the short
  vowels, which word formation depends on, so Murfulu works on the Behnevis
  transliteration and never on raw Arabic script.
- **karbon** is the companion project that supplies the Latin forms, the stems
  and the lexicon: Persian script to Latin phonemic form, the linguist's word
  bank of 58,983 words built from Dehkhoda's dictionary (karbon 1.3.2), and
  stem extraction. Murfulu reads its lexicon read-only and never edits it;
  faults found here go to karbon as issues ([docs/UPSTREAM.md](docs/UPSTREAM.md)).
- **The corpus** is classical Persian poetry from Ganjoor, indexed in
  Elasticsearch. It is not part of this repository (see *Licence*).
- **Stack:** Python 3.11, FastAPI, PostgreSQL, Elasticsearch, a React web app,
  Docker.

## Running it

The library and its tests need Python 3.11 or newer, and neither the lexicon
nor the corpus:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e ".[dev,api]"
make check
```

`make check` runs the linter, strict type checks and the test suite;
`make web-check` checks the web app, and `make check-all` runs both.

The whole system runs on a machine with Docker. Copy `.env.example` to `.env`,
put the karbon lexicon snapshot into `data/` ([data/README.md](data/README.md)),
then:

```bash
docker compose up
```

The schema is built by migration, never by hand:

```bash
docker compose run --rm api alembic upgrade head
```

Building the corpus index is described in
[docs/ENGINEERING.md](docs/ENGINEERING.md) ("Building a corpus version").
Running on a server, behind HTTPS and a password, is in
[docs/DEPLOY.md](docs/DEPLOY.md), which also says why the password is
required: the corpus terms are unsettled.

## Team

Murfulu is built by a team of three. The repository and its docs name people
by role:

| Role | Responsible for |
|---|---|
| **Project lead** | concept and scientific direction, development, this repository |
| **Engineer** | architecture and development; also maintains karbon, the companion library for Persian transliteration, the lexicon and stem extraction |
| **Linguist** | the word-formation rules, the grammar terminology and the Behnevis script; every linguistic ruling is theirs, and the code follows it |

## How we work

- **We use AI coding assistants** to draft code, tests and documentation, and
  we say so here. A team member decides what each change does, reads the
  diff, runs the tests and is responsible for what is committed.
- **Linguistic decisions are never left to a tool.** The rule pack is
  transcribed from the linguist's grammar and built from that transcription by
  a script; a ruling goes into `rules/decisions.yaml`, and a test fails if the
  committed pack differs from what the builder produces. Where a ruling is
  missing, the question goes to
  [docs/FOR_THE_LINGUIST.md](docs/FOR_THE_LINGUIST.md) and the provisional
  choice is marked as unconfirmed.
- **Every push is checked** in CI ([`.github/workflows/check.yml`](.github/workflows/check.yml)):
  ruff, strict mypy, more than 4,000 tests, the web app's lint, types, tests
  and browser layout tests, and the tests again inside the container image.
- **Nothing private reaches the repository.** A pre-commit hook
  ([`tools/public_check.py`](tools/public_check.py), installed with
  `make hooks`) refuses a commit that would publish a credential, a server's
  details or a person's name.
- **Every working session ends with the docs updated**: what was learned in
  [FINDINGS.md](docs/FINDINGS.md), what was settled in
  [DECISIONS.md](docs/DECISIONS.md), what is still open in
  [OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md).

Development started in August 2026 in a private repository. This public
repository begins with a cleaned snapshot of 25 October 2026, because the
earlier history contained details of the server the demo ran on.

## Licence

**Apache-2.0**, see [LICENSE](LICENSE). Take the code, change it, build on it,
sell it; keep the notice, and you have a patent grant.

**It covers what this project wrote** and nothing else. [NOTICE](NOTICE) sets
out the three things it does not reach and why:

| | |
|---|---|
| the corpus | Ganjoor's poetry. Their own FAQ, asked whether the data are copyright-free, answers *not necessarily*: no legal review has been made, and free access is not a licence. Do not assume it is redistributable. |
| the lexicon | karbon's, mounted read-only. Its terms are karbon's question. |
| the expert feedback set | judgements experts made about the language. Not code, and not ours to hand on. |

## Documentation

To get a picture of the system:

| Doc | What it covers |
|---|---|
| [WALKTHROUGH_RAFTAN.md](docs/WALKTHROUGH_RAFTAN.md) | One verb traced end to end through the whole system |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Containers, storage, indices, pipelines, API |
| [RULE_PACK.md](docs/RULE_PACK.md) | The rules as data: the schema |
| [ENGINEERING.md](docs/ENGINEERING.md) | Standards: Docker, modules, file size, tests, docs |

The working record:

| Doc | What it covers |
|---|---|
| [FINDINGS.md](docs/FINDINGS.md) | Everything established so far, newest session first |
| [DECISIONS.md](docs/DECISIONS.md) | Settled choices, with reasons |
| [OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) | What is still undecided |
| [FOR_THE_LINGUIST.md](docs/FOR_THE_LINGUIST.md) | Questions only the linguist can settle |
| [UPSTREAM.md](docs/UPSTREAM.md) | What belongs in karbon rather than here, with measurements |
| [PLAN.md](docs/PLAN.md) | The prototype's build tasks, each with a test for "done" |

Further detail: [SEARCH.md](docs/SEARCH.md) (query language and index design),
[FRONTEND.md](docs/FRONTEND.md) (screens and UI rules),
[REVIEW.md](docs/REVIEW.md) (expert feedback, also the evaluation set),
[USER_JOURNEYS.md](docs/USER_JOURNEYS.md) (six journeys and the gaps they
found), [RESEARCH_SCORING.md](docs/RESEARCH_SCORING.md) and
[RULE_DISCOVERY.md](docs/RULE_DISCOVERY.md) (literature basis for judging
words and finding new rules), [OWNERSHIP.md](docs/OWNERSHIP.md) (which rules
belong to karbon, which to us), [LEXICON_ANALYSIS.md](docs/LEXICON_ANALYSIS.md)
(what is in the lexicon, measured), [SOURCES.md](docs/SOURCES.md) (index of
the project archive).

## Layout

```
src/          the Python package
rules/        the Persian rule pack, as data
tools/        build, measurement and check scripts
tests/        test suite
migrations/   Alembic migrations; the schema is never edited by hand
web/          the React app, with its own toolchain (`make web-check`)
data/         lexicon snapshot and build outputs (large files gitignored)
docs/         design and findings, updated at the end of every session
```
