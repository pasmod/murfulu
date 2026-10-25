# Research basis: scoring a generated word

How do we judge whether a rule-generated word is good? Literature reviewed
2026-08-11. Established methods first, our gaps last.

## The problem

A rule produces a form. Three cases:

1. **Attested** in the corpus → we have evidence.
2. **Not attested, but plausible** → the corpus is too small, or the word is
   simply unused but formable.
3. **Not attested and implausible** → the rule fired where it should not have.

We need a defensible way to separate 2 from 3, and to quantify 1.

## Rule productivity

**Baayen's P** = V₁ / N — hapax legomena formed by an affix, divided by total
tokens with that affix. A high hapax share means the rule is still coining new
words. Baayen & Renouf split this into:

- *potential productivity*: hapaxes with the affix / tokens with the affix
- *expanding productivity*: hapaxes with the affix / all hapaxes in the corpus

**Known weaknesses** (Pierrehumbert & Granell, SIGMORPHON 2018): P depends
heavily on corpus size, is unstable under small corpus changes, and hapax
counts alone underdetermine productivity. They recommend modelling the
vocabulary growth curve rather than reporting a single ratio.

**Closest to our design** (Monakhov 2023): define productivity as the
probability that an affix combines with a random base, and measure it by
*simulating* the construction of forms and checking attestation. This is
literally our pipeline — generate, then look up. It also weights neologisms and
established words equally, so token frequency does not dominate.

**Consequence for us:** every productivity number is tied to a corpus version.
Report "P = 0.31, corpus v3" — never a bare number.

## Semantic plausibility

**FRACSS** (Marelli & Baroni, *Psychological Review*). Each affix is a matrix
**A**. The derived meaning is **c = A·s**, where **s** is the stem vector. **A**
is trained on all attested stem → derived pairs for that affix. The model
predicts human judgements of how meaningful a novel affixed word is.

This dissolves the out-of-vocabulary problem stated in the NGI application: we
do not need a vector for a word nobody has written, we compute one.

Follow-up work comparing FRACSS with LLM judgements of novel derived words
finds the LLMs lean on affix frequency and productivity rather than genuine
semantic composition. Do not assume an LLM can replace this step.

### How a similarity number becomes a plausibility judgement

This is the mechanism, and it is worth stating precisely because the obvious
guess about it is **wrong**. Marelli & Baroni measured it on **600 nonce
forms** across 6 affixes, each rated by **10 people** on how easy it was to
assign a meaning. Three measures were computed on the *predicted* vector of
the novel word:

| measure | how | result |
|---|---|---|
| **stem proximity** | cosine of the new word's vector with its stem's | significant, and **an inverted U** |
| **vector entropy** | how evenly the vector's mass is spread | significant, **negative** (−0.91) |
| **neighbourhood density** | mean cosine with its 10 nearest neighbours | **dropped** — did not contribute |

**Highest similarity to the stem is not best.** Acceptability peaks at a
proximity of about **0.4** and falls away on both sides: linear term +0.78,
quadratic −3.39. Too close and the affix did nothing — the paper's examples
are *opticianist* and *scholarist*, which people rejected because they do
exactly what *optician* and *scholar* already do. Too far and the derivation
broke down: *windowist*.

**Entropy separated the two populations completely.** 900 existing derived
words fell in 2.01–4.51 (mean 3.27); the nonce forms in 4.77–5.58 (mean 5.34).
**No overlap at all.** A vector whose mass is spread evenly does not name
anything in particular, and a word like that is hard to interpret.

**And the finding that decides whether we need any of this**: the paper tested
the productivity indices of Hay & Baayen against the meaningfulness ratings
and found **no significant correlation**. In their words, semantic
acceptability is a property of a *specific derived word* and cannot be reduced
to productivity, which is a property of a *word-formation process*.

That is the argument for PLAN 5.6 stated by someone else's measurement rather
than by us. Task 5.3 measured productivity for every rule; that number is real
and it will not tell anyone whether *Raftbān* is a word.

