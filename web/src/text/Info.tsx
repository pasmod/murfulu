/**
 * A small ⓘ that says, in one or two plain sentences, what a label means.
 *
 * The project lead's finding, going through the app on 2026-08-17: *the names
 * do not say what they do*. «املای جداگانه» beside «واژه‌گونه» is two numbers
 * a thousand apart with nothing saying why they differ; «سروده‌ها»،
 * «واژه‌گونه‌ها»، «ساخته‌ها» are three cards a reader is asked to tell apart
 * on the label alone. docs/FRONTEND.md already required this — *the interface
 * has to explain itself without a manual* — and it had been honoured for the
 * grammar terms and nowhere else.
 *
 * **Term.tsx is the sibling and this is not a replacement for it.** A grammar
 * term's Persian belongs to the rule pack and is passed in from the data; what
 * goes in here is the interface explaining its own words — *what is a word
 * type*, *what is a spelling* — which is the interface's to write.
 *
 * The interaction rules are Term's, for the same reasons: a button, so a
 * keyboard reaches it; open on focus as well as hover, because a tooltip only
 * a mouse can reach is not available to everyone; Escape closes it — WCAG
 * 1.4.13. The hit area is padded to the touch target while the mark itself
 * stays small, so it explains without competing with the number beside it.
 */

import { useEffect, useId, useState } from "react";

import styles from "./Info.module.css";

export interface InfoProps {
  /** What is being explained, for a reader who cannot see the layout. */
  label: string;
  /** One or two plain sentences. No jargon, or the jargon explained. */
  children: React.ReactNode;
}

export function Info({ label, children }: InfoProps) {
  const [open, setOpen] = useState(false);
  const tooltipId = useId();

  useEffect(() => {
    if (!open) return;
    const dismiss = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", dismiss);
    return () => document.removeEventListener("keydown", dismiss);
  }, [open]);

  return (
    <span
      className={styles.holder}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className={styles.mark}
        // The mark is a glyph, so the button needs a name of its own or a
        // screen reader announces "i, button".
        aria-label={`${label} چیست؟`}
        aria-describedby={open ? tooltipId : undefined}
        aria-expanded={open}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        // **Opening, not toggling.** One press is three events — enter, focus,
        // click — and a toggle on the last one undid what the first two had
        // just done, so on a phone, where there is no hover to fall back on,
        // the explanation flashed and vanished. Nothing here closes it because
        // three other things already do: leaving it, moving focus off it, and
        // Escape. A test names the phone case.
        onClick={() => setOpen(true)}
      >
        <span aria-hidden="true">i</span>
      </button>
      {open ? (
        <span role="tooltip" id={tooltipId} className={styles.tooltip}>
          {children}
        </span>
      ) : null}
    </span>
  );
}
