/**
 * The two number rows of the search filters: frequency and century.
 *
 * Their own file since 2026-11-20, when the project lead asked for them in
 * Persian digits, right to left, and filled with what the search covers —
 * which brought enough of their own state that Builder.tsx outgrew the
 * project's 400 lines. They write into the same query as every other row.
 */

import { useEffect, useRef, useState } from "react";

import { corpusCenturies, type CorpusCenturies } from "../../api/corpus";
import { latinDigits } from "../../text/numbers";
import { DigitField } from "./DigitField";
import { COUNTS, getTerm, setTerm } from "./syntax";
import styles from "./Builder.module.css";

/** A range typed backwards, in the search's own words for it (Search.tsx). */
const BACKWARDS = "سدهٔ اول دیرتر از سدهٔ دوم است.";

export interface NumberRowsProps {
  query: string;
  /** The search the screen is showing, which the address holds. */
  searched?: string;
  onChange: (next: string) => void;
}

/**
 * `century:10-13` as its two ends, so each gets its own field. In Latin
 * digits whatever the query was typed in: the parser reads `century:۱۰-۱۳`
 * too, and a Persian end turned into a number here was `NaN`.
 */
function centuries(query: string): [string, string] {
  const [low = "", high = ""] = latinDigits(getTerm(query, "century")).split("-");
  return [low, high || low];
}

/** What the frequency fields show while the query asks nothing of it. */
const ANY_COUNT = { operator: "gt", value: "0" };

