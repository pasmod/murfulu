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
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import {
  type Decision,
  type Scope,
  type UnsureKind,
  type UnsurePage,
  type UnsureSpelling,
  decideReading,
  unsureSpellings,
  withdrawDecision,
} from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { Waiting } from "../../text/Waiting";
import { KIND_FA, decidedFate, reach, replacing, scopeLabel } from "./decide";
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

type Sending = "idle" | "sending" | "done" | "failed";

/** The readings in the order offered: the bank's first, then what the model read or offered. */
function readingsOf(one: UnsureSpelling): string[] {
  return [
    ...new Set([
      ...one.known,
      ...one.read_as.map(([latin]) => latin),
      ...one.offered.map(([latin]) => latin),
    ]),
  ];
}

function Decide({
  id,
  one,
  corpusVersion,
  onDecided,
}: {
  id: string;
  one: UnsureSpelling;
  corpusVersion: string;
  onDecided: (change: (now: Decision[]) => Decision[]) => void;
}) {
  const group = useId();
  const scopes = useId();
  const [picked, setPicked] = useState("");
  const [typed, setTyped] = useState("");
  const [scope, setScope] = useState<Scope>("everywhere");
  const [after, setAfter] = useState(one.before[0]?.[0] ?? "");
  const [before, setBefore] = useState(one.after[0]?.[0] ?? "");
  const [state, setState] = useState<Sending>("idle");
  const [sent, setSent] = useState<{ latin: string; inBank: boolean; label: string } | null>(
    null,
  );
  const decisions = one.decided ?? [];
  const chosen = typed.trim() || picked;
  const inBank = one.known.includes(chosen);
  const word = scope === "after_word" ? after : scope === "before_word" ? before : null;
  const reached = reach(one, scope, word);
  const busy = state === "sending";
  const fit = one.marked && one.marked.fitted >= 5 ? one.marked : null;

  function send() {
    if (!chosen || (scope !== "everywhere" && !word)) return;
    const label = scopeLabel(scope, word);
    setState("sending");
    setSent({ latin: chosen, inBank, label });
    decideReading(
      one.spelling,
      { latin: chosen, in_bank: inBank, scope, scope_word: word },
      { corpus_version: corpusVersion },
    )
      .then((stored) => {
        setState("done");
        const now: Decision = {
          id: stored.id,
          latin: chosen,
          scope,
          scope_word: word,
          in_bank: inBank,
          created_at: stored.created_at,
        };
        // The newest for a reach replaces the one before it.
        onDecided((all) => replacing(all, now));
      })
      .catch(() => setState("failed"));
  }

  return (
    <section id={id} className={styles.panel} aria-label={`تصمیم دربارهٔ ${one.written}`}>
      {decisions.length > 0 ? (
        <Decided spelling={one.spelling} decisions={decisions} corpusVersion={corpusVersion} onDecided={onDecided} />
      ) : null}

      {fit ? (
        <p className={styles.note}>
          در <Num value={fit.fitted} /> جایی که ویراستاران این واژه را اعراب گذاشته‌اند، یک خوانش
          {fit.reading ? (
            <>
              {" "}
              (<Latin>{fit.reading}</Latin>)
            </>
          ) : null}{" "}
          در {percent(fit.best / fit.fitted)} آن‌ها جور است.
          {fit.best / fit.fitted < 0.8
            ? " پس شاید بهتر باشد به‌جای «همه‌جا» برای واژهٔ پیش یا پس از آن تصمیم بگیرید."
            : null}
        </p>
      ) : null}

      {state === "done" && sent ? (
        <div className={styles.done} role="status">
          <p className={styles.doneHead}>
            <span aria-hidden="true">✓ </span>
            «<Latin>{sent.latin}</Latin>» برای {sent.label} ثبت شد.
          </p>
          <p>{decidedFate(sent.inBank)}</p>
          <button
            type="button"
            className={styles.again}
            onClick={() => {
              setPicked("");
              setTyped("");
              setState("idle");
            }}
          >
            تصمیم دیگری بگیرید
          </button>
        </div>
      ) : (
        <>
          <fieldset className={styles.choices}>
            <legend className={styles.step}>این املا را چطور می‌خوانید؟</legend>
            {readingsOf(one).map((latin) => {
              const on = !typed.trim() && picked === latin;
              return (
                <label key={latin} className={styles.choice} data-checked={on || undefined}>
                  <input
                    type="radio"
                    className={styles.radio}
                    name={group}
                    value={latin}
                    checked={on}
                    disabled={busy}
                    onChange={() => {
                      setPicked(latin);
                      setTyped("");
                    }}
                  />
                  {on ? (
                    <span className={styles.tick} aria-hidden="true">
                      ✓
                    </span>
                  ) : null}
                  <Latin>{latin}</Latin>
                </label>
              );
            })}
          </fieldset>
          <label className={styles.typeLabel}>
            اگر در میان این‌ها نیست، خودتان بنویسید:
            <input
              className={styles.typeField}
              dir="ltr"
              lang="fa-Latn"
              value={typed}
              disabled={busy}
              onChange={(event) => {
                setTyped(event.target.value);
                if (event.target.value.trim()) setPicked("");
              }}
            />
          </label>

          <fieldset className={styles.scopes}>
            <legend className={styles.step}>برای کجا؟</legend>
            <label className={styles.scope}>
              <input
                type="radio"
                name={scopes}
                value="everywhere"
                checked={scope === "everywhere"}
                disabled={busy}
                onChange={() => setScope("everywhere")}
              />
              <span>
                همه‌جا{" "}
                <span className={styles.reach}>
                  (<Num value={one.places} /> جا، <Num value={one.unsure} /> تا نامطمئن)
                </span>
              </span>
            </label>
            {one.before.length > 0 ? (
              <NearScope
                name={scopes}
                label="فقط هر جا پس از"
                on={scope === "after_word"}
                busy={busy}
                words={one.before}
                value={after}
                onPick={() => setScope("after_word")}
                onWord={(next) => {
                  setAfter(next);
                  setScope("after_word");
                }}
              />
            ) : null}
            {one.after.length > 0 ? (
              <NearScope
                name={scopes}
                label="فقط هر جا پیش از"
                on={scope === "before_word"}
                busy={busy}
                words={one.after}
                value={before}
                onPick={() => setScope("before_word")}
                onWord={(next) => {
                  setBefore(next);
                  setScope("before_word");
                }}
              />
            ) : null}
          </fieldset>

          <p className={styles.summary} aria-live="polite" data-empty={!chosen || undefined}>
            {chosen ? (
              <>
                ثبت می‌شود: <Latin className={styles.summaryLatin}>{chosen}</Latin>،{" "}
                {scopeLabel(scope, word)}
                {reached ? (
                  <>
                    {" "}
                    (<Num value={reached.places} /> جا)
                  </>
                ) : null}
                . {decidedFate(inBank)}
              </>
            ) : (
              "هنوز خوانشی برنگزیده یا ننوشته‌اید."
            )}
          </p>
          <button type="button" className={styles.decide} disabled={!chosen || busy} onClick={send}>
            {chosen ? (
              <>
                ثبت «<Latin>{chosen}</Latin>» برای {scopeLabel(scope, word)}
              </>
            ) : (
              "ثبت"
            )}
          </button>
          {state === "failed" ? (
            <p className={styles.failed} role="status">
              ثبت نشد. کمی بعد دوباره امتحان کنید.
            </p>
          ) : null}
        </>
      )}

      {one.examples.length > 0 ? (
        <div className={styles.examples}>
          <p className={styles.step}>چند جا که برنامه در آن‌ها نامطمئن بود:</p>
          <ul className={styles.lines}>
            {one.examples.map((place) => (
              <li key={`${place.document_id}:${place.unit}:${place.line}:${place.word}`} className={styles.line}>
                <ExampleLine text={place.text} at={place.word} spelling={one.spelling} />
                <p className={styles.lineWhere}>
                  {place.heading}{" "}
                  <Link
                    to={`/texts?text=${encodeURIComponent(place.document_id)}&unit=${place.unit}&word=${encodeURIComponent(one.written)}`}
                  >
                    در متن ←
                  </Link>
                </p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

/** Harakat and half-spaces, which the list's spelling does not carry. */
const MARKS = /[\u064B-\u065F\u0670\u200c]/g;

/** A token as the list keys it: no harakat, no half-space, no punctuation after it. */
function bare(token: string | undefined): string | undefined {
  return token?.replace(MARKS, "").replace(/[^\p{L}]+$/u, "");
}

/** How many words around the spelling a long line keeps. */
const AROUND = 10;

/**
 * One line where the model was unsure, the spelling marked in it. A long
 * paragraph of prose is cut to the words around it. The line is the words
 * as the screen counts them, joined by spaces, so the word's place finds it;
 * where it does not (a token with a space of its own), the line is shown
 * whole and unmarked rather than marking the wrong word.
 */
export function ExampleLine({ text, at: place, spelling }: { text: string; at: number; spelling: string }) {
  const pieces = text.split(" ");
  // The word itself, not a longer word holding its letters (دل in دلداده).
  // A token with spaces of its own (a Latin name) moves the words after it
  // on, so a few places further are tried; otherwise nothing is marked.
  const at = [0, 1, 2, 3].map((k) => place + k).find((i) => bare(pieces[i]) === spelling);
  const found = at === undefined ? undefined : pieces[at];
  if (at === undefined || found === undefined) {
    return <p className={styles.lineText}>{text}</p>;
  }
  const from = pieces.length > 2 * AROUND + 4 ? Math.max(0, at - AROUND) : 0;
  const to = pieces.length > 2 * AROUND + 4 ? Math.min(pieces.length, at + AROUND + 1) : pieces.length;
  return (
    <p className={styles.lineText}>
      {from > 0 ? "… " : null}
      {pieces.slice(from, at).join(" ")}
      {at > from ? " " : null}
      <mark className={styles.hit}>{found}</mark>
      {to > at + 1 ? " " : null}
      {pieces.slice(at + 1, to).join(" ")}
      {to < pieces.length ? " …" : null}
    </p>
  );
}

/** «فقط هر جا پس از [که ▾]»: a scope by one neighbour, the neighbour picked from a list. */
function NearScope({
  name,
  label,
  on,
  busy,
  words,
  value,
  onPick,
  onWord,
}: {
  name: string;
  label: string;
  on: boolean;
  busy: boolean;
  words: [string, number, number][];
  value: string;
  onPick: () => void;
  onWord: (word: string) => void;
}) {
  const select = useId();
  return (
    <div className={styles.scope}>
      <input
        type="radio"
        name={name}
        checked={on}
        disabled={busy}
        onChange={onPick}
        aria-labelledby={`${select}-label`}
      />
      <span id={`${select}-label`}>{label}</span>
      <select
        id={select}
        className={styles.near}
        aria-label={`${label}: کدام واژه`}
        value={value}
        disabled={busy}
        onChange={(event) => onWord(event.target.value)}
      >
        {words.map(([word, places, unsure]) => (
          <option key={word} value={word}>
            {word} — {places.toLocaleString("fa-IR")} جا، {unsure.toLocaleString("fa-IR")} نامطمئن
          </option>
        ))}
      </select>
    </div>
  );
}

/** The decisions in force for a spelling, each of which can be taken back. */
function Decided({
  spelling,
  decisions,
  corpusVersion,
  onDecided,
}: {
  spelling: string;
  decisions: Decision[];
  corpusVersion: string;
  onDecided: (change: (now: Decision[]) => Decision[]) => void;
}) {
  const [busy, setBusy] = useState<number | null>(null);
  const [failed, setFailed] = useState(false);
  return (
    <div className={styles.decided}>
      <p className={styles.step}>تصمیم‌هایی که برای این املا ثبت شده است:</p>
      <ul className={styles.decisions}>
        {decisions.map((one) => (
          <li key={one.id} className={styles.decision}>
            <span>
              <span aria-hidden="true">✓ </span>
              {scopeLabel(one.scope, one.scope_word)}: <Latin>{one.latin}</Latin>
              {one.in_bank === false ? (
                <span className={styles.forKarbon}> (برای کاربن)</span>
              ) : null}
            </span>
            <button
              type="button"
              className={styles.withdraw}
              disabled={busy !== null}
              onClick={() => {
                setBusy(one.id);
                setFailed(false);
                withdrawDecision(spelling, one, corpusVersion)
                  .then(() => onDecided((all) => all.filter((d) => d.id !== one.id)))
                  .catch(() => setFailed(true))
                  .finally(() => setBusy(null));
              }}
            >
              پس گرفتن
            </button>
          </li>
        ))}
      </ul>
      <p className={styles.note}>
        تا به‌روزرسانیِ بعدیِ برنامه، متن‌ها هنوز مثل پیش خوانده می‌شوند.
      </p>
      {failed ? (
        <p className={styles.failed} role="status">
          پس گرفته نشد. کمی بعد دوباره امتحان کنید.
        </p>
      ) : null}
    </div>
  );
}
