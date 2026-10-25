/**
 * The one thing this screen asks for.
 *
 * **Two ways in, one language.** The builder composes a query for a reader who
 * does not want to learn a syntax; the reference lists every form the language
 * takes. Both write into this box, and the box is still what runs. See
 * Builder.tsx for why that is not a *simple mode* beside an *advanced* one.
 *
 * **The loose row of example chips is gone, and nothing was lost with it.**
 * Four real queries used to sit under the box, unfolded. Every one of them —
 * `*nā`, `type:karnam`, `count:1`, `stem2:gu` — is already a row inside
 * راهنمای نحو, so they were a duplicate of its opening lines shown twice. They
 * also read as buttons without being controls the reader had asked for, which
 * the project lead raised on 2026-08-18: *the information about how to search
 * feels like a button; it should be a folded box*. It now is one, and it is
 * the box that was already there rather than a third beside it.
 *
 * docs/FRONTEND.md still asks every empty state to carry a working example.
 * The input's placeholder is `*نا` — a query that runs as typed — so the empty
 * screen still shows one; what it no longer does is show four.
 *
 * The input is left in the reader's own direction — Persian typed into it is
 * Persian, `*nā` is Latin — so it declares `dir="auto"` rather than forcing
 * either. Syntax *shown* is the opposite case, and Reference.tsx isolates it
 * left to right, exactly as it must be typed.
 */

import { useEffect, useState } from "react";

import { Builder } from "./Builder";
import { Reference } from "./Reference";
import styles from "./QueryBox.module.css";

export interface QueryBoxProps {
  value: string;
  onSearch: (query: string) => void;
  busy?: boolean;
}

export function QueryBox({ value, onSearch, busy = false }: QueryBoxProps) {
  const [draft, setDraft] = useState(value);
  /** Whether the syntax guide is open. Closed until the ⓘ is pressed. */
  const [guide, setGuide] = useState(false);
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
      {/* The label, and the ⓘ that opens the syntax guide beside it. */}
      <div className={styles.labelRow}>
        <label className={styles.label} htmlFor="query">
          جست‌وجوی واژه
        </label>
        <button
          type="button"
          className={styles.guide}
          aria-expanded={guide}
          aria-controls="syntax-guide"
          aria-label="راهنمای نحو"
          onClick={() => setGuide((was) => !was)}
        >
          ⓘ
        </button>
      </div>

      <div className={styles.row}>
        <input
          id="query"
          name="query"
          className={styles.input}
          type="search"
          dir="auto"
          autoComplete="off"
          spellCheck={false}
          placeholder="*نا"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        <button className={styles.submit} type="submit" disabled={busy}>
          {busy ? "در حال جست‌وجو" : "جست‌وجو"}
        </button>
      </div>

      {/* The builder writes into the draft and does not run it: a control
          changed mid-thought should not fire a search on every keystroke, and
          the reader presses جست‌وجو when the query says what they meant. */}
      {guide ? (
        <div id="syntax-guide">
          <Reference
            onPick={(query) => {
              setDraft(query);
              onSearch(query);
              setGuide(false);
            }}
          />
        </div>
      ) : null}

      {/* The filters, open. They write into the box and never run it. */}
      <Builder query={draft} onChange={setDraft} />
    </form>
  );
}
