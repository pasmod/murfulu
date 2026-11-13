/**
 * Every reading marked wrong, for the linguist to go through.
 *
 * Read from the feedback store, where the marks live (`GET /texts/marked`):
 * one row per mark, newest first — the word as written, the reading, the
 * text and the unit it stood in, and a way back to that line. The marks are
 * karbon's data and are exported to it; nothing here changes a reading.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { type Marked as MarkedRow, marked as fetchMarked } from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { Waiting } from "../../text/Waiting";
import styles from "./Texts.module.css";

/** Marks per page of the list. */
const PAGE = 50;

const DAY = new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium" });

export function Marked() {
  const [rows, setRows] = useState<MarkedRow[] | null>(null);
  const [total, setTotal] = useState(0);
  const [failed, setFailed] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stop = new AbortController();
    fetchMarked({ limit: PAGE }, stop.signal)
      .then((found) => {
        setRows(found.marked);
        setTotal(found.total);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setFailed(true);
      });
    return () => stop.abort();
  }, []);

  return (
    <section className={styles.card} aria-labelledby="marked">
      <h2 id="marked" className={styles.title}>
        خوانش‌هایی که نادرست دانسته شده‌اند
      </h2>
      <p className={styles.note}>
        هر بار که در متنی «این خوانش نادرست است» زده شود، اینجا می‌آید تا زبان‌شناس بازبینی‌اش
        کند. خوانش در بانک واژه دست نمی‌خورد؛ علامت برای کاربن فرستاده می‌شود.
      </p>
      {failed ? (
        <p className={styles.trouble} role="status">
          فهرست خوانده نشد. کمی بعد دوباره بیازمایید.
        </p>
      ) : rows === null ? (
        <Waiting />
      ) : rows.length === 0 ? (
        <p className={styles.note}>هنوز خوانشی نادرست دانسته نشده است.</p>
      ) : (
        <>
          <p className={styles.note}>
            <Num value={total} /> علامت، تازه‌ترین نخست
            {rows.length < total ? (
              <>
                ؛ <Num value={rows.length} /> نشان داده شده
              </>
            ) : null}
            .
          </p>
          <ol className={styles.marks}>
            {rows.map((row) => (
              <li key={row.id} className={styles.mark}>
                <p className={styles.markHead}>
                  <span className={styles.markWord}>{row.written ?? row.spelling_fa}</span>
                  <Latin className={styles.markLatin}>{row.latin}</Latin>
                  {row.created_at ? (
                    <span className={styles.markDate}>{DAY.format(new Date(row.created_at))}</span>
                  ) : null}
                </p>
                {row.heading ? <p className={styles.markWhere}>{row.heading}</p> : null}
                {row.note ? <p className={styles.markNote}>{row.note}</p> : null}
                {row.document_id ? (
                  <Link
                    className={styles.markLink}
                    to={`/texts?text=${encodeURIComponent(row.document_id)}${
                      row.unit != null ? `&unit=${row.unit}` : ""
                    }&word=${encodeURIComponent(row.spelling_fa)}`}
                  >
                    همان سطر ←
                  </Link>
                ) : null}
              </li>
            ))}
          </ol>
          {rows.length < total ? (
            <button
              type="button"
              className={styles.more}
              disabled={loading}
              onClick={() => {
                setLoading(true);
                fetchMarked({ offset: rows.length, limit: PAGE })
                  .then((next) => setRows((now) => [...(now ?? []), ...next.marked]))
                  .catch(() => setFailed(true))
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
