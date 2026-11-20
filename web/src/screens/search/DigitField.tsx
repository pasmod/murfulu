import {
  type InputHTMLAttributes,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";

import { latinDigits, persianDigits } from "../../text/numbers";

/**
 * A number field in Persian digits, right to left.
 *
 * The digits were Latin and the field ran left to right in a Persian row; the
 * project lead asked on 2026-11-20 for Persian. A `type="number"` field shows
 * only Latin digits in most browsers, so this is a text field that takes
 * digits from either keyboard and shows them in Persian, while the query
 * still gets the Latin ones its parser reads.
 *
 * While the reader is in it, it shows what they typed, even where that does
 * not make a query yet — a century range half typed, the field emptied to
 * write a new figure. On leaving, it shows the query's figure again.
 *
 * The caret is put back where the reader left it. Rewriting the value moves
 * it to the end, so a digit typed into the middle of «۱۲۳» would have pushed
 * the next one past the last digit and written a different number.
 */
export function DigitField({
  value,
  onValue,
  resetOn,
  invalid,
  ...input
}: {
  value: string;
  onValue: (digits: string) => void;
  /** The search being shown; when it changes, what was typed gives way. */
  resetOn?: string;
  /**
   * Why what the field shows is not a search yet. While it is set the form
   * will not submit: the browser holds it and says this sentence, so a
   * search never runs on a range other than the one on the screen.
   */
  invalid?: string;
} & Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "value" | "onChange" | "type"
>) {
  const [draft, setDraft] = useState<string | null>(null);
  const ref = useRef<HTMLInputElement>(null);
  /** Where the caret goes after the value is rewritten, counted in digits. */
  const caret = useRef<number | null>(null);
  useLayoutEffect(() => {
    if (caret.current === null || !ref.current) return;
    ref.current.setSelectionRange(caret.current, caret.current);
    caret.current = null;
  });
  // A search that changes from elsewhere — the Back button restoring an
  // older one, a facet, a submitted query — replaces what was typed, so the
  // field never shows one figure while the search holds another.
  useEffect(() => setDraft(null), [resetOn]);
  useEffect(() => {
    ref.current?.setCustomValidity(invalid ?? "");
  }, [invalid]);
  return (
    <input
      {...input}
      ref={ref}
      type="text"
      inputMode="numeric"
      dir="rtl"
      autoComplete="off"
      value={persianDigits(draft ?? value)}
      onChange={(event) => {
        const typed = event.target.value;
        const at = event.target.selectionStart ?? typed.length;
        // Every character kept is one digit, so the caret's place is the
        // number of digits before it.
        caret.current = latinDigits(typed.slice(0, at)).replace(/\D/g, "").length;
        const digits = latinDigits(typed).replace(/\D/g, "");
        setDraft(digits);
        onValue(digits);
      }}
      onBlur={(event) => {
        setDraft(null);
        input.onBlur?.(event);
      }}
    />
  );
}
