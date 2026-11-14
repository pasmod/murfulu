/**
 * One unit of a text: a couplet, a verse half, a prose paragraph or a note.
 *
 * Each word stands over its Behnevis — **every** reading the bank has, one
 * under another and all alike, because none is proposed — and the words run
 * right to left and wrap like text (the project lead's direction A,
 * 2026-11-13). A couplet's halves stand side by side where the window has
 * room and one under the other on a phone, the second set in. A note is the
 * source's own words: shown, never split into words, never counted.
 */

import type React from "react";

import type { TextUnit, TextWord, WordKnown } from "../../api/texts";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { KIND } from "./kinds";
import styles from "./Reader.module.css";

export interface Chosen {
  line: number;
  word: number;
}

export interface UnitViewProps {
  unit: TextUnit;
  words: Record<string, WordKnown>;
  chosen: Chosen | null;
  onChoose: (chosen: Chosen | null) => void;
  /** The id of the panel a chosen word opens, for `aria-controls`. */
  panelId: string;
  /** The spelling a citation led here for, when this is its unit. */
  found: string | null;
  /** The word's panel, drawn under the lines while a word here is chosen. */
  panel: React.ReactNode;
}

export function UnitView({
  unit,
  words,
  chosen,
  onChoose,
  panelId,
  found,
  panel,
}: UnitViewProps) {
  if (unit.kind === "note") {
    return (
      <li className={styles.note} id={`unit-${unit.index}`}>
        <span className={styles.noteKind}>{KIND.note}</span>
        {unit.lines.map((line, index) => (
          <p key={index} className={styles.noteText}>
            {line.text}
          </p>
        ))}
      </li>
    );
  }

  const verse = unit.kind === "couplet";
  return (
    <li
      className={found !== null ? `${styles.unit} ${styles.hit}` : styles.unit}
      id={`unit-${unit.index}`}
      data-kind={unit.kind}
    >
      <span className={styles.number}>
        {unit.number !== null ? <Num value={unit.number} /> : null}
        <span className={styles.kind}>{KIND[unit.kind]}</span>
      </span>
      <div className={styles.body}>
        {found !== null ? (
          <p className={styles.hitNote}>همان سطرِ شاهدمثالِ «{found}»</p>
        ) : null}
        <div className={verse ? styles.couplet : styles.flow}>
          {unit.lines.map((line, lineIndex) => (
            <div key={lineIndex} className={styles.line} data-position={line.position ?? ""}>
              {(line.words ?? []).map((word, wordIndex) => (
                <WordButton
                  key={wordIndex}
                  word={word}
                  known={word.s ? words[word.s] : undefined}
                  open={chosen?.line === lineIndex && chosen.word === wordIndex}
                  sought={found !== null && word.s === found}
                  panelId={panelId}
                  onPress={(open) =>
                    onChoose(open ? null : { line: lineIndex, word: wordIndex })
                  }
                />
              ))}
            </div>
          ))}
        </div>
        {panel}
      </div>
    </li>
  );
}

function WordButton({
  word,
  known,
  open,
  sought,
  panelId,
  onPress,
}: {
  word: TextWord;
  known: WordKnown | undefined;
  open: boolean;
  sought: boolean;
  panelId: string;
  onPress: (open: boolean) => void;
}) {
  if (!word.s) {
    // Not a counted word — an opening «, a number, a Latin name: part of the
    // text, isolated so its direction cannot reorder its neighbours.
    return <bdi className={styles.punctuation}>{word.fa}</bdi>;
  }
  const readings = known?.readings ?? [];
  const against = new Set(word.against ?? []);
  const state = readings.length === 0 ? "none" : readings.length === 1 ? "one" : "several";
  const fitting = readings.filter((one) => !against.has(one.id));
  const ruledOut = readings.filter((one) => against.has(one.id));
  const said =
    readings.length === 0
      ? "خوانشی در بانک واژه نیست"
      : [
          fitting.map((one) => one.latin).join("، "),
          ruledOut.length > 0
            ? `اعراب متن با ${ruledOut.map((one) => one.latin).join("، ")} نمی‌خواند`
            : "",
        ]
          .filter(Boolean)
          .join("؛ ");
  return (
    <button
      type="button"
      className={styles.word}
      data-state={state}
      data-sought={sought || undefined}
      aria-expanded={open}
      aria-controls={open ? panelId : undefined}
      aria-label={`${word.fa}: ${said}`}
      onClick={() => onPress(open)}
    >
      <span className={styles.fa}>
        {word.fa}
        {word.after ? <span className={styles.after}>{word.after}</span> : null}
      </span>
      <span className={styles.latins}>
        {readings.length === 0 ? (
          <span className={styles.unread}>؟</span>
        ) : (
          readings.map((one) => (
            <Latin
              key={one.id}
              className={against.has(one.id) ? `${styles.latin} ${styles.ruledOut}` : styles.latin}
            >
              {one.latin}
            </Latin>
          ))
        )}
      </span>
    </button>
  );
}
