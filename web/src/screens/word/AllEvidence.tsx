/**
 * Every text the spelling is written in, below the six citations.
 *
 * The six are one line per author on purpose — thirty hits in one poem are
 * often a rhyme. This is the rest, for a reader who wants all of it: every
 * text, each with every line holding the spelling, a page of twenty at a time,
 * with the authors to choose one from. Authors come by how many texts are
 * theirs, most first, and each author's texts in the source's order, so a page
 * is the same on every reload; the state is in the address (`?all=1`,
 * `author`, `page`), so a page can be linked to.
 *
 * **Its counts are the search index's, the word's counts the counting's.**
 * The two can differ by a few texts, and where they do the list says why in
 * one sentence rather than letting two figures disagree in silence.
 *
 * **The lines are evidence for the spelling, never for one reading** — the
 * same lines serve مرد as *mard* and as *mord*.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { EVIDENCE_PAGE, evidence as fetchEvidence, type Evidence } from "../../api/evidence";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { Waiting } from "../../text/Waiting";
import { AuthorFilter, EVERY, UNNAMED } from "./AuthorFilter";
import { EvidenceText } from "./EvidenceText";
import styles from "./AllEvidence.module.css";

export interface AllEvidenceProps {
  spelling: string;
  /** The counting's number of texts, from the word's own record. */
  docCount: number | undefined;
  /** The corpus version the word's own figures belong to. */
  version: string | undefined;
}

/** An answer, and the request it answers, so a late one is never shown for another. */
interface Answer {
  key: string;
  data: Evidence;
}

