# Walkthrough: user enters رفتن

**Status: draft.** 2026-08-11. Traces one request through the whole system, to
pin down what each layer must hold.

## Step 1 — Input

User types `رفتن` (or `raftan`).

- detect script
- normalize: ZWNJ, Arabic ي/ك → Persian ی/ک, Persian digits
- if Latin: normalize loose input (`sh`→`š`, `aa`→`ā`), **never lowercase**

## Step 2 — Resolve against the lexicon

karbon lookup → entry: phonemic `raftan`, category `nābesudkārvāže`.

Three outcomes, all of which the UI must handle:

| Outcome | Action |
|---|---|
| one entry | proceed |
| several entries (homograph) | ask the user which reading |
| no entry | OOV resolver, flag low confidence, warn that the Latin is a guess |

## Step 3 — Derive the stems

karbon `derive_stems()`:

- strip `-an` → **kārbon-e yek = raft** (رفت)
- stem 1 ends in `-ft` → rule 9 (drop `-t`, `f`→`b`) would give *rab*
- but رفتن is on the **exception list** for rule 9 → **kārbon-e do = row** (رو)

**Show this.** "Rule 9 applies, but this verb is an exception." The user learns
why, and the linguist can check us against his own list.

## Step 4 — Match rules

Collect every rule whose input type is `karbon_yek`, `karbon_do`, or
`nabesudkarvaze`. For *raftan* that is roughly 40 candidate rules.

## Step 5 — Apply, with glide rules

This is where *raftan* gets interesting. Stem 2 is `row`, which ends in the
`ow` vowel, so the glide table fires constantly:

```
row + eš   → glide 16 (ow + e → av)  → Raveš     روش
row + ande → glide 15 (ow + a → av)  → ravande   رونده
row + ān                             → ravān     روان
row + ā                              → ravā      روا
```

Without the glide rules the engine would produce *Roweš*, which is wrong. So
the glide step is not a detail — for this verb it changes almost every output.

**Show which glide rule fired.** `row + eš → Raveš (glide 16: ow + e → av)`.
That single line explains a result that otherwise looks arbitrary.

From stem 1:

```
raft + ār  → Raftār    رفتار     rule 10 (stem1 ending in -t/-d)
raft + e   → rafte     رفته      rule 8, patient participle
raft + o + row → Raftorow       rule 46, stem1 + o + own stem2
```

Prefixed infinitives:

```
foru- + raftan → foruraftan   فرورفتن   rule 61
var-  + raftan → varraftan    ورفتن     rule 74
dar-  + raftan → darraftan    دررفتن    rule 56
```

## Step 6 — Recurse

Outputs feed back in. the source grammar cite these chains explicitly:

```
row → ravande → Ravandegi     (rule 22, then rule 23)
row → ravān   → Ravāni        (rule 29, then rule 30)
```

Depth-limited, cycle-detected. Each output keeps its full path.

## Step 7 — Check attestation

**Search happens in Latin, not in Persian script.** Corpus words get a Latin
form during the *link* pipeline step, by matching a lexicon entry. Once linked,
`word_types` carries both spelling and Latin, so a generated Latin form is
looked up directly against `word_types.latin`. No back-conversion is involved.

The limit: corpus word types that never matched a lexicon entry have no Latin
and are therefore invisible to Latin search. That share is the coverage number,
and it is one of the things the Corpus screen reports.

Three levels of certainty, distinguished in the data and in the UI:

| Level | Meaning |
|---|---|
| `reading` | matched a linked reading in `word_types` — confirmed |
| `spelling` | only the Persian spelling occurs, with no confirmed reading |
| `none` | not found in this corpus version |

*Raveš* will match at `reading` level. A novel form will usually be `none`, or
`spelling` if it collides with an unrelated homograph.

## Step 8 — Score

Per [RESEARCH_SCORING.md](RESEARCH_SCORING.md): rule strength as prior, measured
Baayen P as evidence, attestation statistics, semantic plausibility later.

## Step 9 — Present

---

# What else we can show

Everything below is derivable from data we already plan to hold. This is the
difference between a word list and a tool.

**About the input**
- both stems, in Persian and Latin
- which stem rule applied, and whether the verb is an exception
- how frequent the base verb is — derivations from a common verb are safer

**About each generated word**
- the rule, by number, clickable to the linguist's original row
- which glide rule fired, if any
- the composed meaning, from the semantic tag
- the full derivation path for multi-step forms
- attestation level and counts, qualified by corpus version
- citations — the actual lines
- dispersion: how many authors, which centuries

**By analogy — the strongest plausibility signal for a human**
- **sister forms**: other verbs where this same rule produced an attested word.
  For rule 10 (`stem1 + -ār`): *Goftār*, *Raftār*, *Didār*, *Kardār*. Seeing
  four attested siblings tells a translator more than a score does.
- **the word family**: everything else already derived from *raft* / *row*

**About the rule itself**
- how many words this rule produced across the corpus
- its measured productivity, and whether that agrees with the authored `strength`

**Related existing words** — shown as information, never as a penalty.

---

# Consequences

## Persian spelling: composed, not converted

The UI is in Farsi, so every generated form needs a Persian spelling. There is
no Latin → Persian converter anywhere, and we do not need one.

We generate by composing stem + affix, so we compose **both** spellings at the
same time: the stem's Persian spelling comes from the lexicon, the affix's from
the rule pack. Latin and Persian are built in parallel and travel together
through the whole derivation.

```yaml
affix:    "-ār"
affix_fa: "ار"
```

Still to encode: the joining rules from the Behnevis specification — when a
prefix is written joined, where a ZWNJ goes, and where the glide *y* surfaces
as ی.

## For the rule pack

Sister forms and rule productivity both need the same thing: knowing which
attested words each rule produced. We cannot get that from corpus text alone,
because corpus words are not decomposed.

**So: a batch job that applies every rule to every applicable lexicon entry,
then checks attestation.** This is exactly Monakhov's simulate-and-check method
from the research note, and it yields three things at once:

1. Baayen P per rule, measured
2. sister forms, precomputed
3. instant lookup for common queries, instead of generating on demand

Rough size: ~1,750 infinitives × ~40 verb rules ≈ 70k derivations. The nominal
rules over 45k lexicon entries are far larger and will need depth limits. Worth
measuring before committing.

## For Elasticsearch

- `word_types` must support lookup **by reading** and **by spelling**
  separately — attestation confidence depends on which one matched.
- a `derivations` index for the precomputed space: form, stem, rule chain,
  attestation level, scores, corpus version. This is what makes `in:generated`
  searchable.
- `stem_1` / `stem_2` on word types gives the word family for free.

## For the rule YAML

The UI is in Farsi, so the rules must carry Farsi text — the engine cannot
invent it:

```yaml
- id: V-010
  affix: "-ār"
  label_fa: "کاربن یک + ār-"
  explanation_fa: "از کاربن یک با پسوند ār- کارنام ساخته می‌شود"
  output: {type: karnam}
```

Same for glide rules and semantic tags. Every user-facing string comes from the
rule pack, not from code.

## For the frontend

- whole app RTL and in Farsi, with Latin forms as LTR islands
- the project's grammar terms is primary (کاربن یک، کارنام، برنام); traditional terms
  (بن ماضی، اسم مصدر، صفت) as a tooltip, since most users know only those
- ❓ Persian digits (۱۲۳) or Latin digits for counts?
- exceptions, glide rules and derivation paths need somewhere to live in the
  layout — an expandable row, not a separate page
