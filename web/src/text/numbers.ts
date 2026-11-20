/**
 * Persian numerals, settled in docs/FRONTEND.md.
 *
 * Formatting goes through `Intl` rather than a digit-swapping table, because a
 * number is more than its digits: Persian groups thousands with its own
 * separator and writes its own decimal mark, and a hand-rolled swap gets those
 * wrong the moment a figure passes a thousand — which every corpus count does.
 */

const PERSIAN = new Intl.NumberFormat("fa-IR");

/** A count, written in Persian numerals with Persian grouping. */
export function persianNumber(value: number): string {
  return PERSIAN.format(value);
}

/**
 * A century, written the way the corpus screens say it: «سدهٔ ۵».
 *
 * Kept here rather than in a component so the two screens that show centuries
 * cannot drift apart.
 */
export function persianCentury(century: number): string {
  return `سدهٔ ${persianNumber(century)}`;
}

/**
 * A range of centuries. One century is not written as a range.
 */
export function persianCenturyRange(first: number, last: number): string {
  if (first === last) {
    return persianCentury(first);
  }
  return `${persianCentury(first)} تا ${persianNumber(last)}`;
}

const PERSIAN_PERCENT = new Intl.NumberFormat("fa-IR", {
  style: "percent",
  maximumFractionDigits: 0,
});

/** A share in Persian numerals: ۸۶٪. */
export function persianPercent(value: number): string {
  return PERSIAN_PERCENT.format(value);
}

const LATIN_DIGIT = /[0-9]/g;
const OTHER_DIGIT = /[۰-۹٠-٩]/g;

/**
 * Digits written in Persian, one for one, with nothing grouped — for a number
 * that sits in a field the reader edits, where a separator would be one more
 * character in the way of the caret.
 */
export function persianDigits(text: string): string {
  return text.replace(LATIN_DIGIT, (digit) => String.fromCharCode(0x06f0 + Number(digit)));
}

/**
 * The other way: Persian and Arabic-Indic digits back to the ones a query is
 * written in. A reader types on whichever keyboard is up, and both are read.
 */
export function latinDigits(text: string): string {
  return text.replace(OTHER_DIGIT, (digit) => {
    const code = digit.charCodeAt(0);
    return String(code >= 0x06f0 ? code - 0x06f0 : code - 0x0660);
  });
}
