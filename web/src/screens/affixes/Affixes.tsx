/**
 * Affixes by meaning — the screen the project started from.
 *
 * A writer arrives with a meaning and leaves with an affix. So the meaning is
 * what is large on the page, and the affixes sit under it; the reverse would
 * be a grammar book with the index at the back, which is the thing this is
 * meant to replace.
 *
 * **Every Persian word here comes from the rule pack.** The gloss, the affix's
 * Persian spelling and the examples are all transcribed from the source
 * grammar. Nothing on this screen is written by a component.
 *
 * **The affixes the source says nothing about are shown, separately.**
 * Measured: 81 of 189. Hiding them would leave a reader believing the
 * inventory is complete; mixing them in would let them believe those affixes
 * had been checked and found meaningless.
 *
 * **And nineteen of those eighty-one are not affixes at all** — ten
 * compounding templates, six slots, three zero-derivations. Twelve of them
 * have a dash where the affix goes, because the source writes a dash: a
 * template joins two words with nothing between them. Rendered straight, that
 * was twelve identical blank chips in a row on a screen called *affixes*.
 * They are not dropped — a reader would then take the inventory for affixes
 * only — but they are shown as what they are, with their example, which is
 * the one readable thing about a rule whose affix is nothing.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  affixes as fetchAffixes,
  type AffixEntry,
  type Affixes as Data,
} from "../../api/affixes";
import { ApiError } from "../../api/client";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { SCREENS } from "../../shell/screens";
import styles from "./Affixes.module.css";
import { MeaningCard } from "./MeaningCard";

const SCREEN = SCREENS.find((one) => one.path === "/affixes")!;

/**
 * The three kinds that put something in front of, after, or inside a word.
 * Everything else in the pack builds without an affix.
 */
const AFFIXING = new Set(["suffix", "prefix", "infix"]);

function isAffix(rule: AffixEntry): boolean {
  return AFFIXING.has(rule.kind);
}

