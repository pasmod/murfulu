/**
 * Compound words: what the grammar joins to a word, and who wrote which.
 *
 * **The first screen in this app to show a compound at all.** Sixteen rules
 * have licensed compounding since the rule pack was transcribed and nothing
 * ever called them, so a reader could see *soxanguy* named as an example and
 * never see one made.
 *
 * **What the screen shows is the attested list, and it says what it is not
 * showing.** One noun makes thousands and the corpus holds a fraction of a
 * percent — دل builds 4,652 and 220 were ever written — so the three counts
 * are printed beside every list. A list of forty is meaningless without the
 * number it came out of.
 *
 * **A row that may not be a compound is marked and sunk, never dropped.** دلم
 * carries 12,947 documents and is دل plus a possessive; دلبر carries 2,920 and
 * is a real compound the dictionary also holds. Both are shown, the difference
 * is on the row, and only the first sinks.
 */

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import { compound as fetchCompound, type Compounds } from "../../api/compound";
import { wordClasses, type WordClass } from "../../api/generate";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { notFound } from "../../text/lexicon";
import { SCREENS } from "../../shell/screens";
import { Pairings } from "./Pairings";
import styles from "./Compound.module.css";

const SCREEN = SCREENS.find((one) => one.path === "/compound")!;

/** Nouns that make compounds. Checked against the API, never guessed. */
const EXAMPLES = ["دل", "آب", "سر", "دست", "کار"];

