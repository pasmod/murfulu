/**
 * One word class: the tile that chooses it, and the words behind it.
 *
 * **The class is what the reader chooses; the words are what they get after
 * choosing.** رفتن at depth 2 answers with 660 words in 8 classes, per
 * reading — so the screen used to open sixteen groups at twenty rows each and
 * hand back a scroll of 320 rows with the headings buried in it. The
 * categories were there and nobody could use them.
 *
 * **The tiles stay put when one is opened.** They are a grid, and the words
 * appear *below the whole grid* rather than inside the tile. The first attempt
 * let the opened tile span the grid, which pushed the other five classes below
 * a screenful of words — choosing one class hid the rest, which is the fault
 * being fixed rather than a smaller version of it. So `Build` owns which class
 * is open and renders the two parts apart.
 *
 * **A tile looks like a control, and a word row does not.** Both used to be
 * the same shape: a two-line block under a hairline. Nothing told a reader
 * which was a choice and which was content, which the project lead reported on
 * 2026-08-18 as *not visually clear what is a category and what is examples*.
 * A surface and a border is a different shape, not merely different text.
 *
 * **The explanation is written out, not put in a tooltip.** It used to be a
 * `Term`, and a `Term` is a button; a button inside the button that opens the
 * class is invalid and unreachable by keyboard. The folded grid is also
 * exactly where a reader decides what کارنام means to them.
 *
 * **Nothing is hidden, only folded.** Measured at 375px, بلند at depth 2
 * rendered 3,185 rows and 588,102px of page — 724 phone screens. An opened
 * class still starts at its first rows and says on the control how many it
 * holds back: an absent word is ranked down, never dropped.
 */

import type { BuiltForm } from "../../api/generate";
import { Num } from "../../text/Num";
import styles from "./Build.module.css";
import { FormRow } from "./FormRow";

/**
 * How many rows an opened class starts with.
 *
 * Twenty is what a reader was asked to judge in the walkthrough — *read the
 * top twenty and say whether a writer would use any of them* — and it is
 * about a phone screen and a half, enough to see the shape of a class without
 * losing the grid above it.
 */
export const FIRST = 20;

export function ClassTile({
  name,
  explanation,
  traditional,
  count,
  open,
  panelId,
  onToggle,
}: {
  /** The class, in the project's own term. From the rule pack, never here. */
  name: React.ReactNode;
  /** The one line saying what the class is. From the rule pack. */
  explanation?: string;
  /** What traditional grammar calls it, where it has a name there. */
  traditional?: string;
  count: number;
  open: boolean;
  panelId: string;
  onToggle: () => void;
}) {
  return (
    <h3 className={styles.groupHeading}>
      <button
        type="button"
        className={styles.groupToggle}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={onToggle}
      >
        <span className={styles.groupName}>
          {name}
          <span className={styles.groupCount}>
            <Num value={count} />
          </span>
        </span>
        {/* What the class is, and what the reader was taught to call it.
            Both come from `/rules`; nothing Persian is written here. */}
        {explanation ? (
          <span className={styles.groupSays}>
            {explanation}
            {traditional ? (
              <span className={styles.groupTraditional}>{traditional}</span>
            ) : null}
          </span>
        ) : null}
      </button>
    </h3>
  );
}

export function ClassWords({
  forms,
  corpusVersion,
  panelId,
  whole,
  onWhole,
}: {
  forms: BuiltForm[];
  corpusVersion: string | null;
  panelId: string;
  whole: boolean;
  onWhole: () => void;
}) {
  const shown = whole ? forms : forms.slice(0, FIRST);
  const folded = forms.length - shown.length;

  return (
    <div id={panelId} className={styles.words}>
      <ul className={styles.forms}>
        {shown.map((form) => (
          <FormRow
            key={`${form.form_latin}:${form.depth}`}
            form={form}
            corpusVersion={corpusVersion}
          />
        ))}
      </ul>
      {folded > 0 ? (
        <button type="button" className={styles.more} onClick={onWhole}>
          <Num value={folded} /> واژهٔ دیگر در این گروه — نشان بده
        </button>
      ) : null}
    </div>
  );
}
