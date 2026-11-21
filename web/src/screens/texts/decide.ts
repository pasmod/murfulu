/**
 * Deciding a reading once for every like place of a spelling (2026-11-21):
 * what a scope reaches, and how the screens say it.
 *
 * A decision says a spelling reads so everywhere, or wherever it follows one
 * word, or wherever it precedes one. The model reads the decisions in force
 * at its next build; a reading the bank lacks goes to karbon instead. The
 * counts of places come from the measured list (`GET /texts/unsure`), which
 * keys a spelling as the model does: without half-spaces.
 */

import type { Decision, Scope, UnsureKind, UnsureSpelling } from "../../api/texts";

const ZWNJ = "\u200c";

/** A spelling as the list and the model key it. */
export function keyOf(spelling: string): string {
  return spelling.replaceAll(ZWNJ, "");
}

/** How many places a scope reaches, and how many of them are unsure now. */
export interface Reach {
  places: number;
  unsure: number;
}

/**
 * What a decision with this scope reaches, as the list measured it; null
 * where the list does not know (a spelling or a neighbour it did not keep).
 */
export function reach(
  listed: UnsureSpelling | null | undefined,
  scope: Scope,
  word: string | null,
): Reach | null {
  if (!listed) return null;
  if (scope === "everywhere") return { places: listed.places, unsure: listed.unsure };
  if (!word) return null;
  // The words before the spelling are the ones it stands after.
  const side = scope === "after_word" ? listed.before : listed.after;
  const found = side.find(([near]) => near === keyOf(word));
  return found ? { places: found[1], unsure: found[2] } : null;
}

/** «همه‌جا», «پس از «که»», «پیش از «که»». */
export function scopeLabel(scope: Scope, word: string | null): string {
  if (scope === "after_word") return `هر جا پس از «${word ?? ""}»`;
  if (scope === "before_word") return `هر جا پیش از «${word ?? ""}»`;
  return "همه‌جا";
}

/** What becomes of a decision, in one sentence. */
export function decidedFate(inBank: boolean): string {
  return inBank
    ? "برنامه این خوانش را می‌شناسد و در به‌روزرسانیِ بعدی همهٔ این جاها را چنین می‌خواند."
    : "این خوانش در بانک واژه نیست. آن را برای افزودن به کاربن پیشنهاد می‌کنیم؛ تا آن وقت برنامه این جاها را مثل پیش می‌خواند.";
}

/** What a kind of decision means, in two or three words. */
export const KIND_FA: Record<UnsureKind, string> = {
  choice: "چند خوانش در بانک",
  one: "یک خوانش در بانک",
  missing: "در بانک نیست",
};

/** Whether two decisions reach the same places: same scope, same word as keyed. */
export function sameReach(one: Decision, scope: Scope, word: string | null): boolean {
  return one.scope === scope && keyOf(one.scope_word ?? "") === keyOf(word ?? "");
}

/** The decisions in force once `now` is saved: it replaces the one with its reach. */
export function replacing(decisions: Decision[], now: Decision): Decision[] {
  return [now, ...decisions.filter((one) => !sameReach(one, now.scope, now.scope_word))];
}
