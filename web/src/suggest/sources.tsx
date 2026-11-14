/**
 * What the boxes suggest, and how each suggestion looks.
 *
 * Two kinds, one per thing the app searches. **A word** from the bank —
 * the spelling with its readings when Persian was typed, the reading with its
 * spellings when Latin was — for every box that takes a word. **A text or a
 * group of texts** — an author, a work, a section, one text — for the reading
 * screen. Each says what it is at the end of its line, so «حافظ» the author
 * and «حافظ · غزلیات» the work are not two of the same.
 */

import {
  type TextSuggestion,
  type WordSuggestion,
  suggestTexts,
  suggestWords,
} from "../api/suggest";
import { Latin } from "../text/Latin";
import { persianNumber } from "../text/numbers";
import type { Source, Suggestion } from "./Suggest";
import styles from "./Suggest.module.css";

/** Readings shown beside a spelling; the rest are behind «…». */
const READINGS_SHOWN = 3;

export interface WordItem extends Suggestion {
  word: WordSuggestion;
}

function wordView(word: WordSuggestion, script: "fa" | "latin") {
  if (script === "fa") {
    const shown = word.latin.slice(0, READINGS_SHOWN);
    return (
      <>
        <span className={styles.main}>{word.value}</span>
        <span className={styles.aside}>
          {shown.map((one, at) => (
            <span key={one}>
              {at > 0 ? "، " : null}
              <Latin>{one}</Latin>
            </span>
          ))}
          {word.latin.length > shown.length ? "، …" : null}
        </span>
      </>
    );
  }
  return (
    <>
      <Latin className={styles.main}>{word.value}</Latin>
      <span className={styles.aside}>{word.spellings.join("، ")}</span>
    </>
  );
}

/**
 * Words of the bank. `builds` keeps to the words the rules build from;
 * `primary` to a word's first reading, for a box that finds no other.
 */
export function wordSource(
  options: { builds?: boolean; primary?: boolean } = {},
): Source<WordItem> {
  return async (text, signal) => {
    const answer = await suggestWords(text, options, signal);
    const script = answer.script === "latin" ? "latin" : "fa";
    return (answer.suggestions ?? []).map((word) => ({
      key: word.value,
      text:
        script === "fa"
          ? `${word.value}، ${word.latin.join("، ")}`
          : `${word.value}، ${word.spellings.join("، ")}`,
      view: wordView(word, script),
      word,
    }));
  };
}

const KINDS: Record<TextSuggestion["kind"], string> = {
  author: "نویسنده",
  work: "کتاب",
  section: "بخش",
  text: "متن",
};

export interface TextItem extends Suggestion {
  found: TextSuggestion;
}

/** Authors, works, sections and single texts of the corpus. */
export function textSource(kinds?: TextSuggestion["kind"][]): Source<TextItem> {
  return async (text, signal) => {
    const answer = await suggestTexts(text, signal);
    return (answer.suggestions ?? [])
      .filter((found) => !kinds || kinds.includes(found.kind))
      .map((found) => {
        const kind =
          found.kind === "text"
            ? KINDS.text
            : `${KINDS[found.kind]}، ${persianNumber(found.texts)} متن`;
        return {
          key: found.document_id ?? `${found.kind}:${found.query}`,
          text: `${found.parts.join("، ")} (${kind})`,
          view: (
            <>
              <span className={styles.clamp}>{found.parts.join(" · ")}</span>
              <span className={styles.kind}>{kind}</span>
            </>
          ),
          found,
        };
      });
  };
}
