/**
 * The readings the bank lacks, for the linguist to confirm and karbon to take.
 *
 * The project lead's rule of 2026-11-22: what the linguist confirms on the
 * reading screen and the bank lacks is gathered with an example and sent to
 * karbon as one issue, after a while. So this list holds every reading the
 * bank lacks — typed or decided by a reader, or used by the program for a
 * function word — in two groups: **the bank has no reading for the spelling
 * at all**, and **it has readings, and not this one**. Each row shows where
 * the reading was proposed and what the bank holds, and one button: the
 * linguist confirms. Only confirmed rows go into karbon's issue
 * (`tools/export_reading_proposals.py --confirmed`).
 *
 * **A confirmation is a statement, not an identity.** The app has one
 * account, so it cannot know who presses; the button says in words whose
 * confirmation it records. It can be taken back, so it does not ask twice.
 *
 * Nothing here changes the bank or what the program reads.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import {
  type KarbonPage,
  type KarbonRow,
  type KarbonState,
  confirmReading,
  forKarbon,
  withdrawConfirmation,
} from "../../api/karbon";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { Waiting } from "../../text/Waiting";
import { scopeLabel } from "./decide";
import styles from "./ForKarbon.module.css";

/** Rows per page of the list. */
const PAGE = 50;

const DAY = new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium" });

const STATES: [KarbonState, string][] = [
  ["all", "همه"],
  ["open", "تأییدنشده"],
  ["confirmed", "تأییدشده"],
];

/** A row's key: one spelling, one reading. */
function keyOf(row: KarbonRow): string {
  return `${row.spelling}:${row.latin}`;
}

export function ForKarbon() {
  const [state, setState] = useState<KarbonState>("all");
  const [page, setPage] = useState<KarbonPage | null>(null);
  const [rows, setRows] = useState<KarbonRow[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stop = new AbortController();
    setPage(null);
    setRows([]);
    setError(null);
    forKarbon({ state, size: PAGE }, stop.signal)
      .then((found) => {
        setPage(found);
        setRows(found.rows);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(
          reason instanceof ApiError ? reason : new ApiError("unreachable", 0, String(reason)),
        );
      });
    return () => stop.abort();
  }, [state]);

  /** A row's confirmation as the store now holds it, and the count with it. */
  function confirmed(row: KarbonRow, now: KarbonRow["confirmed"]) {
    setRows((all) =>
      all.map((one) => (keyOf(one) === keyOf(row) ? { ...one, confirmed: now } : one)),
    );
    setPage((was) =>
      was
        ? { ...was, confirmed: was.confirmed + (now ? 1 : 0) - (row.confirmed ? 1 : 0) }
        : was,
    );
  }

  const missing = rows.filter((one) => one.kind === "missing");
  const reading = rows.filter((one) => one.kind === "reading");

  return (
    <section className={styles.card} aria-labelledby="karbon">
      <h2 id="karbon" className={styles.title}>
        خوانش‌هایی که کاربن ندارد
      </h2>
      <p className={styles.note}>
        هر خوانشی که کسی در متنی ثبت کند و بانک واژه (کاربن) آن را نداشته باشد، اینجا می‌آید.
        خوانش‌هایی هم که برنامه برای واژه‌های دستوری به کار می‌برد و بانک واژه ندارد، اینجا
        هستند.
      </p>
      <p className={styles.note}>
        زبان‌شناس هر خوانشِ درست را تأیید می‌کند. فقط خوانش‌های تأییدشده برای کاربن فرستاده
        می‌شوند. این صفحه چیزی را در بانک واژه تغییر نمی‌دهد.
      </p>
      {error ? (
        <p className={styles.trouble} role="status">
          {error.trouble === "not-built"
            ? "بانک واژه در دسترس نیست، پس نمی‌دانیم کدام خوانش‌ها را ندارد."
            : "نتوانستیم فهرست را بیاوریم. کمی بعد دوباره امتحان کنید."}
        </p>
      ) : !page ? (
        <Waiting />
      ) : (
        <>
          <p className={styles.note}>
            <Num value={page.total} /> خوانش؛ <Num value={page.confirmed} /> تای آن تأیید شده
            است.
          </p>
          <div className={styles.states} role="group" aria-label="کدام خوانش‌ها">
            {STATES.map(([one, label]) => (
              <button
                key={one}
                type="button"
                className={styles.state}
                aria-pressed={state === one}
                onClick={() => setState(one)}
              >
                {label}
              </button>
            ))}
          </div>
          {rows.length === 0 ? (
            <p className={styles.note}>
              {state === "confirmed"
                ? "هنوز هیچ خوانشی تأیید نشده است."
                : state === "open"
                  ? "خوانشِ تأییدنشده‌ای نمانده است."
                  : "هنوز خوانشی اینجا نیست."}
            </p>
          ) : null}
          <Group
            id="karbon-missing"
            title="املا در بانک واژه نیست"
            about="بانک واژه برای این املاها هیچ خوانشی ندارد."
            rows={missing}
            onConfirmed={confirmed}
          />
          <Group
            id="karbon-reading"
            title="املا هست، این خوانش نیست"
            about="بانک واژه این املاها را دارد، ولی نه با این خوانش."
            rows={reading}
            onConfirmed={confirmed}
          />
          {rows.length < page.matching ? (
            <button
              type="button"
              className={styles.more}
              // One page at a time: two presses before the first answer would
              // ask for the same page twice.
              disabled={loading}
              onClick={() => {
                setLoading(true);
                forKarbon({ state, offset: rows.length, size: PAGE })
                  .then((next) => setRows((now) => [...now, ...next.rows]))
                  .catch(() => undefined)
                  .finally(() => setLoading(false));
              }}
            >
              بیشتر
            </button>
          ) : null}
        </>
      )}
    </section>
  );
}

