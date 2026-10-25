/**
 * Writing a ruling.
 *
 * **Options first, and the box is always there.** The project lead asked on
 * 2026-10-18 for the questions to become a multiple-choice form: each one
 * offers a few options as full Persian sentences, he picks one — and a free-text
 * box sits under them on every question, whether or not he picks anything, so
 * he can say what no option says, or answer in his own words alone. One submit
 * per question. A question without options is the box alone, as before.
 *
 * **What is sent.** The option's id and whatever is written. Neither is
 * refused here and by the API; an option with nothing written is stored in the
 * option's own Persian, so a ruling always reads as a sentence.
 *
 * **One box, and it is Persian.** There were three — Persian, then Behnevis,
 * then an English rendering — and the project lead asked on 2026-08-20 why the
 * last two were there at all. They were there for us. Nothing is lost that was
 * written: `ruling_latin` and `ruling_en` stay in the store and in the export.
 *
 * **Answering again is offered rather than hidden.** A question that already
 * has a ruling can be ruled on a second time — the earlier one is kept and the
 * screen says the answer changed. So the form stays, with a checkbox saying
 * that this reverses the previous answer, because a reversal that does not
 * announce itself reads as though the grammar had always said this.
 */

import { useId, useState } from "react";

import { ApiError } from "../../api/client";
import { rule, type Choice } from "../../api/questions";
import styles from "./Questions.module.css";

export function Answer({
  reference,
  choices = [],
  answered,
  onAnswered,
}: {
  reference: string;
  choices?: Choice[];
  answered: boolean;
  onAnswered: () => void;
}): React.ReactElement {
  const [chosen, setChosen] = useState<string | null>(null);
  const [persian, setPersian] = useState("");
  const [reverses, setReverses] = useState(false);
  const [sending, setSending] = useState(false);
  const [trouble, setTrouble] = useState<string | null>(null);
  const group = useId();

  const empty = !persian.trim() && !chosen;
  const offers = choices.length > 0;

  async function send(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    if (empty || sending) return;
    setSending(true);
    setTrouble(null);
    try {
      await rule(reference, {
        ruling_fa: persian.trim(),
        choice_id: chosen,
        ruling_latin: null,
        ruling_en: null,
        supersedes_earlier: reverses,
      });
      setChosen(null);
      setPersian("");
      setReverses(false);
      onAnswered();
    } catch (failed: unknown) {
      setTrouble(
        failed instanceof ApiError && failed.trouble === "not-allowed"
          ? "این حساب اجازهٔ پاسخ دادن ندارد."
          : failed instanceof Error
            ? failed.message
            : String(failed),
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <form className={styles.answer} onSubmit={send}>
      {offers ? (
        <fieldset className={styles.choices}>
          <legend>{answered ? "پاسخ تازه: یک گزینه را برگزینید" : "یک گزینه را برگزینید"}</legend>
          {choices.map((one) => (
            <label
              key={one.id}
              className={styles.choice}
              data-chosen={chosen === one.id ? "true" : undefined}
            >
              <input
                type="radio"
                name={group}
                value={one.id}
                checked={chosen === one.id}
                onChange={() => setChosen(one.id)}
              />
              <span className={styles.choiceText}>
                {one.text_fa}
                {one.suggested ? (
                  <span className={styles.suggested}>پیشنهاد ما</span>
                ) : null}
              </span>
            </label>
          ))}
          {chosen ? (
            <button
              type="button"
              className={styles.clearChoice}
              onClick={() => setChosen(null)}
            >
              برداشتن گزینه
            </button>
          ) : null}
        </fieldset>
      ) : null}

      <label className={styles.written}>
        {offers
          ? "توضیح یا پاسخ خودتان"
          : answered
            ? "پاسخ تازه"
            : "پاسخ"}
        {offers ? (
          <span className={styles.hint}>
            می‌توانید تنها گزینه‌ای را برگزینید، تنها بنویسید، یا هر دو.
          </span>
        ) : null}
        <textarea
          value={persian}
          onChange={(e) => setPersian(e.currentTarget.value)}
          rows={3}
          placeholder={
            offers
              ? "هر چه می‌خواهید دربارهٔ این پرسش بنویسید."
              : "پاسخ خود را به فارسی بنویسید."
          }
        />
      </label>

      {answered ? (
        <label className={styles.reverses}>
          <input
            type="checkbox"
            checked={reverses}
            onChange={(e) => setReverses(e.currentTarget.checked)}
          />
          این پاسخ، پاسخ پیشین را نقض می‌کند
        </label>
      ) : null}

      {trouble ? <p className={styles.trouble}>{trouble}</p> : null}

      <button type="submit" className={styles.send} disabled={empty || sending}>
        {sending ? "در حال ثبت…" : "ثبت پاسخ"}
      </button>
    </form>
  );
}
