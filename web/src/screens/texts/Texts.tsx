/**
 * The reading screen: any text of the corpus, word by word, in Persian script
 * and in Behnevis.
 *
 * Asked for by the linguist (IDEAS item 12), widened by the project lead to
 * **any text, not only poetry**, because the corpus will take prose and other
 * books; built as direction A of the 2026-11-13 drafts, the one the project
 * lead chose. Everything lives in the address, so a text, a line and a word
 * can be linked to:
 *
 *   ?q=حافظ غزل ۳                    texts whose heading holds every word
 *   ?text=ganjoor:hafez:2132           one text
 *   &unit=4&word=دل                    opened at a unit, a citation's word marked
 *   ?view=marked                       the readings marked wrong, for review
 */

import { type FormEvent, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import { type TextFound, findTexts, headingOf } from "../../api/texts";
import { SCREENS } from "../../shell/screens";
import { Num } from "../../text/Num";
import { Waiting } from "../../text/Waiting";
import { Marked } from "./Marked";
import { Reader } from "./Reader";
import styles from "./Texts.module.css";

const SCREEN = SCREENS.find((one) => one.path === "/texts")!;

/** Ready to press, so an empty screen is never a dead end. */
const EXAMPLES = ["حافظ غزل ۳", "گلستان دیباچه"];

function whole(value: string | null): number | null {
  if (value === null || value === "") return null;
  const number = Number(value);
  return Number.isInteger(number) && number >= 0 ? number : null;
}

export function Texts() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const textId = params.get("text") ?? "";
  const view = params.get("view") ?? "";
  const [typed, setTyped] = useState(q);

  useEffect(() => {
    setTyped(q);
  }, [q]);

  useEffect(() => {
    if (!textId) document.title = `${SCREEN.title} — مورفولو`;
  }, [textId]);

  function open(event: FormEvent) {
    event.preventDefault();
    const asked = typed.trim();
    setParams(asked ? { q: asked } : {});
  }

  return (
    <article className={styles.screen}>
      <h1>{SCREEN.title}</h1>
      <p className={styles.purpose}>{SCREEN.purpose}</p>

      <form className={styles.open} onSubmit={open} role="search">
        <label htmlFor="text-query">متنی را باز کنید</label>
        <div className={styles.row}>
          <input
            id="text-query"
            className={styles.input}
            type="search"
            dir="auto"
            autoComplete="off"
            value={typed}
            onChange={(event) => setTyped(event.target.value)}
            placeholder="نویسنده، کتاب یا عنوان"
            maxLength={120}
          />
          <button type="submit" className={styles.go}>
            باز کن
          </button>
        </div>
        <p className={styles.hint}>
          از شاهدمثال‌های یک واژه، در صفحهٔ همان واژه، هم می‌شود درست به همان سطر رسید.
        </p>
      </form>

      {textId ? (
        <>
          {q ? (
            <p className={styles.back}>
              <Link to={`/texts?q=${encodeURIComponent(q)}`}>→ بازگشت به یافته‌های «{q}»</Link>
            </p>
          ) : null}
          <Reader
            documentId={textId}
            unit={whole(params.get("unit"))}
            word={params.get("word")}
            start={whole(params.get("start"))}
            onPage={(start) => {
              const next = new URLSearchParams(params);
              next.delete("unit");
              next.delete("word");
              next.set("start", String(start));
              setParams(next);
              window.scrollTo({ top: 0 });
            }}
          />
        </>
      ) : q ? (
        // Keyed on the search, so a page still loading for the last one can
        // never land in this one's list.
        <Found key={q} q={q} />
      ) : view === "marked" ? (
        <Marked />
      ) : (
        <>
          <section className={styles.card} aria-labelledby="start">
            <h2 id="start" className={styles.title}>
              {SCREEN.invitation}
            </h2>
            <div className={styles.examples}>
              {EXAMPLES.map((one) => (
                <button
                  key={one}
                  type="button"
                  className={styles.example}
                  onClick={() => setParams({ q: one })}
                >
                  {one}
                </button>
              ))}
            </div>
          </section>
          <Marked />
        </>
      )}
    </article>
  );
}

/** The texts a search found, the best first, twenty at a time. */
function Found({ q }: { q: string }) {
  const [found, setFound] = useState<TextFound | null>(null);
  const [more, setMore] = useState<TextFound["texts"]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stop = new AbortController();
    setFound(null);
    setMore([]);
    setError(null);
    findTexts(q, 0, stop.signal)
      .then(setFound)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(
          reason instanceof ApiError ? reason : new ApiError("unreachable", 0, String(reason)),
        );
      });
    return () => stop.abort();
  }, [q]);

  if (error) {
    return (
      <p className={styles.trouble} role="status">
        متن‌ها خوانده نشدند. کمی بعد دوباره بیازمایید.
      </p>
    );
  }
  if (!found) return <Waiting />;

  const shown = [...found.texts, ...more];
  return (
    <section className={styles.card} aria-labelledby="found">
      <h2 id="found" className={styles.title}>
        {found.total === 0 ? (
          <>متنی با «{q}» در سرآغازش پیدا نشد.</>
        ) : (
          <>
            <Num value={found.total} /> متن
          </>
        )}
      </h2>
      {found.total === 0 ? (
        <p className={styles.note}>
          نام نویسنده، کتاب یا بخش را کوتاه‌تر بنویسید؛ هر واژه‌ای که می‌نویسید باید در سرآغاز متن
          باشد.
        </p>
      ) : null}
      <ol className={styles.found}>
        {shown.map((one) => (
          <li key={one.document_id}>
            <Link
              className={styles.foundLink}
              to={`/texts?q=${encodeURIComponent(q)}&text=${encodeURIComponent(one.document_id)}`}
            >
              {headingOf(one).join(" · ")}
            </Link>
          </li>
        ))}
      </ol>
      {shown.length < found.total ? (
        <button
          type="button"
          className={styles.more}
          // One page at a time: two presses before the first answer would ask
          // for the same page twice and skip the next.
          disabled={loading}
          onClick={() => {
            setLoading(true);
            findTexts(q, shown.length)
              .then((next) => setMore((now) => [...now, ...next.texts]))
              .catch(() => undefined)
              .finally(() => setLoading(false));
          }}
        >
          بیشتر
        </button>
      ) : null}
    </section>
  );
}
