# Search — draft design

**Status: draft.** 2026-08-11.

Requirement: search by anything. Prefix, suffix, infix, stem 1, stem 2,
category, rule, source, frequency — and combinations.

## Three populations, one search

A hit can come from three places, and the result must say which:

| Population | What it is |
|---|---|
| `corpus` | word types actually found in ingested text |
| `lexicon` | karbon's Dehkhoda entries |
| `generated` | forms Murfulu built from rules |

"All words ending in *-nā*" means different things across the three, and the
user wants all three. So population is a facet, not a mode. A word can be in
more than one.

## Query language

A text box plus facets. The text box takes a small syntax that maps 1:1 onto
Elasticsearch, so it stays predictable.

```
*nā                ends with nā
bar*               starts with bar
*raft*             contains raft
gereft             exact
/g[ou]ft/          regex

stem1:goft         words whose kārbon-e yek is goft
stem2:gu           words whose kārbon-e do is gu
type:karnam        category
rule:V-010         formed by this rule
affix:-eš          contains this affix

tag:ja             semantic tag — "which affixes mean 'place'?"
in:corpus          population
count:>10          frequency band
count:1            hapax only
author:فردوسی
century:10-13
source:ganjoor
```

Bare terms are matched against Latin. Persian script input is detected and
matched against the spelling field instead.

Everything combines: `*nā type:nam in:corpus count:>2 century:10-14`.

## Affix search vs string search

`*nā` is a string match. It returns *Tonoknā* and *Derāznā*, but also *Banā*
and *Sanā*, where those letters are not a suffix at all. This is the flagship
query, so the false positives matter.

Results are therefore split into two groups:

1. **confirmed derivations with this affix** — present in `derivations` with
   the matching affix
2. **merely ends in these letters** — string match only

The user sees both, clearly separated, and can collapse the second.

## Search by meaning

A first-class dimension, not a later addition. The linguist's complaint that started
the project was that a writer who wants to use *-gān* must open a grammar book
to learn what it means.

- `tag:ja` filters to derivations whose rule carries that semantic tag
- a **browse affixes by meaning** view lists the ~35 tags with their glosses,
  the affixes under each, and example words

This makes the affix inventory navigable by what things mean, not only by how
they are spelled.

## Aggregate statistics over a result set

Per-word dispersion is not enough. A researcher asking "is *-nā* alive or
medieval?" needs the whole result set charted by century and by author.

So every search returns aggregations alongside the hits: counts by century, by
author, by source, by category. ES gives this for free from the same query.

## Export

Any result set is exportable as CSV or JSONL, with the query and corpus version
recorded in the file. The NGI application promises open outputs, and this is
the cheapest way to honour it.

## Index fields that make this work

On `word_types`:

| Field | Type | Serves |
|---|---|---|
| `latin` | keyword | exact, prefix |
| `latin_reversed` | keyword | suffix, as a prefix query — fast |
| `latin_wild` | wildcard | infix and mixed patterns |
| `spelling_fa` | keyword | Persian-script search |
| `stem_1`, `stem_2` | keyword | stem search |
| `category` | keyword | type filter |
| `rule_ids` | keyword[] | generated words only |
| `affixes` | keyword[] | affix search, once decomposition exists |
| `semantic_tags` | keyword[] | search by meaning |
| `population` | keyword[] | corpus / lexicon / generated |
| `total_count`, `doc_count`, `author_count` | integer | frequency bands |
| `first_century`, `last_century` | integer | time filters |
| `authors`, `sources` | keyword[] | provenance filters |

Suffix search is the one query that is slow if done naively. The reversed
keyword field turns it into a prefix query, which is why it is stored twice.

## Input tolerance

Latin input uses `ā š ž č ˈ`, which nobody types comfortably. Accept loose
input and normalize:

- `sh` → `š`, `zh` → `ž`, `ch` → `č`, `aa` → `ā`
- plain ASCII matches its diacritic form unless the user is explicit

**Case is never normalized.** In Behnevis a capital first letter marks a noun,
so `Gofte` and `gofte` are different words. Lowercasing anywhere is a bug.

## Results

Each row shows: Persian spelling, Latin, category, population badges, counts,
and corpus version. Counts are always qualified — `412 × in corpus v3`, never a
bare number.

Sorting: relevance, frequency, dispersion, or alphabetical by Latin.

## Later

Once decomposition of *corpus* words is reliable, group 2 above shrinks and
affix search becomes exact for attested words too. Today the `derivations`
index gives us exactness for everything we generated, which is already most of
what the flagship query needs.
