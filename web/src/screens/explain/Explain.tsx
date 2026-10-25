/**
 * The reverse of building: paste a word, see what it is made of.
 *
 * **Every account shown was rebuilt.** The check proposes an analysis by
 * stripping an affix, then builds the remainder forward again and keeps only
 * what reproduces the word. That round trip is why *مولانا* comes back
 * unexplained: stripping *-nā* leaves a word the dictionary knows, and
 * nothing can build it back.
 *
 * **More than one account is the normal case, and none of them is chosen.**
 * *Raveš* can be built from two different verbs; which is meant is a question
 * about meaning and belongs to the linguist, not to this screen.
 *
 * **Not explained is not the same as not a word.** Most words are simple —
 * measured on 200 corpus words with a reading, 14% have an account — so the
 * screen says what it tried rather than implying the word is malformed.
 */

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import { explain as fetchExplain, type Explanation } from "../../api/explain";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { LEXICON } from "../../text/lexicon";
import { SCREENS } from "../../shell/screens";
import { Account } from "./Account";
import styles from "./Explain.module.css";

const SCREEN = SCREENS.find((one) => one.path === "/explain")!;

/**
 * Whether the reader typed Persian script rather than the Behnevis.
 *
 * The check works on the Behnevis form and on nothing else — *Goftār* is taken
 * apart, گفتار is not — while every other screen in the app takes Persian.
 * Answering a Persian word with *most words are simple* would give a reason
 * that is not the reason, so the script is named instead.
 */
const PERSIAN = /[؀-ۿ]/;