export function AllEvidence({ spelling, docCount, version }: AllEvidenceProps) {
  const [params, setParams] = useSearchParams();
  const open = params.get("all") === "1";
  const unnamed = params.get("unnamed") === "1";
  const author = unnamed ? undefined : (params.get("author") ?? undefined);
  const asked = Number(params.get("page") ?? "1");
  const pageNumber = Number.isInteger(asked) && asked >= 1 ? asked : 1;

  const listKey = [spelling, unnamed ? UNNAMED : (author ?? EVERY)].join("\u0001");
  const pageKey = `${listKey}\u0001${pageNumber}`;
  const [summary, setSummary] = useState<Answer | null>(null);
  const [found, setFound] = useState<Answer | null>(null);
  // Two requests, two failures: one must never hide the other.
  const [summaryFailed, setSummaryFailed] = useState(false);
  const [pageFailed, setPageFailed] = useState(false);

  // The counts, and the lines counted once for the list being paged: they
  // change with the author, not with the page.
  useEffect(() => {
    const stop = new AbortController();
    setSummaryFailed(false);
    fetchEvidence({ spelling, author, unnamed, size: 0, countLines: true }, stop.signal)
      .then((data) => setSummary({ key: listKey, data }))
      .catch(() => {
        // An abandoned request — the reader moved on — is no failure, however
        // it ended: an abort can surface as an unreadable error body.
        if (!stop.signal.aborted) setSummaryFailed(true);
      });
    return () => stop.abort();
  }, [spelling, author, unnamed, listKey]);

  useEffect(() => {
    if (!open) return;
    const stop = new AbortController();
    setPageFailed(false);
    fetchEvidence({ spelling, author, unnamed, page: pageNumber - 1 }, stop.signal)
      .then((data) => setFound({ key: pageKey, data }))
      .catch(() => {
        if (!stop.signal.aborted) setPageFailed(true);
      });
    return () => stop.abort();
  }, [open, spelling, author, unnamed, pageNumber, pageKey]);

  // The whole list's figures stay on screen while one author's load; the
  // figures of the list being paged, and the page, only once they are its own.
  const whole = summary?.data.spelling === spelling ? summary.data : null;
  const current = summary?.key === listKey ? summary.data : null;
  const shown = found?.key === pageKey ? found.data : null;
  const matching = current?.matching ?? 0;
  // Named authors, as the word's own author count has them.
  const named = whole?.authors.filter((one) => one.author !== null).length ?? 0;
  const sameVersion = !whole?.corpus_version || !version || whole.corpus_version === version;
  const lastPage = Math.max(1, Math.ceil(matching / EVIDENCE_PAGE));
  const first = matching === 0 ? 0 : (pageNumber - 1) * EVIDENCE_PAGE + 1;
  const last = Math.min(matching, pageNumber * EVIDENCE_PAGE);

  function choose(next: { all?: boolean; author?: string; page?: number }) {
    setParams(
      (now) => {
        const out = new URLSearchParams(now);
        if (next.all === true) out.set("all", "1");
        if (next.all === false) {
          for (const name of ["all", "author", "unnamed", "page"]) out.delete(name);
        }
        if (next.author !== undefined) {
          out.delete("author");
          out.delete("unnamed");
          if (next.author === UNNAMED) out.set("unnamed", "1");
          else if (next.author !== EVERY) out.set("author", next.author);
        }
        if (next.page !== undefined) {
          if (next.page > 1) out.set("page", String(next.page));
          else out.delete("page");
        }
        return out;
      },
      { replace: next.page === undefined },
    );
  }

  // A page past the end — an old link, a hand-typed address — goes to the
  // last one, as the word bank's does.
  useEffect(() => {
    if (!current || pageNumber <= lastPage) return;
    setParams(
      (now) => {
        const out = new URLSearchParams(now);
        if (lastPage > 1) out.set("page", String(lastPage));
        else out.delete("page");
        return out;
      },
      { replace: true },
    );
  }, [current, pageNumber, lastPage, setParams]);

  return (
    <section className={styles.block} aria-labelledby="all-evidence">
      <h2 id="all-evidence" className={styles.blockTitle}>
        همهٔ شواهد
      </h2>
      {summaryFailed && !whole ? (
        <p className={styles.trouble}>شمار متن‌ها نرسید. کمی بعد دوباره بیازمایید.</p>
      ) : !whole ? (
        <Waiting />
      ) : (
        <>
          <p className={styles.summary}>
            {whole.corpus_version ? (
              <>
                در نسخهٔ <Latin>{whole.corpus_version}</Latin> پیکره،{" "}
              </>
            ) : null}
            املای «{spelling}» در <Num value={whole.total} /> متن از <Num value={named} /> نویسنده
            آمده است
            {current && !author && !unnamed && current.lines !== null ? (
              <>
                ، در <Num value={current.lines} /> سطر
              </>
            ) : null}
            .
            {current && current.lines === null ? (
              // Counting them means reading every text, which for و is the
              // whole corpus; each text below still says how many it has.
              <span className={styles.aside}> سطرهای فهرستی به این بلندی شمرده نمی‌شوند.</span>
            ) : null}
          </p>
          <p className={styles.note}>
            این سطرها شاهد املای «{spelling}»اند، نه یکی از خوانش‌های آن؛ اینکه هر سطر کدام خوانش را
            می‌خواهد، گفته نمی‌شود.
          </p>
          <button
            type="button"
            className={styles.toggle}
            aria-expanded={open}
            aria-controls="all-evidence-list"
            onClick={() => choose({ all: !open })}
          >
            {open ? "بستن همهٔ شواهد" : "نشان دادن همهٔ شواهد"}
          </button>
        </>
      )}

      {/* Always there, so the toggle's `aria-controls` names an element. */}
      <div id="all-evidence-list">
        {open && whole ? (
          <div className={styles.list}>
            {!sameVersion ? (
              <p className={styles.note}>
                این فهرست از نسخهٔ <Latin>{whole.corpus_version ?? ""}</Latin> پیکره است و شمارش‌های
                بالا از نسخهٔ <Latin>{version ?? ""}</Latin>.
              </p>
            ) : docCount !== undefined && whole.total !== docCount ? (
              <p className={styles.note}>
                این فهرست <Num value={whole.total} /> متن دارد و شمارش بالا <Num value={docCount} />
                ، چون جست‌وجوی متن‌ها چند حرف را که شمارش جدا می‌شمارد یکی می‌گیرد، مانند آ و ا یا ۀ
                و ه، و چند واژه را جور دیگری از هم جدا می‌کند.
              </p>
            ) : null}

            <AuthorFilter
              evidence={whole}
              chosen={unnamed ? UNNAMED : (author ?? EVERY)}
              onChoose={(value) => choose({ author: value, page: 1 })}
            />

            {summaryFailed ? (
              <p className={styles.trouble}>شمار این فهرست نرسید. کمی بعد دوباره بیازمایید.</p>
            ) : current ? (
              <p className={styles.count} role="status">
                {matching === 0 ? (
                  "متنی در این فهرست نیست."
                ) : (
                  <>
                    <Num value={first} />–<Num value={last} /> از <Num value={matching} /> متن
                    {(author || unnamed) && current.lines !== null ? (
                      <>
                        ، در <Num value={current.lines} /> سطر
                      </>
                    ) : null}
                  </>
                )}
              </p>
            ) : null}

            {pageFailed ? (
              <p className={styles.trouble}>این صفحه نرسید. کمی بعد دوباره بیازمایید.</p>
            ) : shown ? (
              <ol className={styles.texts}>
                {shown.texts.map((one) => (
                  <EvidenceText key={one.document_id} text={one} spelling={spelling} />
                ))}
              </ol>
            ) : (
              <Waiting />
            )}

            {matching > EVIDENCE_PAGE ? (
              <nav className={styles.pages} aria-label="صفحه‌های همهٔ شواهد">
                <button
                  type="button"
                  className={styles.page}
                  disabled={pageNumber <= 1}
                  onClick={() => choose({ page: pageNumber - 1 })}
                >
                  صفحهٔ پیشین
                </button>
                <button
                  type="button"
                  className={styles.page}
                  disabled={last >= matching}
                  onClick={() => choose({ page: pageNumber + 1 })}
                >
                  صفحهٔ پسین
                </button>
              </nav>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}
