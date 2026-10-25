# Sources

The project archive lives in Google Drive at
`Geteilte Ablagen/Projekte/Morphology`. This is an index of what is there and
what each file is good for. All of it was read on 2026-08-11.

**The archive is private, and none of its files is in this repository.** The
two rule documents are transcribed into `rules/source_rows.json` and
`rules/stem_source_rows.json`; no other file from the archive is copied here.

## The rule material (most important)

| File | What it is |
|---|---|
| `Dasturhāye Vāžesāzi az Kārbonhā.docx` | **The core asset.** The full grammar: new terminology, verb categories, and ~200 word-formation rules in tables (from stems; from nouns/adjectives/adverbs; glide rules; conjugation table) |
| `Forschung/قواعد_مصدر_و_لاتین‌نویسی_..._۲۰۲۶۰۵۱۴.docx` | **The stem-rules file.** Stem rules 1–9 with exception lists, plus the Latin alphabet table (the later, canonical convention). This is what karbon implements, and the source for rule family `S` |

## Concept and rationale

| File | What it is |
|---|---|
| `Konzept/درآمد_پروژه.docx` | The clearest statement of *why*. The *tonoknā* / *Lichtung* example, the *zibānā* argument, the earlier Latin convention, Behnevis alphabet table |
| `Konzept/هوش_مصنوعی_..._تکمیل‌شده.docx` | Three classes of rule (documented / proposed / undiscovered), why a corpus + morpheme search engine is the prerequisite for all three, four project phases |
| `Konzept/Wortbildung-und-sprachliche-Generativitaet-im-Persischen.docx` | German-language academic framing (Heidegger, Gadamer). Four modules: corpus, morphology, semantics, generativity |
| `Konzept/نگرش_واژه‌سازانه_….rtf` (the linguist's) | The *barresidan* case study — how one prefix (*bar-*) can be given a new, deliberately constructed meaning |

## Team communication and funding

The archive also holds the team's protocols, voice messages and funding
papers. They are private and are not indexed here.

## Research notes

| File | What it is |
|---|---|
| `Forschung/Persian-Open-Corpora-Reference.md` | Map of every open Persian corpus with sizes and licences. Read this before starting corpus work |
| `Forschung/Persian-NLP-Tooling-Reference.md` | Persian NLP tools and models, what each is good for |
| `Forschung/Publikationen/2026_GLEMM_*.pdf` | Multilingual derivational-morphology dataset, 7 European languages, CC-BY-4.0. Closest existing thing to our rule base |
| `Forschung/Publikationen/2026_A Computational Approach to Language Contact*.pdf` | Probing ParsBERT for traces of language contact in Persian |

## Code

| Repo | What it is |
|---|---|
| `~/code/karbon` (`kp-multiverse/karbon`) | Persian → Latin engine, Dehkhoda lexicon, stem derivation, OOV resolver, review web app. See FINDINGS.md |
| `~/Code/mosaic/murfulu` | **Earlier prototype**, April–May 2026. Pipeline, FastAPI backend, React frontend, Postgres. Holds the nine stem rules already seeded, 19 hand-picked derivation rules, and corpus fetchers for Ganjoor, Wikisource and Miras. Read the fetchers before writing PLAN task 4.2. Its rule ids contain a person's name and cannot be reused |
