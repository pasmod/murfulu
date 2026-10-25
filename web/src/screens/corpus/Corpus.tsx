/**
 * What the app is reading, how big it is, and how much of it we can read.
 *
 * Every count in this system is true for one corpus version and no other, and
 * this is the screen that says which one and where it came from. Three things
 * it is careful about:
 *
 * **The figures are what an ingest measured**, read from the file that run
 * wrote. Nothing here counts anything, because counting from the search index
 * gives the wrong answer twice over and both ways look right — see
 * `murfulu/corpus/report.py`.
 *
 * **A report describing another version is labelled, never passed off as
 * current.**
 *
 * **What the evidence does not cover is on the screen.** Three quarters of the
 * poems cannot be dated, so the dispersion chart on the word screen rests on a
 * quarter of the corpus. That belongs here, next to the sizes, rather than in
 * a document nobody opens.
 */

import { useEffect, useState } from "react";

import { ApiError } from "../../api/client";
import { corpus as fetchCorpus, type CorpusState } from "../../api/corpus";
import { Info } from "../../text/Info";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { LEXICON } from "../../text/lexicon";
import { SCREENS } from "../../shell/screens";
import { Coverage } from "./Coverage";
import { Dating } from "./Dating";
import { Gaps } from "./Gaps";
import styles from "./Corpus.module.css";

const SCREEN = SCREENS.find((one) => one.path === "/corpus")!;

/**
 * The three stores, and what each one holds.
 *
 * A reader was asked to tell «سروده‌ها» from «واژه‌گونه‌ها» from «ساخته‌ها» on
 * the label alone, with the same version number under each. The names are the
 * index names and they stay; what they mean is now said beside them.
 */
const ALIASES: { key: string; label: string; what: string }[] = [
  {
    key: "documents",
    label: "سروده‌ها",
    what: "متن‌هایی که خوانده‌ایم: هر سروده یک متن است، با شاعر و سرچشمه‌اش. جست‌وجوی شاهدمثال در این‌جاست.",
  },
  {
    key: "word_types",
    label: "واژه‌گونه‌ها",
    what: "واژه‌های جداگانه‌ای که در آن متن‌ها آمده‌اند، هر کدام یک بار — نه هر بار که تکرار شده‌اند. جست‌وجوی واژه در این‌جاست.",
  },
  {
    key: "derivations",
    label: "ساخته‌ها",
    what: "واژه‌هایی که ما با دستورهای واژه‌سازی ساخته‌ایم، همراه با راهی که از آن ساخته شده‌اند. این‌ها در متن‌ها نیامده‌اند؛ ما آن‌ها را ساخته‌ایم.",
  },
];

/**
 * The ingest date, in Persian words and the European calendar.
 *
 * `fa-IR` alone gives the Persian calendar — the date read ۲۶ مرداد ۱۴۰۵ —
 * and the project lead's call on 2026-08-17 is the European one. The language
 * does not change with it: the month is still named in Persian and the digits
 * are still Persian, because the reader is Persian and only the *calendar* was
 * in question. `-u-ca-gregory` is the one part that says so.
 */
function builtOn(stamp: string): string | null {
  const when = new Date(stamp);
  if (Number.isNaN(when.getTime())) return null;
  return new Intl.DateTimeFormat("fa-IR-u-ca-gregory", {
    dateStyle: "long",
  }).format(when);
}