export function NumberRows({ query, searched, onChange }: NumberRowsProps) {
  /** The corpus's first and last century, which the century fields open on. */
  const [span, setSpan] = useState<CorpusCenturies>({ first: null, last: null });

  // **The one thing asked on arrival.** The century fields open filled with
  // the corpus's first and last century, so a reader narrows a range instead
  // of having to know where the corpus begins — the project lead's request of
  // 2026-11-20. That needs the range before anyone touches the fields. It is
  // one small answer, and the screen works without it: the fields then open
  // empty, as they did before.
  useEffect(() => {
    const stop = new AbortController();
    corpusCenturies(stop.signal)
      .then(setSpan)
      .catch(() => undefined);
    return () => stop.abort();
  }, []);

  // **Filled, not empty.** Each field shows what the search covers when the
  // query says nothing of it — frequency «بیش از ۰», and the corpus's whole
  // range of centuries — so the reader only moves them (the project lead,
  // 2026-11-20). What is shown that way is not written: a query is only
  // given `count:` or `century:` once the reader changes the figure, and put
  // back to what it showed, the term goes again. Writing them on arrival
  // would have narrowed every search — a word built by the rules and not yet
  // seen in a text has no count and no century, and would have dropped out.
  const [low, high] = centuries(query);
  /**
   * An end typed so the range runs backwards — «۹» as the upper end of
   * «۱۰ تا ۱۳» on the way to «۴ تا ۹». It is no query yet, so it is not
   * written; it is held and shown, marked, until the other end makes the
   * range whole. Dropped on leaving the field, it let the next edit write a
   * wider range than the reader meant.
   */
  const [pending, setPending] = useState<{ low?: string; high?: string }>({});
  const centuryTerm = getTerm(query, "century");
  useEffect(() => setPending({}), [centuryTerm, searched]);
  const shownLow = pending.low ?? (low || (span.first === null ? "" : String(span.first)));
  const shownHigh = pending.high ?? (high || (span.last === null ? "" : String(span.last)));
  const backwards = pending.low !== undefined || pending.high !== undefined;
  /**
   * The other end of the century range, as it stood when the reader stepped
   * into a field. Read from the query instead, it moved under the reader's
   * own typing: with no corpus range to fill from, the «۱» of «۱۰» wrote
   * `century:1`, which then stood for both ends, and the «۰» made a range
   * running backwards that was never written.
   */
  const other = useRef({ low: "", high: "" });
  /**
   * True once the search has changed under the capture — submitted from a
   * field, or brought back by the Back button. The next keystroke then
   * captures the ends afresh, before it writes anything, so the capture is
   * the search as the reader saw it and not one their typing has moved.
   */
  const stale = useRef(false);
  useEffect(() => {
    stale.current = true;
  }, [searched]);
  const capture = () => {
    other.current = { low: shownLow, high: shownHigh };
    stale.current = false;
  };
  /** The other end: a held one, or as it stood when this edit began. */
  const otherEnd = (end: "low" | "high") => {
    if (pending[end] !== undefined) return pending[end];
    if (stale.current) capture();
    return other.current[end];
  };
  /**
   * The frequency's comparison while its field is emptied to write a new
   * figure. The emptied field takes the term out of the query — so what is
   * submitted is what the field shows — but «دقیقاً» must still be «دقیقاً»
   * when the next digit comes, not «بیش از», which is what a query with no
   * count shows. Let go when the reader leaves the field.
   */
  const [held, setHeld] = useState<string | null>(null);
  // A search brought back by the Back button has its own comparison.
  useEffect(() => setHeld(null), [searched]);
  const count = latinDigits(getTerm(query, "count"));
  const countOperator = !count
    ? (held ?? ANY_COUNT.operator)
    : count.startsWith(">")
      ? "gt"
      : count.startsWith("<")
        ? "lt"
        : "eq";
  const countValue = count ? count.replace(/^[<>]=?/, "") : ANY_COUNT.value;

  const writeCount = (operator: string, value: string) => {
    const found = COUNTS.find((one) => one.key === operator) ?? COUNTS[0]!;
    const any =
      !value ||
      (operator === ANY_COUNT.operator && Number(value) === Number(ANY_COUNT.value));
    if (any) return onChange(setTerm(query, "count", null));
    onChange(
      setTerm(query, "count", found.write(Number(value)).split(":")[1]!),
    );
  };

  const writeCentury = (from: string, to: string, edited: "from" | "to") => {
    // An end the reader empties stands for the corpus's own bound. With no
    // corpus range to stand for, emptying it takes the century filter away:
    // without that, the other end was copied into it and the filter could
    // not be removed from these fields at all.
    const emptied = edited === "from" ? !from && span.first === null : !to && span.last === null;
    if (emptied) {
      // Whatever was held goes with the filter.
      setPending({});
      return onChange(setTerm(query, "century", null));
    }
    let start = from ? Number(from) : span.first;
    let end = to ? Number(to) : span.last;
    if (start === null && end === null) {
      setPending({});
      return onChange(setTerm(query, "century", null));
    }
    start ??= end!;
    end ??= start;
    // A range that runs backwards is not a query the parser reads. It is
    // what a field holds halfway through being retyped — «۴ تا ۱» on the way
    // to «۴ تا ۱۲» — so the query waits for the reader rather than breaking,
    // and the typed end is held until the range is whole again.
    if (start > end) {
      // Both ends may be held at once: «۱۸ تا ۱۷» on the way to «۱۸ تا ۱۹».
      setPending((was) => (edited === "from" ? { ...was, low: from } : { ...was, high: to }));
      return;
    }
    setPending({});
    if (start === span.first && end === span.last) {
      return onChange(setTerm(query, "century", null));
    }
    onChange(setTerm(query, "century", start === end ? `${start}` : `${start}-${end}`));
  };

  return (
    <>
      <p className={styles.row}>
        <label className={styles.label} htmlFor="build-count">
          چند بار در پیکره آمده
        </label>
        <span className={styles.controls}>
          <span className={styles.picker}>
            <select
              className={styles.select}
              id="build-count-operator"
              aria-label="بیشتر، کمتر یا درست همین شمار"
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
          <DigitField
            className={styles.number}
            resetOn={searched}
            id="build-count"
            value={countValue}
            onValue={(digits) => {
              setHeld(digits ? null : countOperator);
              writeCount(countOperator, digits);
            }}
            onBlur={() => setHeld(null)}
          />
        </span>
      </p>

      <p className={styles.row}>
        <label className={styles.label} htmlFor="build-century-from">
          سده
        </label>
        <span className={styles.controls}>
          <DigitField
            className={styles.number}
            resetOn={searched}
            id="build-century-from"
            aria-label="از سدهٔ"
            aria-invalid={pending.low !== undefined || undefined}
            invalid={pending.low !== undefined ? BACKWARDS : undefined}
            aria-describedby={backwards ? "build-century-backwards" : undefined}
            value={shownLow}
            onFocus={() => {
              capture();
            }}
            onValue={(digits) => writeCentury(digits, otherEnd("high"), "from")}
          />
          <span className={styles.between}>تا</span>
          <DigitField
            className={styles.number}
            resetOn={searched}
            id="build-century-to"
            aria-label="تا سدهٔ"
            aria-invalid={pending.high !== undefined || undefined}
            invalid={pending.high !== undefined ? BACKWARDS : undefined}
            aria-describedby={backwards ? "build-century-backwards" : undefined}
            value={shownHigh}
            onFocus={() => {
              capture();
            }}
            onValue={(digits) => writeCentury(otherEnd("low"), digits, "to")}
          />
          {/* Said, not only marked in colour. The words are the search's own
              for the same fault (Search.tsx). */}
          {backwards ? (
            <span id="build-century-backwards" className={styles.backwards}>
              {BACKWARDS}
            </span>
          ) : null}
        </span>
      </p>
    </>
  );
}
