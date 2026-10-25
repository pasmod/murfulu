# Discovering new rules from data — research basis

**Status: research note.** 2026-08-11.

The concept document already names this as the **third class of rules**:
*قوانین کشف‌نشده از دل داده* — patterns implicit in speakers' minds that no
grammar book records. Class one is documented rules, class two is proposed
rules needing corpus evidence, class three is discovery. This note covers
class three.

## What is established

### Morphological rules as vector offsets

**Soricut & Och (2015), *Unsupervised Morphology Induction Using Word
Embeddings*.** Language-agnostic, no external morphological tools, no
hand-tuned features. The method:

1. train word embeddings on the corpus
2. generate candidate (base, derived) pairs, grouped by the orthographic
   transformation that relates them — each group is a candidate **rule**
3. validate each candidate with two models: an orthographic one (does the
   string change apply consistently) and a semantic one (is the vector offset
   consistent across the group)

Evaluated on six languages. This maps almost exactly onto what we want: we
already plan to hold word types with Latin forms, and the "orthographic
transformation" is our affix.

The key idea for us: **a real rule shows a consistent semantic offset**. If
*goft → Goftār* and *raft → Raftār* and *did → Didār* all shift meaning in the
same direction in vector space, that is evidence the transformation is a rule
and not a coincidence.

### Paradigm discovery

**Erdmann et al. (2020), *The Paradigm Discovery Problem* (ACL).** Formalises
learning a morphological system from unannotated text, defines evaluation
metrics, and gives a benchmark that clusters forms by paradigm using embeddings
plus string similarity. There is a SIGMORPHON 2020 shared task on unsupervised
morphological paradigm completion built on it.

Caveat: this line of work is **inflectional**, not derivational. Persian
derivation is a different shape — one stem produces a family of different words
rather than filling a fixed grid of cells. Useful for method and for evaluation
design, not directly transferable.

### Root-and-pattern

*Fixing the Infix: Unsupervised Discovery of Root-and-Pattern Morphology*
(arXiv 1702.02211) — relevant if we ever handle the Arabic-origin vocabulary in
Persian, which follows root-and-pattern rather than stem-and-affix.

## How this fits Murfulu

We have an advantage the cited work does not: **a rule pack and a lexicon**. So
discovery is not from scratch. Two concrete uses:

**1. Find affixes we have no rule for.** Take the unlinked pile — corpus word
types that matched no lexicon entry — and look for recurring final or initial
strings that also show a consistent semantic offset against a known stem. Those
are candidate rules for expert review.

**2. Validate and extend existing rules.** For a rule we already have, check
whether the semantic offset is consistent across its attested outputs. Where it
splits into two clusters, the rule probably has two senses — which is exactly
what the bracketed semantic tags encode by hand (*-sār* appears four times
in the source grammar with four different meanings).

Both are batch jobs over the same data the derivation pipeline already builds.

## Generating new combinations

Separate from discovering rules: proposing rule *combinations* that no one has
written down — chains like stem2 + `-ande` + `-gi`. This needs no research. The
recursion already produces them; what it needs is the scoring to say which
chains are plausible, and an expert to rule on the ones that look interesting.

## Honest position

Discovery is a research track, not a v1 feature. It depends on:

- a corpus large enough for stable embeddings (Ganjoor alone is probably not)
- ~~Persian embeddings trained on our own Latin forms, since public models are
  trained on Arabic script~~ — **measured 2026-08-12 and softened.** Keying a
  script-based model on the Persian spelling, which the engine composes
  anyway, loses only the words one spelling reads two ways: **1,037 of 16,714
  linked spellings, 6.2%**. Our own vector space is a fallback, not a
  prerequisite. See [RESEARCH_SCORING.md](RESEARCH_SCORING.md)
- the FRACSS work from [RESEARCH_SCORING.md](RESEARCH_SCORING.md), which uses
  the same machinery

Sensible order: get generation and scoring working, then reuse the embeddings
built for scoring to do discovery. Not a separate infrastructure.

## Sources

- Soricut & Och 2015, *Unsupervised Morphology Induction Using Word Embeddings*
  — https://research.google/pubs/pub46763/
- Erdmann et al. 2020, *The Paradigm Discovery Problem* —
  https://aclanthology.org/2020.acl-main.695/
- SIGMORPHON 2020 shared task on unsupervised morphological paradigm completion
  — https://arxiv.org/pdf/2005.13756
- *Derivational Morphological Relations in Word Embeddings* —
  https://aclanthology.org/W19-4818.pdf
- *Fixing the Infix: Unsupervised Discovery of Root-and-Pattern Morphology* —
  https://arxiv.org/pdf/1702.02211
