# Corpus v15 → v16 (the Persian side of a join)

Measured 2026-11-13 on the Mac, **before any release**. v16 is v15's recipe
(docs/ENGINEERING.md) with one code change and nothing else: commit 08a954a,
*Write a half-space after a silent heh, and the glide ye only once*
(`src/murfulu/engine/glides.py`, `join_fa`). Lexicon (`lexicon-20261111`),
corpus text, semantic vectors and suspect claims are v15's. Built with
`tools/build_corpus_mac.sh v16 lexicon-20261111` in **6.5 minutes**.

## The five report figures and the build

`tools/compare_versions.py --report … --derivations …`:

| | v15 | v16 | |
|---|---|---|---|
| documents | 133,148 | 133,148 | same |
| tokens | 25,497,189 | 25,497,189 | same |
| spellings | 409,916 | 409,916 | same |
| spellings_linked | 23,127 | 23,127 | same |
| documents_without_century | 98,627 | 98,627 | same |
| records | 2,949,164 | 2,949,164 | same |
| paths | 4,342,574 | 4,342,574 | same |
| attested | 30,158 | 31,484 | **+1,326** |
| function_word | 39 | 39 | same |

No rule's output count moved. Every record exists in both versions under the
same id; only the Persian spelling and what the corpus says about it changed.

## What moved, record by record

**692,606 records changed spelling** — a zero-width non-joiner after a silent
ه, or one ی fewer where the glide ی met a base already ending in ی.

**Attestation moved for 1,579 records**: 1,451 newly found (1,411 at spelling
level, 40 at reading level), 125 no longer found, 3 between the two levels.

| newly found, by cause | records | examples (corpus count) |
|---|---|---|
| the half-space | 245 | لاله‌زار 165, تازه‌تر 83, بنده‌وار 55, شوره‌زار 27 — real words, reported as never written before |
| the glide, a form like *ziyān* | 952 | زیان 2,969, ایرانیان 727, تازیانه 682, سیاوش 461 — mostly the real word; a few homographs (شبیه read *šabiye*) |
| the glide, a Latin form ending in *-iy* | 254 | شبی *Šabiy* 4,334, آفتابی *Āftābiy* 1,221, سالی *Sāliy* 841 — **homographs**: the corpus word is *šabi*, not the engine's *šabiy* |

The 254 are a new instance of a known fault, not a new fault: attestation
credits a spelling to whatever derivation writes it (FINDINGS, the homograph
pass; `research/results/fixes-and-questions-v14.md` A3 on the research branch).
v15 hid them only because it spelled the forms with three ی.

**The 125 no longer found are false credits removed.** All are built through
V-034 (*-e* on a present stem) and then a suffix: *Kove + stān* is now
کوه‌ستان and no longer claims کوهستان (*kuhestān*, 63), *Re + vār* no longer
claims رهوار (*rahvār*, 115), *mode + vaš* no longer claims مدهوش (*madhuš*,
627). The engine's word was never the corpus word.

Record-level moves: `build/attestation-moves-v15-v16.json` (not in git).
