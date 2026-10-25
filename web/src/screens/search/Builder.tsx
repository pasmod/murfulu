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
import { POPULATION_LABEL } from "../../text/lexicon";
import {
  COUNTS,
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

/** `century:10-13` as its two ends, so each gets its own field. */
function centuries(query: string): [string, string] {
  const [low = "", high = ""] = getTerm(query, "century").split("-");
  return [low, high];
}

export function Builder({ query, onChange }: BuilderProps) {
  const read = patternMode(query);
  // The mode is held rather than derived: a reader who picks «آغازشده با»
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
  const [low, high] = centuries(query);
  const count = getTerm(query, "count");
  const countOperator = count.startsWith(">")
    ? "gt"
    : count.startsWith("<")
      ? "lt"
      : "eq";
  const countValue = count.replace(/^[<>]=?/, "");

  const writeCount = (operator: string, value: string) => {
    const found = COUNTS.find((one) => one.key === operator) ?? COUNTS[0]!;
    if (!value) return onChange(setTerm(query, "count", null));
    onChange(
      setTerm(query, "count", found.write(Number(value)).split(":")[1]!),
    );
  };

  const writeCentury = (from: string, to: string) => {
    if (!from && !to) return onChange(setTerm(query, "century", null));
    const start = from || to;
    onChange(
      setTerm(query, "century", to && to !== start ? `${start}-${to}` : start),
    );
  };

  return (
    /* **Open, not folded.** The filters were behind «ساختن جست‌وجو» and a
       reader had to know to press it. The project lead asked for them visible
       on 2026-08-18.

       **The word classes are still fetched late.** They are the one control
       needing the API, and `docs/DECISIONS.md` holds *the screen asks nothing
       until there is a query* with a test behind it. So the list is asked for
       when a reader first reaches that one select — on focus or on a press —
       not when the screen loads. Everything else here is local.

       **Every row is a label and one `controls` span**, and every select sits
       in a `picker` that draws the arrow. Both are for the eye rather than the
       reader: the span holds a row's controls in the second column so a row
       with three of them begins where a row with one does, and the picker
       replaces the arrow that `appearance: none` takes away. See the CSS. */
    <div className={styles.builder}>
      <p className={styles.about}>
        هر گزینه، جست‌وجو را در همان کادر بالا می‌نویسد. می‌توانید همان را
        دست‌کاری کنید، یا نشانی صفحه را برای کسی بفرستید.
      </p>

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
                      {one.label_fa ?? one.name}
                    </option>
                  ))}
                </select>
              </span>
            </span>
          </p>
        ) : null}

        <p className={styles.row}>
          <label className={styles.label} htmlFor="build-in">
            کجا پیدا شده
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
                    {POPULATION_LABEL[one] ?? one}
                  </option>
                ))}
              </select>
            </span>
          </span>
        </p>

        <p className={styles.row}>
          <label className={styles.label} htmlFor="build-count">
            بسامد در پیکره
          </label>
          <span className={styles.controls}>
            <span className={styles.picker}>
              <select
                className={styles.select}
                id="build-count-operator"
                aria-label="جور بسامد"
                value={countOperator}
                onChange={(event) => writeCount(event.target.value, countValue)}
              >
                {COUNTS.map((one) => (
                  <option key={one.key} value={one.key}>
                    {one.label}
                  </option>
                ))}
              </select>
            </span>
            <input
              className={styles.number}
              id="build-count"
              type="number"
              min={0}
              inputMode="numeric"
              value={countValue}
              onChange={(event) => writeCount(countOperator, event.target.value)}
            />
          </span>
        </p>

        <p className={styles.row}>
          <label className={styles.label} htmlFor="build-century-from">
            سده
          </label>
          <span className={styles.controls}>
            <input
              className={styles.number}
              id="build-century-from"
              type="number"
              min={1}
              inputMode="numeric"
              aria-label="سده از"
              value={low}
              onChange={(event) => writeCentury(event.target.value, high)}
            />
            <span className={styles.between}>تا</span>
            <input
              className={styles.number}
              id="build-century-to"
              type="number"
              min={1}
              inputMode="numeric"
              aria-label="سده تا"
              value={high}
              onChange={(event) => writeCentury(low, event.target.value)}
            />
          </span>
        </p>
      </div>

      {/* What it wrote, in the direction it has to be typed. The reader who
          watches this fill in has learnt the syntax without being taught it. */}
      <p className={styles.written}>
        <span className={styles.writtenLabel}>می‌نویسد:</span>
        <span className={styles.writtenQuery} dir="ltr">
          {query || "—"}
        </span>
      </p>
    </div>
  );
}
