/**
 * How the whole result set breaks down.
 *
 * A page of fifty rows says nothing about the shape of an answer. *Is `-nā`
 * alive or medieval?* is a question about every hit, and these counts come
 * from Elasticsearch over the whole set — see `murfulu/search/facets.py`.
 *
 * Each value is a **link into a narrower search**, not a checkbox. The query
 * language already says how to narrow a search, so a facet writes the query it
 * stands for and the box shows it. The reader learns the syntax by using the
 * interface, and there is one way to express a search rather than two.
 *
 * **The field names come from syntax.ts and are not spelled out here.** This
 * panel wrote `category:…` from the day it was built and the parser had no
 * `category` field, so every click on a category value replaced a working
 * search with *this query was not read*. Nothing failed: the screen's tests
 * click the population panel only, and they mock the API, so the string this
 * file writes had never once been given to the thing that reads it. It is one
 * list now, and `tests/test_search_syntax_contract.py` checks it against the
 * parser.
 *
 * On a phone the panels are collapsed. They are supporting evidence, and the
 * results are what the reader came for.
 */

import type { Bucket, FacetName, Facets as FacetData } from "../../api/search";
import { Num } from "../../text/Num";
import { POPULATION_LABEL } from "../../text/lexicon";
import { persianCentury } from "../../text/numbers";
import { FIELDS, term } from "./syntax";
import styles from "./Facets.module.css";

/** The searchable field a facet narrows on, by the name the parser knows. */
function field(name: string) {
  const found = FIELDS.find((one) => one.name === name);
  if (!found) throw new Error(`${name} is not a searchable field`);
  return found;
}

/** What each facet is called, and how a value of it narrows a search. */
const PANELS: {
  name: FacetName;
  title: string;
  term: (value: string | number) => string;
  label: (value: string | number) => string;
}[] = [
  {
    name: "population",
    title: field("in").title,
    term: (value) => term(field("in").name, value),
    label: (value) => POPULATION_LABEL[String(value)] ?? String(value),
  },
  {
    name: "category",
    title: field("category").title,
    // Dehkhoda's categories are «اسم ذات», «اسم معنی» — two words, and an
    // unquoted space ended the term at the parser. `term` quotes it.
    term: (value) => term(field("category").name, value),
    label: (value) => String(value),
  },
  {
    name: "century",
    title: "سده",
    term: (value) => `century:${value}-${value}`,
    label: (value) => persianCentury(Number(value)),
  },
  {
    name: "author",
    title: field("author").title,
    term: (value) => term(field("author").name, value),
    label: (value) => String(value),
  },
  {
    name: "source",
    title: field("source").title,
    term: (value) => term(field("source").name, value),
    label: (value) => String(value),
  },
];

export interface FacetsProps {
  facets: FacetData;
  /** The query these counts belong to; a facet narrows it rather than replacing it. */
  query: string;
  onNarrow: (query: string) => void;
}

function Panel({
  title,
  buckets,
  onPick,
  label,
}: {
  title: string;
  buckets: Bucket[];
  onPick: (value: string | number) => void;
  label: (value: string | number) => string;
}) {
  return (
    <details className={styles.panel} open>
      <summary className={styles.summary}>{title}</summary>
      <ul className={styles.values}>
        {buckets.map((bucket) => (
          <li key={String(bucket.value)}>
            <button
              type="button"
              className={styles.value}
              onClick={() => onPick(bucket.value)}
            >
              <span className={styles.name}>{label(bucket.value)}</span>
              <Num className={styles.count} value={bucket.count} />
            </button>
          </li>
        ))}
      </ul>
    </details>
  );
}

export function Facets({ facets, query, onNarrow }: FacetsProps) {
  const shown = PANELS.filter((panel) => (facets[panel.name]?.length ?? 0) > 0);
  if (shown.length === 0) return null;

  return (
    <aside className={styles.facets} aria-label="باریک‌کردن نتیجه">
      {shown.map((panel) => (
        <Panel
          key={panel.name}
          title={panel.title}
          buckets={facets[panel.name] ?? []}
          label={panel.label}
          onPick={(value) => {
            const term = panel.term(value);
            // Narrowing, not replacing: the reader keeps what they asked for.
            onNarrow(query.includes(term) ? query : `${query} ${term}`.trim());
          }}
        />
      ))}
    </aside>
  );
}