**One caveat we cannot yet answer.** Entropy is defined for vectors with no
negative values — the paper used non-negative matrix factorisation. BGE-m3's
vectors have negative components, so the strongest of the three measures does
not transfer unchanged. Either the count matrix is factorised ourselves, or a
different measure of how spread a meaning is has to be found. Nobody has
solved this here yet.

### A cheaper measure that beat it (2025)

Reviewed 2026-08-12. A study of Malay prefixed words — 4,226 of them, an
under-resourced language, plain fastText 300d vectors — compared FRACSS with
simpler measures of semantic transparency and found the simplest one fitted
human data **better**: the correlation between a derived word's vector and the
**centroid** of all words carrying that affix. AIC 12,325 for the centroid
measure against 12,341 for FRACSS.

The difference that matters here is not the fit. It is the input:

| measure | needs a vector for | needs pairs per affix |
|---|---|---|
| **affix centroid** | the **derived** words only | as many derived words as exist |
| **FRACSS** | the **base** and the derived word | enough pairs to fit a matrix |

That distinction is decisive for this grammar, because **76.8% of our attested
pairs have a bound verb stem as the base** (measured — see below). A measure
that never needs a base vector sidesteps the whole problem.

**But the centroid alone cannot score a word nobody has written**, which is
what this project generates: it scores a word that already has a vector. Three
shapes are therefore on the table, and they are not the same question:

1. **Affix centroid** over attested derived words — *is this existing word
   semantically typical of its affix?* Cheap, robust with few pairs, published
   as the better fit. Cannot score a novel form.
2. **FRACSS** — predicts the novel word's vector from its base, which can then
   be compared with the affix centroid. Needs base vectors and enough pairs.
3. **Base centroid** — *does this base resemble the bases this affix usually
   takes?* Needs base vectors only, no matrix, and scores a novel form. **This
   one is our extrapolation, not something the literature reports**, and it
   would have to be validated against the feedback set like anything else.

### What the material actually is

Measured 2026-08-12 on the v1 precompute (1,738,711 words), by
`tools/count_semantic_pairs.py`. Single-step derivations only: a two-step
chain is evidence about the chain, not about either affix.

| | |
|---|---|
| rules with any attested pair | **63 of 195** |
| rules with ≥ 200 pairs | 22 |
| rules with ≥ 50 pairs | 47 |
| rules with ≥ 50 pairs **on confirmed readings alone** | **7** |
| bases that are bound verb stems | **12,341 of 16,069 — 76.8%** |

Two things follow, and neither depends on which embedding model is chosen.

**A per-affix model is possible for a few dozen rules, not for the pack.**
Twenty-two rules have enough material to be comfortable about; 132 rules have
no attested pair at all and no amount of modelling will invent one.

**Most of the evidence is at spelling level, not reading level.** Drop to
confirmed readings and only 7 rules clear 50 pairs. That is the same gap
UPSTREAM B2 already records: the corpus has the word, the dictionary has no
entry for it, so we cannot be sure how it is read.

### Do the bound stems occur at all?

They do, and this was worth checking rather than assuming. Measured against
the v1 corpus: **1,753 of 1,930 stem forms (90.8%) occur as corpus word
types**, because in Persian the past stem is also the third-person past tense
form and the present stem is also the imperative. Free-word bases occur at
92.4%, so the two are barely different.

The caveat is what the vector then *means*: it is the vector of an inflected
verb form, not of an abstract stem, and 593 of those stems occur fewer than
ten times, which is too rare for a stable vector whatever the model.

## Which embeddings, and trained on what

Reviewed 2026-08-12. The question PLAN 5.6 is blocked on, with what is
actually available.

### Do we need our own Latin-form vectors?

[RULE_DISCOVERY.md](RULE_DISCOVERY.md) assumed yes — "public models are
trained on Arabic script". **Measured, that assumption costs less than it
looks.** The engine composes the Persian spelling in the same step as the
Latin (task 2.1), so a script-keyed vector can be attached to any form we
build. What is lost is only the words where one spelling has two readings:
**1,037 of the 16,714 linked corpus spellings — 6.2%**. Those can be flagged
rather than guessed at, which is what the rest of the app already does with
مرد.

