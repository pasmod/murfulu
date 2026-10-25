/**
 * The search screen.
 *
 * The query lives in the address bar, so a search can be linked to, bookmarked
 * and reloaded. Everything else follows from it.
 *
 * **The two-group split is the reason this screen exists.** `*nā` returns
 * *Tonoknā*, which was formed with the affix, next to *Fanā*, an Arabic loan
 * where those letters are not a suffix at all. Mixing them makes the search
 * useless for studying an affix. The groups are separated, labelled, and the
 * first is shown even when it is empty — because "nothing was formed this way"
 * and "we have not worked out what was formed this way" are different answers,
 * and today it is the second one. See PLAN 6.4.
 */

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import { affixOf, search, type SearchResult } from "../../api/search";
import { Num } from "../../text/Num";
import { SCREENS } from "../../shell/screens";
import { Facets } from "./Facets";
import { QueryBox } from "./QueryBox";
import styles from "./Search.module.css";
import { Results } from "./Results";

/**
 * Why a query could not be read, in Persian.
 *
 * The parser's own messages are English — *poem: is not a searchable field* —
 * and they were printed straight under a Persian heading until 2026-08-17. The
 * API now names the fault instead, and this says it. Each one names what to do
 * next rather than only what was wrong, which is what FRONTEND.md asks of an
 * error state.
 */
const UNREADABLE: Record<string, (facts: Record<string, string>) => string> = {
  "unknown-field": (facts) =>
    `«${facts.name}» چیزی نیست که بتوان بر آن جست‌وجو کرد. راهنمای نحو را باز کنید تا ببینید چه چیزهایی هست.`,
  "no-value": (facts) =>
    `پس از «${facts.name}:» چیزی نوشته نشده است. برای نمونه: ${facts.name}:x`,
  "bad-count": (facts) =>
    `بسامد باید عدد باشد، نه «${facts.value}». برای نمونه: count:1 یا count:>10`,
  "bad-century": (facts) =>
    `سده باید عدد یا بازه باشد، نه «${facts.value}». برای نمونه: century:10 یا century:10-13`,
  "century-backwards": (facts) =>
    `در «${facts.value}» سدهٔ آغاز از سدهٔ پایان بزرگ‌تر است. جای دو عدد را عوض کنید.`,
  "two-patterns": (facts) =>
    `دو الگو با هم آمده است: «${facts.first}» و «${facts.second}». تنها یکی را نگه دارید.`,
  "only-stars": () =>
    "الگویی که تنها ستاره است همه‌چیز را می‌گیرد. چند حرف هم بنویسید، مثلاً *nā",
  "unbalanced-quotes": () => "گیومه‌ای بسته نشده است.",
  empty: () => "جست‌وجو خالی است.",
};

/** What went wrong, said in a way that tells the reader what to do next. */
function trouble(error: ApiError): { title: string; advice: string } {
  if (error.trouble === "unreadable-query") {
    const said = error.reason ? UNREADABLE[error.reason.code] : undefined;
    return {
      title: "این جست‌وجو خوانده نشد.",
      // An API that has not been updated yet, or a fault this list has no
      // sentence for, still says *something* — and a general sentence in
      // Persian is better than a precise one in English.
      advice: said
        ? said(error.reason!.facts)
        : "چیزی در این جست‌وجو خوانده نشد. راهنمای نحو را باز کنید تا شکل درست را ببینید.",
    };
  }
  if (error.trouble === "not-built") {
    return {
      title: "هنوز پیکره‌ای برای جست‌وجو ساخته نشده است.",
      advice: "پس از اجرای درون‌ریزی پیکره، این صفحه کار خواهد کرد.",
    };
  }
  return {
    title: "پاسخی از سرور نرسید.",
    advice: "کمی بعد دوباره بیازمایید.",
  };
}

/** The screen's own name and purpose, from the one list the menu also reads. */
const SCREEN = SCREENS.find((one) => one.path === "/")!;

export function Search() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";

  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    document.title = `${SCREEN.title} — مورفولو`;
  }, []);

  useEffect(() => {
    if (!query) {
      setResult(null);
      setError(null);
      return;
    }
    const stop = new AbortController();
    setBusy(true);
    setError(null);
    search({ q: query, affix: affixOf(query), size: 50 }, stop.signal)
      .then((found) => setResult(found))
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setResult(null);
        setError(
          reason instanceof ApiError
            ? reason
            : new ApiError("unreachable", 0, String(reason)),
        );
      })
      .finally(() => setBusy(false));
    return () => stop.abort();
  }, [query]);

  const run = useCallback(
    (next: string) => {
      setParams(next ? { q: next } : {}, { replace: false });
    },
    [setParams],
  );

  return (
    <article className={styles.screen}>
      <h1>{SCREEN.title}</h1>
      <p className={styles.purpose}>{SCREEN.purpose}</p>

      <QueryBox value={query} onSearch={run} busy={busy} />

      {error ? (
        <div className={styles.trouble} role="status">
          <p className={styles.troubleTitle}>{trouble(error).title}</p>
          <p className={styles.troubleAdvice}>{trouble(error).advice}</p>
        </div>
      ) : null}

      {result ? (
        <div className={styles.answer}>
          <p className={styles.total} role="status">
            <Num value={result.total} /> واژه یافت شد.
          </p>
          <div className={styles.columns}>
            <Results result={result} affix={affixOf(query)} />
            <Facets facets={result.facets} query={query} onNarrow={run} />
          </div>
        </div>
      ) : null}
    </article>
  );
}
