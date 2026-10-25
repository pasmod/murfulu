/**
 * The rule pack, and what the corpus says about each rule.
 *
 * `productivity` is null for a rule no run has measured — which includes
 * every rule when no precompute has been run on this machine. That is a
 * different thing from a rule measured at zero, and the two never share a
 * shape here.
 */

import { get } from "./client";

export interface Productivity {
  rule_id: string;
  authored_strength: string | null;
  types_built: number;
  types_attested: number;
  types_confirmed: number;
  tokens: number;
  hapaxes: number;
  types_echoing_source: number;
  echo_share: number | null;
  potential_p: number | null;
  potential_p_confirmed: number | null;
  realisation_rate: number | null;
  measured: boolean;
  /** Set when the run could not measure it. Says why. */
  unmeasurable_reason: string;
  /** Which tercile of the measured spread it falls in. */
  band: "high" | "middle" | "low" | null;
  /** True when the authored strength puts it in a different band. */
  disagrees_with_strength: boolean;
  expected_band: string | null;
  corpus_version: string;
}

/**
 * One of the bases a rule's semantic centre was built from, and how close to
 * the centre it sits. Ranked by the batch job that had the vectors; nothing
 * here computes a cosine.
 */
export interface TypicalBase {
  latin: string;
  fa: string;
  typicality: number;
}

/**
 * What a rule's semantic centre is made of. `null` for a rule the artefact has
 * no centroid for — most of them — which is *not measured* and never a low
 * score.
 */
export interface SemanticCentre {
  bases: number;
  typical_bases: TypicalBase[];
}

/**
 * One vowel-meeting rule.
 *
 * A different shape from an affix rule, and served as one: a glide has no
 * affix, no input class, no semantic tag and no productivity, because it does
 * not build a word — it decides a letter where two vowels meet. Giving it
 * those fields as nulls would put blanks on screen where an affix goes.
 */
export interface Glide {
  id: string;
  family: "G";
  kind: "glide";
  left: string;
  right: string;
  result: string;
  examples: string[];
  explanation_fa: string | null;
  active: boolean;
  retired_reason: string;
  /**
   * The same reason in Persian, which is the only one a reader of this
   * interface can use.
   *
   * The screen used to show a **بازنشسته** badge and stop there, because every
   * `retired_reason` is written in English for whoever reads the repository —
   * so a reader was told *that* a rule no longer applies and never *why*, and
   * for N-090 the why is the whole of the interesting part. That was S14.
   *
   * Empty where nobody has authored it. The interface may not invent Persian,
   * so an empty string means the badge alone rather than a guessed sentence.
   */
  retired_reason_fa?: string;
}

export function isGlide(rule: Rule | Glide): rule is Glide {
  return rule.kind === "glide";
}

/** The other side of {@link isGlide}, so `filter` narrows rather than widening. */
export function isAffixRule(rule: Rule | Glide): rule is Rule {
  return rule.kind !== "glide";
}

export interface Rule {
  id: string;
  family: string;
  kind: string;
  affix: string | null;
  affix_fa: string | null;
  input_types: string[];
  output_types: string[];
  semantic_tags: string[];
  strength: string | null;
  examples: string[];
  label_fa: string | null;
  explanation_fa: string | null;
  active: boolean;
  /** The English record of why a retired rule was retired. Never shown. */
  retired_reason?: string;
  /**
   * The same reason in Persian, which is the only one a reader of this
   * interface can use.
   *
   * The screen showed a **بازنشسته** badge and stopped there, because every
   * `retired_reason` is written in English for whoever reads the repository —
   * so a reader was told *that* a rule no longer applies and never *why*, and
   * for N-090, the ezāfe filed as word formation, the why is the whole of the
   * interesting part. That was S14.
   *
   * Empty where nobody has authored it. The interface may not invent Persian,
   * so an empty string means the badge alone rather than a guessed sentence.
   */
  retired_reason_fa?: string;
  needs_expert_check: boolean;
  notes?: string[];
  source?: { table?: string; row?: string };
  productivity: Productivity | null;
  semantic: SemanticCentre | null;
}

export interface RulePack {
  rule_pack_version: string;
  count: number;
  corpus_version: string | null;
  measured_rules: number;
  /** How many rules have a semantic centre at all. */
  semantic_rules: number;
  /** Affix rules and glide rules in one list; tell them apart with isGlide. */
  rules: (Rule | Glide)[];
}

export function rules(signal?: AbortSignal): Promise<RulePack> {
  return get<RulePack>("/rules", {}, signal).then((body) => ({
    ...body,
    rules: body.rules ?? [],
  }));
}