So a public Persian-script model is usable. That is a much cheaper starting
point than training a vector space over Behnevis forms nobody else has.

### What the sister project already uses

The Persian poetry search project in the same group runs **BGE-m3**
(1024-dimensional, multilingual) with BM25 beside it and a `bge-reranker-v2-m3`
cross-encoder on top. It searches the same material we do — classical Persian
couplets — and the model is already downloaded (4.3 GB on the project lead's
machine).

**It is the right model for that job and the wrong shape for this one.** BGE-m3
turns a whole line into one vector, which is what finding a couplet needs. We
need one vector per *word*, so that two words can be compared.

The same model can still be used, differently: run it over the lines a word
appears in and average that word's vectors across its occurrences. That is a
published method, and it has an advantage nothing off-the-shelf has — the
vectors would come from **classical poetry**, which is our corpus, rather than
from modern web Persian. That it already works well on this material in the
sister project is real evidence, not a guess.

### The pilot: measured on our own corpus, 2026-08-13

The go/no-go check before anything is built, runnable again with
`tools/semantic_pilot.py`. Word vectors were made the cheap way — up to six
corpus lines per attested word, each embedded with **BGE-m3** (the sister
search project's local copy, MIT), mean-pooled. Then leave-one-out: is each
word closer to its own rule's centroid than to the other rules'?

| | |
|---|---|
| rules | V-010 *-ār*, V-041 *-nāk*, N-044 *-bān* |
| words with enough lines | 45 |
| **leave-one-out accuracy** | **42/45 = 93%** (chance 33%) |
| mean cosine, own affix | 0.802 |
| mean cosine, other affixes | 0.741 |

So the go/no-go answers **go**: vectors from our own classical corpus separate
affix families cleanly, with no training and no new downloads. The gap (0.06)
is small in absolute terms — poetry lines share a register — but consistent
enough for 93%.

**Two honest caveats.** Three rules is an easy test; the measure has to be
validated against expert verdicts (the feedback set) before it ranks anything
a user sees. And part of the separation may be topical rather than
morphological — *-nāk* words live in different poems than *-ār* words.

**The pilot also caught a data fault worth more than the pilot.** The *-dān*
and *-stān* rules were dropped because their sister lists are contaminated by
homographs: **شاهدان counted as شاه + -dān is the plural of شاهد**, and نوزادان,
راکبان, کوهستان's neighbours have the same problem. These lists come from the
affix backfill (task 6.4), which only claims **confirmed readings** — but a
confirmed reading of the *whole word* does not confirm the *parse*. A
spelling-level trap, now visible; the semantic distance itself may become the
cheap detector for it, since شاهدان sits near people-words, not near
container-words.

### Built on the pilot's result, 2026-08-13: typicality is live

`tools/build_semantic_vectors.py` (batch, torch environment) embeds every verb
stem and every base of an attested pair — up to six corpus lines each — and
stores base vectors plus a **base centroid for each of the 57 rules with ≥10
attested pairs** in `data/semantic-<version>.json` (19.7 MB). The app reads
the artefact (`murfulu/scoring/semantics.py`) and never embeds anything.

`/generate` now carries a `semantic` part per form — the cosine of the first
step's base with its rule's base centroid — and the build screen shows it as
its own sentence and uses it as the **last** tie-breaker, after attestation
and after the ground under the chain. On رفتن, 129 of 510 forms carry one.

Three boundaries, stated because they are the design:

- **scored on the first step only.** Deeper steps stand on generated
  intermediates with no vector, and a made-up number is worse than none.
- **unmeasured is `null`, never low.** It never loses a tie to a measured
  score; it only fails to win one.
- **unvalidated against people.** The ranking use is the project lead's call
  (2026-08-13); fitting against the expert feedback set (8.3) remains the
  gate before this is treated as more than a hint.

**Building it surfaced a corpus-infrastructure fault worth recording on its
own:** the `documents` index analyses text with Lucene's stock Persian
analyzer, whose stopword list swallows **رفت، گفت، شد** and the rest of the
most common verb forms — a phrase query for them finds *nothing* in a corpus
that contains them millions of times. The batch tool therefore reads the
Ganjoor source directly. The same hole affects `/word`'s citations for those
words: the counts are right (they come from `word_types`), but the quoted
lines come up empty. Registered as its own fix.

### The wider test of the 93%: all 57 centroid rules, 2026-08-13

Three rules is a small board, and 93% against 33% chance is what a small board
gives. `tools/semantic_pilot.py` now runs the same leave-one-out over **every
rule the artefact has a centroid for**, on corpus v3. The board is 57 rules and
2,025 attested words — at most 40 per rule so one broad rule does not outweigh
forty narrow ones, at least 6, and doubted claims (the homograph pass) left
out. The full table is `build/pilot-v3.md`.

| | |
|---|---|
| leave-one-out accuracy | **25.4%** |
| counting a rule with the same affix as right | **64.0%** |
| chance | 1.8% |
| mean cosine, own rule | 0.823 |
| mean cosine, every other rule | 0.790 |

**25.4% is fourteen times chance and it is also the wrong number to quote**,
because the board is not 57 distinguishable things. **35 of the 57 rules share
their affix with another rule on the board** — V-070 to V-073 are all *vā-*,
V-005 and V-006 are both *-an*, V-001 and V-002 are both *-āndan* — and those
35 score **105 of 1,266** strictly while their same-affix score runs to 90%.
There is nothing in a word's meaning that could separate *-an* the infinitive
from *-an* the noun; the difference is the output class, which the grammar
states and no vector was ever asked about.

**On the 22 rules with an affix of their own, strict accuracy is 53.9%** —
409 of 759. That is the figure to carry forward.

| does well | | | does badly | | |
|---|---|---|---|---|---|
| N-021 | *nā-* | 35/40 | N-072 | *-nā* | 0/31 |
| V-022 | *-ande* | 34/40 | N-023 | *-nā-* | 2/32 |
| N-045 | *-tar* | 32/40 | N-020 | *-na-* | 6/40 |
| V-032 | *-gar* | 32/40 | V-048 | *-ār* | 6/40 |
| V-014 | *-mān* | 22/25 | N-033 | *-ā* | 6/38 |

**What separates the two columns is not the model.** *nā-*, *-ande*, *-tar*
and *-gar* each do one thing to one kind of base. *-nā*, *-na-*, *-nā-* and
*-ā* are short, they collide with each other and with Arabic endings — the
same collision the affix backfill refuses *Fanā* over — and their attested
lists are the ones the homograph pass found thinnest.

**So the honest statement of the 93% is:** the method works, and how well
depends on whether the affix is a real distinction in the corpus. It ranks as
the last tie-breaker and still waits on the expert feedback set before it is
more than a hint.

### The same vectors, used backwards: which claims are homographs, 2026-08-13

The pilot found the sister lists of *-dān* and *-stān* contaminated by
plural-ان homographs — **شاهدان is the plural of شاهد, not شاه + -dān** — and
dropped those two rules rather than measure round it. This is that measurement.
`tools/flag_homograph_claims.py` with `tools/homograph_fit.py`, on corpus v3.

**The first attempt failed, and the way it failed set the method.** Score each
claim by the cosine of the word to the centroid of the words its rule claims,
that word left out, and cut low:

| | n | mean | sd |
|---|---|---|---|
| a claim against its own rule | 16,498 | **0.811** | 0.052 |
| a claim against every other rule | 1.49 M | **0.780** | 0.055 |

Two distributions that overlap almost entirely. Any absolute cut flags nearly
everything or nothing — the first run flagged **100%**. Absolute cosines from a
line-averaged encoder carry a large shared component, and it drowns the signal.

**So both statistics are ranks.** For a claim, what share of the candidates it
has nothing to do with fit the word better. Under the null — the claim is
unrelated — the rank of one candidate among unrelated ones is uniform, so the
null density is exactly 1 and the cut is *the first bin whose claim density
falls below it*. Nothing is picked by hand. The uniformity is checked rather
than assumed: a null built by pairing every word with every rule that never
claimed it has a **median of 0.495**.

**Two checks, because the first one is blind exactly where it is needed.**

| | what it compares | cut | doubted |
|---|---|---|---|
| **rule fit** | the word against its rule's centroid, itself left out | 0.160 | 1,940 |
| **base fit** | the word against the word it was built from | 0.080 | 2,062 |

A rule whose claims are *mostly* homographs has a centroid **made of** them,
and شاهدان then sits comfortably inside it — measured: rule fit doubted nothing
in *-dān* or *-stān*. Base fit needs no centroid and works per claim, so no
amount of contamination in a rule can hide a claim from it. It is the one that
catches the case the pilot named:

| doubted | claimed as | what it is | share of bases fitting better |
|---|---|---|---|
| **شاهدان** | شاه + *-dān* | the plural of شاهد, a witness | **84%** |
| **لهستان** | له + *-stān* | Poland | **78%** |
| **مردمان** | مرد + *-mān* | the plural of مردم | rule fit, 100% |
| **کرنا** | کر + *-nā* | a trumpet, a loanword | base fit |

**Measured on corpus v3: 3,613 of 16,627 checkable claims doubted — 21.7% —
across 108 of 120 rules.** Twelve rules have nothing doubted. The per-rule
table is `build/homograph-report-v3.md`; the worst are small rules whose
claims are nearly all wrong (N-012, 11 of 11).

**What it costs downstream.** The affix map falls from **1,573 corpus word
types traced to a rule to 1,397**, with 2,948 individual claims contested. The
`*nā` search's *formed with this affix* group drops *Karnā* and keeps four.

**Two limits, stated rather than smoothed.** A claim can only be checked if
its word has **two corpus lines** to average — 16,627 of 27,276 clear that —
so the rare words that fill a small rule's list are largely unchecked, and
*-dān* keeps twelve one-occurrence entries nobody has measured. And this is a
cosine, not a ruling: doubted claims are **ranked last in the sister lists, not
removed**, and held out of the index's assertions rather than deleted.

### The candidates

| option | licence | what it is | why it might not do |
|---|---|---|---|
| **fastText `cc.fa.300`** | CC-BY-**SA** 3.0 | 300d static vectors, Common Crawl + Wikipedia. What the Malay study used | 2018 web Persian; share-alike travels to anything derived from it |
| **type vectors averaged from an encoder over our own corpus** | MIT for BGE-m3 | run **BGE-m3** — already used and downloaded for the sister project — over Ganjoor and average each word's vectors across its occurrences | more work than a lookup; the vectors have to be built once |
| **train our own on a large open corpus** | ours to choose | HPLT v3.0 is **CC0**, Naab is **MIT** — see the corpora reference in the Drive archive | days of compute, and still modern-web Persian |
| **train on classical poetry alone** | ours | Ganjoor's 25.5M tokens, plus PARSI's 1.12M mesras | 25.5M tokens is small for stable vectors |

Two warnings worth writing down before anyone starts.

**Share-alike is a licence decision, not a technical one.** fastText's vectors
are CC-BY-SA 3.0. Anything derived from them inherits it, and PLAN 8.4 has not
settled this repository's licence. HPLT v3.0 (CC0) and Naab (MIT) do not have
that problem.

**A modern-web vector for a classical word is not obviously the right
vector.** Our corpus is a thousand years of poetry. Nobody has measured how
far a word's modern distribution is from its classical one, and the honest
first step is to measure coverage — how many of our 16,714 linked spellings a
candidate model even has — before arguing about quality.

**And fastText will flatter us if we let it.** Its subword vectors compose a
plausible-looking vector for *any* unseen string from its character n-grams —
including the affix we just attached. Scoring a generated word against a
fastText vector *of that generated word* would measure the spelling, not the
meaning. The generated form's vector has to be **predicted from its parts**,
never looked up.

## Acceptability

Studies of novel derived words model acceptability with four predictors:
**lexicality, suffix identity, stem syntactic category, stem frequency** — all
significant. Three of the four are data we will already hold, so this is a cheap
baseline regression.

## Phonotactics / wordlikeness

Phonotactic probability affects wordlikeness judgements **asymmetrically**: it
raises the tendency to judge an item *wordlike*, but does not drive the
judgement that an item is *not* wordlike. So a phonotactic model is a positive
signal, never a filter. An earlier draft of this note overstated it.

## Explicitly not a signal: blocking

An existing word covering the same meaning (*zibāyi* vs *zibānā*) is **not** a
reason to score a form down. Both can exist and both can mean something. The
project exists to fill gaps that convention left. Show related existing words as
information; never as a penalty. — project lead, 2026-08-11.

## Attestation, when the word is found

Store more than a count:

| Field | Why |
|---|---|
| total occurrences | raw frequency |
| distinct documents | 30 hits in one poem is a rhyme, not a word |
| distinct authors | one author = that author's coinage |
| first / last date | survived, or died out |
| citations | an expert reads the lines and judges |

Dispersion matters more than the raw count.

## The gap

None of this has been done for Persian, and there is no gold standard for an
under-resourced language. That is a real contribution, and it is what the NGI
application already promises under technical challenges 4 and 5.

## Rule for the interface

Never print "this word does not exist". Print "not found in corpus v3
(119,061 documents)". When the corpus grows and the word turns up, the earlier
answer was not wrong — it was the answer for a smaller corpus.

## Sources

- Pierrehumbert & Granell 2018, *On Hapax Legomena and Morphological
  Productivity* — https://aclanthology.org/W18-5814.pdf
- Monakhov 2023, *Probabilistic Method of Measuring Linguistic Productivity* —
  https://arxiv.org/abs/2308.12643
- Baayen 2009, *Corpus linguistics in morphology: morphological productivity* —
  https://quantling.org/~hbaayen/publications/BaayenHSK2009.pdf
- Marelli & Baroni, *Affixation in Semantic Space* (FRACSS) —
  https://marcobaroni.org/composes/FRACSS/Marelli_Baroni_PsychReview_preprint.pdf
- Amenta & Marelli, *A (distributional) semantic perspective on the processing
  of morphologically complex words* — https://benjamins.com/catalog/ml.00014.ame
- *Can AI mimic the human ability to define neologisms?* —
  https://arxiv.org/pdf/2502.14900
- *An Exploratory Analysis on the Explanatory Potential of Embedding-Based
  Measures of Semantic Transparency for Malay Word Recognition* (2025) —
  https://arxiv.org/abs/2505.05973 — the centroid measure, and FRACSS on an
  under-resourced language with off-the-shelf fastText
- *Obtaining Better Static Word Embeddings Using Contextual Embedding Models*
  — https://arxiv.org/pdf/2106.04302 — averaging a word's contextual vectors
  over real occurrences. Feeding a word with **no** context to an encoder and
  pooling performs badly; averaging over contexts does not
- fastText word vectors for 157 languages, CC-BY-SA 3.0 —
  https://fasttext.cc/docs/en/crawl-vectors.html
- *FaMTEB: Massive Text Embedding Benchmark in Persian* —
  https://arxiv.org/pdf/2502.11571 — the current Persian encoder ranking.
  Sentence-level; useful for picking an encoder, not a source of word vectors
- *Hakim: Farsi Text Embedding Model* — https://arxiv.org/abs/2505.08435 —
  state of the art on FaMTEB, 11B-token corpus, but passage-level and its
  licence is not stated on the model card
- `Forschung/Persian-Open-Corpora-Reference.md` in the Drive archive — the
  corpus map this section's licences come from (HPLT v3.0 CC0, Naab MIT,
  MADLAD-400 highest baseline quality)
