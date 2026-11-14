/**
 * Every text the spelling is written in, below the six citations.
 *
 * The six are one line per author on purpose — thirty hits in one poem are
 * often a rhyme. This is the rest, for a reader who wants all of it: every
 * text, each with every line holding the spelling, a page of twenty at a time,
 * with the authors to choose one from. Authors come by how many texts are
 * theirs, most first, and each author's texts in the source's order, so a page
 * is the same on every reload; the state is in the address (`?all=1`,
 * `author`, `page`), so a page can be linked to.
 *
 * The list itself is shared with the build screen's corpus panel
 * (`evidence/EvidenceList.tsx`); this card adds the totals, the note and the
 * control, and keeps the choice in the address.
 *
 * **The lines are evidence for the spelling, never for one reading** — the
 * same lines serve مرد as *mard* and as *mord*.
 */

import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

import { EVIDENCE_PAGE } from "../../api/evidence";
import { EVERY, UNNAMED } from "../../evidence/AuthorFilter";
import { EvidenceList } from "../../evidence/EvidenceList";
import { chosenOf, useEvidence } from "../../evidence/useEvidence";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { Waiting } from "../../text/Waiting";
import styles from "./AllEvidence.module.css";

export interface AllEvidenceProps {
  spelling: string;
  /** The counting's number of texts, from the word's own record. */
  docCount: number | undefined;
  /** The corpus version the word's own figures belong to. */
  version: string | undefined;
}

export function AllEvidence({ spelling, docCount, version }: AllEvidenceProps) {
  const [params, setParams] = useSearchParams();
  const open = params.get("all") === "1";
  const unnamed = params.get("unnamed") === "1";
  const author = unnamed ? undefined : (params.get("author") ?? undefined);
  const asked = Number(params.get("page") ?? "1");
  const pageNumber = Number.isInteger(asked) && asked >= 1 ? asked : 1;
  const choice = { author, unnamed, page: pageNumber };

  const found = useEvidence(spelling, choice, { open, size: EVIDENCE_PAGE });
  const { whole, current, summaryFailed } = found;
  // Named authors, as the word's own author count has them.
  const named = whole?.authors.filter((one) => one.author !== null).length ?? 0;
  const lastPage = Math.max(1, Math.ceil((current?.matching ?? 0) / EVIDENCE_PAGE));

  function choose(next: { all?: boolean; author?: string; page?: number }) {
    setParams(
      (now) => {
        const out = new URLSearchParams(now);
        if (next.all === true) out.set("all", "1");
        if (next.all === false) {
          for (const name of ["all", "author", "unnamed", "page"]) out.delete(name);
        }
        if (next.author !== undefined) {
          out.delete("author");
          out.delete("unnamed");
          if (next.author === UNNAMED) out.set("unnamed", "1");
          else if (next.author !== EVERY) out.set("author", next.author);
        }
        if (next.page !== undefined) {
          if (next.page > 1) out.set("page", String(next.page));
          else out.delete("page");
        }
        return out;
      },
      { replace: next.page === undefined },
    );
  }

  // A page past the end — an old link, a hand-typed address — goes to the
  // last one, as the word bank's does.
  useEffect(() => {
    if (!current || pageNumber <= lastPage) return;
    setParams(
      (now) => {
        const out = new URLSearchParams(now);
        if (lastPage > 1) out.set("page", String(lastPage));
        else out.delete("page");
        return out;
      },
      { replace: true },
    );
  }, [current, pageNumber, lastPage, setParams]);

  return (
    <section className={styles.block} aria-labelledby="all-evidence">
      <h2 id="all-evidence" className={styles.blockTitle}>
        همهٔ شواهد
      </h2>
      {summaryFailed && !whole ? (
        <p className={styles.trouble}>شمار متن‌ها نرسید. کمی بعد دوباره بیازمایید.</p>
      ) : !whole ? (
        <Waiting />
      ) : (
        <>
          <p className={styles.summary}>
            {whole.corpus_version ? (
              <>
                در نسخهٔ <Latin>{whole.corpus_version}</Latin> پیکره،{" "}
              </>
            ) : null}
            املای «{spelling}» در <Num value={whole.total} /> متن از <Num value={named} /> نویسنده
            آمده است
            {current && !author && !unnamed && current.lines !== null ? (
              <>
                ، در <Num value={current.lines} /> سطر
              </>
            ) : null}
            .
            {current && current.lines === null ? (
              // Counting them means reading every text, which for و is the
              // whole corpus; each text below still says how many it has.
              <span className={styles.aside}> سطرهای فهرستی به این بلندی شمرده نمی‌شوند.</span>
            ) : null}
          </p>
          <p className={styles.note}>
            این سطرها شاهد املای «{spelling}»اند، نه یکی از خوانش‌های آن؛ اینکه هر سطر کدام خوانش را
            می‌خواهد، گفته نمی‌شود.
          </p>
          <button
            type="button"
            className={styles.toggle}
            aria-expanded={open}
            aria-controls="all-evidence-list"
            onClick={() => choose({ all: !open })}
          >
            {open ? "بستن همهٔ شواهد" : "نشان دادن همهٔ شواهد"}
          </button>
        </>
      )}

      {/* Always there, so the toggle's `aria-controls` names an element. */}
      <div id="all-evidence-list">
        {open ? (
          <EvidenceList
            spelling={spelling}
            found={found}
            chosen={chosenOf(choice)}
            page={pageNumber}
            size={EVIDENCE_PAGE}
            docCount={docCount}
            version={version}
            onChoose={(value) => choose({ author: value, page: 1 })}
            onPage={(page) => choose({ page })}
          />
        ) : null}
      </div>
    </section>
  );
}
