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

import { useEffect, useId, useRef, useState } from "react";
import { Link } from "react-router-dom";

import {
  type AutoReading,
  type Decision,
  type MarkedWhere,
  type Reading,
  type Scope,
  type UnsureOne,
  type WordKnown,
  decideReading,
  marked as fetchMarked,
  markWrong,
  proposeReading,
  unsureSpelling,
} from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { decidedFate, reach, replacing, scopeLabel } from "./decide";
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
          total={known?.total_count ?? null}
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
              بانک واژه برای این املا <Num value={readings.length} /> خوانش دارد. همه را به ترتیب
              الفبا آورده‌ایم و نمی‌گوییم کدام در این سطر درست است
              {anyRuledOut
                ? "؛ فقط می‌دانیم که اعراب خود متن با خوانش‌های کم‌رنگ جور نیست."
                : "."}
            </p>
          ) : anyRuledOut ? (
            <p className={styles.note}>اعرابی که در خود متن آمده با این خوانش جور نیست.</p>
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
            این املا <Num value={known.total_count} /> بار در{" "}
            <Num value={known.doc_count ?? 0} /> متن از پیکرهٔ{" "}
            <Latin>{corpusVersion ?? "?"}</Latin> آمده است
            {known.function_word
              ? "؛ ولی بیشترِ این‌ها یک واژهٔ دستوری با همین املاست، پس این عدد بیشتر شمارِ همان واژهٔ دستوری است."
              : "."}
          </>
        ) : (
          <>
            نمی‌دانیم این املا در پیکرهٔ <Latin>{corpusVersion ?? "?"}</Latin> چند بار آمده است.
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
        {ruledOut ? <span className={styles.ruledOut}>با اعراب متن جور نیست</span> : null}
        {reading.latin_variants.length > 0 ? (
          <span className={styles.variants}>
            یا{" "}
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
          این خوانش علامتِ «نادرست» خورده و به فهرست بازبینی رفته است.{" "}
          <Link to="/texts?view=marked">دیدن فهرست ←</Link>
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
            بازبینی زبان‌شناس ثبت می‌شود و دیگر نمی‌شود پاکش کرد.
          </p>
          <label className={styles.noteLabel}>
            اگر بخواهید، یادداشتی هم بنویسید
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
              ثبت نشد. کمی بعد دوباره امتحان کنید.
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

/** Where a reading saved from a line holds: only here, or every like place. */
type Reach = "here" | Scope;

/**
 * The model's reading for this line, and a way to say which is right here:
 * pick one of the offered readings, or type one — one or the other — and
 * say how far it holds: only here, or wherever the spelling follows or
 * precedes the same word, or everywhere (2026-11-21).
 */
function Here({
  spelling,
  auto,
  readings,
  where,
  saved,
  onSaved,
  total,
}: {
  spelling: string;
  auto: AutoReading;
  readings: Reading[];
  where: MarkedWhere;
  saved?: Saved;
  onSaved?: (saved: Saved) => void;
  /** The spelling's running words in the corpus, when known. */
  total: number | null;
}) {
  const group = useId();
  const reaches = useId();
  const [picked, setPicked] = useState<string>("");
  const [typed, setTyped] = useState<string>("");
  const [scope, setScope] = useState<Reach>("here");
  const [state, setState] = useState<Proposing>("idle");
  // What was sent, so the confirmation names it whatever is typed meanwhile.
  const [sent, setSent] = useState<(Omit<Saved, "id"> & { label: string | null }) | null>(
    null,
  );
  // The spelling in the measured list (how many places a decision reaches)
  // and the decisions in force. Without them the panel still saves.
  const [about, setAbout] = useState<UnsureOne | null>(null);
  // Decisions saved from this panel: an answer that arrives after one of them
  // is merged with them, never put in their place.
  const mine = useRef<Decision[]>([]);
  const chosen = typed.trim() || picked;
  const busy = state === "sending";
  // Held by the bank (a variant too: رخ is *rex*, and *rox* as well) or by
  // the function-word list (و *o*): the model learns it, karbon is not asked.
  const inBank = isInBank(readings, chosen) || (auto.known ?? []).includes(chosen);
  const word =
    scope === "after_word" ? (where.before ?? null) : scope === "before_word" ? (where.after ?? null) : null;

  useEffect(() => {
    const stop = new AbortController();
    unsureSpelling(spelling, stop.signal)
      .then((found) =>
        setAbout({
          ...found,
          decided: mine.current.reduce(
            (all, one) => replacing(all, one),
            found.decided ?? [],
          ),
        }),
      )
      .catch(() => undefined);
    return () => stop.abort();
  }, [spelling]);

  function count(one: Scope, near: string | null): number | null {
    const found = reach(about?.listed, one, near);
    if (found) return found.places;
    return one === "everywhere" ? total : null;
  }

  function send() {
    if (!chosen) return;
    const one = { latin: chosen, inBank };
    const label = scope === "here" ? null : scopeLabel(scope, word);
    setState("sending");
    setSent({ ...one, label });
    const stored =
      scope === "here"
        ? proposeReading(spelling, { latin: chosen, in_bank: inBank, model: auto }, where)
        : decideReading(
            spelling,
            { latin: chosen, in_bank: inBank, scope, scope_word: word, model: auto },
            where,
          );
    stored
      .then((done) => {
        setState("done");
        // A decision for every like place is not this word's pick: the word
        // keeps the model's reading until the next build (2026-11-21); the
        // decisions in force at the top of the panel take it in.
        if (scope === "here") {
          onSaved?.({ ...one, id: done.id });
          return;
        }
        const now: Decision = {
          id: done.id,
          latin: chosen,
          scope,
          scope_word: word,
          in_bank: inBank,
          created_at: done.created_at,
        };
        mine.current = [...mine.current, now];
        setAbout((was) =>
          was ? { ...was, decided: replacing(was.decided ?? [], now) } : { spelling, listed: null, decided: [now] },
        );
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
      {about?.decided?.length ? <InForce decisions={about.decided} /> : null}
      {state === "done" && sent ? (
        <div className={styles.proposed} role="status">
          <p className={styles.proposedHead}>
            <span aria-hidden="true">✓ </span>
            {sent.label ? (
              <>
                خوانش «<Latin>{sent.latin}</Latin>» برای {sent.label} ثبت شد.
              </>
            ) : (
              <>
                خوانش «<Latin>{sent.latin}</Latin>» برای این واژه در این سطر ثبت شد.
              </>
            )}
          </p>
          <p>{sent.label ? decidedFate(sent.inBank) : fate(sent.inBank)}</p>
          <button type="button" className={styles.again} onClick={again}>
            خوانش دیگری ثبت کنید
          </button>
        </div>
      ) : (
        <>
          {auto.source === "decided" ? (
            <p className={styles.note}>
              این خوانش را کسی برای همهٔ جاهای همانندِ این املا برگزیده است، نه برنامه. اگر
              اینجا درست نیست، خوانش درست را برای همین سطر ثبت کنید.
            </p>
          ) : null}
          {saved ? (
            <p className={styles.savedNote}>
              <span aria-hidden="true">✓ </span>
              پیش‌تر برای این سطر <Latin>{saved.latin}</Latin> ثبت شده است. اگر خوانش دیگری
              ثبت کنید، تازه‌ترین ثبت حساب می‌شود.
            </p>
          ) : auto.source === "decided" ? null : (
            <p className={styles.note}>
              این خوانش را برنامه پیشنهاد می‌کند و درصدِ کنارش نشان می‌دهد برنامه چقدر آن را
              درست می‌داند. اگر خوانش درست چیز دیگری است، یکی از گزینه‌ها را برگزینید یا خودتان
              بنویسید. گزینه‌های بی‌درصد را برنامه از ستاک‌های بانک واژه یا از روی حرف‌ها ساخته و
              نسنجیده است.
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
            اگر در میان این‌ها نیست، خودتان بنویسید:
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
          <fieldset className={styles.reaches}>
            <legend className={styles.step}>برای کجا؟</legend>
            <ReachOption
              name={reaches}
              on={scope === "here"}
              busy={busy}
              onPick={() => setScope("here")}
              label="فقط همین‌جا"
              places={null}
            />
            {where.before ? (
              <ReachOption
                name={reaches}
                on={scope === "after_word"}
                busy={busy}
                onPick={() => setScope("after_word")}
                label={scopeLabel("after_word", where.before)}
                places={count("after_word", where.before)}
              />
            ) : null}
            {where.after ? (
              <ReachOption
                name={reaches}
                on={scope === "before_word"}
                busy={busy}
                onPick={() => setScope("before_word")}
                label={scopeLabel("before_word", where.after)}
                places={count("before_word", where.after)}
              />
            ) : null}
            <ReachOption
              name={reaches}
              on={scope === "everywhere"}
              busy={busy}
              onPick={() => setScope("everywhere")}
              label={`هر جا که «${spelling}» آمده`}
              places={count("everywhere", null)}
            />
          </fieldset>
          <p className={styles.summary} aria-live="polite" data-empty={!chosen || undefined}>
            {chosen ? (
              <>
                ثبت می‌شود: <Latin className={styles.summaryLatin}>{chosen}</Latin>
                {typed.trim() ? " (نوشتهٔ شما)" : " (برگزیدهٔ شما)"}
                {scope === "here" ? "" : `، ${scopeLabel(scope, word)}`}.{" "}
                {scope === "here" ? fate(inBank) : decidedFate(inBank)}
              </>
            ) : (
              "هنوز خوانشی برنگزیده یا ننوشته‌اید."
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
                {scope === "here" ? "" : ` برای ${scopeLabel(scope, word)}`}
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
    </section>
  );
}

/** One choice of how far a saved reading holds, with the places it reaches. */
function ReachOption({
  name,
  on,
  busy,
  onPick,
  label,
  places,
}: {
  name: string;
  on: boolean;
  busy: boolean;
  onPick: () => void;
  label: string;
  places: number | null;
}) {
  return (
    <label className={styles.reach}>
      <input type="radio" name={name} checked={on} disabled={busy} onChange={onPick} />
      <span>
        {label}
        {places !== null ? (
          <span className={styles.reachCount}>
            {" "}
            (<Num value={places} /> جا)
          </span>
        ) : null}
      </span>
    </label>
  );
}

/** The decisions in force for this spelling, read before the model's next build. */
function InForce({ decisions }: { decisions: Decision[] }) {
  return (
    <div className={styles.inForce}>
      <p>برای این املا پیش‌تر تصمیم گرفته شده است:</p>
      <ul>
        {decisions.map((one) => (
          <li key={one.id}>
            {scopeLabel(one.scope, one.scope_word)}: <Latin>{one.latin}</Latin>
          </li>
        ))}
      </ul>
      <p className={styles.inForceNote}>
        برنامه این تصمیم‌ها را در به‌روزرسانیِ بعدی‌اش به کار می‌بندد. تصمیم تازه برای همان
        جاها جای تصمیم پیشین را می‌گیرد.
      </p>
    </div>
  );
}

/** Whether the bank reads the spelling so, a variant included. */
function isInBank(readings: Reading[], latin: string): boolean {
  return readings.some((one) => one.latin === latin || one.latin_variants.includes(latin));
}

/** What becomes of a saved reading, in one sentence. */
function fate(inBank: boolean): string {
  return inBank
    ? "برنامه این خوانش را می‌شناسد و در به‌روزرسانیِ بعدی یاد می‌گیرد که همین جای متن را چنین بخواند."
    : "این خوانش در بانک واژه نیست. آن را برای افزودن به کاربن پیشنهاد می‌کنیم؛ تا آن وقت برنامه از آن یاد نمی‌گیرد.";
}
