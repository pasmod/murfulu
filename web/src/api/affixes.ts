/**
 * Affixes, grouped by what they mean.
 *
 * This is the question the project started from: a writer who wants to use
 * *-gān* should not have to open a grammar book to learn what it does. The
 * grouping is by meaning rather than by affix, because one affix carries
 * several meanings and one meaning is carried by several affixes.
 */

import { get } from "./client";

export interface AffixEntry {
  affix: string;
  affix_fa: string | null;
  rule_id: string;
  kind: string;
  output_types: string[];
  examples: string[];
}

export interface Meaning {
  tag: string;
  gloss_fa: string | null;
  gloss_en: string | null;
  affixes: AffixEntry[];
}

export interface Affixes {
  rule_pack_version: string;
  count: number;
  meanings: Meaning[];
  /** Affixes the source records no meaning for. Not a meaning of their own. */
  without_a_meaning: AffixEntry[];
}

export function affixes(tag?: string, signal?: AbortSignal): Promise<Affixes> {
  return get<Affixes>("/affixes", { tag }, signal).then((body) => ({
    ...body,
    meanings: body.meanings ?? [],
    without_a_meaning: body.without_a_meaning ?? [],
  }));
}
