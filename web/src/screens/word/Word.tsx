/**
 * Everything known about one word.
 *
 * **Readings are never merged.** مرد is *mard* and *mord*, and showing one and
 * calling it the word would invent a third. Every reading of the spelling is
 * listed, with the one being read marked, and each links to its own page.
 *
 * **A count is only true for one corpus version**, so the version is on the
 * page rather than assumed.
 *
 * The citations are the only part of the evidence a reader can check for
 * themselves, so they are not behind an expander.
 */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import { word as fetchWord, type WordDetail } from "../../api/search";
import { useSubject } from "../../feedback/subject";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import {
  ALSO_WRITTEN,
  FROM_LEXICON,
  FUNCTION_WORD_HOMOGRAPH,
  FUNCTION_WORD_LETTERS,
  NO_READING,
  wasCut,
} from "../../text/lexicon";
import { persianCentury } from "../../text/numbers";
import { Dispersion } from "./Dispersion";
import styles from "./Word.module.css";

export function Word() {
  const { wordId = "" } = useParams();
  const [detail, setDetail] = useState<WordDetail | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    if (!wordId) return;
    const stop = new AbortController();
    setError(null);
    fetchWord(wordId, stop.signal)
      .then((found) => {
        setDetail(found);
        document.title = `${found.word.spelling_fa} — مورفولو`;
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setDetail(null);
        setError(
          reason instanceof ApiError
            ? reason
            : new ApiError("unreachable", 0, String(reason)),
        );
      });
    return () => stop.abort();
  }, [wordId]);

  // *This count looks wrong* is one of docs/REVIEW.md's targets, and the
  // count is the whole of this screen. Declared before the early returns,
  // because a hook may not be conditional.
  useSubject(
    detail
      ? {
          target_type: "statistic",
          target_id: detail.id,
          label: detail.word.spelling_fa,
          corpus_version: detail.word.corpus_version ?? null,
          context: {
            spelling_fa: detail.word.spelling_fa,
            latin: detail.word.latin ?? null,
            total_count: detail.word.total_count ?? null,
            doc_count: detail.word.doc_count ?? null,
            author_count: detail.word.author_count ?? null,
            readings: detail.readings.map((one) => one.latin),
          },
        }
      : null,
  );

  if (error) {
    return (
      <article className={styles.screen}>
        <h1>واژه</h1>
        <p className={styles.trouble}>
          {error.trouble === "missing"
            ? "این واژه در پیکرهٔ کنونی نیست."
            : "پاسخی از سرور نرسید. کمی بعد دوباره بیازمایید."}
        </p>
        <Link to="/">بازگشت به جست‌وجو</Link>
      </article>
    );
  }

  if (!detail) {
    return (
      <article className={styles.screen}>
        <h1>واژه</h1>
      </article>
    );
  }

  const word = detail.word;
  const others = detail.readings.filter((one) => one.id !== word.id);

  return (
    <article className={styles.screen}>
      <header className={styles.head}>
        <h1 className={styles.spelling}>{word.spelling_fa}</h1>
        {word.latin ? (
          <Latin className={styles.latin}>{word.latin}</Latin>
        ) : (
          <span className={styles.unread}>{NO_READING}</span>
        )}
        {word.lexicon_category ? (
          <span className={styles.category}>{word.lexicon_category}</span>
        ) : null}
        {/* A second pronunciation the dictionary itself lists. Distinct from
            the other *readings* below: those are different words sharing a
            spelling, this is one word the dictionary writes two ways. */}
        {/* The dictionary's own words, labelled as such. The «…» is appended
            only where karbon actually cut the text — 53.5% of v11's
            definitions — because the other 46.5% are whole sentences and an
            ellipsis after their full stop says the dictionary trailed off when
            it did not. See `wasCut`. */}
        {word.definition_fa ? (
          <p className={styles.definition}>
            <span className={styles.definitionLabel}>{FROM_LEXICON}</span>{" "}
            {word.definition_fa}
            {wasCut(word.definition_fa) ? "…" : ""}
          </p>
        ) : null}
        {word.latin_variants?.length ? (
          <p className={styles.note}>
            {ALSO_WRITTEN}{" "}
            {word.latin_variants.map((variant, index) => (
              <span key={variant}>
                {index > 0 ? "، " : ""}
                <Latin>{variant}</Latin>
              </span>
            ))}
          </p>
        ) : null}
      </header>

      {others.length > 0 ? (
        <section className={styles.block} aria-labelledby="readings">
          <h2 id="readings" className={styles.blockTitle}>
            خوانش‌های دیگر همین املا
          </h2>
          <p className={styles.note}>
            یک املا می‌تواند چند واژه باشد. اینها یکی نمی‌شوند.
          </p>
          <ul className={styles.readings}>
            {others.map((one) => (
              <li key={one.id}>
                <Link to={`/word/${encodeURIComponent(one.id)}`}>
                  <Latin>{one.latin ?? "—"}</Latin>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className={styles.block} aria-labelledby="evidence">
        <h2 id="evidence" className={styles.blockTitle}>
          شواهد
        </h2>
        {/* The letters are a function word's. A reading then carries no
            count — said, not shown as zero — and the spelling's own page says
            whose count it holds. */}
        {word.function_word ? (
          <p className={styles.note}>
            {word.latin ? FUNCTION_WORD_HOMOGRAPH : FUNCTION_WORD_LETTERS}
          </p>
        ) : null}
        {word.function_word && word.latin ? null : (
          <dl className={styles.stats}>
            <div>
              <dt>همه‌ٔ کاربردها</dt>
              <dd>
                <Num value={word.total_count ?? 0} />
              </dd>
            </div>
            <div>
              <dt>در چند سروده</dt>
              <dd>
                <Num value={word.doc_count ?? 0} />
              </dd>
            </div>
            <div>
              <dt>از چند شاعر</dt>
              <dd>
                <Num value={word.author_count ?? 0} />
              </dd>
            </div>
            {word.first_century != null && word.last_century != null ? (
              <div>
                <dt>از سده</dt>
                <dd>
                  {persianCentury(word.first_century)} تا{" "}
                  <Num value={word.last_century} />
                </dd>
              </div>
            ) : null}
          </dl>
        )}

        {word.function_word && word.latin ? null : (
          <Dispersion
            counts={word.counts_by_century ?? {}}
            total={word.total_count ?? 0}
          />
        )}

        <p className={styles.version}>
          این شمارش‌ها تنها برای نسخهٔ{" "}
          <Latin>{word.corpus_version ?? "?"}</Latin> پیکره درست است.
        </p>
      </section>

      <section className={styles.block} aria-labelledby="citations">
        <h2 id="citations" className={styles.blockTitle}>
          شاهدمثال‌ها
        </h2>
        {detail.citations.length === 0 ? (
          <p className={styles.note}>
            بیتی برای نشان‌دادن پیدا نشد. این به معنای نبودن واژه نیست.
          </p>
        ) : (
          <ul className={styles.citations}>
            {detail.citations.map((one) => (
              <li key={one.document_id} className={styles.citation}>
                <p className={styles.line}>{one.line}</p>
                <p className={styles.source}>
                  {one.author ?? "بی‌نام"}
                  {one.title ? ` — ${one.title}` : ""}
                  {one.century != null ? ` — ${persianCentury(one.century)}` : ""}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </article>
  );
}
