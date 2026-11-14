/**
 * One text of the list: where it is, and every line in it holding the word.
 *
 * The word is underlined in the accent the way the reading screen marks the
 * word a citation led to, and every line opens that screen at its unit —
 * the same «در متن ←» the six citations have. A text with more lines than
 * fit at a glance shows the first few and the rest on a press; the rest are
 * already here, nothing is fetched.
 */

import { useState } from "react";
import { Link } from "react-router-dom";

import type { EvidenceLine, EvidenceText as Text } from "../../api/evidence";
import { Num } from "../../text/Num";
import { persianCentury } from "../../text/numbers";
import styles from "./AllEvidence.module.css";

/** Lines shown before the rest are asked for. */
const AT_A_GLANCE = 6;

export function EvidenceText({ text, spelling }: { text: Text; spelling: string }) {
  const [whole, setWhole] = useState(false);
  const lines = whole ? text.lines : text.lines.slice(0, AT_A_GLANCE);
  const listId = `lines-${text.document_id}`;
  return (
    <li className={styles.text}>
      <p className={styles.source}>
        {text.author ?? "بی‌نام"}
        {text.work ? ` — ${text.work}` : ""}
        {text.title ? ` — ${text.title}` : ""}
        {text.century != null ? ` — ${persianCentury(text.century)}` : ""}
        {/* In brackets, not after a middle dot: a dot beside a Persian
            numeral reads as a zero, and «۱ · سطر» was read as ten lines. */}
        <span className={styles.lineCount}>
          {" ("}
          <Num value={text.lines.length} /> سطر)
        </span>
      </p>
      {text.held === "near" ? (
        <p className={styles.near}>
          این متن واژه را تنها با املایی نزدیک دارد که شمارش جدا می‌شمارد.
        </p>
      ) : text.held === "none" ? (
        <p className={styles.near}>
          جست‌وجو این متن را یافت، ولی شمارش در هیچ سطرش این واژه را نمی‌یابد.
        </p>
      ) : null}
      {lines.length > 0 ? (
        <ul className={styles.lines} id={listId}>
          {lines.map((line, index) => (
            <Line key={index} line={line} documentId={text.document_id} spelling={spelling} />
          ))}
        </ul>
      ) : null}
      {text.lines.length > AT_A_GLANCE ? (
        <button
          type="button"
          className={styles.more}
          aria-expanded={whole}
          aria-controls={listId}
          onClick={() => setWhole(!whole)}
        >
          {whole ? (
            "تنها چند سطر نخست"
          ) : (
            <>
              همهٔ <Num value={text.lines.length} /> سطر
            </>
          )}
        </button>
      ) : null}
    </li>
  );
}

function Line({
  line,
  documentId,
  spelling,
}: {
  line: EvidenceLine;
  documentId: string;
  spelling: string;
}) {
  return (
    <li className={styles.line}>
      <p className={styles.verse}>
        {line.parts.map((part, index) =>
          index % 2 === 1 ? (
            <mark key={index} className={styles.word}>
              {part}
            </mark>
          ) : (
            part
          ),
        )}
      </p>
      {line.unit != null ? (
        // Straight to the line on the reading screen, with the word marked —
        // the link the six citations have.
        <Link
          className={styles.inText}
          to={`/texts?text=${encodeURIComponent(documentId)}&unit=${line.unit}&word=${encodeURIComponent(line.word ?? spelling)}`}
        >
          در متن ←
        </Link>
      ) : null}
    </li>
  );
}
