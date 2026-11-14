/**
 * One open text: a short source line, what the marks under the words mean,
 * and the units word by word.
 *
 * Opened from the list, or from a citation straight at its line: `unit` is
 * the unit's place in the text, and the window holding it is read and
 * scrolled to; `word` is the spelling the citation was for, marked in that
 * unit. A text longer than one window is read a window at a time.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import { type Text, type TextWord, WINDOW, headingOf, readText } from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { Waiting } from "../../text/Waiting";
import { percent } from "./levels";
import { UnitView, type Chosen } from "./UnitView";
import { WordPanel } from "./WordPanel";
import styles from "./Reader.module.css";

export interface ReaderProps {
  documentId: string;
  /** The unit to open at, by its place in the text. */
  unit: number | null;
  /** The spelling a citation led here for. */
  word: string | null;
  /** The first unit of the window, when the reader paged. */
  start: number | null;
  onPage: (start: number) => void;
}

export function Reader({ documentId, unit, word, start, onPage }: ReaderProps) {
  const from = start ?? (unit !== null ? Math.floor(unit / WINDOW) * WINDOW : 0);
  const [text, setText] = useState<Text | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [chosen, setChosen] = useState<{ unit: number } & Chosen>();
  // Readings marked in this visit. What was marked before, a word's panel
  // asks for itself, by its spelling.
  const [marks, setMarks] = useState<ReadonlySet<string>>(new Set());

  useEffect(() => {
    const stop = new AbortController();
    setError(null);
    setChosen(undefined);
    readText(documentId, from, stop.signal)
      .then((found) => {
        setText(found);
        document.title = `${headingOf(found).join(" · ")} — مورفولو`;
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setText(null);
        setError(
          reason instanceof ApiError ? reason : new ApiError("unreachable", 0, String(reason)),
        );
      });
    return () => stop.abort();
  }, [documentId, from]);

  useEffect(() => {
    if (!text || unit === null) return;
    // The word itself, not the unit: a paragraph of prose can be taller than
    // the window, and centring it can leave the word far above the view.
    const at = document.getElementById(`unit-${unit}`);
    (at?.querySelector("button[data-sought]") ?? at)?.scrollIntoView({ block: "center" });
  }, [text, unit]);

  useEffect(() => {
    if (!chosen) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setChosen(undefined);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [chosen]);

  if (error) {
    return (
      <p className={styles.trouble} role="status">
        {error.trouble === "missing"
          ? "این متن در پیکره‌ای که اکنون خوانده می‌شود نیست. از فهرست، متنی دیگر را باز کنید."
          : "متن خوانده نشد. کمی بعد دوباره بیازمایید."}
      </p>
    );
  }
  if (!text || text.document_id !== documentId) {
    return <Waiting />;
  }

  const heading = headingOf(text);
  const last = Math.min(text.units_total, text.start + text.limit);
  // The legend says what a pale reading means only where there is one.
  const anyRuledOut = text.units.some((one) =>
    one.lines.some((line) => line.words?.some((word) => (word.against?.length ?? 0) > 0)),
  );
  return (
    <section className={styles.card} aria-label={heading.join(" · ")}>
      <p className={styles.source}>
        {text.author ? (
          <Link to={`/texts?q=${encodeURIComponent(text.author)}`}>{text.author}</Link>
        ) : null}
        {text.work ? (
          <>
            <span className={styles.separator} aria-hidden="true">
              ·
            </span>
            <Link
              to={`/texts?q=${encodeURIComponent([text.author, text.work].filter(Boolean).join(" "))}`}
            >
              {text.work}
            </Link>
          </>
        ) : null}
        {[...text.section, text.title].filter(Boolean).map((part, index) => (
          <span key={index} className={styles.part}>
            <span className={styles.separator} aria-hidden="true">
              ·
            </span>
            {part}
          </span>
        ))}
        <span className={styles.version}>
          پیکرهٔ <Latin>{text.corpus_version ?? "?"}</Latin>
          {text.source_name_fa ? ` · از ${text.source_name_fa}` : ""}
        </span>
      </p>

      {text.behnevis ? (
        <div className={styles.legend}>
          <p>
            زیر هر واژه، خوانشی که برنامه برای همین سطر پیشنهاد می‌کند، و این‌که چقدر به آن
            مطمئن است. روی واژه بزنید تا خوانش‌های دیگر را ببینید و خوانش درست را برگزینید
            یا بنویسید.
          </p>
          <p className={styles.levels}>
            <span>
              <span className={styles.auto} data-level="sure">
                <Latin>agar</Latin>
              </span>{" "}
              مطمئن: {percent(text.behnevis.sure)} یا بیشتر
            </span>
            <span>
              <span className={styles.auto} data-level="mid">
                <Latin>Bode</Latin>
              </span>{" "}
              کمابیش: {percent(text.behnevis.mid)} تا {percent(text.behnevis.sure)}
            </span>
            <span>
              <span className={styles.auto} data-level="unsure">
                <Latin>Ārd</Latin>
              </span>{" "}
              نامطمئن: کمتر از {percent(text.behnevis.mid)}
            </span>
          </p>
        </div>
      ) : (
        <div className={styles.legend}>
          <p>
            زیر هر واژه، خوانش‌هایش در بانک واژه
            {text.lexicon_snapshot_id ? (
              <>
                ، نسخهٔ <Latin>{text.lexicon_snapshot_id.split(":")[0] ?? ""}</Latin>
              </>
            ) : null}
            . روی واژه بزنید تا خوانش‌ها، شمارش در پیکره و پیوندش به بانک واژه را ببینید.
          </p>
          <p>
            چند خوانش: همه آمده‌اند و هیچ‌کدام پیشنهاد نشده. <span className={styles.unread}>؟</span>{" "}
            بانک واژه این املا را نمی‌خواند.
          </p>
          {anyRuledOut ? (
            <p>
              <Latin className={`${styles.latin} ${styles.ruledOut}`}>Tarak</Latin> کم‌رنگ: اعرابِ
              خودِ متن با این خوانش نمی‌خواند؛ برای نمونه «تُرک» با ضمه.
            </p>
          ) : null}
        </div>
      )}

      {text.units_total > text.limit ? (
        <p className={styles.window}>
          واحدهای <Num value={text.start + 1} />–<Num value={last} /> از{" "}
          <Num value={text.units_total} />
        </p>
      ) : null}

      <ol className={styles.units}>
        {text.units.map((one) => {
          const open = chosen?.unit === one.index ? chosen : null;
          const panelId = `word-${one.index}`;
          const shown = open ? (one.lines[open.line]?.words?.[open.word] ?? null) : null;
          return (
            <UnitView
              key={one.index}
              unit={one}
              words={text.words}
              chosen={open}
              panelId={panelId}
              found={unit === one.index ? word : null}
              onChoose={(next) => setChosen(next ? { unit: one.index, ...next } : undefined)}
              panel={
                shown && shown.s && open ? (
                  <WordPanel
                    // One panel per word occurrence: a pick made for one word
                    // must never be sent for the next (the review of 2026-11-14).
                    key={`${one.index}:${open.line}:${open.word}`}
                    id={panelId}
                    spelling={shown.s}
                    known={text.words[shown.s]}
                    against={new Set(shown.against ?? [])}
                    auto={shown.auto}
                    corpusVersion={text.corpus_version}
                    where={{
                      document_id: text.document_id,
                      unit: one.index,
                      heading: heading.join(" · "),
                      written: shown.fa,
                      corpus_version: text.corpus_version,
                      ...neighbours(one.lines[open.line]?.words ?? [], open.word),
                    }}
                    marked={marks}
                    onMarked={(id) => setMarks((now) => new Set([...now, id]))}
                    onClose={() => setChosen(undefined)}
                  />
                ) : null
              }
            />
          );
        })}
      </ol>

      {text.units_total > text.limit ? (
        <nav className={styles.pages} aria-label="پاره‌های متن">
          <button
            type="button"
            className={styles.page}
            disabled={text.start === 0}
            onClick={() => onPage(Math.max(0, text.start - WINDOW))}
          >
            پارهٔ پیشین
          </button>
          <button
            type="button"
            className={styles.page}
            disabled={last >= text.units_total}
            onClick={() => onPage(text.start + WINDOW)}
          >
            پارهٔ پسین
          </button>
        </nav>
      ) : null}
    </section>
  );
}

/** The counted words just before and after the word at `at` in its line. */
function neighbours(words: TextWord[], at: number): { before: string | null; after: string | null } {
  let before: string | null = null;
  for (let i = at - 1; i >= 0 && before === null; i--) before = words[i]?.s ?? null;
  let after: string | null = null;
  for (let i = at + 1; i < words.length && after === null; i++) after = words[i]?.s ?? null;
  return { before, after };
}

