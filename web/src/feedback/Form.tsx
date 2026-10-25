/**
 * The form, which is three forms.
 *
 * docs/REVIEW.md: the category is chosen **first** and the form adapts, because
 * a graded verdict does not fit "this button does nothing". A linguistic
 * judgement carries a verdict and nothing else does — the API refuses a record
 * that breaks that pairing either way, and so does the database under it.
 *
 * **Only an expert may grade a generated word.** The account is asked once,
 * when the panel opens, so nobody writes a careful note in Persian and loses
 * it to a 403.
 */

import { useState } from "react";

import { ApiError } from "../api/client";
import {
  leave,
  type Account,
  type Category,
  type FeedbackIn,
  type Verdict,
} from "../api/feedback";
import type { Subject } from "./subject";
import styles from "./Feedback.module.css";

const CATEGORIES: { key: Category; label: string; hint: string }[] = [
  {
    key: "linguistic",
    label: "داوری زبانی",
    hint: "این واژه درست ساخته شده است یا نه.",
  },
  { key: "data", label: "داده", hint: "شمار، خوانش یا مدخلی نادرست است." },
  { key: "bug", label: "ایراد برنامه", hint: "چیزی کار نمی‌کند." },
];

const VERDICTS: { key: Verdict; label: string }[] = [
  { key: "good", label: "درست و به‌کار‌آمدنی" },
  { key: "possible", label: "درست ساخته، ولی نامأنوس" },
  { key: "wrong", label: "این دستور نباید اینجا اجرا می‌شد" },
  { key: "unsure", label: "نیاز به گفت‌وگو" },
];

export interface FormProps {
  subject: Subject;
  account: Account;
  /** The route and the query, added to every record. */
  where: Record<string, unknown>;
  onDone: () => void;
}

export function Form({ subject, account, where, onDone }: FormProps) {
  const [category, setCategory] = useState<Category | null>(null);
  const [verdict, setVerdict] = useState<Verdict | null>(null);
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Two different reasons a verdict cannot be given, and they are not the
  // same sentence to a reader. One is about the account; the other is about
  // what is being judged — *is this app good, possible or wrong* is not a
  // question, and docs/REVIEW.md maps the app to a bug report.
  const judgeable = subject.target_type !== "app";
  const gradeable = judgeable && account.may_leave_a_verdict;
  const ready =
    category !== null &&
    (category !== "linguistic" || verdict !== null) &&
    (category === "linguistic" || note.trim().length > 0);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!category || !ready) return;
    setSending(true);
    setError(null);
    const record: FeedbackIn = {
      category,
      target_type: subject.target_type,
      target_id: subject.target_id ?? null,
      verdict: category === "linguistic" ? verdict : null,
      note: note.trim() || null,
      context: { ...where, ...(subject.context ?? {}) },
      corpus_version: subject.corpus_version ?? null,
    };
    try {
      await leave(record);
      onDone();
    } catch (reason) {
      setError(
        reason instanceof ApiError && reason.trouble === "not-allowed"
          ? "این حساب اجازهٔ داوری زبانی ندارد."
          : "بازخورد ثبت نشد. کمی بعد دوباره بیازمایید.",
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <form className={styles.form} onSubmit={submit}>
      <fieldset className={styles.fieldset}>
        <legend className={styles.legend}>دربارهٔ چه می‌گویید؟</legend>
        <div className={styles.choices}>
          {CATEGORIES.map((one) => {
            const barred = one.key === "linguistic" && !gradeable;
            const why = judgeable
              ? "تنها برای حساب کارشناس"
              : "داوری زبانی دربارهٔ خودِ برنامه معنا ندارد";
            return (
              <button
                key={one.key}
                type="button"
                disabled={barred}
                aria-pressed={category === one.key}
                className={category === one.key ? styles.chosen : styles.choice}
                onClick={() => {
                  setCategory(one.key);
                  setVerdict(null);
                }}
              >
                <span>{one.label}</span>
                <span className={styles.hint}>
                  {barred ? why : one.hint}
                </span>
              </button>
            );
          })}
        </div>
      </fieldset>

      {category === "linguistic" ? (
        <fieldset className={styles.fieldset}>
          <legend className={styles.legend}>داوری</legend>
          <div className={styles.choices}>
            {VERDICTS.map((one) => (
              <button
                key={one.key}
                type="button"
                aria-pressed={verdict === one.key}
                className={verdict === one.key ? styles.chosen : styles.choice}
                onClick={() => setVerdict(one.key)}
              >
                {one.label}
              </button>
            ))}
          </div>
        </fieldset>
      ) : null}

      {category ? (
        <p className={styles.field}>
          <label className={styles.label} htmlFor="feedback-note">
            یادداشت{category === "linguistic" ? " (اختیاری)" : ""}
          </label>
          <textarea
            id="feedback-note"
            className={styles.note}
            rows={4}
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
        </p>
      ) : null}

      {error ? (
        <p className={styles.trouble} role="alert">
          {error}
        </p>
      ) : null}

      <div className={styles.actions}>
        <button type="submit" className={styles.send} disabled={!ready || sending}>
          {sending ? "در حال ثبت…" : "ثبت"}
        </button>
        <p className={styles.forever}>
          بازخورد ثبت‌شده پس نمی‌گردد و ویرایش نمی‌شود؛ این مجموعه سنجهٔ
          ارزیابی است.
        </p>
      </div>
    </form>
  );
}
