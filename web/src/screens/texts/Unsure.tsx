/**
 * The spellings the reading screen most often leaves to a person, and a way
 * to decide each once for every like place (the project lead's request of
 * 2026-11-21: one person's decision should fix many places at once).
 *
 * The list is measured over the whole corpus as the reading screen reads it
 * (`tools/measure_unsure_spellings.py`) and served beside the model
 * (`GET /texts/unsure`), the most unsure places first. A row opens a panel:
 * the readings to pick from or a field to type one, how far the decision
 * reaches — everywhere, or after or before one word, each with the number of
 * places it covers — three lines where the model was unsure, and the
 * decisions already in force, each of which can be taken back. Nothing
 * changes on screen before the model's next build; a reading the bank lacks
 * goes to karbon's list instead.
 */

import { useEffect, useId, useRef, useState } from "react";

import { ApiError } from "../../api/client";
import {
  type Decision,
  type UnsureKind,
  type UnsurePage,
  type UnsureSpelling,
  unsureSpellings,
} from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { Waiting } from "../../text/Waiting";
import { Decide } from "./DecidePanel";
import { KIND_FA } from "./decide";
import { percent } from "./levels";
import styles from "./Unsure.module.css";

/** Spellings per page of the list. */
const PAGE = 50;

const KINDS: (UnsureKind | null)[] = [null, "choice", "one", "missing"];

export function Unsure() {
  const [kind, setKind] = useState<UnsureKind | null>(null);
  const [page, setPage] = useState<UnsurePage | null>(null);
  const [rows, setRows] = useState<UnsureSpelling[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  // Which list a page was asked for: each change of filter starts a new one,
  // and a page that arrives for an older list, or for an offset the list has
  // moved past, is dropped (the review of 2026-11-21).
  const generation = useRef(0);

  useEffect(() => {
    const stop = new AbortController();
    generation.current += 1;
    setLoading(false);
    setPage(null);
    setRows([]);
    setError(null);
    setOpen(null);
    unsureSpellings({ kind: kind ?? undefined, size: PAGE }, stop.signal)
      .then((found) => {
        setPage(found);
        setRows(found.spellings);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(
          reason instanceof ApiError ? reason : new ApiError("unreachable", 0, String(reason)),
        );
      });
    return () => stop.abort();
  }, [kind]);

  /** Change one row's decisions against its current ones, never a stale copy. */
  function decided(spelling: string, change: (now: Decision[]) => Decision[]) {
    setRows((all) =>
      all.map((one) =>
        one.spelling === spelling ? { ...one, decided: change(one.decided ?? []) } : one,
      ),
    );
  }

  return (
    <section className={styles.card} aria-labelledby="unsure">
      <h2 id="unsure" className={styles.title}>
        پرتکرارترین واژه‌های نامطمئن
      </h2>
      <p className={styles.note}>
        برنامه این املاها را در بیشترِ جاها با اطمینانِ کم می‌خواند و خواندنشان را به شما
        می‌سپارد. اگر یک بار بگویید هر کدام چطور خوانده می‌شود، برنامه در به‌روزرسانیِ بعدی‌اش همهٔ
        جاهای همانند را همان‌طور می‌خواند: همه‌جا، یا فقط هر جا که پس از واژه‌ای یا پیش از واژه‌ای
        آمده است.
      </p>
      {error ? (
        <p className={styles.trouble} role="status">
          {error.trouble === "not-built"
            ? "این فهرست هنوز برای این نسخهٔ برنامه ساخته نشده است."
            : "نتوانستیم فهرست را بیاوریم. کمی بعد دوباره امتحان کنید."}
        </p>
      ) : !page ? (
        <Waiting />
      ) : (
        <>
          <p className={styles.note}>
            در پیکرهٔ <Latin>{page.meta.corpus_version}</Latin>، از{" "}
            <Num value={page.meta.words} /> واژهٔ متن‌ها{" "}
            <Num value={page.meta.unsure_words} /> تا (
            {percent(page.meta.unsure_words / page.meta.words)}) به شما سپرده می‌شود.
          </p>
          <div className={styles.kinds} role="group" aria-label="کدام املاها">
            {KINDS.map((one) => (
              <button
                key={one ?? "all"}
                type="button"
                className={styles.kind}
                aria-pressed={kind === one}
                onClick={() => setKind(one)}
              >
                {one ? KIND_FA[one] : "همه"}
              </button>
            ))}
          </div>
          <p className={styles.note}>
            <Num value={page.total} /> املا، از آنکه بیشتر از همه به شما سپرده می‌شود.
          </p>
          <ol className={styles.rows}>
            {rows.map((one) => (
              <Row
                key={one.spelling}
                one={one}
                open={open === one.spelling}
                onToggle={() => setOpen((now) => (now === one.spelling ? null : one.spelling))}
                corpusVersion={page.meta.corpus_version}
                onDecided={(now) => decided(one.spelling, now)}
              />
            ))}
          </ol>
          {rows.length < page.total ? (
            <button
              type="button"
              className={styles.more}
              disabled={loading}
              onClick={() => {
                const asked = generation.current;
                const offset = rows.length;
                setLoading(true);
                unsureSpellings({ kind: kind ?? undefined, offset, size: PAGE })
                  .then((next) => {
                    if (generation.current !== asked) return;
                    setRows((now) => (now.length === offset ? [...now, ...next.spellings] : now));
                  })
                  .catch(() => undefined)
                  // Only the current list's request frees its button.
                  .finally(() => {
                    if (generation.current === asked) setLoading(false);
                  });
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

function Row({
  one,
  open,
  onToggle,
  corpusVersion,
  onDecided,
}: {
  one: UnsureSpelling;
  open: boolean;
  onToggle: () => void;
  corpusVersion: string;
  onDecided: (change: (now: Decision[]) => Decision[]) => void;
}) {
  const panel = useId();
  const usual = one.read_as[0]?.[0];
  const decisions = one.decided ?? [];
  return (
    <li className={styles.row} data-open={open || undefined}>
      <button
        type="button"
        className={styles.rowButton}
        aria-expanded={open}
        aria-controls={panel}
        onClick={onToggle}
      >
        <span className={styles.rank}>
          <Num value={one.rank} />
        </span>
        <span className={styles.word}>{one.written}</span>
        <span className={styles.counts}>
          <Num value={one.unsure} /> جای نامطمئن از <Num value={one.places} />
        </span>
        <span className={styles.kindLabel} data-kind={one.kind}>
          {KIND_FA[one.kind]}
        </span>
        {usual ? (
          <span className={styles.usual}>
            برنامه: <Latin>{usual}</Latin>
          </span>
        ) : null}
        {decisions.length > 0 ? (
          <span className={styles.decidedBadge}>
            <span aria-hidden="true">✓ </span>
            {decisions.length === 1 ? "تصمیم گرفته شده" : `${decisions.length.toLocaleString("fa-IR")} تصمیم`}
          </span>
        ) : null}
      </button>
      {open ? (
        <Decide id={panel} one={one} corpusVersion={corpusVersion} onDecided={onDecided} />
      ) : null}
    </li>
  );
}
