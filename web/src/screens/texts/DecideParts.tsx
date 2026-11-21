/**
 * Two parts of the decide panel: a reach by one neighbour, and the decisions
 * in force with a way to take each back. Split out of `Unsure.tsx` unchanged.
 */

import { useId, useState } from "react";

import { type Decision, withdrawDecision } from "../../api/texts";
import { Latin } from "../../text/Latin";
import { scopeLabel } from "./decide";
import styles from "./Unsure.module.css";

/** «فقط هر جا پس از [که ▾]»: a scope by one neighbour, the neighbour picked from a list. */
export function NearScope({
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
export function Decided({
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
