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
 * to pick from and a field to type one. A reading is picked **or** typed,
 * never both: each clears the other, and the panel says which one will be
 * saved and what becomes of it (the project lead, 2026-11-14). A pick among
 * the bank's readings teaches the model at its next build; a reading the bank
 * lacks goes on the list for karbon (`tools/export_reading_proposals.py`).
 * Once saved, the word in the text shows it with a check mark.
 */

import { useEffect, useId, useState } from "react";
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
import { LEVEL_FA, type Saved, percent } from "./levels";
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
  /** The reading saved for this very word, newest first, if any. */
  saved?: Saved;
  onSaved?: (saved: Saved) => void;
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
  saved,
  onSaved,
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
        <Here
          spelling={spelling}
          auto={auto}
          readings={readings}
          where={where}
          saved={saved}
          onSaved={onSaved}
        />
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
 * pick one of the offered readings, or type one — one or the other.
 */
function Here({
  spelling,
  auto,
  readings,
  where,
  saved,
  onSaved,
}: {
  spelling: string;
  auto: AutoReading;
  readings: Reading[];
  where: MarkedWhere;
  saved?: Saved;
  onSaved?: (saved: Saved) => void;
}) {
  const group = useId();
  const [picked, setPicked] = useState<string>("");
  const [typed, setTyped] = useState<string>("");
  const [state, setState] = useState<Proposing>("idle");
  // What was sent, so the confirmation names it whatever is typed meanwhile.
  const [sent, setSent] = useState<Omit<Saved, "id"> | null>(null);
  const chosen = typed.trim() || picked;
  const busy = state === "sending";
  // Held by the bank (a variant too: رخ is *rex*, and *rox* as well) or by
  // the function-word list (و *o*): the model learns it, karbon is not asked.
  const inBank = isInBank(readings, chosen) || (auto.known ?? []).includes(chosen);

  function send() {
    if (!chosen) return;
    const one = { latin: chosen, inBank };
    setState("sending");
    setSent(one);
    proposeReading(spelling, { latin: chosen, in_bank: inBank, model: auto }, where)
      .then((stored) => {
        setState("done");
        onSaved?.({ ...one, id: stored.id });
      })
      .catch(() => setState("failed"));
  }

  function again() {
    setPicked("");
    setTyped("");
    setState("idle");
  }

  return (
    <section className={styles.here} aria-label="خوانش در این سطر">
      <p className={styles.hereHead}>
        در این سطر: <Latin className={styles.hereLatin}>{auto.latin}</Latin>
        <span className={styles.level} data-level={auto.level}>
          {LEVEL_FA[auto.level]} · {percent(auto.confidence)}
        </span>
      </p>
      {state === "done" && sent ? (
        <div className={styles.proposed} role="status">
          <p className={styles.proposedHead}>
            <span aria-hidden="true">✓ </span>
            خوانش «<Latin>{sent.latin}</Latin>» برای این واژه در این سطر ثبت شد.
          </p>
          <p>{fate(sent.inBank)}</p>
          <button type="button" className={styles.again} onClick={again}>
            خوانش دیگری ثبت کنید
          </button>
        </div>
      ) : (
        <>
          {saved ? (
            <p className={styles.savedNote}>
              <span aria-hidden="true">✓ </span>
              پیش‌تر برای این سطر ثبت شده: <Latin>{saved.latin}</Latin>. اگر خوانش دیگری
              ثبت کنید، تازه‌ترین به حساب می‌آید.
            </p>
          ) : (
            <p className={styles.note}>
              این خوانش را برنامه پیشنهاد می‌کند و درصد، برآورد آن از درستی است. اگر خوانش
              درست چیز دیگری است، یکی را برگزینید یا آن را بنویسید؛ خوانش‌های بی‌درصد را
              برنامه از ستاک‌های بانک واژه یا از حروف ساخته و نسنجیده است.
            </p>
          )}
          {/* Native radio buttons: one tab stop, arrow keys move the pick
              (the review of 2026-11-14); each looks like a button. */}
          <fieldset className={styles.choices}>
            <legend className={styles.step}>یکی را برگزینید:</legend>
            {auto.candidates.map(([latin, share]) => {
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
                      // Picking clears what was typed: one or the other.
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
                  {share === null ? null : <span className={styles.share}>{percent(share)}</span>}
                </label>
              );
            })}
          </fieldset>
          <label className={styles.typeLabel}>
            یا، اگر در میان نیست، بنویسید:
            <input
              className={styles.typeField}
              dir="ltr"
              lang="fa-Latn"
              value={typed}
              disabled={busy}
              onChange={(event) => {
                // Typing clears the pick: one or the other.
                setTyped(event.target.value);
                if (event.target.value.trim()) setPicked("");
              }}
            />
          </label>
          <p className={styles.summary} aria-live="polite" data-empty={!chosen || undefined}>
            {chosen ? (
              <>
                ثبت می‌شود: <Latin className={styles.summaryLatin}>{chosen}</Latin>
                {typed.trim() ? " (نوشته‌شده)" : " (برگزیده)"}. {fate(inBank)}
              </>
            ) : (
              "هنوز خوانشی برگزیده یا نوشته نشده است."
            )}
          </p>
          <button
            type="button"
            className={styles.propose}
            disabled={!chosen || busy}
            onClick={send}
          >
            {chosen ? (
              <>
                ثبت «<Latin>{chosen}</Latin>»
              </>
            ) : (
              "ثبت"
            )}
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

/** Whether the bank reads the spelling so, a variant included. */
function isInBank(readings: Reading[], latin: string): boolean {
  return readings.some((one) => one.latin === latin || one.latin_variants.includes(latin));
}

/** What becomes of a saved reading, in one sentence. */
function fate(inBank: boolean): string {
  return inBank
    ? "برنامه این خوانش را می‌شناسد و در به‌روزرسانیِ بعدی آن را برای همین جای متن یاد می‌گیرد."
    : "این خوانش در بانک واژه نیست؛ برای افزودن به کاربن پیشنهاد می‌شود و برنامه تا آن زمان از آن یاد نمی‌گیرد.";
}
