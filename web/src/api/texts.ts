/**
 * Reading a text: finding one, the text word by word, and the readings marked
 * wrong.
 *
 * A reading is marked wrong through the feedback store (`leave` in
 * `feedback.ts`), as a linguistic verdict on a `lexicon_entry` — karbon's
 * data, which this project records and never fixes. Nothing here writes.
 */

import { get } from "./client";
import { leave, type FeedbackOut } from "./feedback";

/** A text as a search result: where it sits, not what it says. */
export interface TextHeading {
  document_id: string;
  author: string | null;
  work: string | null;
  /** The sections between the work and the text, outermost first. */
  section: string[];
  title: string | null;
  century: number | null;
}

export interface TextFound {
  q: string;
  total: number;
  offset: number;
  size: number;
  texts: TextHeading[];
  corpus_version: string | null;
}

/** One word as written, and the spelling the corpus counted it under. */
export interface TextWord {
  /** As written, harakat and all. */
  fa: string;
  /** The counted spelling; null for what is not a counted word (« a number, a Latin name). */
  s: string | null;
  /** Punctuation written straight after it. */
  after?: string;
}

export type LinePosition =
  | "first"
  | "second"
  | "band_first"
  | "band_second"
  | "free"
  | "prose"
  | "note"
  | null;

export interface TextLine {
  position: LinePosition;
  /** A counted line's words. */
  words?: TextWord[];
  /** A note's text, which was never counted and is not split into words. */
  text?: string;
}

export interface TextUnit {
  /** Its place in the whole text, from 0. */
  index: number;
  /** Its number among the counted units, as the reader sees it; null for a note. */
  number: number | null;
  /** `line` is a text stored before units existed (corpus v16 and older). */
  kind: "couplet" | "half" | "prose" | "note" | "line";
  lines: TextLine[];
}

export interface Reading {
  /** The word type's id, `spelling:latin` — what a mark names. */
  id: string;
  latin: string;
  latin_variants: string[];
  /** The linguist's group names. */
  groups: string[];
  definition_fa: string | null;
}

export interface WordKnown {
  /** Every reading the bank has, in alphabetical order. None is proposed. */
  readings: Reading[];
  /** The spelling's corpus counts — the letters', whichever word they are. */
  total_count: number | null;
  doc_count: number | null;
  function_word: string | null;
}

export interface Text extends TextHeading {
  source_id: string | null;
  /** What the source is called, in Persian: «گنجور». */
  source_name_fa?: string | null;
  corpus_version: string | null;
  lexicon_snapshot_id: string | null;
  units_total: number;
  start: number;
  limit: number;
  units: TextUnit[];
  words: Record<string, WordKnown>;
}

/** One reading marked wrong, as the review list shows it. */
export interface Marked {
  id: number;
  target_id: string | null;
  spelling_fa: string;
  latin: string;
  written: string | null;
  document_id: string | null;
  unit: number | null;
  heading: string | null;
  note: string | null;
  corpus_version: string | null;
  created_at: string | null;
}

/** How many units one read asks for; a longer text is read in windows. */
export const WINDOW = 200;

export function findTexts(
  q: string,
  offset = 0,
  signal?: AbortSignal,
): Promise<TextFound> {
  return get<TextFound>("/texts", { q, offset, size: 20 }, signal);
}

export function readText(
  documentId: string,
  start = 0,
  signal?: AbortSignal,
): Promise<Text> {
  return get<Text>(
    `/texts/${encodeURIComponent(documentId)}`,
    { start, limit: WINDOW },
    signal,
  );
}

export interface MarkedPage {
  total: number;
  offset: number;
  returned: number;
  marked: Marked[];
}

/** One page of the marks, newest first — or every mark on one spelling. */
export function marked(
  options: { spelling?: string; offset?: number; limit?: number } = {},
  signal?: AbortSignal,
): Promise<MarkedPage> {
  return get<MarkedPage>(
    "/texts/marked",
    { spelling: options.spelling, offset: options.offset, limit: options.limit },
    signal,
  );
}

/** Where a word stood when its reading was marked. */
export interface MarkedWhere {
  document_id: string;
  unit: number;
  heading: string;
  written: string;
  corpus_version: string | null;
}

/** Record that one reading of one spelling is wrong. Append-only. */
export function markWrong(
  spelling: string,
  reading: Reading,
  where: MarkedWhere,
  note: string,
): Promise<FeedbackOut> {
  return leave({
    category: "linguistic",
    target_type: "lexicon_entry",
    target_id: reading.id,
    verdict: "wrong",
    note: note.trim() || null,
    context: {
      screen: "texts",
      spelling_fa: spelling,
      latin: reading.latin,
      written: where.written,
      document_id: where.document_id,
      unit: where.unit,
      heading: where.heading,
    },
    corpus_version: where.corpus_version,
  });
}

/** The source line's words, in order: author, work, sections, title. */
export function headingOf(text: TextHeading): string[] {
  return [text.author, text.work, ...text.section, text.title].filter(
    (part): part is string => Boolean(part),
  );
}
