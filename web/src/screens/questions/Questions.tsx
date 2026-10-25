/**
 * The questions waiting on the linguist, and the place he answers them.
 *
 * **This screen is why the store exists.** The questions used to live in
 * `docs/FOR_THE_LINGUIST.md` and be answered in one conversation at the end of
 * a session — English Markdown, in a repository, for someone who works in
 * Persian. The store is the record now and the document is its export, so this
 * is where an answer is actually created.
 *
 * Three things it is careful about:
 *
 * **One version, and it is Persian.** The English and Behnevis renderings were
 * taken out on 2026-08-16: a question shown three ways is three things to keep
 * in step, and the two extra ones were for us rather than for him. Everything a
 * question has to say is now said in the Persian.
 *
 * **The evidence is downloadable, not described.** A question that names the
 * grammar document, or a list of twenty-one words, cannot be answered until
 * that document and that list are in front of the reader.
 *
 * **The evidence is on the screen with the question.** A question about 21
 * words cannot be answered without the 21 words, and sending him back to the
 * repository to find them is the thing this replaces.
 *
 * **Answering is refused before it is offered, not after.** The answer says
 * whether this account may rule, so a reader is told plainly instead of writing
 * a ruling and losing it to a 403.
 *
 * **One question at a time.** All sixteen set out one after another was a
 * page minutes long, and finding the one under discussion took longer than
 * reading it. See `Pager`.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import {
  questions as fetchQuestions,
  type Question,
  type Questions as QuestionList,
} from "../../api/questions";
import { Num } from "../../text/Num";
import { SCREENS } from "../../shell/screens";
import { Answer } from "./Answer";
import styles from "./Questions.module.css";

const SCREEN = SCREENS.find((one) => one.path === "/questions")!;

/** What each state is called on screen. */
const STATE_LABEL: Record<string, string> = {
  open: "در انتظار پاسخ",
  blocked: "کار را متوقف کرده",
  answered: "پاسخ داده شده",
  withdrawn: "پس گرفته شده",
};

/**
 * The boxes at the top: how many questions are in each state, and the filter.
 *
 * **The states are the store's own four**, not a set invented here:
 * `open`, `blocked`, `answered`, `withdrawn` (see `db/models/rulings.py`).
 * *Resolved* — a maintainer closing a question after the linguist has ruled
 * on it — is a fifth the database does not have yet.
 */
interface Tally {
  key: string;
  label: string;
  holds: (one: Question) => boolean;
}

/** The box that holds everything, and the fallback when none is chosen. */
const EVERY: Tally = { key: "all", label: "همهٔ پرسش‌ها", holds: () => true };

const TALLIES: Tally[] =
  [
    EVERY,
    {
      key: "waiting",
      label: "بی‌پاسخ",
      holds: (one) => one.state === "open" || one.state === "blocked",
    },
    {
      key: "blocked",
      label: "کار را متوقف کرده",
      holds: (one) => one.state !== "answered" && one.blocks_work,
    },
    { key: "answered", label: "پاسخ داده شده", holds: (one) => one.state === "answered" },
    { key: "withdrawn", label: "پس گرفته شده", holds: (one) => one.state === "withdrawn" },
  ];

function Trouble({ error }: { error: ApiError }): React.ReactElement {
  // Every message says what to do next, which for this screen is almost
  // always "paste a token" — reading the questions needs one.
  const said =
    error.trouble === "unidentified"
      ? "برای دیدن پرسش‌ها باید کلید دسترسی را وارد کنید."
      : error.trouble === "not-built"
        ? "هنوز پرسشی ثبت نشده است."
        : error.message;
  return <p className={styles.trouble}>{said}</p>;
}

/** The question itself, set as the paragraphs it was written in.
 *
 * **A question is several paragraphs and was being poured into one.** The
 * text is written as context, then the measurement, then what we did, then the
 * question — and rendering it as a single `<p>` ran all four together into a
 * wall nobody would read to the end of, which for the one person who has to
 * answer it is the whole failure.
 */
