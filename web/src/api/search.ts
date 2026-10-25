/**
 * The shape of a search, and the one call that runs it.
 *
 * The field names mirror the `word_types` index exactly, because inventing a
 * second vocabulary for the same data is how the two drift apart.
 */

import { get } from "./client";

/** One hit: a *reading*, not a spelling. مرد the man and مرد the dead are two. */
export interface WordType {
  id: string;
  spelling_fa: string;
  latin: string | null;
  /**
   * Every other pronunciation the dictionary lists for this reading. برنا is
   * barnā and the same row also says bornā; 16.0% of readings carry one.
   * Shown beside the primary, never chosen between. Absent before corpus v6.
   */
  latin_variants?: string[];
  /** The dictionary's own definition, cut at 200 characters. Absent before v6. */
  definition_fa?: string | null;
  /** The dictionary's own category, in Persian. Shown as it is written. */
  lexicon_category?: string | null;
  /** corpus / lexicon / generated. A word can be in more than one. */
  population?: string[];
  total_count?: number;
  doc_count?: number;
  author_count?: number;
  first_century?: number | null;
  last_century?: number | null;
  authors?: string[];
  affixes?: string[];
  rule_ids?: string[];
  semantic_tags?: string[];
  corpus_version?: string;
  sense_count?: number;
  /**
   * The letters are, almost always, a function word of this class. On a
   * reading the counts are then absent — unknown, not zero — and the
   * spelling's own document (latin null) carries them. Since v14.
   */
  function_word?: string;
}

/** One bucket of a facet: a value and how many of the whole result set have it. */
export interface Bucket {
  value: string | number;
  count: number;
}

/**
 * The breakdown of the **whole** result set, from Elasticsearch — never
 * counted from the page, which would change with the page size and look
 * exactly like a real figure.
 */
export type Facets = Partial<Record<FacetName, Bucket[]>>;

export type FacetName =
  | "population"
  | "category"
  | "source"
  | "author"
  | "century";

export interface SearchResult {
  query: string;
  index: string;
  total: number;
  returned: number;
  facets: Facets;
  /** Words the derivation pass showed were **formed** with the affix asked about. */
  formed_with_affix: WordType[];
  /** Words that merely end in those letters. The two are never mixed. */
  string_match_only: WordType[];
}

export interface SearchRequest {
  q: string;
  /** Splits the hits into the two groups. Without it everything is a string match. */
  affix?: string;
  size?: number;
}

export function search(
  request: SearchRequest,
  signal?: AbortSignal,
): Promise<SearchResult> {
  return get<SearchResult>(
    "/search",
    { q: request.q, affix: request.affix, size: request.size },
    signal,
  );
}

/**
 * The affix a suffix query is asking about, or nothing.
 *
 * `*nā` is a question about the ending *-nā*, and the two-group split needs to
 * know that. A prefix or infix query is not asking about an affix in the same
 * way, so it gets no split rather than a wrong one.
 */
export function affixOf(query: string): string | undefined {
  const term = query.trim().split(/\s+/)[0] ?? "";
  const suffix = /^\*([^*\s]+)$/.exec(term);
  if (suffix?.[1]) return `-${suffix[1]}`;
  const prefix = /^([^*\s]+)\*$/.exec(term);
  if (prefix?.[1]) return `${prefix[1]}-`;
  return undefined;
}

/** One line a word was written in, and where it comes from. */
export interface Citation {
  document_id: string;
  author: string | null;
  title: string | null;
  century: number | null;
  line: string;
}

export interface WordDetail {
  id: string;
  index: string;
  word: WordType & { counts_by_century?: Record<string, number> };
  /** Every reading of the spelling. مرد is *mard* and *mord*; never merged. */
  readings: WordType[];
  citations: Citation[];
}

export function word(id: string, signal?: AbortSignal): Promise<WordDetail> {
  return get<WordDetail>(
    `/word/${encodeURIComponent(id)}`,
    { index: "word_types", citations: 6 },
    signal,
  );
}
