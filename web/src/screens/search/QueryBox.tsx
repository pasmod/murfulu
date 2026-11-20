/**
 * The one thing this screen asks for.
 *
 * **Two ways in, one language.** The builder composes a query for a reader who
 * does not want to learn a syntax; the box's own suggestions show every form
 * the language takes. Both write into this box, and the box is still what
 * runs. See Builder.tsx for why that is not a *simple mode* beside an
 * *advanced* one.
 *
 * **The examples are what the box suggests.** They were a table behind an ⓘ
 * beside the label until 2026-11-20, when the project lead asked for them to
 * open under the box the way a search engine's suggestions do: stepping into
 * the empty box shows them all, typing narrows them, and each carries a line
 * of Persian saying what it finds. A reader learns the syntax where they are
 * already looking, and a pick runs it.
 *
 * docs/FRONTEND.md still asks every empty state to carry a working example.
 * The input's placeholder is `*نا` — a query that runs as typed — so the empty
 * screen still shows one, and the rest are one press away.
 *
 * The input is left in the reader's own direction — Persian typed into it is
 * Persian, `*nā` is Latin — so it declares `dir="auto"` rather than forcing
 * either. Syntax *shown* is the opposite case: an example is isolated left to
 * right, exactly as it must be typed.
 */

import { useEffect, useState } from "react";

import { type Source, type Suggestion, Suggest } from "../../suggest/Suggest";
import { textSource, wordSource } from "../../suggest/sources";
import { Builder } from "./Builder";
import styles from "./QueryBox.module.css";
import { examplesFor } from "./syntax";
import { complete, typing, wanted } from "./typing";

/** A suggestion for the box: what it shows, and the whole query it makes. */
interface TermItem extends Suggestion {
  query: string;
}

/** The examples that fit what is typed, each with what it finds. */
function examples(text: string): TermItem[] {
  return examplesFor(text).map((one) => ({
    key: `example:${one.query}`,
    text: `${one.query}، ${one.hint}`,
    view: (
      <>
        {/* Syntax as it must be typed: left to right, isolated. */}
        <span className={styles.example} dir="ltr">
          {one.query}
        </span>
        <span className={styles.hint}>{one.hint}</span>
      </>
    ),
    query: one.query,
  }));
}

/**
 * Only first readings: the search matches a Latin word against a reading's
 * first form, so *Kenār*, کنار's second reading, would find nothing here.
 */
const WORDS = wordSource({ primary: true });
const AUTHORS = textSource(["author"]);

/** What the last term can be finished with. */
const TERMS: Source<TermItem> = async (text, signal) => {
  const at = typing(text);
  const want = at ? wanted(at.term) : null;
  if (!at || !want) return [];
  if (want.kind === "author") {
    const found = await AUTHORS(want.text, signal);
    return found.map((one) => ({
      ...one,
      query: complete(at, "author", one.found.query),
    }));
  }
  const found = await WORDS(want.text, signal);
  return found.map((one) => ({ ...one, query: complete(at, "word", one.word.value) }));
};

/** How long fitting examples wait for the words before they are shown alone. */
const PATIENCE = 1200;

/**
 * The examples that fit, then the words or authors that finish the last term.
 * An empty box asks the API nothing: its suggestions are the examples alone.
 */
const SUGGESTIONS: Source<TermItem> = async (text, signal) => {
  const shown = examples(text);
  if (!text.trim()) return shown;
  // The words and authors come from the API, the examples from here. A word
  // bank that fails, or is slow, must not take the examples down with it:
  // where some example fits, the words get {@link PATIENCE} ms to come.
  let terms: TermItem[] = [];
  try {
    const asked = Promise.resolve(TERMS(text, signal));
    // Settled after the wait is over, it has nobody left to tell.
    asked.catch(() => undefined);
    terms = shown.length
      ? await Promise.race([
          asked,
          new Promise<TermItem[]>((done) => window.setTimeout(() => done([]), PATIENCE)),
        ])
      : await asked;
  } catch (reason) {
    if (signal.aborted) throw reason;
  }
  // «author:فرد» finds the example «author:فردوسی» and the author as well;
  // the author is said once, as an author, with the number of texts.
  const finished = new Set(terms.map((one) => one.query));
  return [...shown.filter((one) => !finished.has(one.query)), ...terms];
};

export interface QueryBoxProps {
  value: string;
  onSearch: (query: string) => void;
  busy?: boolean;
}

export function QueryBox({ value, onSearch, busy = false }: QueryBoxProps) {
  const [draft, setDraft] = useState(value);
  // The query can change without the box changing it — a facet writes one,
  // and the Back button restores one. Seeding the draft once left the box
  // showing the old query while the address and the results had moved on, so
  // a facet narrowed the search and never showed the reader the syntax it had
  // written, which is the whole reason facets are links here.
  //
  // In an effect rather than adjusted during the render: the router navigates
  // inside a transition, and a render-time adjustment made during one can be
  // discarded when the transition replays. See the note in Explain.tsx, where
  // a browser test caught it.
  useEffect(() => setDraft(value), [value]);

  return (
    <form
      className={styles.box}
      role="search"
      onSubmit={(event) => {
        event.preventDefault();
        onSearch(draft.trim());
      }}
    >
      <label className={styles.label} htmlFor="query">
        جست‌وجوی واژه
      </label>

      <div className={styles.row}>
        {/* Stepping in shows the examples; typing narrows them and adds what
            finishes the last term: a word of the bank, or an author after
            `author:`. Taking one runs the search, as Enter on what was typed
            would. */}
        <Suggest
          id="query"
          name="query"
          className={styles.input}
          type="search"
          dir="auto"
          spellCheck={false}
          placeholder="*نا"
          value={draft}
          onChange={setDraft}
          source={SUGGESTIONS}
          atEndOnly
          openOnFocus
          listLabel="نمونه‌ها، واژه‌ها و نویسندگان"
          onPick={(one) => {
            setDraft(one.query);
            onSearch(one.query);
          }}
        />
        <button className={styles.submit} type="submit" disabled={busy}>
          {busy ? "در حال جست‌وجو" : "جست‌وجو"}
        </button>
      </div>

      {/* The filters, open. They write into the box and never run it: a
          control changed mid-thought should not fire a search on every
          keystroke, and the reader presses جست‌وجو when the query says what
          they meant. */}
      <Builder query={draft} searched={value} onChange={setDraft} />
    </form>
  );
}