function Asked({ text }: { text: string }) {
  const paragraphs = text.split(/\n\s*\n/).filter((one) => one.trim());
  return (
    <div className={styles.question}>
      {paragraphs.map((one, at) => (
        // The text is a stored field, not a list that reorders — the index is
        // stable for as long as the string is.
        <p key={at}>{one.trim()}</p>
      ))}
    </div>
  );
}

/** The files attached to a question, each one downloadable.
 *
 * **A question that names a document is not answerable without it.** L1 turns
 * on what the grammar document says about three verbs and L13 on a list of
 * twenty-one words — so the document and the list are here, and nobody has to
 * go to a shared drive to find them.
 */
function Files({ question }: { question: Question }) {
  if (!question.files?.length) return null;
  return (
    <ul className={styles.files}>
      {question.files.map((file) => (
        <li key={file.filename}>
          <a href={`/api${file.href}`} download={file.filename}>
            {file.filename}
          </a>
          <span className={styles.fileWhat}>{file.description_fa}</span>
        </li>
      ))}
    </ul>
  );
}

/** Whether a string has any Persian in it at all. */
const PERSIAN = /[\u0600-\u06FF]/;

/** Where `db/rulings.py` writes why a question was taken back. */
const WITHDRAWN = "withdrawn_because";

/**
 * Context keys that are the form's own bookkeeping, not evidence: the options
 * (shown as the form), which handles a question covers, and its earlier
 * wording. Listed here so the evidence fold never opens onto raw JSON.
 */
const NOT_EVIDENCE = new Set(["from_document", WITHDRAWN, "choices", "covers", "reworded"]);

/** The evidence a question carries, as it was written — if it is Persian.
 *
 * **English evidence is not shown.** It was imported from the repository's own
 * Markdown, which is written for us, and it arrived on the screen as a wall of
 * left-to-right prose inside a right-to-left page: line ends in the wrong
 * place, the emphasis marks still in it, unreadable to the one person the
 * screen exists for. The project lead asked on 2026-08-20 whether it was
 * needed at all. It is not: the **files** are the evidence a question turns on
 * — the grammar document, the list of twenty-one words — and those stay.
 * Persian evidence still shows, so nothing is lost when it is written for him.
 */
