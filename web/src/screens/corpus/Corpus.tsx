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
import { Waiting } from "../../text/Waiting";
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
 * A reader was asked to tell «متن‌ها» (until 2026-11-13 «سروده‌ها») from «واژه‌گونه‌ها» from «ساخته‌ها» on
 * the label alone, with the same version number under each. The names are the
 * index names and they stay; what they mean is now said beside them.
 */
const ALIASES: { key: string; label: string; what: string }[] = [
  {
    key: "documents",
    label: "متن‌ها",
    what: "متن‌هایی که برنامه خوانده است. هر متن یک شعر یا یک صفحه نثر است، با نویسنده، کتاب و سرچشمه‌اش. جست‌وجوی شاهدمثال و صفحهٔ خواندن متن از همین انبار می‌خوانند.",
  },
  {
    key: "word_types",
    label: "واژه‌گونه‌ها",
    what: "واژه‌هایی که در این متن‌ها آمده‌اند، هر کدام یک بار، هر چند بار هم که تکرار شده باشند. جست‌وجوی واژه از همین انبار می‌خواند.",
  },
  {
    key: "derivations",
    label: "ساخته‌ها",
    what: "واژه‌هایی که خودمان با دستورهای واژه‌سازی ساخته‌ایم، همراه با راهِ ساختِ هر کدام. این‌ها در متن‌ها نیامده‌اند.",
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
            ? "هنوز هیچ پیکره‌ای در جست‌وجوگر نیست. وقتی نخستین پیکره بارگذاری شود، این صفحه پر می‌شود."
            : "نتوانستیم وضعیت پیکره را بیاوریم. کمی بعد دوباره امتحان کنید."}
        </p>
      ) : null}

      {!state && !error ? <Waiting /> : null}

      {state ? (
        <section className={styles.block} aria-labelledby="serving">
          <h2 id="serving">نسخه‌هایی که الان به کار می‌روند</h2>
          <p className={styles.lede}>
            برنامه از سه انبار جدا می‌خواند و هر کدام نسخهٔ خودش را دارد.
            شمارهٔ نسخه‌ها فقط وقتی یکی است که هر سه با هم ساخته شده باشند.
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
          اندازه‌های این پیکره هنوز هنگام بارگذاری سنجیده نشده است. تا آن وقت
          اندازه و پوشش را نشان نمی‌دهیم، چون عددِ ساختگی از نبودِ عدد بدتر
          است.
        </p>
      ) : null}

      {report ? (
        <>
          {!state?.describes_the_served_version ? (
            <p className={styles.mismatch} role="status">
              این اندازه‌ها مالِ نسخهٔ <Latin>{report.corpus_version}</Latin>{" "}
              است، نه نسخه‌ای که الان به کار می‌رود. هر شمارش فقط برای نسخهٔ
              خودش درست است.
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
                    is written with, and the search box's examples are where that is taught;
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
                <dt>تاریخ بارگذاری</dt>
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
                  متن
                  <Info label="متن">
                    شمار متن‌هایی که برنامه خوانده است. هر شعر یا هر صفحهٔ نثر
                    یک متن حساب می‌شود.
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
                    هر بار که واژه‌ای در متن بیاید، یک بار شمرده می‌شود. اگر
                    «دل» هزار بار آمده باشد، هزار بار شمرده شده است.
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
                    واژه‌ها آن‌گونه که <b>نوشته</b> می‌شوند، هر کدام یک بار. «دل»
                    هر چند بار هم که آمده باشد، یکی شمرده می‌شود.
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
                    واژه‌ها آن‌گونه که <b>خوانده</b> می‌شوند، هر کدام یک بار.
                    شمارشان از املاها بیشتر است، چون یک املا می‌تواند دو خوانش داشته باشد:
                    «مرد» هم <Latin>mard</Latin> است و هم <Latin>mord</Latin>.
                  </Info>
                </dt>
                <dd className={styles.big}>
                  <Num value={report.word_types} />
                </dd>
              </div>
            </dl>
            <p className={styles.note}>
              چرا واژه‌گونه‌ها از املاها بیشترند؟ چون هر خوانش یک واژه‌گونه است.
              «مرد» هم <Latin>mard</Latin> است و هم <Latin>mord</Latin>، و متنِ
              بی‌اعراب نمی‌گوید کدام.{" "}
              <Num value={report.ambiguous_spellings} /> املا بیش از یک خوانش
              دارد و همهٔ خوانش‌هایشان را نگه می‌داریم.
            </p>
            {report.units && Object.keys(report.units).length > 0 ? (
              <p className={styles.note}>
                این متن‌ها روی هم <Num value={report.units.couplet ?? 0} /> بیت،{" "}
                <Num value={report.units.half ?? 0} /> مصراعِ تنها و{" "}
                <Num value={report.units.prose ?? 0} /> بند نثر دارند.{" "}
                <Num value={report.units.note ?? 0} /> یادداشتِ سرچشمه را هم کنار
                متن‌ها نگه داشته‌ایم، ولی واژه‌هایشان را نشمرده‌ایم.
              </p>
            ) : null}
          </section>

          <section className={styles.block} aria-labelledby="coverage">
            <h2 id="coverage">پوشش {LEXICON}</h2>
            <Coverage
              shares={[
                {
                  label: "از واژگان",
                  note: `چند درصد از املاهای پیکره در ${LEXICON} مدخل دارند؛ یعنی چه بخشی از واژگان را می‌توانیم بخوانیم. این عدد نشانهٔ کیفیت نیست.`,
                  share: report.type_share,
                  covered: report.spellings_linked,
                  total: report.spellings,
                },
                {
                  label: "از متن",
                  note: "از همهٔ واژه‌های متن‌ها، با تکرارهایشان، چند درصد خوانش دارند. این عدد خیلی بالاتر است، چون واژه‌هایی که می‌شناسیم همان‌هایی‌اند که بیشتر به کار می‌روند.",
                  share: report.token_share,
                  covered: report.tokens_linked,
                  total: report.tokens,
                },
              ]}
            />
          </section>

          <section className={styles.block} aria-labelledby="dating">
            <h2 id="dating">کاستی‌های شواهد</h2>
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
