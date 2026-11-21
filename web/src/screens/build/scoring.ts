/**
 * The two values' explanations, filters and sorts — shared by the row
 * (`Score.tsx`) and the table (`Build.tsx`).
 *
 * **The project lead's choice of 2026-11-21 (second)**: how well a word is
 * built (0 to 100, from its rules alone) and what the corpus says about it,
 * kept apart. The single score of the same day capped a word the corpus lacks
 * at 30, so good new words sank — the very words the project looks for. The
 * API decides both (`murfulu/scoring/score.py`); this file only explains,
 * filters and sorts. Unconfirmed until the linguist rules (L36).
 */

import type { Attestation, FormScore } from "../../api/generate";

/**
 * What the filters, sorts and cells read of a row: its two values and its
 * corpus answer. A built word is one; so is a compound (the compound page,
 * 2026-11-21), whose build value may be null where its half was not measured.
 */
export interface Scored {
  score?: Omit<FormScore, "build"> & { build: number | null };
  attestation: Pick<
    Attestation,
    "level" | "doc_count" | "function_word" | "headword_homograph"
  > | null;
}

/** The build value's ceiling, as the API sets it. Said, never computed here. */
export const BUILD_MAX = 100;

/** What «ساخت» means, in the ⓘ beside its filter. */
export const BUILD_SAYS =
  "این عدد، از ۰ تا ۱۰۰، می‌گوید واژه چقدر خوب ساخته شده است. فقط به دستوری بستگی دارد که واژه را ساخته: این دستور از واژه‌هایی که می‌سازد، چند تا را در پیکره داریم. برای واژه‌ای که در پیکره هست و واژه‌ای که نیست، یکسان حساب می‌شود.";

/** What «در پیکره» means, in the ⓘ beside its filter. */
export const CORPUS_SAYS =
  "در چند متن از پیکره، با همین معنا، آمده است. پیکره بیشتر شعر کهن است؛ پس واژه‌ای که در آن نیامده، شاید امروز به کار برود یا واژهٔ تازهٔ خوبی باشد.";

/** What the candidates view shows, said above its rows. */
export const CANDIDATES_SAY =
  "واژه‌هایی که در پیکره نیامده‌اند، خوش‌ساخت‌ترین‌ها اول. شاید واژهٔ تازهٔ خوبی میانشان باشد.";

export interface Filter {
  key: string;
  label: string;
  keeps: (form: Scored) => boolean;
}

/**
 * Whether the API sent the two values. The API of the morning of 2026-11-21
 * sent `{value, corpus: number, rule}`, and reading its numeric `corpus` as
 * the new answer put attested words among the candidates (the review of
 * 2026-11-21); such a form is read from its attestation instead.
 */
export function hasValues(form: Scored): boolean {
  const score = form.score as Partial<FormScore> | undefined;
  return (
    !!score &&
    // A number, or null where a compound's half was not measured (the
    // compound page, 2026-11-21): its corpus answer is still the API's.
    (typeof score.build === "number" || score.build === null) &&
    (score.corpus === null || typeof score.corpus === "string")
  );
}

const build = (form: Scored) => (hasValues(form) ? form.score!.build : null);

/** What the corpus says, from the API's answer, or from the attestation of an older API. */
export function corpusKind(form: Scored): FormScore["corpus"] {
  if (hasValues(form)) return form.score!.corpus;
  const found = form.attestation;
  if (!found) return null;
  if (found.level === "none") return "none";
  if (found.function_word || found.headword_homograph) return "other";
  return found.level === "reading" ? "reading" : "letters";
}

/** Build-value ranges. A word with no value is kept only by «همه». */
export const BUILD_RANGES: Filter[] = [
  { key: "all", label: "همه", keeps: () => true },
  { key: "high", label: "۷۰ و بیشتر", keeps: (f) => (build(f) ?? -1) >= 70 },
  {
    key: "middle",
    label: "۴۰ تا ۶۹",
    keeps: (f) => {
      const v = build(f);
      return v !== null && v >= 40 && v < 70;
    },
  },
  {
    key: "low",
    label: "زیر ۴۰",
    keeps: (f) => {
      const v = build(f);
      return v !== null && v < 40;
    },
  },
];

/** What the corpus says, kept as distinct as the API keeps it. */
export const IN_CORPUS: Filter[] = [
  { key: "all", label: "همه", keeps: () => true },
  {
    key: "reading",
    label: "با همین معنا آمده",
    keeps: (f) => corpusKind(f) === "reading",
  },
  {
    key: "letters",
    label: "فقط همین حروف",
    keeps: (f) => corpusKind(f) === "letters" || corpusKind(f) === "other",
  },
  {
    key: "none",
    label: "نیامده",
    keeps: (f) => corpusKind(f) === "none",
  },
];

/**
 * The candidates for new words: not in the corpus at all.
 *
 * **Not the letters-only words** (DECISIONS 2026-11-21): on رفتن the view
 * opened on رفته, its letters in 4,796 texts, and on another word's letters
 * such as روه — words that are written already, under this reading or
 * another, and so cannot be offered as new.
 */
export function isCandidate(form: Scored): boolean {
  return corpusKind(form) === "none";
}

export type SortKey = "build" | "texts" | "alpha";

/** How strongly the corpus speaks for a word, as `CORPUS_ORDER` in score.py. */
const CORPUS_ORDER: Record<string, number> = {
  reading: 0,
  letters: 1,
  other: 2,
  none: 3,
};

/**
 * The texts a word's own count rests on — zero where the count is another
 * word's (a function word, the bank's other headword).
 */
export function creditedTexts(form: Scored): number {
  const found = form.attestation;
  if (!found || found.function_word || found.headword_homograph) return 0;
  return found.doc_count;
}

/**
 * The default order's keys: how well built, then what the corpus says.
 *
 * **`order` in murfulu/scoring/score.py says the same**: steps 1 and 2 are
 * sorted here, a deep answer there. An older API sends no score, and every
 * form then ties here and the old order below decides, as it did before.
 */
export function buildOrder(form: Scored): number {
  if (!hasValues(form)) return 0;
  const score = form.score!;
  // No value ranks with the zeros, as the compound route ranks it.
  return -(score.build ?? 0) * 10 + (CORPUS_ORDER[score.corpus ?? ""] ?? 4);
}