export function Corpus() {
  const [state, setState] = useState<CorpusState | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    document.title = `${SCREEN.title} — مورفولو`;
    const stop = new AbortController();
    fetchCorpus(stop.signal)
      .then(setState)
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

  const report = state?.report ?? null;
  const when = report ? builtOn(report.built_at) : null;

  return (
    <article className={styles.screen}>
      <h1>{SCREEN.title}</h1>
      <p className={styles.purpose}>{SCREEN.purpose}</p>

      {error ? (
        <p className={styles.trouble} role="status">
          {error.trouble === "not-built"
            ? "هنوز هیچ پیکره‌ای در جست‌وجوگر ساخته نشده است. پس از نخستین درون‌ریزی اینجا پر می‌شود."
            : "وضعیت پیکره خوانده نشد. کمی بعد دوباره بیازمایید."}
        </p>
      ) : null}

      {state ? (
        <section className={styles.block} aria-labelledby="serving">
          <h2 id="serving">نسخه‌ای که به کار می‌رود</h2>
          <p className={styles.lede}>
            سه انبار جداگانه، هر کدام با نسخهٔ خودش. شماره‌ها با هم برابر
            نیستند مگر آنکه هر سه با هم ساخته شده باشند.
          </p>
          <ul className={styles.versions}>
            {ALIASES.map((alias) => (
              <li key={alias.key} className={styles.version}>
                <span className={styles.versionLabel}>
                  {alias.label}
                  <Info label={alias.label}>{alias.what}</Info>
                </span>
                {state.serving[alias.key] ? (
                  <Latin>{state.serving[alias.key]!}</Latin>
                ) : (
                  <span className={styles.absent}>ساخته نشده</span>
                )}
                <span className={styles.versionCount}>
                  <Num value={(state.built[alias.key] ?? []).length} /> نسخهٔ ساخته‌شده
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {state && !report ? (
        <p className={styles.unmeasured} role="status">
          هنوز هیچ درون‌ریزی‌ای اندازه‌های این پیکره را ثبت نکرده است. تا آن
          زمان اندازه و پوشش نشان داده نمی‌شود؛ عددِ ساختگی بدتر از نبودِ عدد
          است.
        </p>
      ) : null}

      {report ? (
        <>
          {!state?.describes_the_served_version ? (
            <p className={styles.mismatch} role="status">
              این اندازه‌ها برای نسخهٔ <Latin>{report.corpus_version}</Latin>{" "}
              سنجیده شده‌اند، نه نسخه‌ای که هم‌اکنون به کار می‌رود. هر شمارشی
              تنها برای نسخهٔ خودش درست است.
            </p>
          ) : null}

          <section className={styles.block} aria-labelledby="source">
            <h2 id="source">سرچشمه</h2>
            <dl className={styles.facts}>
              <div className={styles.fact}>
                <dt>پیکره</dt>
                {/* The name to read, not the identifier to type. This said
                    «ganjoor» — Latin, on an otherwise Persian page — until
                    2026-08-18. The identifier is still what `source:ganjoor`
                    is written with, and راهنمای نحو is where that is taught;
                    it falls back to it for a source that has no Persian name
                    yet, so a new corpus is named badly rather than not at
                    all. */}
                <dd>
                  {report.source_name_fa || (
                    <Latin className={styles.identifier}>
                      {report.source_id}
                    </Latin>
                  )}
                </dd>
              </div>
              <div className={styles.fact}>
                <dt>پروانهٔ استفاده</dt>
                {/* Persian when the source has written it, and the English
                    otherwise — marked as English so it is not read as broken
                    Persian. This said the English to every reader until
                    2026-08-17. */}
                <dd>
                  {report.licence_fa || (
                    <span lang="en" dir="ltr">
                      {report.licence}
                    </span>
                  )}
                </dd>
              </div>
              <div className={styles.fact}>
                <dt>تاریخ درون‌ریزی</dt>
                <dd>{when ?? "ثبت نشده"}</dd>
              </div>
              <div className={styles.fact}>
                <dt>نسخهٔ {LEXICON}</dt>
                <dd>
                  <Latin className={styles.identifier}>
                    {report.lexicon_snapshot_id}
                  </Latin>
                </dd>
              </div>
            </dl>
          </section>

          <section className={styles.block} aria-labelledby="size">
            <h2 id="size">اندازه</h2>
            <dl className={styles.facts}>
              <div className={styles.fact}>
                <dt>
                  سروده
                  <Info label="سروده">
                    شمار متن‌هایی که خوانده‌ایم — هر شعر یک سروده.
                  </Info>
                </dt>
                <dd className={styles.big}>
                  <Num value={report.documents} />
                </dd>
              </div>
              <div className={styles.fact}>
                <dt>
                  واژه در متن
                  <Info label="واژه در متن">
                    هر بار که واژه‌ای در متن آمده، جداگانه شمرده می‌شود. اگر
                    «دل» هزار بار آمده باشد، هزار تا شمرده شده است.
                  </Info>
                </dt>
                <dd className={styles.big}>
                  <Num value={report.tokens} />
                </dd>
              </div>
              <div className={styles.fact}>
                <dt>
                  املای جداگانه
                  <Info label="املای جداگانه">
                    واژه‌های جداگانه، آن‌گونه که <b>نوشته</b> شده‌اند. «دل» هر
                    چند بار که آمده باشد، یکی شمرده می‌شود.
                  </Info>
                </dt>
                <dd className={styles.big}>
                  <Num value={report.spellings} />
                </dd>
              </div>
              <div className={styles.fact}>
                <dt>
                  واژه‌گونه
                  <Info label="واژه‌گونه">
                    واژه‌های جداگانه، آن‌گونه که <b>خوانده</b> می‌شوند. از
                    املاها بیشتر است، چون یک املا می‌تواند دو خوانش داشته باشد:
                    «مرد» هم <Latin>mard</Latin> است و هم <Latin>mord</Latin>.
                  </Info>
                </dt>
                <dd className={styles.big}>
                  <Num value={report.word_types} />
                </dd>
              </div>
            </dl>
            <p className={styles.note}>
              واژه‌گونه‌ها از املاها بیشترند، چون هر خوانش یک واژه‌گونه است:
              «مرد» هم <Latin>mard</Latin> است و هم <Latin>mord</Latin>، و پیکره
              — که مصوت ندارد — نمی‌تواند میان آن دو جدا کند.{" "}
              <Num value={report.ambiguous_spellings} /> املا بیش از یک خوانش
              دارد و هر دو نگه داشته می‌شود.
            </p>
          </section>

          <section className={styles.block} aria-labelledby="coverage">
            <h2 id="coverage">پوشش {LEXICON}</h2>
            <Coverage
              shares={[
                {
                  label: "از واژگان",
                  note: `چه اندازه از املاهای جداگانهٔ پیکره در ${LEXICON} مدخل دارند. این پاسخِ «چقدر از واژگان را می‌توانیم بخوانیم» است و نباید آن را نشانهٔ کیفیت گرفت.`,
                  share: report.type_share,
                  covered: report.spellings_linked,
                  total: report.spellings,
                },
                {
                  label: "از متن",
                  note: "چه اندازه از واژه‌های جاری متن خوانش دارند. بسیار بالاتر است، چون واژه‌هایی که می‌شناسیم همان واژه‌هایی‌اند که بیشتر به کار می‌روند.",
                  share: report.token_share,
                  covered: report.tokens_linked,
                  total: report.tokens,
                },
              ]}
            />
          </section>

          <section className={styles.block} aria-labelledby="dating">
            <h2 id="dating">آنچه شواهد نمی‌پوشاند</h2>
            <Dating report={report} />
          </section>

          <section className={styles.block} aria-labelledby="gaps">
            <h2 id="gaps">املاهای بی‌مدخل</h2>
            <Gaps gaps={report.biggest_gaps} total={report.spellings_unlinked} />
          </section>
        </>
      ) : null}
    </article>
  );
}