export function Affixes() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    document.title = `${SCREEN.title} — مورفولو`;
    const stop = new AbortController();
    fetchAffixes(undefined, stop.signal)
      .then(setData)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(
          reason instanceof ApiError
            ? reason
            : new ApiError("unreachable", 0, String(reason)),
        );
      });
    return () => stop.abort();
  }, []);

  // Two lists out of the one the API sends, split on what a rule *is*: the
  // affixes the source records no meaning for, and the rules that build with
  // no affix at all. Both are shown; neither is counted as the other.
  const silent = useMemo(
    () => (data?.without_a_meaning ?? []).filter(isAffix),
    [data],
  );
  const joined = useMemo(
    () => (data?.without_a_meaning ?? []).filter((one) => !isAffix(one)),
    [data],
  );

  const shown = useMemo(() => {
    if (!data) return [];
    const wanted = filter.trim();
    if (!wanted) return data.meanings;
    return data.meanings.filter(
      (meaning) =>
        (meaning.gloss_fa ?? "").includes(wanted) ||
        meaning.tag.toLowerCase().includes(wanted.toLowerCase()) ||
        meaning.affixes.some((one) => one.affix.includes(wanted)),
    );
  }, [data, filter]);

  /**
   * The meanings offered as buttons, because the box cannot be guessed.
   *
   * A `type="search"` box with a placeholder says *type anything*, and the
   * vocabulary it accepts is a closed set of 42 words transcribed from the
   * source grammar — a reader who types «مکان» gets nothing and learns
   * nothing. Reported by the project lead on 2026-08-18. So the set is on the
   * screen: the richest handful as buttons, and every one of the 42 in a
   * `datalist`, which is the browser's own suggestion list and needs no
   * component. Both are read off the API; no meaning is written here.
   */
  const suggested = useMemo(() => {
    const all = [...(data?.meanings ?? [])];
    all.sort((a, b) => b.affixes.length - a.affixes.length);
    return all.slice(0, 6);
  }, [data]);

  return (
    <article className={styles.screen}>
      <h1>{SCREEN.title}</h1>
      <p className={styles.purpose}>{SCREEN.purpose}</p>

      {error ? (
        <p className={styles.trouble} role="status">
          دستورها خوانده نشد. کمی بعد دوباره بیازمایید.
        </p>
      ) : null}

      {data ? (
        <>
          <label className={styles.filterLabel} htmlFor="meaning">
            میان معناها بگردید
          </label>
          <input
            id="meaning"
            className={styles.filter}
            type="search"
            dir="auto"
            autoComplete="off"
            list="meanings"
            placeholder="جا"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
          />
          <datalist id="meanings">
            {(data.meanings ?? []).map((meaning) => (
              <option key={meaning.tag} value={meaning.gloss_fa ?? meaning.tag} />
            ))}
          </datalist>

          {/* The buttons carry how many affixes each meaning holds: a reader
              choosing between «جا» and «ابزار» is choosing between 6 and 1,
              and that is the only thing distinguishing them before the click. */}
          <p className={styles.suggests}>
            <span className={styles.suggestsSays}>برای نمونه:</span>
            {suggested.map((meaning) => (
              <button
                key={meaning.tag}
                type="button"
                className={styles.suggest}
                aria-pressed={filter.trim() === (meaning.gloss_fa ?? meaning.tag)}
                onClick={() => setFilter(meaning.gloss_fa ?? meaning.tag)}
              >
                {meaning.gloss_fa ?? meaning.tag}
                <span className={styles.suggestCount}>
                  <Num value={meaning.affixes.length} />
                </span>
              </button>
            ))}
            {filter.trim() ? (
              <button
                type="button"
                className={styles.suggest}
                onClick={() => setFilter("")}
              >
                همهٔ معناها
              </button>
            ) : null}
          </p>

          <p className={styles.total} role="status">
            <Num value={shown.length} /> معنا از <Num value={data.count} />.
          </p>

          <ul className={styles.meanings}>
            {shown.map((meaning) => (
              <MeaningCard key={meaning.tag} meaning={meaning} />
            ))}
          </ul>

          {silent.length > 0 ? (
            <section className={styles.silent} aria-labelledby="silent">
              <h2 id="silent" className={styles.silentTitle}>
                وندهایی که سرچشمه معنایی برایشان ننوشته است
              </h2>
              <p className={styles.silentNote}>
                <Num value={silent.length} /> وند. این به معنای بی‌معنا بودن
                آنها نیست؛ دستورنامه دربارهٔ آنها چیزی نگفته است.
              </p>
              <ul className={styles.silentList}>
                {silent.map((one) => (
                  <li key={one.rule_id}>
                    <Latin affix>{one.affix}</Latin>
                    {one.affix_fa ? (
                      <span className={styles.fa}>{one.affix_fa}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {/* The rules that make a word out of no affix at all. On an affixes
              screen they used to be a row of blank chips, because the source
              writes a dash where a template's affix would go — and a dash is
              the honest answer, since a template joins two words with nothing
              between them. Shown here by what they build instead: the rule
              and its example, both followable. */}
          {joined.length > 0 ? (
            <section className={styles.silent} aria-labelledby="joined">
              <h2 id="joined" className={styles.silentTitle}>
                دستورهایی که وندی ندارند
              </h2>
              <p className={styles.silentNote}>
                <Num value={joined.length} /> دستور. اینها واژه را با وند
                نمی‌سازند: دو واژه را به هم می‌پیوندند، یا گونهٔ واژه را
                دگرگون می‌کنند بی‌آنکه چیزی بیفزایند. نمونه، خواناترین چیز
                دربارهٔ آنهاست.
              </p>
              <ul className={styles.joinedList}>
                {joined.map((one) => (
                  <li key={one.rule_id} className={styles.joinedItem}>
                    <Link className={styles.rule} to={`/rules?rule=${one.rule_id}`}>
                      <Latin>{one.rule_id}</Latin>
                    </Link>
                    {one.examples.length > 0 ? (
                      <span className={styles.examples}>
                        {one.examples.slice(0, 3).map((example) => (
                          <Latin key={example}>{example}</Latin>
                        ))}
                      </span>
                    ) : (
                      <span className={styles.noExample}>نمونه‌ای ثبت نشده</span>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </>
      ) : null}
    </article>
  );
}
