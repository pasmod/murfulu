/**
 * Two parts of the word panel's top: one choice of how far a saved reading
 * holds, and the decisions already in force. Split out of `Here.tsx` when the
 * automatic suggestion was added (2026-11-22), unchanged.
 */

import type { Decision } from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { scopeLabel } from "./decide";
import styles from "./WordPanel.module.css";

/** One choice of how far a saved reading holds, with the places it reaches. */
export function ReachOption({
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
export function InForce({ decisions }: { decisions: Decision[] }) {
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
