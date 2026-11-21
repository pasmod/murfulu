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
  /**
   * As written, with the short vowels of the bank's one reading, for display
   * only (2026-11-21). Only on a word the bank reads one way and the source
   * wrote without marks of its own, and only where it adds a mark.
   */
  fa_marked?: string;
  /** The counted spelling; null for what is not a counted word (« a number, a Latin name). */
  s: string | null;
  /** Punctuation written straight after it. */
  after?: string;
  /**
   * Ids of the readings this word's own harakat rule out, shown paler; only
   * on a word written with signs that rule one out (since 2026-11-14).
   */
  against?: string[];
  /**
   * The automatic Behnevis's reading of this word here, when a model is
   * configured (direction A, 2026-11-14): one reading, how sure, its level,
   * and the readings a reader may pick instead.
   */
  auto?: AutoReading;
}

export type Level = "sure" | "mid" | "unsure";

export interface AutoReading {
  latin: string;
  /**
   * The word as written with this reading's short vowels, for display only
   * (2026-11-21); absent where it would add no mark.
   */
  fa_marked?: string;
  /** 0–1: the model's estimate that this reading is right here. */
  confidence: number;
  level: Level;
  /** Where it came from: the bank, a choice among its readings, a guess from the letters… */
  source: string;
  /**
   * Readings to pick from, likeliest first, each with its estimate — or null
   * for an alternative offered without one (built from the bank's stems, or
   * a letter guess on an inflected form).
   */
  candidates: [string, number | null][];
  /**
   * The readings the bank or the function-word list holds: a pick of one
   * teaches the model; any other reading is a proposal for karbon.
   */
  known?: string[];
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
  /** The levels' lower edges when the automatic Behnevis is on; null when it is off. */
  behnevis?: { sure: number; mid: number } | null;
}