function Evidence({ context }: { context: Record<string, unknown> }) {
  const written = context.from_document;
  if (typeof written === "string" && written.trim()) {
    return PERSIAN.test(written) ? (
      <pre className={styles.evidence}>{written}</pre>
    ) : null;
  }
  const rest = Object.entries(context).filter(([key]) => !NOT_EVIDENCE.has(key));
  if (!rest.length) return null;
  return (
    <dl className={styles.facts}>
      {rest.map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{typeof value === "object" ? JSON.stringify(value) : String(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Whether the evidence fold would have anything in it.
 *
 * Asked before the fold is drawn, so «شواهد» is never a summary that opens
 * onto nothing — which is what happened the moment English evidence stopped
 * being shown.
 */
function hasEvidence(context: Record<string, unknown> | null): boolean {
  if (!context) return false;
  const written = context.from_document;
  if (typeof written === "string" && written.trim() && PERSIAN.test(written)) {
    return true;
  }
  return Object.keys(context).some((key) => !NOT_EVIDENCE.has(key));
}


function Card({
  question,
  mayAnswer,
  onAnswered,
}: {
  question: Question;
  mayAnswer: boolean;
  onAnswered: () => void;
}): React.ReactElement {
  const [open, setOpen] = useState(false);
  const withdrawnBecause = question.context?.[WITHDRAWN];

  return (
    <article className={styles.card} data-state={question.state}>
      <header>
        <span className={styles.reference}>{question.reference}</span>
        {/* **The state is a badge, not a grey word.** One question is on
            screen at a time now, and paging through them a reader could not
            see which had been answered — the state was small, soft-coloured
            and last in the row, which is where the eye goes least. Coloured by
            state, and first after the reference. Raised 2026-08-20. */}
        <span className={styles.state} data-state={question.state}>
          {STATE_LABEL[question.state]}
        </span>
        {/* Not when the state badge already says it: a blocked question
            read «کار را متوقف کرده» twice in one row. */}
        {question.blocks_work &&
        question.state !== "answered" &&
        question.state !== "blocked" ? (
          <span className={styles.blocking}>کار را متوقف کرده</span>
        ) : null}
      </header>

      <Asked text={question.question_fa} />
      <Files question={question} />

      {question.ruling ? (
        <div className={styles.ruling}>
          {/* **The option and his words, each said once.** When he chose an
              option and wrote nothing, ruling_fa is that option's sentence,
              so it is not repeated as though he had written it. */}
          {question.ruling.choice_fa ? (
            <p className={styles.rulingChoice}>
              <span className={styles.rulingLabel}>گزینهٔ برگزیده</span>
              {question.ruling.choice_fa}
            </p>
          ) : null}
          {question.ruling.ruling_fa !== question.ruling.choice_fa ? (
            <p className={styles.rulingText}>
              {question.ruling.choice_fa ? (
                <span className={styles.rulingLabel}>نوشتهٔ شما</span>
              ) : null}
              {question.ruling.ruling_fa}
            </p>
          ) : null}
          {question.ruling.ruling_latin ? (
            <p className={styles.behnevis} dir="ltr">
              {question.ruling.ruling_latin}
            </p>
          ) : null}
          {question.rulings > 1 ? (
            <p className={styles.changed}>
              این پرسش {question.rulings} بار پاسخ داده شده و پاسخ تغییر کرده است.
            </p>
          ) : null}
        </div>
      ) : null}

      {hasEvidence(question.context) ? (
        <details className={styles.more} open={open} onToggle={(e) => setOpen(e.currentTarget.open)}>
          <summary>شواهد</summary>
          <Evidence context={question.context ?? {}} />
        </details>
      ) : null}

      {/* **Why it was taken back, in words.** The store keeps the reason on the
          question and nothing showed it, so «پس گرفته شده» was a label with no
          account behind it — asked about on 2026-08-20. */}
      {question.state === "withdrawn" && typeof withdrawnBecause === "string" ? (
        <p className={styles.withdrawn}>پس گرفته شد، چون {withdrawnBecause}</p>
      ) : null}

      {mayAnswer && question.state !== "withdrawn" ? (
        <Answer
          reference={question.reference}
          choices={question.choices ?? []}
          answered={question.state === "answered"}
          onAnswered={onAnswered}
        />
      ) : null}
    </article>
  );
}

/**
 * One question at a time, with the way to the next one.
 *
 * **Sixteen questions on one page is a scroll, not a list.** Each is several
 * paragraphs, its files, its evidence and a box to answer in — so the screen
 * was minutes of scrolling to find the one being talked about, and nothing on
 * it said where you were. The project lead asked for next and previous on
 * 2026-08-20.
 *
 * The bar is shown above the question and again below it, because the reason
 * to move on is usually that you have read to the end.
 */
function Pager({
  at,
  count,
  onGo,
}: {
  at: number;
  count: number;
  onGo: (to: number) => void;
}): React.ReactElement {
  return (
    <nav className={styles.pager} aria-label="رفتن میان پرسش‌ها">
      {/* In Persian the page runs right to left, so *previous* is the button
          on the right and *next* the one on the left. Writing them in this
          order puts each on its own side without a direction being named. */}
      <button type="button" onClick={() => onGo(at - 1)} disabled={at <= 0}>
        پرسش پیشین
      </button>
      <span className={styles.place}>
        پرسش <Num value={at + 1} /> از <Num value={count} />
      </span>
      <button
        type="button"
        onClick={() => onGo(at + 1)}
        disabled={at >= count - 1}
      >
        پرسش بعدی
      </button>
    </nav>
  );
}

export function Questions(): React.ReactElement {
  const [list, setList] = useState<QuestionList | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  // Opens on the unanswered, which is what the screen opened on before —
  // the linguist arrives to answer, not to read what he already answered.
  const [only, setOnly] = useState("waiting");
  // **Which question is open is in the address**, so one can be linked to.
  // The rules screen has had `/rules/{id}` as a stable address since the
  // beginning for the same reason: a question is a thing to point at.
  const [params, setParams] = useSearchParams();
  const asked = params.get("q");
  const top = useRef<HTMLDivElement>(null);
  const wasAt = useRef<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    fetchQuestions()
      .then(setList)
      .catch((trouble: unknown) => {
        setList(null);
        setError(
          trouble instanceof ApiError
            ? trouble
            : new ApiError("unreachable", 0, String(trouble)),
        );
      });
  }, []);

  useEffect(load, [load]);

  const all = list?.questions ?? [];
  const chosen = TALLIES.find((one) => one.key === only) ?? EVERY;
  // **The open question stays in the list whatever the filter says.** Answer
  // one while looking at the unanswered and it stops being unanswered — the
  // filter would drop it, the screen would jump to a different question, and
  // the ruling just written would vanish before it could be read back.
  const shown = all.filter(
    (one) => chosen.holds(one) || one.reference === asked,
  );
  const found = shown.findIndex((one) => one.reference === asked);
  const at = found >= 0 ? found : 0;
  const current = shown[at] ?? null;

  /** Move to the question at this position, if there is one there. */
  const step = (to: number) => {
    const next = shown[to];
    if (next) setParams({ q: next.reference });
  };

  // The address names the question on screen, even when it arrived without a
  // `q` or with one the filter no longer holds.
  useEffect(() => {
    if (current && current.reference !== asked) {
      setParams({ q: current.reference }, { replace: true });
    }
  }, [current, asked, setParams]);

  // Moving to another question puts its start on screen. Only on a move: on
  // the first render the heading and the counts should be what a reader sees.
  useEffect(() => {
    const now = current?.reference ?? null;
    if (wasAt.current && now && wasAt.current !== now) {
      top.current?.scrollIntoView?.({ block: "start" });
    }
    wasAt.current = now;
  }, [current]);

  return (
    <section className={styles.screen}>
      <h1>{SCREEN.title}</h1>
      <p className={styles.purpose}>{SCREEN.purpose}</p>

      {error ? <Trouble error={error} /> : null}

      {list ? (
        <>
          {/* **Not the account id.** This read «شما به‌عنوان expert-1 می‌توانید
              پاسخ دهید», and `expert-1` is a row in a table: the app has had
              one account and no roles since 2026-08-17, so the id names
              nothing a reader can act on and invites the question *what is an
              expert here?*. What matters is whether answering is open. */}
          <p className={styles.summary}>
            {list.answering_as
              ? "پاسخ دادن برای شما باز است."
              : "پرسش‌ها را می‌بینید، ولی پاسخ دادن برای شما باز نیست."}
          </p>

          <ul className={styles.tallies}>
            {TALLIES.map((tally) => (
              <li key={tally.key}>
                <button
                  type="button"
                  className={styles.tally}
                  data-kind={tally.key}
                  aria-pressed={only === tally.key}
                  // **The place is cleared with the filter.** A question is
                  // held on screen when its own state changes underneath it —
                  // see `shown` — and that must not follow a reader who asked
                  // for a different box.
                  onClick={() => {
                    setOnly(tally.key);
                    setParams({});
                  }}
                >
                  <span className={styles.tallyCount}>
                    <Num value={all.filter(tally.holds).length} />
                  </span>
                  <span className={styles.tallyLabel}>{tally.label}</span>
                </button>
              </li>
            ))}
          </ul>

          {current ? (
            <div className={styles.list} ref={top}>
              <Pager at={at} count={shown.length} onGo={step} />
              <Card
                key={current.reference}
                question={current}
                mayAnswer={Boolean(list.answering_as)}
                onAnswered={load}
              />
              <Pager at={at} count={shown.length} onGo={step} />
            </div>
          ) : (
            <p className={styles.empty}>
              {only === "waiting"
                ? "هیچ پرسشی بی‌پاسخ نمانده است."
                : `هیچ پرسشی در «${chosen.label}» نیست.`}
            </p>
          )}
        </>
      ) : null}
    </section>
  );
}
