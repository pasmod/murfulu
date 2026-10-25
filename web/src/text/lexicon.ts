/**
 * What the interface calls karbon's dictionary, in one place.
 *
 * It was «فرهنگ» in twenty places across ten screens, and «فرهنگ» is also the
 * ordinary Persian word for *culture* — so the label beside «پیکره» and
 * «ساخته‌شده» never quite said which of the three a word came from. The
 * project lead settled it on 2026-08-16: **the dictionary is named after the
 * library that holds it**, «واژه‌نامهٔ کاربن».
 *
 * Kept here rather than written into each screen for the same reason
 * `persianCentury` is kept in `numbers.ts`: ten screens that each spell a name
 * out cannot be renamed, only re-spelled ten times, and the eleventh drifts.
 *
 * **Only karbon's dictionary is named this way.** Where the text means a
 * dictionary in general — «فرهنگِ سرواژه‌ها», a headword dictionary, in the
 * gap list — the ordinary word is still the right one and stays.
 *
 * Note for whoever raises it with the linguist: «کاربن» is also this project's
 * grammar term for a verb stem — کاربن یک، کاربن دو — so «واژه‌نامهٔ کاربن»
 * can be read for a moment as *the dictionary of stems*. It is the library's
 * own name, and the collision is recorded rather than worked around.
 */

/** karbon's dictionary. The one string this file exists for. */
export const LEXICON = "واژه‌نامهٔ کاربن";

/**
 * Where a word was found. A word can be in more than one population, and the
 * search rows and the facet panel have to agree on what to call each.
 */
export const POPULATION_LABEL: Record<string, string> = {
  corpus: "پیکره",
  lexicon: LEXICON,
  generated: "ساخته‌شده",
};

/**
 * The corpus has the letters and the dictionary has no entry for them — which
 * is the coverage gap itself, not an error and not a blank. Said the same way
 * on a search row and on a word screen.
 */
export const NO_READING = `خوانشی در ${LEXICON} نیست`;

/** The dictionary's own words, labelled as the dictionary's. */
export const FROM_LEXICON = `از ${LEXICON}:`;

/** A second pronunciation the dictionary itself lists — برنا is barnā and bornā. */
export const ALSO_WRITTEN = `${LEXICON} این خوانش را چنین هم نوشته است:`;

/**
 * The letters are, almost always, a function word — که, از, را — so the
 * corpus count is that word's and says nothing about this one. Said instead of
 * a number, never by hiding the row (rules/function_words.yaml). The adjective
 * *keh* was being shown with the conjunction's 609,699 occurrences.
 */
export const FUNCTION_WORD_HOMOGRAPH =
  "هم‌نویسهٔ یک واژهٔ دستوری: شمار پیکره از آنِ آن واژه است، پس گواهیِ این یکی نامعلوم است.";

/** The same, short enough for a row. */
export const FUNCTION_WORD_SHORT = "هم‌نویسهٔ واژهٔ دستوری — گواهی نامعلوم";

/** On the spelling's own document, which carries the count the readings do not. */
export const FUNCTION_WORD_LETTERS =
  "این املا در پیکره تقریباً همیشه یک واژهٔ دستوری است؛ این شمار از آنِ همان است.";

/** The dictionary's own doubt, which a reader is told rather than shielded from. */
export const NEEDS_REVIEW = `${LEXICON} این خوانش را بازبینی‌نشده نشان کرده است.`;

/**
 * The word was not found, so the screen has nothing to work from. Each screen
 * says what it therefore cannot do, because «نیست» alone leaves the reader to
 * guess whether they mistyped or whether the tool gave up.
 */
export function notFound(consequence: string): string {
  return `این واژه در ${LEXICON} نیست، پس ${consequence}`;
}

/**
 * Where karbon cuts a definition. Measured, not assumed: in the served v11
 * index the longest `definition_fa` is exactly 200 characters and 9,353 of
 * them sit at 199 or 200, which is the cut showing up as a spike.
 */
export const LEXICON_CUT = 199;

/**
 * True when the dictionary's text was cut off rather than finished.
 *
 * **The screens used to append «…» to every definition**, on the strength of
 * karbon cutting at 200 characters — but only 53.5% of the 17,471 definitions
 * in v11 are anywhere near that limit. The other 8,118 are whole sentences
 * that end in a full stop and their own citation, and marking them as
 * unfinished told the reader something false about the dictionary. فنا is one:
 * 90 characters, complete, and it was shown as «…(فهرست مخزن الادویه).» with
 * an ellipsis after the stop.
 */
export function wasCut(definition: string): boolean {
  return definition.length >= LEXICON_CUT;
}