/** One reading marked wrong, as the review list shows it. */
export interface Marked {
  id: number;
  target_id: string | null;
  spelling_fa: string;
  /** The spelling with this reading's short vowels, for display only. */
  spelling_fa_marked?: string | null;
  latin: string;
  written: string | null;
  /** The word as written with this reading's short vowels, for display only. */
  written_marked?: string | null;
  document_id: string | null;
  unit: number | null;
  /** A proposal's line in its unit and place in the line (sent since 2026-11-14). */
  line?: number | null;
  word?: number | null;
  before?: string | null;
  after?: string | null;
  in_bank?: boolean | null;
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
  options: {
    spelling?: string;
    kind?: "wrong" | "proposed";
    document_id?: string;
    /** Only the units from … to, as the text's window holds them. */
    unit_from?: number;
    unit_to?: number;
    offset?: number;
    limit?: number;
  } = {},
  signal?: AbortSignal,
): Promise<MarkedPage> {
  return get<MarkedPage>(
    "/texts/marked",
    {
      spelling: options.spelling,
      kind: options.kind,
      document_id: options.document_id,
      unit_from: options.unit_from,
      unit_to: options.unit_to,
      offset: options.offset,
      limit: options.limit,
    },
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
  /**
   * The counted words before and after it in its line, as spelled: a pick is
   * a choice in context, and the model learns it with its neighbours.
   */
  before?: string | null;
  after?: string | null;
  /** The line in the unit and the word's place in it, to show a saved pick there. */
  line?: number;
  word?: number;
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

/** What the model had read where a reader proposes another reading. */
export interface Proposed {
  latin: string;
  /** Whether the proposed reading is one of the bank's for this spelling. */
  in_bank: boolean;
  model: AutoReading;
}

/**
 * Record that a reading is right for a word in this line — picked among the
 * readings or typed. A proposal for karbon, append-only; it changes nothing
 * here (direction A, 2026-11-14).
 */
export function proposeReading(
  spelling: string,
  proposed: Proposed,
  where: MarkedWhere,
): Promise<FeedbackOut> {
  return leave({
    category: "linguistic",
    target_type: "lexicon_entry",
    target_id: `${spelling}:${proposed.latin}`,
    verdict: "good",
    note: null,
    context: {
      screen: "texts",
      kind: "reading_here",
      spelling_fa: spelling,
      latin: proposed.latin,
      in_bank: proposed.in_bank,
      model_latin: proposed.model.latin,
      model_confidence: proposed.model.confidence,
      written: where.written,
      before: where.before ?? null,
      after: where.after ?? null,
      document_id: where.document_id,
      unit: where.unit,
      line: where.line ?? null,
      word: where.word ?? null,
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

// -- deciding a reading once for every like place (2026-11-21) ----------------

/** How far a decision reaches: everywhere, or after or before one word. */
export type Scope = "everywhere" | "after_word" | "before_word";

/** What a decision means: a choice among the bank's readings, its one reading doubted, or none. */
export type UnsureKind = "choice" | "one" | "missing";

/** A neighbour of a listed spelling: the word, its places beside it, and how many of those are unsure. */
export type Neighbour = [word: string, places: number, unsure: number];

/** One place where the spelling was left to a person, with its line. */
export interface UnsurePlace {
  document_id: string;
  unit: number;
  line: number;
  /** The word's place in the line, as the reading screen counts it. */
  word: number;
  heading: string;
  text: string;
}

/** A reading decided for every like place of a spelling, in force. */
export interface Decision {
  id: number;
  latin: string;
  scope: Scope;
  /** The word it follows or precedes, as written; null for everywhere. */
  scope_word: string | null;
  in_bank: boolean | null;
  created_at: string | null;
}

/** A spelling the reading screen often leaves to a person, as measured over the corpus. */
export interface UnsureSpelling {
  rank: number;
  /** The spelling as the model keys it. */
  spelling: string;
  /** Its most frequent written form. */
  written: string;
  /** All its running words in the corpus, and those left to a person. */
  places: number;
  unsure: number;
  kind: UnsureKind;
  /** The readings the bank or the function-word list holds: a decision of one is learned. */
  known: string[];
  /** The model's readings at the unsure places, and how often. */
  read_as: [string, number][];
  /** The readings the panel offered there, and how often. */
  offered: [string, number][];
  /** The words before it (it stands after them) and after it, most unsure places first. */
  before: Neighbour[];
  after: Neighbour[];
  examples: UnsurePlace[];
  /** The marked corpus read against its readings; null where the editions never marked it. */
  marked?: { fitted: number; best: number; none: number; reading: string | null } | null;
  decided?: Decision[];
}

export interface UnsurePage {
  meta: {
    corpus_version: string;
    words: number;
    unsure_words: number;
    metre: boolean;
    measured: string;
  };
  total: number;
  offset: number;
  size: number;
  spellings: UnsureSpelling[];
}

/** One page of the most frequent unsure spellings, the most places first. */
export function unsureSpellings(
  options: { kind?: UnsureKind; offset?: number; size?: number } = {},
  signal?: AbortSignal,
): Promise<UnsurePage> {
  return get<UnsurePage>(
    "/texts/unsure",
    { kind: options.kind, offset: options.offset, size: options.size },
    signal,
  );
}

export interface UnsureOne {
  spelling: string;
  /** Its entry in the list, or null when it is not among the measured spellings. */
  listed: UnsureSpelling | null;
  decided: Decision[];
}

/** One spelling's place in the list, if any, and the readings decided for it. */
export function unsureSpelling(spelling: string, signal?: AbortSignal): Promise<UnsureOne> {
  return get<UnsureOne>(`/texts/unsure/${encodeURIComponent(spelling)}`, {}, signal);
}

/** A decision as it is sent: the reading, how far it reaches, and whether the bank holds it. */
export interface Deciding {
  latin: string;
  in_bank: boolean;
  scope: Scope;
  /** The word it follows or precedes, as written; for everywhere, none. */
  scope_word: string | null;
  /** What the model had read, where the decision was made from a line. */
  model?: AutoReading;
}

/**
 * Record that a spelling reads so wherever it stands, or after or before one
 * word. Append-only, like a pick; the model learns it at its next build,
 * when the bank holds the reading, and karbon is asked for it otherwise.
 */
export function decideReading(
  spelling: string,
  decision: Deciding,
  where: Partial<MarkedWhere> & { corpus_version: string | null },
): Promise<FeedbackOut> {
  return leave({
    category: "linguistic",
    target_type: "lexicon_entry",
    target_id: `${spelling}:${decision.latin}`,
    verdict: "good",
    note: null,
    context: {
      screen: "texts",
      kind: "reading_decided",
      spelling_fa: spelling,
      latin: decision.latin,
      in_bank: decision.in_bank,
      scope: decision.scope,
      scope_word: decision.scope === "everywhere" ? null : decision.scope_word,
      withdrawn: false,
      model_latin: decision.model?.latin ?? null,
      model_confidence: decision.model?.confidence ?? null,
      written: where.written ?? null,
      before: where.before ?? null,
      after: where.after ?? null,
      document_id: where.document_id ?? null,
      unit: where.unit ?? null,
      line: where.line ?? null,
      word: where.word ?? null,
      heading: where.heading ?? null,
    },
    corpus_version: where.corpus_version,
  });
}

/** Take a decision back: the model reads those places itself again. Append-only too. */
export function withdrawDecision(
  spelling: string,
  decision: Decision,
  corpusVersion: string | null,
): Promise<FeedbackOut> {
  return leave({
    category: "linguistic",
    target_type: "lexicon_entry",
    target_id: `${spelling}:${decision.latin}`,
    verdict: "unsure",
    note: null,
    context: {
      screen: "texts",
      kind: "reading_decided",
      spelling_fa: spelling,
      latin: decision.latin,
      scope: decision.scope,
      scope_word: decision.scope_word,
      withdrawn: true,
      replaces: decision.id,
    },
    corpus_version: corpusVersion,
  });
}