function Group({
  id,
  title,
  about,
  rows,
  onConfirmed,
}: {
  id: string;
  title: string;
  about: string;
  rows: KarbonRow[];
  onConfirmed: (row: KarbonRow, now: KarbonRow["confirmed"]) => void;
}) {
  if (rows.length === 0) return null;
  return (
    <section className={styles.group} aria-labelledby={id}>
      <h3 id={id} className={styles.groupTitle}>
        {title} <span className={styles.groupCount}>(<Num value={rows.length} />)</span>
      </h3>
      <p className={styles.note}>{about}</p>
      <ol className={styles.rows}>
        {rows.map((one) => (
          <Row key={keyOf(one)} row={one} onConfirmed={onConfirmed} />
        ))}
      </ol>
    </section>
  );
}

type Sending = "idle" | "sending" | "failed";

function Row({
  row,
  onConfirmed,
}: {
  row: KarbonRow;
  onConfirmed: (row: KarbonRow, now: KarbonRow["confirmed"]) => void;
}) {
  const [sending, setSending] = useState<Sending>("idle");
  const word = row.spelling_fa_marked ?? row.spelling_fa;

  function confirm() {
    setSending("sending");
    confirmReading(row)
      .then((done) => {
        setSending("idle");
        onConfirmed(row, { id: done.id, created_at: done.created_at });
      })
      .catch(() => setSending("failed"));
  }

  function takeBack(id: number) {
    setSending("sending");
    withdrawConfirmation(row, id)
      .then(() => {
        setSending("idle");
        onConfirmed(row, null);
      })
      .catch(() => setSending("failed"));
  }

  return (
    <li className={styles.row} data-confirmed={row.confirmed ? true : undefined}>
      <p className={styles.head}>
        <span className={styles.word}>{word}</span>
        <Latin className={styles.latin}>{row.latin}</Latin>
        {row.origin === "function" ? (
          <span className={styles.badge}>واژهٔ دستوری</span>
        ) : null}
        {row.times > 0 ? (
          <span className={styles.times}>
            <Num value={row.times} /> بار ثبت شده
          </span>
        ) : null}
      </p>
      {row.bank.length > 0 ? (
        <p className={styles.fact}>
          بانک واژه برای این املا دارد:{" "}
          {row.bank.map((latin, index) => (
            <span key={latin}>
              {index > 0 ? "، " : null}
              <Latin>{latin}</Latin>
            </span>
          ))}
        </p>
      ) : null}
      {row.origin === "function" ? (
        <p className={styles.fact}>
          برنامه این واژهٔ دستوری را در متن‌ها با همین خوانش می‌خواند.
        </p>
      ) : null}
      {row.model && row.model !== row.latin ? (
        <p className={styles.fact}>
          برنامه آن‌جا خوانده بود: <Latin>{row.model}</Latin>
        </p>
      ) : null}
      {row.decided.length > 0 ? (
        <p className={styles.fact}>
          کسی آن را یک بار برای چند جا تعیین کرده است:{" "}
          {row.decided.map((one) => scopeLabel(one.scope, one.word)).join("؛ ")}
        </p>
      ) : null}

      {row.places.length > 0 ? (
        <ul className={styles.lines} aria-label={`جاهایی که ${row.spelling_fa} چنین ثبت شده`}>
          {row.places.map((place, index) => (
            <li key={index} className={styles.line}>
              <Line
                text={
                  place.text ??
                  [place.before, place.written, place.after].filter(Boolean).join(" ")
                }
                at={place.text ? place.word : null}
                target={place.written ?? row.spelling_fa}
                cut={!place.text}
              />
              <Where
                heading={place.heading}
                documentId={place.document_id}
                unit={place.unit}
                spelling={row.spelling_fa}
              />
            </li>
          ))}
        </ul>
      ) : row.examples.length > 0 ? (
        <>
          <p className={styles.fact}>چند جا از پیکره که این املا در آن‌ها آمده است:</p>
          <ul className={styles.lines}>
            {row.examples.map((place) => (
              <li
                key={`${place.document_id}:${place.unit}:${place.line}:${place.word}`}
                className={styles.line}
              >
                <Line text={place.text} at={place.word} target={row.spelling} />
                <Where
                  heading={place.heading}
                  documentId={place.document_id}
                  unit={place.unit}
                  spelling={row.spelling_fa}
                />
              </li>
            ))}
          </ul>
        </>
      ) : null}

      <div className={styles.actions}>
        {row.confirmed ? (
          <>
            <span className={styles.done}>
              <span aria-hidden="true">✓ </span>
              زبان‌شناس تأیید کرده است
              {row.confirmed.created_at
                ? ` · ${DAY.format(new Date(row.confirmed.created_at))}`
                : ""}
            </span>
            <button
              type="button"
              className={styles.back}
              disabled={sending === "sending"}
              onClick={() => takeBack(row.confirmed!.id)}
              aria-label={`برداشتن تأیید ${row.spelling_fa} ${row.latin}`}
            >
              برداشتن تأیید
            </button>
          </>
        ) : (
          <button
            type="button"
            className={styles.confirm}
            disabled={sending === "sending"}
            onClick={confirm}
            aria-label={`زبان‌شناس ${row.spelling_fa} ${row.latin} را تأیید می‌کند`}
          >
            زبان‌شناس تأیید می‌کند
          </button>
        )}
        {sending === "failed" ? (
          <span className={styles.failed} role="status">
            ثبت نشد. کمی بعد دوباره امتحان کنید.
          </span>
        ) : null}
      </div>
    </li>
  );
}

