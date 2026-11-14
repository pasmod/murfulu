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
 *
 * **Where the automatic Behnevis is on** (direction A, 2026-11-14) the panel
 * opens with the model's reading for this line, how sure it is, the readings
 * to pick from and a field to type one. What is picked or typed is a proposal
 * for karbon, gathered by `tools/export_reading_proposals.py`; it changes
 * neither the bank nor the screen.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  type AutoReading,
  type MarkedWhere,
  type Reading,
  type WordKnown,
  marked as fetchMarked,
  markWrong,
  proposeReading,
} from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { LEVEL_FA, percent } from "./levels";
import styles from "./WordPanel.module.css";

export interface WordPanelProps {
  id: string;
  /** The counted spelling. */
  spelling: string;
  known: WordKnown | undefined;
  /** Ids of the readings this word's own harakat rule out. */
  against: ReadonlySet<string>;
  /** The automatic Behnevis's reading here, when it is on. */
  auto?: AutoReading;
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
  against,
  auto,
  corpusVersion,
  where,
  marked,
  onMarked,
  onClose,
}: WordPanelProps) {
  const readings = known?.readings ?? [];
  const anyRuledOut = readings.some((one) => against.has(one.id));
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

      {auto ? (
        <Here spelling={spelling} auto={auto} readings={readings} where={where} />
      ) : null}

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
              الفبا آمده‌اند؛ اینکه در این سطر کدام درست است، گفته نمی‌شود
              {anyRuledOut
                ? "، جز اینکه اعرابِ خودِ متن با خوانش‌های کم‌رنگ نمی‌خواند."
                : "."}
            </p>
          ) : anyRuledOut ? (
            <p className={styles.note}>اعرابِ خودِ متن با این خوانش نمی‌خواند.</p>
          ) : null}
          <ul className={styles.readings}>
            {readings.map((reading) => (
              <ReadingRow
                key={reading.id}
                spelling={spelling}
                reading={reading}
                ruledOut={against.has(reading.id)}
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
  ruledOut,
  marked,
  onMarked,
}: {
  spelling: string;
  reading: Reading;
  ruledOut: boolean;
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
    <li className={styles.reading} data-ruled-out={ruledOut || undefined}>
      <p className={styles.readingHead}>
        <Latin className={styles.latin}>{reading.latin}</Latin>
        {ruledOut ? <span className={styles.ruledOut}>اعرابِ متن با آن نمی‌خواند</span> : null}
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

type Proposing = "idle" | "sending" | "done" | "failed";

/**
 * The model's reading for this line, and a way to say which is right here:
 * pick one of the offered readings, or type one.
 */
function Here({
  spelling,
  auto,
  readings,
  where,
}: {
  spelling: string;
  auto: AutoReading;
  readings: Reading[];
  where: MarkedWhere;
}) {
  const [picked, setPicked] = useState<string>("");
  const [typed, setTyped] = useState<string>("");
  const [state, setState] = useState<Proposing>("idle");
  // What was sent, so the confirmation names it whatever is typed meanwhile.
  const [sent, setSent] = useState<string>("");
  const chosen = typed.trim() || picked;
  const busy = state === "sending";
  // A variant is the bank's too: رخ is *rex*, and *rox* as well.
  const inBank = readings.some(
    (one) => one.latin === chosen || one.latin_variants.includes(chosen),
  );

  function send() {
    if (!chosen) return;
    setState("sending");
    setSent(chosen);
    proposeReading(spelling, { latin: chosen, in_bank: inBank, model: auto }, where)
      .then(() => setState("done"))
      .catch(() => setState("failed"));
  }

  return (
    <section className={styles.here} aria-label="خوانش در این سطر">
      <p className={styles.hereHead}>
        در این سطر: <Latin className={styles.hereLatin}>{auto.latin}</Latin>
        <span className={styles.level} data-level={auto.level}>
          {LEVEL_FA[auto.level]} · {percent(auto.confidence)}
        </span>
      </p>
      <p className={styles.note}>
        این خوانش را برنامه پیشنهاد می‌کند و درصد، برآورد آن از درستی است. اگر خوانش
        درست چیز دیگری است، آن را برگزینید یا بنویسید.
      </p>
      {state === "done" ? (
        <p className={styles.proposed} role="status">
          پیشنهاد «<Latin>{sent}</Latin>» ثبت شد. برای فهرست کاربن جمع می‌شود و بانک
          واژه را تغییر نمی‌دهد.
        </p>
      ) : (
        <>
          <div className={styles.choices} role="group" aria-label="خوانش‌ها">
            {auto.candidates.map(([latin, share]) => (
              <button
                key={latin}
                type="button"
                className={styles.choice}
                disabled={busy}
                aria-pressed={!typed.trim() && picked === latin}
                onClick={() => {
                  setPicked(latin);
                  setTyped("");
                }}
              >
                <Latin>{latin}</Latin>
                <span className={styles.share}>{percent(share)}</span>
              </button>
            ))}
          </div>
          <label className={styles.typeLabel}>
            یا خوانش درست را بنویسید
            <input
              className={styles.typeField}
              dir="ltr"
              lang="fa-Latn"
              value={typed}
              disabled={busy}
              onChange={(event) => setTyped(event.target.value)}
            />
          </label>
          <button
            type="button"
            className={styles.propose}
            disabled={!chosen || busy}
            onClick={send}
          >
            ثبت پیشنهاد
          </button>
          {state === "failed" ? (
            <p className={styles.failed} role="status">
              ثبت نشد. کمی بعد دوباره بیازمایید.
            </p>
          ) : null}
        </>
      )}
    </section>
  );
}

