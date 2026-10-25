# Expert review — draft design

**Status: draft.** 2026-08-11.

Murfulu needs its own review loop. karbon's workshop reviews **lexicon
entries** — is *raftan* transcribed correctly. Murfulu reviews **generated
words** — is *Raftorow* a good word, and is this rule firing where it should.
Different question, different data, so a separate mechanism.

## Scope: everything, not only generated words

Feedback attaches to anything in the app. The target decides the shape of the
record and who can act on it.

| Target | Example | Owner |
|---|---|---|
| generated word | *Raftorow* is not a word | murfulu |
| rule | rule 10 should not fire here | murfulu |
| composed meaning | this gloss is wrong | murfulu |
| statistic / chart | this count looks wrong | murfulu |
| lexicon entry | the Latin for this word is wrong | **karbon** |
| stem derivation | an exception is missing | **karbon** |
| the app | button does nothing; RTL broken | bug |

Two of these belong to karbon, whose lexicon we mount read-only. We cannot fix
them and must not drop them: record locally, mark `owner: karbon`, and export
for the karbon maintainer and the karbon workshop.

## Categories

| Category | Fields |
|---|---|
| `linguistic` | verdict (good / possible / wrong / unsure) + note |
| `data` | what is wrong, expected value, owner |
| `bug` | note, screen, browser, app version, console errors |

A linguistic verdict does not fit "this button is broken", so category is
chosen first and the form adapts.

## Who may leave feedback

**Anyone who is looking at the app**, as of 2026-08-17. There is one account
and no roles.

It used to be two: anyone could report a bug, and only an **expert** could
leave a linguistic verdict, because those become the evaluation set and have to
carry weight. That is still true of the verdicts — what changed is who is
trusted to give one. A reader needed the site password to see anything and an
expert API token to answer anything, and the project lead's call is that a
research app with one reviewer does not need two credentials. The password wall
in front of the whole site is the authentication now.

**What it costs is below, under *the evaluation set*.** It is not nothing.

## The mechanism

Click any element, choose a category, leave a note.

**Built in PLAN 7.9.** The button lives in the shell, so it is on every view
and no screen owns it. What is being judged comes from one of two places: a
screen declares its own subject, or a row hands over its own — a single built
word, a single rule. The route and the query are added automatically, because
a screen that forgot them would leave a record nobody can place afterwards.

**A linguistic verdict about the app itself is refused**, whoever is asking.
That was not written down until the widget was run: *is this app good,
possible or wrong* is not a question, and the table above already maps the app
to a bug report.

Two things get captured:

**Structured context, automatically.** What was on screen, as data:

```json
{
  "target_type": "derivation",
  "form_latin": "Raftorow",
  "form_fa": "رفت‌ورو",
  "stem": "raft",
  "rule_chain": ["V-046"],
  "glide_rules": [],
  "scores": {"rule": 0.8, "corpus": 0.0, "composite": 0.41},
  "attestation": "none",
  "corpus_version": "v3",
  "query": "raftan",
  "screen": "build"
}
```

**No screenshot. Settled 2026-08-17, and it is a decision rather than a gap.**
Earlier drafts of this document offered one, captured from the DOM, for the
sake of *what did he actually see*.

The structured context is the important half and is captured in full — it is
what makes the feedback reusable, and a screenshot is not machine-readable at
all. Against that, an image costs a volume, an upload route, a size limit, and
a rule about what happens to the images when the set is exported as a research
dataset.

**And the export is what decides it.** The feedback manifest deliberately
claims no licence: those records are judgements experts made about the
language, and they were not given to us to hand on. A screenshot compounds
that in a way structured context cannot — it captures whatever else was on the
reviewer's screen, which nobody consented to and which no field of ours
describes. Storing an unbounded, unlicensable, unreadable artefact to answer a
question the context already answers is not worth it.

`screenshot_ref` stays on the record as a nullable column. It is never
written, and it is documented as never written rather than left looking
unmeasured — see the model.

## The verdict

Free-text notes are hard to aggregate. Pair the note with one graded verdict:

| Verdict | Meaning |
|---|---|
| `good` | correct form, useful word |
| `possible` | correctly formed, but odd or unlikely |
| `wrong` | the rule should not have fired here |
| `unsure` | needs discussion |

Plus the free-text note in Persian.

## Why this matters beyond review

**This feedback store is the gold standard.** We cannot tune the four scoring
weights against nothing, and karbon's reviewed entries do not help — they
validate the transcription of *existing* words, not the plausibility of
*generated* ones. There are no generated words in that set at all.

So the review feature doubles as the evaluation set. Two hundred graded
derivations and the weights can be fitted honestly, plus we get a real quality
number to report. Building review early is therefore not a nice-to-have; it is
what makes the score mean anything.

## Consequences

- **Authentication: one account, one password, no roles.** Settled
  2026-08-17. Earlier drafts assumed an open app; PLAN 6.3 then built two
  roles and API tokens; this removes the second credential and keeps the
  first. `/feedback` still decides the author itself and refuses to read one
  from the request body — a record naming the wrong author is worse than no
  record.
- **The evaluation set loses inter-rater agreement, and that is the price.**
  This document's whole argument for storing feedback is that it becomes the
  set the scoring weights are fitted against, and the export carries a
  per-author pseudonym so two reviewers' verdicts on one word can be compared.
  With one identity there is only ever one rater. **Records made before
  2026-08-17 keep their own authors and stay comparable**; everything after
  carries one. The dataset manifest says so in the field's own description,
  because a reader outside this repository has no other way to find out. If a
  second reviewer is ever wanted, accounts come back as a migration rather
  than an excavation — which is why `users` was kept with one row rather than
  dropped.
- **Postgres table** `expert_feedback`: target, context JSON, verdict, note,
  author, timestamp, screenshot reference. Append-only.
- **Screenshots**: **not built and not going to be.** S4, settled
  2026-08-17. No volume exists, nothing captures one, and the widget offers
  none rather than offering one that goes nowhere. The structured context is
  captured in full, and the reason not to add images is above.
- **Export**: the feedback set must be exportable as a dataset. It is a
  research artefact and the NGI application promises open outputs.
  **Built** (PLAN 8.3): `tools/export_feedback.py` writes JSON Lines plus a
  manifest. The author is a stable pseudonym, never an account name — which
  was all inter-rater agreement needed while there was more than one author.
  The manifest claims **no licence** deliberately: these are judgements
  experts made about the language, Apache-2.0 is a licence for software, and
  they were not given to us to hand on. `--owner karbon` gives the share that goes upstream.
