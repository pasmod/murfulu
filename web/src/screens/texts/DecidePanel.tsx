/**
 * The panel a row of the list opens: decide a spelling's reading once for
 * every like place (the project lead's request of 2026-11-21).
 *
 * The readings to pick from or a field to type one, how far the decision
 * reaches — everywhere, or after or before one word, each with the number of
 * places it covers — three lines where the model was unsure, and the
 * decisions already in force, each of which can be taken back. Nothing
 * changes on screen before the model's next build; a reading the bank lacks
 * goes to karbon's list instead. Split out of `Unsure.tsx` unchanged.
 */

import { useId, useState } from "react";
import { Link } from "react-router-dom";

import { type Decision, type Scope, type UnsureSpelling, decideReading } from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { decidedFate, reach, replacing, scopeLabel } from "./decide";
import { Decided, NearScope } from "./DecideParts";
import { ExampleLine } from "./ExampleLine";
import { percent } from "./levels";
import { SuggestedMark, SuggestionBox } from "./Suggestion";
import { type Use, folded, readHere, suggestedAmong, takeUpOf } from "./suggested";
import styles from "./Unsure.module.css";

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

export function Decide({
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
  const offered = readingsOf(one);
  // The automatic suggestion (2026-11-22): marked among the readings, or
  // offered to type; taken up only by the person's own press and save.
  const suggestion = one.suggestion ?? null;
  const among = suggestion ? suggestedAmong(suggestion, offered) : [];

  function take(use: Use) {
    setPicked(use.how === "pick" ? use.latin : "");
    setTyped(use.how === "type" ? use.latin : "");
  }

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
          {suggestion ? (
            <SuggestionBox
              suggestion={suggestion}
              among={among}
              use={takeUpOf(suggestion, offered)}
              onUse={take}
              busy={busy}
              bankOne={one.kind === "one" ? (one.known[0] ?? null) : null}
              marksSaid={!!fit?.reading && folded(fit.reading) === folded(suggestion.latin)}
            />
          ) : null}
          <fieldset className={styles.choices}>
            <legend className={styles.step}>این املا را چطور می‌خوانید؟</legend>
            {offered.map((latin) => {
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
                  {among.includes(latin) ? <SuggestedMark /> : null}
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
                  {suggestion && readHere(suggestion, place) ? " · پیشنهاد خودکار از این سطر است" : null}
                </p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
