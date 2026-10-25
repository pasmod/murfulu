/**
 * Building words from one word, and what the corpus says about each.
 *
 * The shapes mirror what `/generate` returns. Two of them carry a distinction
 * the interface must not flatten:
 *
 * - `attestation: null` means the corpus was **not asked** — Elasticsearch was
 *   not reachable, or the caller turned it off. It is not "not found".
 * - `level: "none"` means it was asked and the word is not there, in **that**
 *   corpus version, which travels with the answer.
 */

import { get } from "./client";

export interface Step {
  rule_id: string;
  affix: string | null;
  applied_to: string;
  label_fa: string | null;
  explanation_fa: string | null;
  /**
   * The sense this rule carries, in Persian, from the rule pack's tags.
   *
   * Often the only thing telling a rule from its neighbours: V-070..V-073 all
   * attach `vā-` to the same stem with a word for word identical
   * `explanation_fa`, and differ only in پس / دوباره / باز / آخشیج. Absent on
   * an unworded answer, and empty for a rule carrying no tag.
   */
  tags_fa?: string[];
  /**
   * This rule's own record: how many words it built, how many the corpus has.
   *
   * Counts rather than a rate, because the form-level `realisation` is a
   * median over the chain and describes no rule in it — وارفته's two steps
   * realise 0.67% and 9.18%. Null where the run never measured the rule.
   */
  built?: {
    types: number | null;
    attested: number | null;
    corpus_version: string;
  } | null;
  stem_form: string | null;
  glide_id: string | null;
  glide_alternatives: string[];
}

export interface Attestation {
  level: "reading" | "spelling" | "none";
  corpus_version: string;
  total_count: number;
  doc_count: number;
  author_count: number;
  first_century: number | null;
  last_century: number | null;
  other_readings: string[];
  unlinked: boolean;
  /**
   * The class of the function word these letters almost always are, or null.
   * When set the counts are zero and mean *unknown*: the occurrences are that
   * word's. Absent from answers built before v14.
   */
  function_word?: string | null;
  wording: string;
}

export interface BuiltForm {
  form_latin: string;
  form_fa: string;
  word_class: string;
  depth: number;
  semantic_tags: string[];
  meaning_fa: string | null;
  /** Null when the corpus was never asked. Never confuse with level "none". */
  attestation: Attestation | null;
  /**
   * Whether some route to this form rests on written ground throughout —
   * an unattested word built *on another unattested word* is the engine
   * compounding a guess. Null when the corpus was not asked; never "no".
   */
  base_attested?: boolean | null;
  /**
   * How often the rules on the way to this word produce words the corpus
   * actually has, summarised as the median of the chain.
   *
   * **The part of the score that can speak about a deep word.** A semantic
   * typicality is measured on the *first* step only, because a base's vector
   * is the average of up to six corpus lines using it — so a word nobody has
   * written can never have one, and every step after the first stands on a
   * word the engine invented. At three steps that leaves 12,999 forms sharing
   * 22 typicality values between them, which cannot order a list.
   *
   * Null where nothing has been measured at all; a rule the run could not
   * measure counts as neither good nor bad rather than as zero.
   */
  realisation?: {
    median: number;
    steps_measured: number;
    steps: number;
  } | null;
  /**
   * How these letters *also* read, when they read as an inflection of a word
   * the dictionary already holds.
   *
   * رفتی is "you went" — an inflection of the stem رفت — before it is anything
   * this project built, and the corpus counts it. Where the lexicon knows no
   * reading for a spelling, this is the only thing that separates it from
   * گفتار, which is exactly the word we make. See S8.
   *
   * **`shared_with` is the honest half.** 95.6% of inflection-shaped forms are
   * spelled by a derivational rule too — آبادانی is the indefinite of آبادان
   * *and* the noun — so the letters cannot settle which it is, and the screen
   * says they cannot. Which reading is right is the linguist's.
   *
   * Null means *not one*, or *not asked* where no lexicon is configured.
   */
  inflection?: {
    base: string;
    pattern: string;
    label_fa: string;
    shared_with: string[];
  } | null;
  /**
   * The semantic part of the score: how much the first step's base resembles
   * the bases its rule usually takes, measured on the corpus (see
   * RESEARCH_SCORING.md). One part, never the score. Null is "not measured" —
   * most rules have no centroid — and must never read as a low score.
   */
  semantic?: {
    typicality: number;
    rule_id: string;
    base: string;
    bases_measured: number;
    /**
     * Where this score sits among every scored word, from a measured
     * distribution. The cosine never leaves the middle — 0.554 to 0.914,
     * middle half 0.800–0.852 — so the bare figure reads far better than it
     * is: 84% is the median. Null where no spread has been measured.
     */
    band?: "lowest" | "low" | "middle" | "high" | "highest" | null;
    median?: number | null;
    lowest?: number | null;
    highest?: number | null;
    /**
     * The bases this rule's centre was built from, nearest first.
     *
     * What makes the figure checkable. شد ۹۱٪ · کرد ۸۹٪ · raft ۸۵٪ asks a
     * reader only to read a list, where a bare 85% asks them to know what a
     * cosine is — and it shows the thing the bare figure hid, that raft sits
     * further out than every one of them.
     */
    typical?: {
      latin: string;
      fa: string;
      typicality: number;
      /**
       * The verbs this stem is written on. **A stem alone cannot be judged**:
       * هز and واز mean nothing to a reader until they are هزیدن and وازیدن.
       * Empty for a nominal rule, whose bases are nouns.
       */
      of?: string[];
    }[];
    /** The rule's own sentence, so the block names it as every other row does. */
    rule_says_fa?: string | null;
  } | null;
  /** Every chain that produces this form, shortest first. Two is information. */
  paths: Step[][];
}

