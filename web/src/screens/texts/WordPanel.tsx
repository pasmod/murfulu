/**
 * What the bank and the corpus say of one word in a text.
 *
 * **Every reading, equally, and none proposed** — the project lead's choice
 * of 2026-11-13. The letters do not say which reading a line needs, and the
 * drafts' rule for picking one put *dall* under دل. So the readings come in
 * alphabetical order, each the same size, and the panel says that none is
 * chosen.
 *
 * **A word with no reading is «؟», never "not a word".** The bank lacks many
 * common words and every inflected form (UPSTREAM B9); the panel says the
 * bank has no reading and links to the bank's search. The inflection
 * analyser's guesses are not shown: they are wrong too often (جنت as جن + ت).
 *
 * **«این خوانش نادرست است»** marks one reading wrong for the linguist's
 * review, through the feedback store. The wording is unconfirmed
 * (FOR_THE_LINGUIST L39). A mark cannot be taken back — the store is
 * append-only — so it asks once more before it is written.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  type MarkedWhere,
  type Reading,
  type WordKnown,
  marked as fetchMarked,
  markWrong,
} from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import styles from "./WordPanel.module.css";

export interface WordPanelProps {
  id: string;
  /** The counted spelling. */
  spelling: string;
  known: WordKnown | undefined;
  corpusVersion: string | null;
  where: MarkedWhere;
  /** Ids of readings marked wrong in this visit; earlier marks are asked for. */
  marked: ReadonlySet<string>;
  onMarked: (readingId: string) => void;
  onClose: () => void;
}

export function WordPanel({
  id,
  spelling,
  known,
  corpusVersion,
  where,
  marked,
  onMarked,
  onClose,
}: WordPanelProps) {
  const readings = known?.readings ?? [];
  const bank = `/bank?q=${encodeURIComponent(spelling)}`;
  const [before, setBefore] = useState<ReadonlySet<string>>(new Set());

  useEffect(() => {
    // Every mark ever made on this spelling's readings, however old. Without
    // the store the panel still reads; only the marks are missing.
    if (readings.length === 0) return;
    const stop = new AbortController();
    fetchMarked({ spelling, limit: 500 }, stop.signal)
      .then((found) =>
        setBefore(new Set(found.marked.map((one) => one.target_id ?? "").filter(Boolean))),
      )
      .catch(() => undefined);
    return () => stop.abort();
  }, [spelling, readings.length]);
  return (
    <section id={id} className={styles.panel} aria-label={`خوانش‌های ${where.written}`}>
      <header className={styles.head}>
        <span className={styles.written}>{where.written}</span>
        {where.written !== spelling ? (
          <span className={styles.spelling}>املا: {spelling}</span>
        ) : null}
        <button type="button" className={styles.close} onClick={onClose}>
          بستن
        </button>
      </header>

      {readings.length === 0 ? (
        <p className={styles.none}>
          <span className={styles.mark} aria-hidden="true">
            ؟
          </span>
          بانک واژه برای این املا خوانشی ندارد.
        </p>
      ) : (
        <>
          {readings.length > 1 ? (
            <p className={styles.note}>
              بانک واژه این املا را به <Num value={readings.length} /> گونه می‌خواند. همه به ترتیب
              الفبا آمده‌اند؛ اینکه در این سطر کدام درست است، گفته نمی‌شود.
            </p>
          ) : null}
          <ul className={styles.readings}>
            {readings.map((reading) => (
              <ReadingRow
                key={reading.id}
                spelling={spelling}
                reading={reading}
                where={where}
                marked={marked.has(reading.id) || before.has(reading.id)}
                onMarked={onMarked}
              />
            ))}
          </ul>
        </>
      )}

      <p className={styles.count}>
        {known?.total_count != null ? (
          <>
            این املا <Num value={known.total_count} /> بار، در{" "}
            <Num value={known.doc_count ?? 0} /> متن از پیکرهٔ{" "}
            <Latin>{corpusVersion ?? "?"}</Latin> آمده است
            {known.function_word
              ? "؛ بیشترِ این‌ها یک واژهٔ دستوری‌اند و شمار، شمارِ حرف‌هاست."
              : "."}
          </>
        ) : (
          <>
            شمار این املا در پیکرهٔ <Latin>{corpusVersion ?? "?"}</Latin> در دست نیست.
          </>
        )}
      </p>

      <p className={styles.links}>
        {readings.length > 0 ? (
          <Link to={`${bank}&exact=1`}>این واژه در بانک واژه ←</Link>
        ) : (
          <Link to={bank}>جست‌وجوی این املا در بانک واژه ←</Link>
        )}
      </p>
    </section>
  );
}

type Sending = "idle" | "asking" | "sending" | "done" | "failed";

function ReadingRow({
  spelling,
  reading,
  where,
  marked,
  onMarked,
}: {
  spelling: string;
  reading: Reading;
  where: MarkedWhere;
  marked: boolean;
  onMarked: (readingId: string) => void;
}) {
  const [state, setState] = useState<Sending>("idle");
  const [note, setNote] = useState("");

  function send() {
    setState("sending");
    markWrong(spelling, reading, where, note)
      .then(() => {
        setState("done");
        onMarked(reading.id);
      })
      .catch(() => setState("failed"));
  }

  return (
    <li className={styles.reading}>
      <p className={styles.readingHead}>
        <Latin className={styles.latin}>{reading.latin}</Latin>
        {reading.latin_variants.length > 0 ? (
          <span className={styles.variants}>
            نیز{" "}
            {reading.latin_variants.map((one) => (
              <Latin key={one}>{one}</Latin>
            ))}
          </span>
        ) : null}
        {reading.groups.length > 0 ? (
          <span className={styles.groups}>{reading.groups.join("، ")}</span>
        ) : null}
      </p>
      {reading.definition_fa ? (
        <p className={styles.definition}>{reading.definition_fa}</p>
      ) : null}

      {marked || state === "done" ? (
        <p className={styles.marked} role="status">
          این خوانش نادرست دانسته شده است و در فهرست بازبینی آمده.{" "}
          <Link to="/texts?view=marked">فهرست ←</Link>
        </p>
      ) : state === "idle" ? (
        <button type="button" className={styles.wrong} onClick={() => setState("asking")}>
          این خوانش نادرست است
        </button>
      ) : (
        <form
          className={styles.ask}
          onSubmit={(event) => {
            event.preventDefault();
            send();
          }}
        >
          <p className={styles.askLine}>
            <Latin>{reading.latin}</Latin> برای «{spelling}» نادرست است؟ این علامت برای
            بازبینی زبان‌شناس ثبت می‌شود و پاک نمی‌شود.
          </p>
          <label className={styles.noteLabel}>
            یادداشت، اگر بخواهید
            <textarea
              className={styles.noteField}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              rows={2}
              maxLength={500}
            />
          </label>
          {state === "failed" ? (
            <p className={styles.failed} role="status">
              ثبت نشد. کمی بعد دوباره بیازمایید.
            </p>
          ) : null}
          <div className={styles.askActions}>
            <button type="submit" className={styles.confirm} disabled={state === "sending"}>
              ثبت کن
            </button>
            <button type="button" className={styles.cancel} onClick={() => setState("idle")}>
              انصراف
            </button>
          </div>
        </form>
      )}
    </li>
  );
}
