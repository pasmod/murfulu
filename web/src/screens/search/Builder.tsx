/**
 * The search, built rather than typed.
 *
 * The screen had one way in: a text box and four clickable examples. That
 * teaches the reader who is willing to learn a syntax, and the facet panel
 * teaches the rest — but the facets only appear *after* a search has worked,
 * so neither helps the writer of J1, who has a German word and no idea that
 * `type:` exists. Ten of the fourteen things the language can do were not
 * named anywhere in the interface.
 *
 * **It writes the query rather than replacing it.** Every control composes the
 * same string into the same box, and the box stays the single input: one
 * language, one address bar, one thing to paste to a colleague. This is the
 * decision Facets.tsx already made for narrowing — *a facet writes the query
 * it stands for and the box shows it* — moved to before the first search. A
 * separate simple mode would have been two ways to say one thing, and the
 * expert reading over the writer's shoulder would have had nothing to read.
 *
 * **Terms it has no control for are left alone.** A reader who typed `tag:ja`
 * and then picks a century keeps the tag; see `setTerm` in syntax.ts.
 *
 * The word classes are fetched, never listed here: their Persian belongs to
 * `rules/word_classes.yaml`, and a component that spelled کارنام out itself
 * would be inventing linguistics. If the API is a version behind, that one
 * control is absent and the rest still work.
 */

import { useEffect, useState } from "react";

import { wordClasses, type WordClass } from "../../api/generate";
import { POPULATION_CHOICE } from "../../text/lexicon";
import { NumberRows } from "./NumberRows";
import {
  PATTERNS,
  POPULATIONS,
  getPattern,
  getTerm,
  setPattern,
  setTerm,
} from "./syntax";
import styles from "./Builder.module.css";

export interface BuilderProps {
  query: string;
  /** The search the screen is showing, which the address holds. */
  searched?: string;
  onChange: (next: string) => void;
}

/** Which pattern the query in the box is written in, so the box can lead. */
function patternMode(query: string): { key: string; value: string } {
  const pattern = getPattern(query);
  for (const one of PATTERNS) {
    const value = one.read(pattern);
    if (value !== null) return { key: one.key, value };
  }
  return { key: PATTERNS[0]!.key, value: "" };
}

/**
 * A class as the list names it: the linguist's term, and the traditional one
 * after it in brackets — «کارنام (اسم مصدر)». The project lead asked for both
 * on 2026-11-20: a reader who knows only the school grammar finds the class by
 * the name they know, and learns the new one beside it. Not repeated where the
 * label already is the traditional term (the vocative, which has no coined
 * one), and left off where the traditional grammar has no name.
 */
function classLabel(one: WordClass): string {
  const label = one.label_fa ?? one.name;
  if (one.label_is_traditional || !one.traditional_fa) return label;
  return `${label} (${one.traditional_fa})`;
}