export function Compound() {
  const [params, setParams] = useSearchParams();
  const word = params.get("word") ?? "";
  const [draft, setDraft] = useState(word);
  // In an effect, not during the render: the router navigates inside a
  // transition and a render-time adjustment can be discarded when the
  // transition replays. Measured on the other two search boxes.
  useEffect(() => setDraft(word), [word]);
  const [found, setFound] = useState<Compounds | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  // **What tells two identical-looking rows apart.** V-078 and V-079 both join
  // a noun to a present stem and both write دلبر; one means the doer and the
  // other the done-to, and `compounding.py` keeps both on purpose because that
  // is information. The screen printed only the rule id, so the reader saw the
  // same word twice with the same evidence and no way to tell why. The class
  // is on every row already; this is the Persian for it, from the rule pack.
  const [classes, setClasses] = useState<WordClass[]>([]);
  // What the list is showing. Opens on what the corpus has — evidence first,
  // the same order every other screen uses — and the other switch is where a
  // coiner goes: those are the words nobody has written yet.
  const [attested, setAttested] = useState(true);

  useEffect(() => {
    document.title = `${SCREEN.title} — مورفولو`;
  }, []);

  useEffect(() => {
    if (!word) return;
    const stop = new AbortController();
    wordClasses(stop.signal)
      .then(setClasses)
      .catch(() => setClasses([]));
    return () => stop.abort();
  }, [word]);

  useEffect(() => {
    if (!word) {
      setFound(null);
      return;
    }
    const stop = new AbortController();
    setError(null);
    fetchCompound(word, attested, stop.signal)
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
  }, [word, attested]);

  const run = useCallback(
    (next: string) => setParams(next ? { word: next } : {}),
    [setParams],
  );

  /** Class ids as the reader's own words: `karnam` → «کارنام». */
  const saying = (names: string[]) => {
    const said = names.map(
      (name) => classes.find((one) => one.name === name)?.label_fa ?? name,
    );
    return said.length ? said.join(" یا ") : "چیز دیگری";
  };

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
        <label className={styles.label} htmlFor="compound-word">
          واژه‌ای بنویسید
        </label>
        <div className={styles.row}>
          <input
            id="compound-word"
            className={styles.input}
            dir="auto"
            autoComplete="off"
            placeholder="دل"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <button className={styles.submit} type="submit">
            بترکیب
          </button>
        </div>
        {/* Five, not one — each checked against the running API. */}
        {!word ? (
          <p className={styles.examples}>
            <span className={styles.examplesSays}>برای نمونه:</span>
            {EXAMPLES.map((one) => (
              <button
                key={one}
                type="button"
                className={styles.example}
                onClick={() => {
                  setDraft(one);
                  run(one);
                }}
              >
                {one}
              </button>
            ))}
          </p>
        ) : null}
      </form>

      {error ? (
        <p className={styles.trouble} role="status">
          {error.trouble === "missing"
            ? notFound("چیزی نمی‌توان با آن ترکیب کرد.")
            : "پاسخی از سرور نرسید. کمی بعد دوباره بیازمایید."}
        </p>
      ) : null}

      {found?.readings.map((reading) => (
        <section
          key={`${reading.latin}-${reading.lexicon_category ?? ""}`}
          className={styles.reading}
          aria-labelledby={`reading-${reading.latin}`}
        >
          <h2 id={`reading-${reading.latin}`} className={styles.readingTitle}>
            {reading.spelling_fa} <Latin>{reading.latin}</Latin>
            {reading.lexicon_category ? (
              <span className={styles.category}>{reading.lexicon_category}</span>
            ) : null}
          </h2>

          {/* **A zero gets a reason, not a count.** «دستور زبان می‌تواند ۰
              ترکیب بسازد؛ ۰ تای آن در پیکره آمده است. برای این شمار، ۱٬۷۴۱
              واژهٔ دیگر … آزموده شد» is three figures about nothing, and the
              reader's actual question — why nothing? — went unanswered.
              Reported for کار on 2026-08-18. */}
          {reading.built > 0 ? (
            <p className={styles.counts}>
              دستور زبان می‌تواند <Num value={reading.built} /> ترکیب بسازد؛{" "}
              <Num value={reading.attested} /> تای آن در پیکره آمده است. برای این
              شمار، <Num value={reading.partners_tried} /> واژهٔ دیگر در جایگاه
              نیمهٔ دوم آزموده شد.
            </p>
          ) : (
            <p className={styles.counts}>
              هیچ ترکیبی از این واژه ساخته نشد.
            </p>
          )}

          {Object.keys(reading.skipped).map((kind) => (
            <p key={kind} className={styles.skipped}>
              {/* **Said with an example, not with a term.** It read «الگوهای
                  دو-بُنی بر این واژه کار نمی‌کنند: آنها هر دو بُن را از یک
                  کارواژه می‌گیرند» — three words a reader has to already know
                  (الگوی دو-بُنی، بُن، کارواژه) to learn one fact. The project
                  lead did not understand it on 2026-08-18, which settles it.
                  «گفت‌وگو» carries the whole idea: both halves out of گفتن. */}
              {kind === "template"
                ? `ده دستور از دستورهای ترکیب، هر دو نیمهٔ واژه را از یک کارواژه می‌گیرند — مانند «گفت‌وگو» که هر دو نیمه‌اش از «گفتن» است. «${reading.spelling_fa}» کارواژه نیست، پس آن ده دستور اینجا کاری نمی‌کنند${
                    reading.built > 0 ? "؛ آنچه می‌بینید کار شش دستور دیگر است" : ""
                  }.`
                : /* **The other six, and why they can refuse a perfectly
                     ordinary noun.** They all want a نام in front, and the
                     source grammar counts a word like کار — اسم معنی — as a
                     کارنام. Nothing is broken; the front slot's meaning is an
                     open question with the linguist (L18). Both class names
                     come from the rule pack, never from here. */
                  `شش دستور دیگر در جای نخست ${saying(reading.slot_wants)} می‌خواهند، و «${reading.spelling_fa}» در دستگاه دستوری ${saying(reading.word_classes)} است. پس هیچ‌کدام بر آن کار نمی‌کنند. اینکه این جای نخست باید ${saying(reading.word_classes)} را هم بپذیرد یا نه، پرسشی است که هنوز پاسخ نگرفته.`}
            </p>
          ))}

          {/* **The switch to the words nobody has written.** The list was
              the attested one and nothing said so — دل shows 109 rows out of
              4,652, and the 4,543 the project exists to produce were not
              reachable from the screen at all. Asked by the project lead on
              2026-08-18: *do we only show words in the corpus?* */}
          {reading.built > 0 ? (
            <p className={styles.showing}>
              <button
                type="button"
                className={styles.pick}
                aria-pressed={attested}
                onClick={() => setAttested(true)}
              >
                آنچه در پیکره آمده
                <span className={styles.pickCount}>
                  <Num value={reading.attested} />
                </span>
              </button>
              <button
                type="button"
                className={styles.pick}
                aria-pressed={!attested}
                onClick={() => setAttested(false)}
              >
                همه، با واژه‌های نو
                <span className={styles.pickCount}>
                  <Num value={reading.built} />
                </span>
              </button>
            </p>
          ) : null}

          {!attested && reading.pairings.length > 0 ? (
            <p className={styles.nothing}>
              واژه‌هایی که نشانی از آنها در پیکره نیست، ساختهٔ همین دستورهایند و
              هنوز کسی ننوشته‌شان. این‌ها همان چیزی‌اند که این ابزار برای آن
              ساخته شده است.
            </p>
          ) : null}

          {reading.pairings.length > 0 ? (
            <Pairings rows={reading.pairings} classes={classes} />
          ) : reading.built > 0 ? (
            <p className={styles.nothing}>
              هیچ‌یک از این ترکیب‌ها در پیکره نیامده است. این به معنای نادرست
              بودن‌شان نیست — پیکره شعر کلاسیک است و واژهٔ نو در آن نیست.
            </p>
          ) : null}
        </section>
      ))}
    </article>
  );
}