/** Where a line is from, and the way to it on the reading screen. */
function Where({
  heading,
  documentId,
  unit,
  spelling,
}: {
  heading: string | null;
  documentId: string;
  unit: number | null;
  spelling: string;
}) {
  const to =
    `/texts?text=${encodeURIComponent(documentId)}` +
    (unit === null ? "" : `&unit=${unit}`) +
    `&word=${encodeURIComponent(spelling)}`;
  return (
    <p className={styles.where}>
      {heading ? `${heading} ` : null}
      <Link to={to}>در متن ←</Link>
    </p>
  );
}

/** Harakat and half-spaces, which a counted spelling does not carry. */
const MARKS = /[ً-ٰٟ‌]/g;

/** A token as a spelling is keyed: no harakat, no half-space, no punctuation around it. */
function bare(token: string | undefined): string | undefined {
  return token?.replace(MARKS, "").replace(/^[^\p{L}]+|[^\p{L}]+$/gu, "");
}

/** How many words around the word a long line keeps. */
const AROUND = 10;

/**
 * One line, the word marked in it. The line is the words as the reading
 * screen counts them, joined by spaces, so the word's place finds it; a token
 * with a space of its own moves the words after it on, so a few places
 * further are tried. Without a place the first word that matches is marked;
 * where none does, the line is shown whole and unmarked rather than marking
 * the wrong word. A long paragraph of prose is cut to the words around it.
 */
export function Line({
  text,
  at: place,
  target,
  cut = false,
}: {
  text: string;
  at: number | null;
  target: string;
  /** The text is only the word and its neighbours, not the whole line. */
  cut?: boolean;
}) {
  const pieces = text.split(" ");
  const wanted = bare(target);
  const tried =
    place === null ? pieces.map((_, index) => index) : [0, 1, 2, 3].map((k) => place + k);
  const at = tried.find((index) => bare(pieces[index]) === wanted);
  if (at === undefined) {
    return <p className={styles.lineText}>{text}</p>;
  }
  const long = pieces.length > 2 * AROUND + 4;
  const from = long ? Math.max(0, at - AROUND) : 0;
  const to = long ? Math.min(pieces.length, at + AROUND + 1) : pieces.length;
  return (
    <p className={styles.lineText}>
      {from > 0 || cut ? "… " : null}
      {pieces.slice(from, at).join(" ")}
      {at > from ? " " : null}
      <mark className={styles.hit}>{pieces[at]}</mark>
      {to > at + 1 ? " " : null}
      {pieces.slice(at + 1, to).join(" ")}
      {to < pieces.length || cut ? " …" : null}
    </p>
  );
}
