/**
 * The word bank (`/bank`): the whole lexicon, browsed by the linguist's groups.
 *
 * Asked for by the linguist with the word bank (2026-11-09): every word of
 * karbon 1.3.2 in his twelve groups and under his names, searchable, with both
 * stems shown for a verb. A word in several groups shows each; a loanword is
 * listed like any other and says that it builds nothing, because that is how
 * he wants them — out of word formation, visible here.
 *
 * The state lives in the address (`?group=…&q=…&page=…`), so a list can be
 * sent as a link and the back button walks back through it.
 */

import type React from "react";
import { type FormEvent, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import {
  type BankGroups,
  type BankPage,
  type BankWord,
  bankGroups,
  bankPage,
} from "../../api/bank";
import { SCREENS } from "../../shell/screens";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import styles from "./Bank.module.css";

const SCREEN = SCREENS.find((one) => one.path === "/bank")!;

/** Words per page: enough to scan, few enough to read on a phone. */
const PAGE_SIZE = 50;

function asError(reason: unknown): ApiError {
  return reason instanceof ApiError ? reason : new ApiError("unreachable", 0, String(reason));
}

function aborted(reason: unknown): boolean {
  return reason instanceof DOMException && reason.name === "AbortError";
}

function Stems({ word, labels }: { word: BankWord; labels: BankGroups["stem_labels"] }) {
  if (!word.past_stem_fa && !word.present_stem_fa) return null;
  return (
    <dl className={styles.stems}>
      <div>
        <dt>{labels.past || "پیشین‌کاربن"}</dt>
        <dd>
          {word.past_stem_fa ?? "—"}{" "}
          {word.past_stem_latin ? <Latin>{word.past_stem_latin}</Latin> : null}
        </dd>
      </div>
      <div>
        <dt>{labels.present || "کنون‌کاربن"}</dt>
        <dd>
          {word.present_stem_fa ?? "—"}{" "}
          {word.present_stem_latin ? <Latin>{word.present_stem_latin}</Latin> : null}
        </dd>
      </div>
    </dl>
  );
}

function Row({ word, labels }: { word: BankWord; labels: BankGroups["stem_labels"] }) {
  return (
    <li className={styles.word} data-out={!word.in_word_formation || undefined}>
      <p className={styles.head}>
        <span className={styles.spelling}>{word.spelling_fa}</span>
        <Latin className={styles.latin}>{word.latin}</Latin>
        {word.latin_variants.length > 0 ? (
          <span className={styles.variants}>
            یا{" "}
            {word.latin_variants.map((one, at) => (
              <span key={one}>
                {at > 0 ? "، " : null}
                <Latin>{one}</Latin>
              </span>
            ))}
          </span>
        ) : null}
      </p>
      <p className={styles.badges}>
        {word.groups.map((group) => (
          <span key={group.key} className={styles.group}>
            {group.label_fa}
          </span>
        ))}
        {!word.in_word_formation ? (
          <span className={styles.out}>در واژه‌سازی به کار نمی‌رود</span>
        ) : null}
        {word.needs_review ? <span className={styles.review}>بازبینی‌نشده</span> : null}
        {word.sense_count > 1 ? (
          <span className={styles.senses}>
            <Num value={word.sense_count} /> مدخل
          </span>
        ) : null}
      </p>
      <Stems word={word} labels={labels} />
      {word.definition_fa ? (
        <p className={styles.definition}>
          {word.definition_fa}
          {word.definition_truncated ? "…" : null}
        </p>
      ) : null}
      {word.in_word_formation ? (
        <p className={styles.actions}>
          <Link to={`/build?word=${encodeURIComponent(word.spelling_fa)}`}>
            ساختن از این واژه
          </Link>
        </p>
      ) : null}
    </li>
  );
}

export function Bank(): React.ReactElement {
  const [params, setParams] = useSearchParams();
  const group = params.get("group") ?? "";
  const query = params.get("q") ?? "";
  // Only a whole page number from 1 up; anything else in the address is page 1.
  const asked = Number(params.get("page") ?? "1");
  const pageNumber = Number.isInteger(asked) && asked >= 1 ? asked : 1;

  const [groups, setGroups] = useState<BankGroups | null>(null);
  const [found, setFound] = useState<BankPage | null>(null);
  // Two requests, two failures: a list that loads must not hide groups that did not.
  const [groupsError, setGroupsError] = useState<ApiError | null>(null);
  const [listError, setListError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [typed, setTyped] = useState(query);
  const [groupsAsked, setGroupsAsked] = useState(0);

  useEffect(() => {
    document.title = `${SCREEN.title} — مورفولو`;
  }, []);

  useEffect(() => {
    const stop = new AbortController();
    setGroupsError(null);
    bankGroups(stop.signal)
      .then(setGroups)
      .catch((reason: unknown) => {
        if (!aborted(reason)) setGroupsError(asError(reason));
      });
    return () => stop.abort();
  }, [groupsAsked]);

  useEffect(() => {
    setTyped(query);
    const stop = new AbortController();
    // The last page stays on screen while the next one loads, so the page
    // buttons — and the focus on them — are not torn down under the reader.
    setBusy(true);
    bankPage(
      {
        group: group || undefined,
        q: query || undefined,
        offset: (pageNumber - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      },
      stop.signal,
    )
      .then((page) => {
        setFound(page);
        setListError(null);
        setBusy(false);
      })
      .catch((reason: unknown) => {
        if (aborted(reason)) return;
        setListError(asError(reason));
        setBusy(false);
      });
    return () => stop.abort();
  }, [group, query, pageNumber]);

  function choose(next: { group?: string; q?: string; page?: number }, replace = false) {
    const merged = { group, q: query, page: String(pageNumber), ...next } as Record<
      string,
      string | number | undefined
    >;
    const kept: Record<string, string> = {};
    for (const [name, value] of Object.entries(merged)) {
      if (value !== undefined && value !== "" && !(name === "page" && String(value) === "1")) {
        kept[name] = String(value);
      }
    }
    setParams(kept, { replace });
  }

  // A page past the end — an old link, a hand-typed address — goes to the
  // last one, replacing the address rather than adding to the history.
  const lastPage = found && found.total > 0 ? Math.ceil(found.total / PAGE_SIZE) : 0;
  useEffect(() => {
    if (lastPage > 0 && pageNumber > lastPage) {
      setParams(
        (current) => {
          const next = new URLSearchParams(current);
          next.set("page", String(lastPage));
          return next;
        },
        { replace: true },
      );
    }
  }, [lastPage, pageNumber, setParams]);

  function search(event: FormEvent) {
    event.preventDefault();
    choose({ q: typed.trim(), page: 1 });
  }

  const labels = groups?.stem_labels ?? { past: "", present: "" };
  const total = found?.total ?? 0;
  const first = total === 0 ? 0 : (pageNumber - 1) * PAGE_SIZE + 1;
  const last = Math.min(total, pageNumber * PAGE_SIZE);
  const chosen = groups?.groups.find((one) => one.key === group);

  return (
    <article className={styles.screen}>
      <h1>{SCREEN.title}</h1>
      <p className={styles.purpose}>{SCREEN.purpose}</p>

      {groupsError ? (
        <p className={styles.trouble} role="status">
          گروه‌های بانک واژه خوانده نشدند.{" "}
          <button type="button" onClick={() => setGroupsAsked((n) => n + 1)}>
            دوباره
          </button>
        </p>
      ) : null}
      {listError ? (
        <p className={styles.trouble} role="status">
          فهرست واژه‌ها خوانده نشد. کمی بعد دوباره بیازمایید.
        </p>
      ) : null}

      {groups && !groups.has_bank ? (
        <p className={styles.note}>
          واژه‌نامه‌ای که برنامه امروز می‌خواند هنوز گروه‌های بانک واژه را ندارد؛ واژه‌ها
          بی‌گروه نشان داده می‌شوند.
        </p>
      ) : null}

      <nav className={styles.groups} aria-label="گروه‌های بانک واژه">
        <button
          type="button"
          aria-pressed={group === ""}
          onClick={() => choose({ group: "", page: 1 })}
        >
          همه {groups ? <Num value={groups.total} /> : null}
        </button>
        {groups?.groups.map((one) => (
          <button
            key={one.key}
            type="button"
            aria-pressed={group === one.key}
            onClick={() => choose({ group: one.key, page: 1 })}
          >
            {one.label_fa} <Num value={one.words} />
          </button>
        ))}
      </nav>

      {chosen && !chosen.in_word_formation ? (
        <p className={styles.note}>
          واژه‌های این گروه، به خواست زبان‌شناس، فعلاً در واژه‌سازی به کار نمی‌روند، ولی در بانک
          واژه دیده و جست‌وجو می‌شوند.
        </p>
      ) : null}

      <form className={styles.search} onSubmit={search} role="search">
        <label htmlFor="bank-query">جست‌وجو در بانک واژه</label>
        <input
          id="bank-query"
          type="search"
          value={typed}
          onChange={(event) => setTyped(event.target.value)}
          placeholder={SCREEN.invitation}
          maxLength={60}
        />
        <button type="submit">جست‌وجو</button>
      </form>

      {found && !busy ? (
        <p className={styles.count} role="status">
          {total === 0 ? (
            "واژه‌ای پیدا نشد."
          ) : (
            <>
              <Num value={first} />–<Num value={last} /> از <Num value={total} /> واژه
            </>
          )}
        </p>
      ) : (
        <p className={styles.count} role="status">
          در حال خواندن…
        </p>
      )}

      <ol className={styles.list} aria-busy={busy}>
        {found?.words.map((word) => (
          <Row key={`${word.spelling_fa}:${word.latin}`} word={word} labels={labels} />
        ))}
      </ol>

      {total > PAGE_SIZE ? (
        <nav className={styles.pages} aria-label="صفحه‌ها">
          <button
            type="button"
            disabled={pageNumber <= 1}
            onClick={() => choose({ page: pageNumber - 1 })}
          >
            صفحهٔ پیشین
          </button>
          <button
            type="button"
            disabled={last >= total}
            onClick={() => choose({ page: pageNumber + 1 })}
          >
            صفحهٔ پسین
          </button>
        </nav>
      ) : null}
    </article>
  );
}
