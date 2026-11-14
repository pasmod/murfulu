/**
 * Every text of a spelling, a page at a time: the list itself.
 *
 * Under the word page's «همهٔ شواهد» and inside the build screen's corpus
 * panel alike — one list, so the two cannot drift apart. Who holds the choice
 * (the address, or a row's own state) is the caller's; this shows what
 * `useEvidence` found and says when the reader chooses.
 *
 * **Its counts are the search index's, the word's counts the counting's.**
 * The two can differ by a few texts, and where they do the list says why in
 * one sentence rather than letting two figures disagree in silence.
 */

import type { ReactNode } from "react";

import { Latin } from "../text/Latin";
import { Num } from "../text/Num";
import { Waiting } from "../text/Waiting";
import { AuthorFilter } from "./AuthorFilter";
import { EvidenceText } from "./EvidenceText";
import type { Found } from "./useEvidence";
import styles from "./Evidence.module.css";

export interface EvidenceListProps {
  spelling: string;
  found: Found;
  /** The author select's value: `EVERY`, `UNNAMED` or a name. */
  chosen: string;
  /** From 1. */
  page: number;
  /** Texts per page. */
  size: number;
  /** The counting's number of texts, where the caller has it. */
  docCount: number | undefined;
  /** The corpus version the caller's own figures belong to. */
  version: string | undefined;
  /** Lines a text shows before the rest are asked for. */
  glance?: number;
  /** What the figures beside the list are called: «شمارش بالا», the default. */
  figures?: ReactNode;
  onChoose: (author: string) => void;
  onPage: (page: number) => void;
}

export function EvidenceList({
  spelling,
  found,
  chosen,
  page,
  size,
  docCount,
  version,
  glance,
  figures = "شمارش بالا",
  onChoose,
  onPage,
}: EvidenceListProps) {
  const { whole, current, shown } = found;
  if (!whole) return null;
  const matching = current?.matching ?? 0;
  const first = matching === 0 ? 0 : (page - 1) * size + 1;
  const last = Math.min(matching, page * size);
  const one = chosen !== "";
  const sameVersion = !whole.corpus_version || !version || whole.corpus_version === version;

  return (
    <div className={styles.list}>
      {!sameVersion ? (
        <p className={styles.note}>
          این فهرست از نسخهٔ <Latin>{whole.corpus_version ?? ""}</Latin> پیکره است و {figures} از
          نسخهٔ <Latin>{version ?? ""}</Latin>.
        </p>
      ) : docCount !== undefined && whole.total !== docCount ? (
        <p className={styles.note}>
          این فهرست <Num value={whole.total} /> متن دارد و {figures} <Num value={docCount} />، چون
          جست‌وجوی متن‌ها چند حرف را که شمارش جدا می‌شمارد یکی می‌گیرد، مانند آ و ا یا ۀ و ه، و چند
          واژه را جور دیگری از هم جدا می‌کند.
        </p>
      ) : null}

      <AuthorFilter evidence={whole} chosen={chosen} onChoose={onChoose} />

      {found.summaryFailed ? (
        <p className={styles.trouble}>شمار این فهرست نرسید. کمی بعد دوباره بیازمایید.</p>
      ) : current ? (
        <p className={styles.count} role="status">
          {matching === 0 ? (
            "متنی در این فهرست نیست."
          ) : (
            <>
              <Num value={first} />–<Num value={last} /> از <Num value={matching} /> متن
              {one && current.lines !== null ? (
                <>
                  ، در <Num value={current.lines} /> سطر
                </>
              ) : null}
            </>
          )}
        </p>
      ) : null}

      {found.pageFailed ? (
        <p className={styles.trouble}>این صفحه نرسید. کمی بعد دوباره بیازمایید.</p>
      ) : shown ? (
        <ol className={styles.texts}>
          {shown.texts.map((text) => (
            <EvidenceText key={text.document_id} text={text} spelling={spelling} glance={glance} />
          ))}
        </ol>
      ) : (
        <Waiting />
      )}

      {matching > size ? (
        <nav className={styles.pages} aria-label={`صفحه‌های شواهد «${spelling}»`}>
          <button
            type="button"
            className={styles.page}
            disabled={page <= 1}
            onClick={() => onPage(page - 1)}
          >
            صفحهٔ پیشین
          </button>
          <button
            type="button"
            className={styles.page}
            disabled={last >= matching}
            onClick={() => onPage(page + 1)}
          >
            صفحهٔ پسین
          </button>
        </nav>
      ) : null}
    </div>
  );
}