export function Builder({ query, searched, onChange }: BuilderProps) {
  const read = patternMode(query);
  // The mode is held rather than derived: a reader who picks «با این شروع شود»
  // before typing anything has written nothing into the query yet, and a
  // derived mode would snap back to the default under them.
  const [mode, setMode] = useState(read.key);
  const [classes, setClasses] = useState<WordClass[]>([]);
  const [opened, setOpened] = useState(false);
  /**
   * Whether the class list has been asked for and answered.
   *
   * It separates *not asked yet* from *asked and there are none*, and the two
   * must look different: before the ask the control has to be on the screen so
   * a reader can reach it, and after an empty answer it has to leave — an API
   * a version behind serves no classes, and this control losing itself is what
   * keeps it from taking the screen down with it.
   */
  const [answered, setAnswered] = useState(false);

  // **Not on mount.** The screen's rule is that it asks the API nothing until
  // there is something to ask about — a test says so, and it caught this: the
  // word classes were fetched when the screen loaded, so every visit to the
  // search page called `/rules` for a panel that is folded shut and that most
  // readers never open.
  useEffect(() => {
    if (!opened) return;
    const stop = new AbortController();
    wordClasses(stop.signal)
      .then((found) => {
        setClasses(found);
        setAnswered(true);
      })
      .catch(() => {
        setClasses([]);
        setAnswered(true);
      });
    return () => stop.abort();
  }, [opened]);

  useEffect(() => setMode(read.key), [read.key]);

  const pattern = PATTERNS.find((one) => one.key === mode) ?? PATTERNS[0]!;
  return (
    /* **Open, not folded.** The filters were behind «ساختن جست‌وجو» and a
       reader had to know to press it. The project lead asked for them visible
       on 2026-08-18.

       **The word classes are still fetched late.** They are the one control
       needing the API, and `docs/DECISIONS.md` holds *the screen asks nothing
       until there is a query* with a test behind it. So the list is asked for
       when a reader first reaches that one select — on focus or on a press —
       not when the screen loads. The one thing asked on arrival is the
       corpus's range of centuries, for the filled century fields (see
       NumberRows.tsx); everything else here is local.

       **Every row is a label and one `controls` span**, and every select sits
       in a `picker` that draws the arrow. Both are for the eye rather than the
       reader: the span holds a row's controls in the second column so a row
       with three of them begins where a row with one does, and the picker
       replaces the arrow that `appearance: none` takes away. See the CSS. */
    <div className={styles.builder}>
      <div className={styles.rows}>
        <p className={styles.row}>
          <label className={styles.label} htmlFor="build-pattern">
            الگوی حرفی
          </label>
          <span className={styles.controls}>
            <span className={styles.picker}>
              <select
                className={styles.select}
                id="build-pattern-mode"
                aria-label="جور الگو"
                value={mode}
                onChange={(event) => {
                  setMode(event.target.value);
                  const next =
                    PATTERNS.find((one) => one.key === event.target.value) ??
                    PATTERNS[0]!;
                  onChange(
                    setPattern(query, read.value ? next.write(read.value) : null),
                  );
                }}
              >
                {PATTERNS.map((one) => (
                  <option key={one.key} value={one.key}>
                    {one.label}
                  </option>
                ))}
              </select>
            </span>
            <input
              className={styles.text}
              id="build-pattern"
              type="text"
              dir="auto"
              autoComplete="off"
              spellCheck={false}
              value={read.value}
              onChange={(event) =>
                onChange(
                  setPattern(
                    query,
                    event.target.value ? pattern.write(event.target.value) : null,
                  ),
                )
              }
            />
          </span>
        </p>

        {/* **Always rendered, even before the list arrives.** It is the one
            control that needs the API, and the list is fetched when a reader
            first reaches it — so it has to exist to be reached. Hiding it
            until the classes loaded made that impossible, and the row then
            appeared out of nowhere once something else triggered the fetch. */}
        {!answered || classes.length > 0 ? (
          <p className={styles.row}>
            <label className={styles.label} htmlFor="build-type">
              گونه
            </label>
            <span className={styles.controls}>
              <span className={styles.picker}>
                <select
                  className={styles.select}
                  id="build-type"
                  onFocus={() => setOpened(true)}
                  onPointerDown={() => setOpened(true)}
                  value={getTerm(query, "type")}
                  onChange={(event) =>
                    onChange(setTerm(query, "type", event.target.value || null))
                  }
                >
                  <option value="">هر گونه</option>
                  {classes.map((one) => (
                    <option key={one.name} value={one.name}>
                      {classLabel(one)}
                    </option>
                  ))}
                </select>
              </span>
            </span>
          </p>
        ) : null}

        <p className={styles.row}>
          <label className={styles.label} htmlFor="build-in">
            این واژه از کجاست
          </label>
          <span className={styles.controls}>
            <span className={styles.picker}>
              <select
                className={styles.select}
                id="build-in"
                value={getTerm(query, "in")}
                onChange={(event) =>
                  onChange(setTerm(query, "in", event.target.value || null))
                }
              >
                <option value="">هر جا</option>
                {POPULATIONS.map((one) => (
                  <option key={one} value={one}>
                    {POPULATION_CHOICE[one] ?? one}
                  </option>
                ))}
              </select>
            </span>
          </span>
        </p>

        <NumberRows query={query} searched={searched} onChange={onChange} />
      </div>
    </div>
  );
}