export interface Reading {
  latin: string;
  spelling_fa: string;
  lexicon_category: string | null;
  /**
   * The dictionary's own doubt about this reading. Reported, never filtered
   * on: بلند is *Baland* flagged and *boland* clean, and the flagged one
   * builds the larger list — so a reader has to be told which they are
   * looking at. Optional, because an older API does not send it.
   */
  needs_review?: boolean;
  latin_variants: string[];
  /**
   * The dictionary's own definition of the word being built from.
   * A **preview**: karbon cuts it at 200 characters, 27.6% of them
   * mid-word, and no مصدر has one — so a verb shows nothing here.
   */
  definition_fa?: string | null;
  built_from: { latin: string; fa: string; word_class: string }[];
  /** The engine cut the chain short. Not the same as a page holding part. */
  truncated: boolean;
  /** Every form this reading built, however few this answer carries. */
  count: number;
  /**
   * Where this page starts, how many it holds, and whether more remain.
   * Optional because an older API does not send them; this screen asks for
   * the whole answer, so `returned` equals `count` here.
   */
  offset?: number;
  returned?: number;
  has_more?: boolean;
  forms: BuiltForm[];
}

export interface Generated {
  word: string;
  depth: number;
  rule_pack_version: string;
  lexicon_snapshot_id: string;
  corpus_version: string | null;
  readings: Reading[];
}

/**
 * How many forms a deep answer asks for.
 *
 * **At one and two steps the screen still asks for everything**, because it
 * groups by word class and shows what each group folds, so it has to have
 * counted every form — and بلند, the largest, is 2,856 forms and 3.94 MB.
 *
 * At three steps the whole answer is **39 MB** and no browser should be sent
 * it. So a deep answer is a page, and the route ranks before it pages: the
 * best thousand, not the first thousand.
 *
 * **A thousand is measured, not picked.** The band worth reading is the words
 * the corpus has plus the new ones whose every step is written — 542 of
 * اندیشیدن's 17,717, 843 of گفتن's, 2,183 of رفتن's. Six hundred covered only
 * the first of those three. A thousand is 2.0 MB and 1.3 seconds, against the
 * 3.94 MB this screen already asks for at two steps, so it costs nothing new.
 *
 * رفتن's band still runs past it. That is honest and said on screen — the
 * reader is told how many of how many — rather than fixed by sending 6 MB.
 */
export const DEEP_LIMIT = 1000;

/**
 * Every word the rules build from this one.
 *
 * `limit: 0` asks for the whole answer, which is what one and two steps do —
 * see {@link DEEP_LIMIT} for why three steps cannot. What this must never do
 * is show a slice and call it the answer: every reading states how many forms
 * it holds in total and how many came back, and the screen says so.
 */
export function generate(
  word: string,
  depth: number,
  signal?: AbortSignal,
  limit = 0,
): Promise<Generated> {
  return get<Generated>("/generate", { word, depth, limit }, signal);
}

/**
 * A word class under both vocabularies. Never invented here.
 *
 * `label_fa` is what to print — the project's own coined term. `traditional_fa`
 * is the tooltip, because that is what most readers were taught. Until
 * 2026-08-17 only the traditional term was in the data, so the build screen
 * labelled its groups اسم مصدر where FRONTEND.md says کارنام is primary; that
 * was S3, and it is closed in `rules/word_classes.yaml`.
 *
 * `label_is_traditional` is true where there is no coined term to show and
 * `label_fa` has fallen back to the old one — the vocative is the only case.
 * A screen that ignored the flag would present the replaced vocabulary as
 * though it were the replacement.
 */
export interface WordClass {
  name: string;
  label_fa: string | null;
  label_is_traditional: boolean;
  coined_fa: string | null;
  traditional_fa: string | null;
  behnevis: string | null;
  explanation_fa: string;
  /** Whether the linguist has ruled on this Persian. Four have not — L17. */
  term_confirmed: boolean;
  description_en: string;
}

export function wordClasses(signal?: AbortSignal): Promise<WordClass[]> {
  // An older API that does not serve this field yet must degrade to unnamed
  // groups, not to a blank screen. The first version returned the field
  // straight through and took the whole build screen down with a
  // `Cannot read properties of undefined` the moment the running container
  // was a version behind the code.
  return get<{ word_classes?: WordClass[] }>(
    "/rules",
    { family: "G" },
    signal,
  ).then((body) => body.word_classes ?? []);
}