export function Explain() {
  const [params, setParams] = useSearchParams();
  const word = params.get("word") ?? "";
  const [draft, setDraft] = useState(word);
  // The address can change without the box changing it — the Back button is
  // where a reader meets this. Seeding the draft once left the screen
  // answering about Ravandegi with Goftār still in the box: one word shown,
  // another named.
  //
  // **In an effect, deliberately.** Adjusting the state during the render is
  // React's shorter answer for this and it does not survive here: the router
  // navigates inside a transition, and a render-time adjustment made during
  // one can be thrown away when the transition replays. Measured, not
  // assumed — a browser test walking the Back button failed every run on the
  // render-time version and passes on this one.
  useEffect(() => setDraft(word), [word]);
  const [found, setFound] = useState<Explanation | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    document.title = `${SCREEN.title} — مورفولو`;
  }, []);

  useEffect(() => {
    if (!word) {
      setFound(null);
      return;
    }
    const stop = new AbortController();
    setError(null);
    fetchExplain(word, stop.signal)
      .then(setFound)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setFound(null);
        setError(
          reason instanceof ApiError
            ? reason
            : new ApiError("unreachable", 0, String(reason)),
        );
      });
    return () => stop.abort();
  }, [word]);

  const run = useCallback(
    (next: string) => setParams(next ? { word: next } : {}),
    [setParams],
  );

  return (
    <article className={styles.screen}>
      <h1>{SCREEN.title}</h1>
      <p className={styles.purpose}>{SCREEN.purpose}</p>

      <form
        className={styles.box}
        onSubmit={(event) => {
          event.preventDefault();
          run(draft.trim());
        }}
      >
        <label className={styles.label} htmlFor="analyse">
          واژه‌ای به بهنویس بنویسید
        </label>
        <div className={styles.row}>
          <input
            id="analyse"
            className={styles.input}
            dir="auto"
            autoComplete="off"
            placeholder="Ravandegi"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <button className={styles.submit} type="submit">
            بشکاف
          </button>
        </div>
        {!word ? (
          <button
            type="button"
            className={styles.example}
            onClick={() => {
              setDraft("Ravandegi");
              run("Ravandegi");
            }}
          >
            برای نمونه: Ravandegi
          </button>
        ) : null}
      </form>

      {error ? (
        <p className={styles.trouble} role="status">
          {error.trouble === "unreadable-query" ? (
            // The one refusal left after S11: a Persian spelling the
            // dictionary does not hold. It cannot be read into Behnevis — the
            // measured accuracy of guessing that is 5.8% — so the reader is
            // asked for the Behnevis rather than given a wrong base under a
            // real chain of rules.
            <>
              این املا در {LEXICON} نیست، پس نمی‌دانیم چگونه خوانده می‌شود.
              واژه را به بهنویس بنویسید — برای نمونه <Latin>Goftār</Latin>{" "}
              به‌جای گفتار.
            </>
          ) : (
            "پاسخی از سرور نرسید. کمی بعد دوباره بیازمایید."
          )}
        </p>
      ) : null}

      {found?.rebuilt ? (
        <section className={styles.results} aria-labelledby="accounts">
          <h2 id="accounts" className={styles.resultsTitle}>
            <Num value={found.accounts.length} /> راه ممکن
          </h2>
          <p className={styles.note}>
            یک املا می‌تواند از چند راه ساخته شده باشد. هر راهی که اینجا
            می‌بینید با دستورهای واقعی دقیقاً به همین املا می‌رسد؛ راه‌هایی که
            نمی‌رسیدند کنار گذاشته شده‌اند. اینکه کدام‌یک معنای مورد نظر شماست،
            از روی املا معلوم نمی‌شود.
          </p>
          {PERSIAN.test(found.word) && found.analysed_as.length > 0 ? (
            <p className={styles.note}>
              این املا در {LEXICON} چنین خوانده می‌شود و هر خوانش جداگانه شکافته
              شد:{" "}
              {found.analysed_as.map((form) => (
                <Latin key={form}>{form}</Latin>
              ))}
            </p>
          ) : null}
          <ol className={styles.accounts} aria-labelledby="accounts">
            {found.accounts.map((account, index) => (
              <Account key={index} account={account} form={account.form_latin} />
            ))}
          </ol>
        </section>
      ) : null}

      {found && !found.rebuilt ? (
        <section className={styles.nothing} aria-labelledby="nothing">
          <h2 id="nothing" className={styles.resultsTitle}>
            {/*
              Two different answers, and they used to be one sentence.

              The engine stops at 20,000 forms for one base, and افکندن reaches
              that at three steps — so درافکندگی was told "no way was found"
              when the search had simply not got that far. Every rule its chain
              needs exists and fires. مولانا is the real refusal, and it must
              not read the same as an unfinished search.
            */}
            {found.settled
              ? "راهی برای ساختن این واژه پیدا نشد"
              : "جست‌وجو ناتمام ماند"}
          </h2>
          {!found.settled ? (
            <p className={styles.note}>
              شمار واژه‌هایی که از این پایه ساخته می‌شود از مرز موتور گذشت، پس
              جست‌وجو پیش از پایان بازایستاد. این <b>به معنای ساخته‌نشدن نیست</b>
              — یعنی هنوز نمی‌دانیم. پایه‌ای که جا کم آورد:{" "}
              {found.searched_partially.map((base) => (
                <Latin key={base}>{base}</Latin>
              ))}
            </p>
          ) : null}
          {/*
            Both of these explain a *settled* no — "most words are simple" is
            not the reason when the search never finished, and offering it
            there would be the same wrong-reason failure S11 fixed.
          */}
          {!found.settled ? null : PERSIAN.test(found.word) &&
            found.analysed_as.length > 0 ? (
            <p className={styles.note}>
              این املا چنین خوانده شد و هیچ‌یک ساخته نشد:{" "}
              {found.analysed_as.map((form) => (
                <Latin key={form}>{form}</Latin>
              ))}
              . این به معنای نادرست بودن واژه نیست.
            </p>
          ) : (
            <p className={styles.note}>
              این به معنای نادرست بودن واژه نیست. بیشتر واژه‌ها ساخته نشده‌اند؛
              ساده‌اند یا وام‌واژه.
            </p>
          )}
          {found.affixes_tried_without_a_base.length > 0 ? (
            <p className={styles.tried}>
              این وندها آزموده شد، ولی آنچه می‌ماند در {LEXICON} نبود:{" "}
              {found.affixes_tried_without_a_base.map((affix) => (
                <Latin key={affix} affix>
                  {affix}
                </Latin>
              ))}
            </p>
          ) : null}
        </section>
      ) : null}
    </article>
  );
}
