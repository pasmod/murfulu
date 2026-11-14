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
import {
  type Marked,
  type Text,
  type TextWord,
  WINDOW,
  headingOf,
  marked as fetchMarked,
  readText,
} from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { Waiting } from "../../text/Waiting";
import { type Saved, percent } from "./levels";
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
  // Readings saved for words of this window, by `unit:line:word`: asked for
  // when the window opens, and added to as readings are saved. Kept with the
  // text they belong to, so a save that completes after the reader moved on
  // is never shown on another text (the review of 2026-11-14).
  const [saved, setSaved] = useState<SavedIn>(NOTHING_SAVED);

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
    if (!text) return;
    const doc = text.document_id;
    setSaved({ doc, map: new Map() });
    if (!text.behnevis) return;
    // Without the store the text still reads; only the check marks are missing.
    const stop = new AbortController();
    savedIn(text, stop.signal)
      .then((found) =>
        // A reading saved while this was asked for is newer: it stays.
        setSaved((now) => (now.doc === doc ? { doc, map: newest(now.map, found) } : now)),
      )
      .catch(() => undefined);
    return () => stop.abort();
  }, [text]);

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
            <span>
              <span className={styles.auto} data-level="mine">
                <span className={styles.tick} aria-hidden="true">
                  ✓
                </span>
                <Latin>Del</Latin>
              </span>{" "}
              ثبت‌شده: خوانشی که برای همین واژه برگزیده یا نوشته شده
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
              saved={saved.map}
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
                    saved={saved.map.get(`${one.index}:${open.line}:${open.word}`)}
                    onSaved={(pick) => {
                      const doc = text.document_id;
                      const at = `${one.index}:${open.line}:${open.word}`;
                      setSaved((now) =>
                        now.doc === doc ? { doc, map: newest(now.map, new Map([[at, pick]])) } : now,
                      );
                    }}
                    corpusVersion={text.corpus_version}
                    where={{
                      document_id: text.document_id,
                      unit: one.index,
                      heading: heading.join(" · "),
                      written: shown.fa,
                      corpus_version: text.corpus_version,
                      line: open.line,
                      word: open.word,
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

/** Readings saved in one text, by `unit:line:word`. */
interface SavedIn {
  doc: string;
  map: ReadonlyMap<string, Saved>;
}

const NOTHING_SAVED: SavedIn = { doc: "", map: new Map() };

/**
 * Every reading saved in this window of the text, page by page: a window
 * with many saves keeps them all (the review of 2026-11-14).
 */
async function savedIn(text: Text, signal: AbortSignal): Promise<Map<string, Saved>> {
  const rows: Marked[] = [];
  for (;;) {
    const found = await fetchMarked(
      {
        kind: "proposed",
        document_id: text.document_id,
        unit_from: text.start,
        unit_to: text.start + text.limit - 1,
        offset: rows.length,
        limit: 500,
      },
      signal,
    );
    rows.push(...found.marked);
    if (found.returned === 0 || rows.length >= found.total) break;
  }
  return placeSaved(text, rows);
}

/**
 * Where in this window each saved reading belongs, newest first, by
 * `unit:line:word`. A proposal names its line and word since 2026-11-14;
 * an older one, or one whose text has changed under it, is found by its
 * spelling, as written, between the same neighbours.
 */
export function placeSaved(text: Text, rows: Marked[]): Map<string, Saved> {
  const placed = new Map<string, Saved>();
  for (const row of rows) {
    const unit = text.units.find((one) => one.index === row.unit);
    if (!unit || !row.latin) continue;
    const at = placeOf(unit, row);
    if (at !== null && !placed.has(at)) {
      placed.set(at, { latin: row.latin, inBank: row.in_bank === true, id: row.id });
    }
  }
  return placed;
}

function placeOf(unit: Text["units"][number], row: Marked): string | null {
  // The saved place first, but only where the word there is still the one
  // saved, as written and between the same neighbours: a corpus revision can
  // put another word of the same spelling there (the review of 2026-11-14).
  if (row.line != null && row.word != null) {
    const words = unit.lines[row.line]?.words ?? [];
    if (sameWord(words, row.word, row)) return `${unit.index}:${row.line}:${row.word}`;
  }
  // Otherwise by its context, and only where that context is unique: two
  // identical halves would leave the save on the wrong one (the review of
  // 2026-11-14), so an ambiguous save is not shown at all.
  const found: string[] = [];
  for (const [lineIndex, line] of unit.lines.entries()) {
    const words = line.words ?? [];
    for (const wordIndex of words.keys()) {
      if (sameWord(words, wordIndex, row)) found.push(`${unit.index}:${lineIndex}:${wordIndex}`);
    }
  }
  return found.length === 1 ? (found[0] ?? null) : null;
}

/**
 * The saves of `now` with `more` laid over them, each place keeping its
 * newest save by the store's id: a save whose answer arrives late never
 * replaces a later one (the review of 2026-11-14).
 */
export function newest(
  now: ReadonlyMap<string, Saved>,
  more: ReadonlyMap<string, Saved>,
): Map<string, Saved> {
  const merged = new Map(now);
  for (const [at, pick] of more) {
    const held = merged.get(at);
    if (!held || pick.id > held.id) merged.set(at, pick);
  }
  return merged;
}

/** Whether the word at `at` is the one a saved reading was for. */
function sameWord(words: TextWord[], at: number, row: Marked): boolean {
  const word = words[at];
  if (!word || word.s !== row.spelling_fa) return false;
  if (row.written && word.fa !== row.written) return false;
  const near = neighbours(words, at);
  if (row.before !== undefined && (row.before ?? null) !== near.before) return false;
  if (row.after !== undefined && (row.after ?? null) !== near.after) return false;
  return true;
}

/** The counted words just before and after the word at `at` in its line. */
function neighbours(words: TextWord[], at: number): { before: string | null; after: string | null } {
  let before: string | null = null;
  for (let i = at - 1; i >= 0 && before === null; i--) before = words[i]?.s ?? null;
  let after: string | null = null;
  for (let i = at + 1; i < words.length && after === null; i++) after = words[i]?.s ?? null;
  return { before, after };
}

