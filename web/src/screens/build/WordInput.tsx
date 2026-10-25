/**
 * The one thing this screen asks for: a word, and how deep to go.
 *
 * The example is real and clickable — docs/FRONTEND.md asks empty states to
 * carry one ready to click, and رفتن is the verb the whole project walks
 * through.
 */

import { useState } from "react";

import { Num } from "../../text/Num";
import styles from "./WordInput.module.css";

export interface WordInputProps {
  value: string;
  depth: number;
  depths: number[];
  busy: boolean;
  onBuild: (word: string, depth: number) => void;
}

/** Verbs the engine answers for. Checked against the API, never guessed. */
const EXAMPLES = ["رفتن", "گفتن", "دیدن", "بستن", "خواندن"];

export function WordInput({ value, depth, depths, busy, onBuild }: WordInputProps) {
  const [draft, setDraft] = useState(value);

  return (
    <form
      className={styles.box}
      onSubmit={(event) => {
        event.preventDefault();
        onBuild(draft.trim(), depth);
      }}
    >
      <label className={styles.label} htmlFor="word">
        واژه‌ای بنویسید
      </label>

      <div className={styles.row}>
        <input
          id="word"
          name="word"
          className={styles.input}
          dir="auto"
          autoComplete="off"
          placeholder="رفتن"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        <button className={styles.submit} type="submit" disabled={busy}>
          {busy ? "در حال ساخت" : "بساز"}
        </button>
      </div>

      <fieldset className={styles.depths}>
        <legend className={styles.legend}>چند گام</legend>
        {depths.map((step) => (
          <label key={step} className={styles.depth}>
            <input
              type="radio"
              name="depth"
              checked={step === depth}
              onChange={() => onBuild(draft.trim() || value, step)}
            />
            <Num value={step} />
          </label>
        ))}
      </fieldset>

      {/* Five, not one. Each is a real verb the engine answers for — checked
          against the running API on 2026-08-18, 38 words apiece at one step
          and 76 for رفتن. One example teaches that the box takes a word;
          five teach what kind of word, which is the thing a first-time
          reader does not know. */}
      {!value ? (
        <p className={styles.examples}>
          <span className={styles.examplesSays}>برای نمونه:</span>
          {EXAMPLES.map((word) => (
            <button
              key={word}
              type="button"
              className={styles.example}
              onClick={() => {
                setDraft(word);
                onBuild(word, depth);
              }}
            >
              {word}
            </button>
          ))}
        </p>
      ) : null}
    </form>
  );
}
