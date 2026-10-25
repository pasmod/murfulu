# Ideas — uses and direction

**Status: ideas, not decisions.** Opened 2026-10-19 by the project lead. Each
use carries a status (`idea`, `candidate`, `in progress`, `dropped`); a use
that is chosen moves into PLAN.md, and a direction that is settled moves into
DECISIONS.md.

---

## Direction proposed 2026-10-19: one core, several languages

**The project lead's principle (2026-10-19):** whenever the project is funded
from Germany, it carries a German-language part.

**Proposal.** Build the core language-independent, so that the rule pack, the
lexicon and the corpus are inputs rather than assumptions. Persian stays the
full showcase. German becomes a second, small showcase.

**Decided 2026-10-19 (project lead):** German is a small pilot that shows the
core carries over to a second language. It is not a second full showcase.

**Not new:** the NGI application (submitted 2026-05-31, Drive
`Förderung/NGI_Zero_Commons_Fund/01_Antrag/`) already proposed a
language-agnostic core with swappable rule packs, a reusable library
(`morphology-core`) and a small German rule pack in its milestone M4. What is
new on 2026-10-19 is the Persian ↔ German bridge as the funded module.

**Why German.**

- The two languages make the central measure comparative. Persian has lost much
  of its derivational productivity to compound verbs (*barresidan* →
  *barresi kardan*); German has kept productive derivation and compounding
  (*Lichtung*, *Sauerstoff*). Once the rules and the data are complete, the
  share of the possible lexicon each language has actually used can be
  compared. The first Persian figure (1.4%, FINDINGS 2026-08-12) is **not a
  result** and must not be quoted as one: the linguist has not yet confirmed
  the rules, most of the attestation is at spelling level only, and the corpus
  is poetry only.
- A German funder or jury sees the public benefit directly: German learners,
  plain-language German, German terminology work.
- Persian-speaking people in Germany, Iranian and Afghan, live between the two
  languages. A bridge between Persian and German word formation serves them in
  both directions.

**What already exists for German.** The novelty claim has to stay honest,
because reviewers will know these resources:

| Resource | What it covers |
|---|---|
| SMOR (Stuttgart) | finite-state morphology of German, including derivation and compounding |
| DErivBase | derivational families of German words |
| DWDS (Berlin-Brandenburg Academy) | corpora and dictionary of German |
| IDS neologism dictionary (Mannheim) | new German words, with the date they appeared |

Licences as checked on 2026-10-20: SMOR is free only for non-commercial use, so
it cannot go into an Apache-2.0 release. DErivBase is listed as CC BY-SA 3.0 in
the Universal Derivations bundle, a secondhand source, which would bind shared
data to the same licence; check its own licence file. DErivBase also applies
derivation rules itself but keeps only words attested in its corpus, so the
claim of novelty rests on unattested words with composed meaning.

The German part should reuse these where their licences allow and claim only
what is new: the possible lexicon with composed
meaning and attestation, the language-independent core, and morphology-informed
translation between the two languages.

**Risks.**

- The scope doubles inside one funding period.
- The project has no German linguist yet; the linguist works in Persian.
- karbon is Persian-only, so the core needs a lexicon interface that does not
  assume karbon.
- German lexicon licences may limit what can be published as open data.

**The pilot.** German as a portability pilot: a handful of
productive patterns (*-ung*, *-heit/-keit*, *-bar*, *-lich*, simple noun
compounds) on an open lexicon, which proves that the core is language-
independent. Next to it, the Persian ↔ German bridge as the clearly new module:
a German term goes in, and the engine proposes Persian words built from Persian
material that carry the same structure of meaning (*Lichtung* →
روشن‌تنکنا, see USER_JOURNEYS J1).

**Name for the method.** "Domain-informed translation" would mislead, because
in machine translation "domain" means the subject area (medicine, law).
Candidates:

- *morphology-informed translation* (German: *wortbildungsgestützte Übersetzung*)
- *linguistically informed term formation* (German: *linguistisch fundierte Begriffsbildung*)

Computational morphology is an established field, so the project should present
this as a new approach within it, not as a new field.

---

## Uses

Uses that only an engine of *possible* words can serve. The obvious ones
(teaching, translation, lexicography, linguistic research, a tool for language
models, three scripts) are listed at the end.

| # | Use | What it does | German angle | Status |
|---|---|---|---|---|
| 1 | **Unseen-word benchmark** | Builds thousands of well-formed, unattested words with their composed meanings and tests whether a language model understands them. Language models have seen only words that were already written; this measures their competence, not their memory. The same words serve as stimuli for psycholinguistic experiments with speakers. | The same benchmark in German, and the two compared. | idea — strongest for research and funding |
| 2 | **Birth register of words** | Every new word that reaches a published text through the engine gets a record: who made it, when, in which text. Then one can watch which words live and spread: a live experiment in language change. The magazine can be its first field. | German neologisms are already tracked (IDS); a joint register would be new. | idea |
| 3 | **Metre and rhyme of possible words** | Joins the engine to metre and rhyme, so a poet can ask which possible word fits this slot of the line and rhymes with this word. Ganjoor already carries metre. | — (Persian-specific) | idea |
| 4 | **Word lens for classical texts** | Shows, for every word of a poem, the parts it is built from, so readers see the image inside the word again (*xerad* as "the eye of the soul"). | Same lens for German compounds in literature and law. | idea |
| 5 | **Coinage fingerprint of authors** | Each poet has walked a part of the possible space that others have not. That profile can serve style research and attribution questions, where word-frequency methods fall short (the poetry search project's Attar study). | — | idea |
| 6 | **Productive spell-checker and writing aid** | Today's spell-checkers mark every new word as an error and so keep the language inside what has already been written. A checker that accepts well-formed new words, and suggests *barresidan* where a writer types *barresi kardan*, removes that wall. | German spell-checkers have the same blind spot for well-formed compounds. | idea — possible income |
| 7 | **Children as word-makers** | Children learning Persian abroad memorise words. Playing with roots and affixes, with the engine saying whether a word is well formed, they experience the language as a tool for making, not a heritage to keep. | German learners, including Persian speakers in Germany, learn to read German compounds the same way. | idea |
| 8 | **Name maker** | Names for children, brands, magazines and columns that are new and whose meaning shows in their form. | Same for German names. | idea — possible income |
| 9 | **Worldbuilding vocabulary** | Writers of science fiction and game designers get vocabulary that sounds foreign yet stays Persian. | Same in German. | idea |
| 10 | **Transparent legal and administrative language** | Words understood from their form make laws and official letters readable for the people they bind. | Fits plain-language German (*Leichte Sprache*, *Einfache Sprache*). | idea |
| 11 | **A method for any language** | If the rule pack, lexicon and corpus stay separate from the engine, the same map can be drawn for Kurdish, Tajik, Pashto or German. | See the direction above. | candidate |

**The obvious uses**, kept for completeness: teaching Persian; translation and
term formation; lexicography (attested words no dictionary has, and meanings
for new words); linguistic research (productivity per affix, rules nobody wrote
down); a tool that language models call to build well-formed words; one word
written in Persian, Tajik Cyrillic and Latin script.
