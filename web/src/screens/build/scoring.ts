/**
 * The score's explanation, its filters and its sorts — shared by the row
 * (`Score.tsx`) and the table (`Build.tsx`).
 *
 * **The project lead's choice of 2026-11-21**: one score from 0 to 100 in
 * place of the three levels of 2026-11-13, so the list can be sorted and
 * filtered. The API decides the score (`murfulu/scoring/score.py`); this file
 * only explains, filters and sorts. Unconfirmed until the linguist rules
 * (docs/FOR_THE_LINGUIST.md L36).
 */

import type { BuiltForm } from "../../api/generate";

/** The two parts' ceilings, as the API sets them. Said, never computed here. */
export const CORPUS_MAX = 70;
export const RULE_MAX = 30;

/**
 * What the score is, said once under the table and in the ⓘ beside its
 * column. It has to say that a low score is little evidence, not a wrong
 * word: the corpus is classical poetry (OPEN_QUESTIONS S33).
 */
export const SCORE_SAYS =
  "امتیاز از ۰ تا ۱۰۰ نشان می‌دهد چقدر شاهد برای این واژه داریم. تا ۷۰ امتیاز از پیکره می‌آید: واژه در چند متن و به همین معنا آمده است. تا ۳۰ امتیاز از دستوری که آن را ساخته: این دستور چند بار واژه‌ای ساخته که در پیکره هست. پیکره بیشتر شعر کهن است، پس امتیاز کم یعنی شاهد کم، نه واژهٔ نادرست.";

export interface Filter {
  key: string;
  label: string;
  keeps: (form: BuiltForm) => boolean;
}

const value = (form: BuiltForm) => form.score?.value ?? null;

/** Score ranges. A word with no score is kept only by «همه». */
export const SCORE_RANGES: Filter[] = [
  { key: "all", label: "همه", keeps: () => true },
  { key: "high", label: "۷۰ و بیشتر", keeps: (f) => (value(f) ?? -1) >= 70 },
  {
    key: "middle",
    label: "۴۰ تا ۶۹",
    keeps: (f) => {
      const v = value(f);
      return v !== null && v >= 40 && v < 70;
    },
  },
  {
    key: "low",
    label: "زیر ۴۰",
    keeps: (f) => {
      const v = value(f);
      return v !== null && v < 40;
    },
  },
];

/** Whether the corpus has the word. The letters alone count as having it. */
export const IN_CORPUS: Filter[] = [
  { key: "all", label: "همه", keeps: () => true },
  {
    key: "in",
    label: "در پیکره آمده",
    keeps: (f) => !!f.attestation && f.attestation.level !== "none",
  },
  {
    key: "out",
    label: "در پیکره نیامده",
    keeps: (f) => f.attestation?.level === "none",
  },
];

export type SortKey = "score" | "texts" | "alpha";

/**
 * The texts a word's own count rests on — zero where the count is another
 * word's (a function word, the bank's other headword).
 */
export function creditedTexts(form: BuiltForm): number {
  const found = form.attestation;
  if (!found || found.function_word || found.headword_homograph) return 0;
  return found.doc_count;
}

/**
 * Where a score sorts: highest first, and no score last.
 *
 * **`order` in murfulu/scoring/score.py says the same**: steps 1 and 2 are
 * sorted here, a deep answer there. An older API sends no score, and every
 * form then ties here and the old order below decides, as it did before.
 */
export function scoreOrder(form: BuiltForm): number {
  return -(value(form) ?? -1);
}
