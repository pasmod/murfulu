/**
 * The automatic suggestion beside a listed unsure spelling, as the screens
 * show it (the project lead's request of 2026-11-22): the reading, how often
 * a reading at its certainty was right in a test, the line it was read in,
 * and what the editions' vowel signs say of it.
 *
 * **Only shown, never applied.** The box's button fills the panel's own
 * controls — the offered reading picked, or the reading in the field where a
 * person types one — and the person still chooses how far it reaches and
 * saves it. The screens never name what made it: «پیشنهاد خودکار», and the
 * method in one paragraph a reader can open.
 */

import type { Suggestion as Suggested } from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { type Use, contextOf, outOf100 } from "./suggested";
import styles from "./Suggestion.module.css";

/** How many marked places the editions' signs need before the box quotes them. */
const MIN_MARKED = 5;

/** The suggestion in a row of the list: the reading, and right in so many of 100. */
export function SuggestionTag({ suggestion }: { suggestion: Suggested }) {
  return (
    <span className={styles.tag}>
      پیشنهاد خودکار: <Latin>{suggestion.latin}</Latin>
      {suggestion.right_share !== null ? (
        <span className={styles.tagShare}>
          {" "}
          (<Num value={outOf100(suggestion.right_share)} /> از <Num value={100} />)
        </span>
      ) : null}
    </span>
  );
}

/** Beside a reading the panel offers: this one is the suggestion. */
export function SuggestedMark() {
  return <span className={styles.mark}>پیشنهاد خودکار</span>;
}

export interface SuggestionBoxProps {
  suggestion: Suggested;
  /** The offered readings that are the suggestion (several: *Xod*, *xod*). */
  among: string[];
  /** How the button takes it up; null: no button, the person picks. */
  use: Use | null;
  onUse: (use: Use) => void;
  busy?: boolean;
  /** The bank's one reading, where the spelling's kind is «one». */
  bankOne?: string | null;
  /** On the reading screen: whether this line is the one it was read in. */
  here?: boolean;
  /** The panel already says how the editions' marks fit this very reading. */
  marksSaid?: boolean;
}

export function SuggestionBox({
  suggestion,
  among,
  use,
  onUse,
  busy = false,
  bankOne = null,
  here,
  marksSaid = false,
}: SuggestionBoxProps) {
  const read = contextOf(suggestion.context);
  const marked =
    !marksSaid && suggestion.marked && suggestion.marked.checked >= MIN_MARKED
      ? suggestion.marked
      : null;
  return (
    <section className={styles.box} aria-label="پیشنهاد خودکار">
      <p className={styles.head}>
        پیشنهاد خودکار: <Latin className={styles.latin}>{suggestion.latin}</Latin>
      </p>
      <p className={styles.share}>
        {suggestion.right_share !== null ? (
          <>
            در آزمون، از هر <Num value={100} /> پیشنهاد با این اطمینان{" "}
            <Num value={outOf100(suggestion.right_share)} /> تا درست بود.
          </>
        ) : (
          "اطمینانِ این پیشنهاد سنجیده نشده است."
        )}
      </p>
      {read ? (
        <p className={styles.note}>
          {here === true
            ? "این پیشنهاد برای همین سطر است: "
            : here === false
              ? "این پیشنهاد برای سطر دیگری است: "
              : "این پیشنهاد از یک سطر آمده است: "}
          «{read.before ? `${read.before} ` : null}
          <mark className={styles.hit}>{read.word}</mark>
          {read.after ? ` ${read.after}` : null}»
          {here === false ? ". ببینید اینجا هم درست است یا نه." : "."}
        </p>
      ) : null}
      {marked ? (
        <p className={styles.note} data-weak={marked.fit < marked.checked / 2 || undefined}>
          ویراستاران این املا را در <Num value={marked.checked} /> جا اعراب گذاشته‌اند و اعرابِ{" "}
          <Num value={marked.fit} /> جا با این پیشنهاد جور است.
          {marked.fit < marked.checked / 2
            ? " ویراستاران بیشتر جاهای دشوار را اعراب می‌گذارند؛ یعنی این املا دست‌کم در برخی جاها جور دیگری خوانده می‌شود. پیش از «همه‌جا» نمونه‌ها را ببینید."
            : null}
        </p>
      ) : null}
      {bankOne && !suggestion.in_bank ? (
        <p className={styles.note}>
          این پیشنهاد با تنها خوانشِ بانک واژه (<Latin>{bankOne}</Latin>) یکی نیست.
        </p>
      ) : null}
      {among.length > 1 ? (
        <p className={styles.note}>
          پیشنهاد خودکار حرف بزرگ نمی‌نویسد، پس میان{" "}
          {among.map((one, i) => (
            <span key={one}>
              {i > 0 ? " و " : null}
              <Latin>{one}</Latin>
            </span>
          ))}{" "}
          فرق نمی‌گذارد. یکی را خودتان برگزینید.
        </p>
      ) : null}
      {use?.how === "type" && use.latin === suggestion.latin ? (
        <p className={styles.note}>
          این خوانش در گزینه‌ها نیست و پیشنهاد خودکار حرف بزرگ نمی‌نویسد. اگر این واژه نام است،
          پیش از ثبت حرف نخستش را بزرگ کنید.
        </p>
      ) : null}
      {use ? (
        <button type="button" className={styles.use} disabled={busy} onClick={() => onUse(use)}>
          {use.how === "pick" ? (
            <>
              «<Latin>{use.latin}</Latin>» را برگزین
            </>
          ) : (
            <>
              «<Latin>{use.latin}</Latin>» را در جای نوشتن بگذار
            </>
          )}
        </button>
      ) : null}
      <details className={styles.about}>
        <summary>این پیشنهاد از کجا آمده است؟</summary>
        <p>
          پیشنهاد خودکار جدا از خوانشِ برنامه است. یک بار، بیرون از این سایت، هر املا با دو
          واژهٔ کنارش در یک سطر خوانده شده است، بی‌آنکه اعراب یا پاسخ درست دیده شود. درستیِ آن
          را روی{" "}
          {suggestion.tested_words ? (
            <>
              <Num value={suggestion.tested_words} />{" "}
            </>
          ) : null}
          واژهٔ اعراب‌دار آزموده‌ایم که برنامه از آن‌ها نیاموخته بود؛ این واژه‌ها از
          دشوارترین‌ها هستند، نه از این واژه‌های پرتکرار. چون فقط یک سطر خوانده
          شده، برای املایی که چند خوانش دارد پیشنهاد فقط خوانشِ همان سطر است، نه لزوماً همه‌جا.
          هیچ تصمیمی خودکار گرفته نمی‌شود: تا کسی پیشنهاد را ثبت نکند، چیزی عوض نمی‌شود.
        </p>
      </details>
    </section>
  );
}
