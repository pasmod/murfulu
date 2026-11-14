/**
 * The verses behind a built word's corpus figures, in the row's «پیکره» panel.
 *
 * «۲ بار، در ۲ متن از ۲ نویسنده» is a claim; the two lines are what a reader
 * can check it against, so they stand under the figures (the project lead's
 * wish, 2026-11-14). Three texts by three authors come when the panel opens —
 * one voice each, the six citations' rule, because three poems of one poet
 * can be one rhyme — and never one request per row as the screen loads; each
 * with every line holding the word, marked, and the way to its unit on the
 * reading screen. Where there are more, a press opens the whole list in
 * place: the word page's list (`evidence/EvidenceList.tsx`), with its author
 * filter and its pages, ten texts to a page so the panel stays a panel on a
 * phone. The button carries no number: the figures above are the counting's
 * and the list's own count can differ by a few; the open list gives its
 * count and says why.
 *
 * **Nothing is listed where nothing is counted.** A word the corpus does not
 * have keeps its sentence and asks for nothing; the letters of a function
 * word count that word's uses, not this one's, and show none of its lines.
 * The letters of another reading (level *spelling*) are listed: they are the
 * evidence the figures above are made of, and the note says whose they are.
 */

import { useEffect, useId, useState } from "react";

import type { BuiltForm } from "../../api/generate";
import { evidence as fetchEvidence, type Evidence } from "../../api/evidence";
import { EvidenceList } from "../../evidence/EvidenceList";
import { EvidenceText } from "../../evidence/EvidenceText";
import { chosenOf, useEvidence, type Choice } from "../../evidence/useEvidence";
import { UNNAMED } from "../../evidence/AuthorFilter";
import { Waiting } from "../../text/Waiting";
import list from "../../evidence/Evidence.module.css";
import styles from "./CorpusLines.module.css";

/** Texts shown when the panel opens, each by another author. */
const FIRST = 3;
/** Texts to a page once the whole list is open. */
const PAGE = 10;
/** Lines a text shows before the rest are asked for: a panel is small. */
const GLANCE = 3;

export function CorpusLines({ form }: { form: BuiltForm }) {
  const found = form.attestation;
  if (!found || found.level === "none" || found.function_word) return null;
  return (
    // Keyed by the spelling, so a row that comes to hold another word starts
    // its list afresh rather than on the last word's page and author.
    <Lines
      key={form.form_fa}
      spelling={form.form_fa}
      docCount={found.doc_count}
      version={found.corpus_version}
    />
  );
}

function Lines({
  spelling,
  docCount,
  version,
}: {
  spelling: string;
  docCount: number;
  version: string;
}) {
  const [first, setFirst] = useState<Evidence | null>(null);
  const [failed, setFailed] = useState(false);
  const [whole, setWhole] = useState(false);
  const [choice, setChoice] = useState<Choice>({ unnamed: false, page: 1 });
  const listId = useId();

  useEffect(() => {
    const stop = new AbortController();
    setFailed(false);
    fetchEvidence({ spelling, size: FIRST, countLines: false, voices: true }, stop.signal)
      .then(setFirst)
      .catch(() => {
        if (!stop.signal.aborted) setFailed(true);
      });
    return () => stop.abort();
  }, [spelling]);

  if (failed) {
    return <p className={list.trouble}>سطرها نرسیدند. کمی بعد دوباره بیازمایید.</p>;
  }
  if (!first || first.spelling !== spelling) return <Waiting />;

  const more = first.total > first.texts.length;
  const toggle = more ? (
    <button
      type="button"
      className={styles.toggle}
      aria-expanded={whole}
      aria-controls={listId}
      onClick={() => setWhole(!whole)}
    >
      {whole ? "بستن همهٔ شواهد" : "نشان دادن همهٔ شواهد"}
    </button>
  ) : null;

  return (
    <div className={styles.lines}>
      <p className={list.note}>این سطرها شاهد املای «{spelling}»اند، نه یکی از خوانش‌های آن.</p>
      {/* One button in one place, above the list either way: replacing it
          as the list opens would drop the reader's focus on the page. */}
      {toggle}
      <div id={listId}>
        {whole ? (
          <Whole
            spelling={spelling}
            docCount={docCount}
            version={version}
            choice={choice}
            onChoice={setChoice}
          />
        ) : (
          <ol className={list.texts}>
            {first.texts.map((text) => (
              <EvidenceText
                key={text.document_id}
                text={text}
                spelling={spelling}
                glance={GLANCE}
              />
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}

/** The whole list, in place, its choice held by the row. */
function Whole({
  spelling,
  docCount,
  version,
  choice,
  onChoice,
}: {
  spelling: string;
  docCount: number;
  version: string;
  choice: Choice;
  onChoice: (choice: Choice) => void;
}) {
  const found = useEvidence(spelling, choice, { open: true, size: PAGE });
  if (found.summaryFailed && !found.whole) {
    return <p className={list.trouble}>شمار متن‌ها نرسید. کمی بعد دوباره بیازمایید.</p>;
  }
  if (!found.whole) return <Waiting />;
  return (
    <EvidenceList
      spelling={spelling}
      found={found}
      chosen={chosenOf(choice)}
      page={choice.page}
      size={PAGE}
      docCount={docCount}
      version={version}
      glance={GLANCE}
      onChoose={(value) =>
        onChoice(
          value === UNNAMED
            ? { unnamed: true, page: 1 }
            : { author: value || undefined, unnamed: false, page: 1 },
        )
      }
      onPage={(page) => onChoice({ ...choice, page })}
    />
  );
}
