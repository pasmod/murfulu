/**
 * The rule pack, and what the corpus says about each rule. The expert's
 * screen; reading comes first and editing is task 8.1.
 *
 * **The disagreements are put at the top, because they are the finding.**
 * The source grammar states a strength for 3 of 195 rules, and all three land
 * in a different band when measured against a thousand years of poetry. That
 * is what the whole scoring argument rests on, and it should not be something
 * a reader has to hunt for.
 *
 * **A rule with no measurement and a rule measured at zero are drawn
 * differently.** 29 rules could not be exercised by this run at all — stem
 * rules are a different operation, compounding is never precomputed — and
 * each carries its reason rather than a zero that looks like a result.
 */

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import {
  isAffixRule,
  isGlide,
  rules as fetchRules,
  type RulePack,
} from "../../api/rules";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { SCREENS } from "../../shell/screens";
import { GlideRow } from "./GlideRow";
import { RuleRow } from "./RuleRow";
import styles from "./Rules.module.css";

const SCREEN = SCREENS.find((one) => one.path === "/rules")!;

/**
 * How many rules the list opens with.
 *
 * Measured in a real browser at 375 px: the whole pack renders **42,840 px**
 * of page — 52 phone screens — because all 212 rules are in the DOM at once.
 * The build screen had the same shape and takes the same answer: open at a
 * length somebody can read, put the count of the rest on the control that
 * opens it, and show the lot on one press. Nothing is hidden.
 *
 * Twenty here as there, and a rule row is the taller of the two, so this is
 * about five phone screens.
 */
const FIRST = 20;

const FAMILIES = [
  { key: "", label: "همه" },
  { key: "V", label: "کارواژه" },
  { key: "N", label: "نام" },
  { key: "G", label: "میانجی" },
  { key: "S", label: "بن" },
];

export function Rules() {
  const [params, setParams] = useSearchParams();
  const family = params.get("family") ?? "";
  const only = params.get("only") ?? "";

  const [pack, setPack] = useState<RulePack | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    document.title = `${SCREEN.title} — مورفولو`;
    const stop = new AbortController();
    fetchRules(stop.signal)
      .then(setPack)
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

  // The affix rules on their own. A glide is not measured for productivity,
  // carries no authored strength and is never flagged for review, so every
  // question below is one it cannot answer — and asking it anyway would count
  // seventeen rules as *unmeasured* when there is nothing there to measure.
  const affixRules = useMemo(
    () => (pack?.rules ?? []).filter(isAffixRule),
    [pack],
  );

  const disagreeing = useMemo(
    () => affixRules.filter((one) => one.productivity?.disagrees_with_strength),
    [affixRules],
  );

  const shown = useMemo(() => {
    let found = pack?.rules ?? [];
    if (family) found = found.filter((one) => one.family === family);
    if (only === "flagged") {
      found = found.filter((one) => isAffixRule(one) && one.needs_expert_check);
    }
    if (only === "unmeasured") {
      found = found.filter((one) => isAffixRule(one) && !one.productivity?.measured);
    }
    return found;
  }, [pack, family, only]);

  // Folded again whenever the reader narrows: opening the whole pack and then
  // pressing a family button would otherwise leave the next list open too,
  // and the page would be long again for a reason nobody chose.
  const [whole, setWhole] = useState(false);
  const listed = whole ? shown : shown.slice(0, FIRST);
  const folded = shown.length - listed.length;

  const narrow = (next: Record<string, string>) => {
    const merged = { family, only, ...next };
    setWhole(false);
    setParams(
      Object.fromEntries(Object.entries(merged).filter(([, value]) => value)),
    );
  };

  return (
    <article className={styles.screen}>
      <h1>{SCREEN.title}</h1>
      <p className={styles.purpose}>{SCREEN.purpose}</p>

      {error ? (
        <p className={styles.trouble} role="status">
          دستورها خوانده نشد. کمی بعد دوباره بیازمایید.
        </p>
      ) : null}

      {pack ? (
        <>
          <p className={styles.provenance}>
            <Num value={pack.count} /> دستور، دستورنامهٔ{" "}
            <Latin>{pack.rule_pack_version}</Latin>.{" "}
            {pack.corpus_version ? (
              <>
                سنجیده بر پیکرهٔ <Latin>{pack.corpus_version}</Latin>.
              </>
            ) : (
              "هنوز هیچ سنجشی بر پیکره انجام نشده است."
            )}
          </p>

          {disagreeing.length > 0 ? (
            <section className={styles.finding} aria-labelledby="finding">
              <h2 id="finding" className={styles.findingTitle}>
                <Num value={disagreeing.length} /> دستور که سرچشمه و سنجش دربارهٔ
                آنها یکی نمی‌گویند
              </h2>
              <p className={styles.findingNote}>
                این یافته است، نه خطا. سرچشمه تنها برای{" "}
                <Num value={affixRules.filter((one) => one.strength).length} />{" "}
                دستور نیرویی نوشته است.
              </p>
              <ul className={styles.rules}>
                {disagreeing.map((rule) => (
                  <RuleRow key={rule.id} rule={rule} />
                ))}
              </ul>
            </section>
          ) : null}

          <div className={styles.filters}>
            {FAMILIES.map((one) => (
              <button
                key={one.key}
                type="button"
                className={one.key === family ? styles.chosen : styles.filter}
                onClick={() => narrow({ family: one.key })}
              >
                {one.label}
              </button>
            ))}
            <button
              type="button"
              className={only === "flagged" ? styles.chosen : styles.filter}
              onClick={() => narrow({ only: only === "flagged" ? "" : "flagged" })}
            >
              نیازمند بررسی
            </button>
            <button
              type="button"
              className={only === "unmeasured" ? styles.chosen : styles.filter}
              onClick={() =>
                narrow({ only: only === "unmeasured" ? "" : "unmeasured" })
              }
            >
              سنجیده‌نشده
            </button>
          </div>

          <p className={styles.total} role="status">
            <Num value={shown.length} /> دستور نشان داده می‌شود.
          </p>

          <ul className={styles.rules}>
            {listed.map((rule) =>
              isGlide(rule) ? (
                <GlideRow key={rule.id} glide={rule} />
              ) : (
                <RuleRow key={rule.id} rule={rule} />
              ),
            )}
          </ul>

          {folded > 0 ? (
            <button
              type="button"
              className={styles.more}
              onClick={() => setWhole(true)}
            >
              <Num value={folded} /> دستور دیگر — نشان بده
            </button>
          ) : null}
        </>
      ) : null}
    </article>
  );
}
