/**
 * The three levels' names, what each means, and where each sorts — shared by
 * the row (`Level.tsx`) and the sort (`Build.tsx`). Unconfirmed until the
 * linguist rules (docs/FOR_THE_LINGUIST.md L36).
 */

import type { FormLevel } from "../../api/generate";

/**
 * Poems a word needs, under its own reading, to be familiar. **The API decides
 * the level with its own copy, `MIN_POEMS` in murfulu/scoring/level.py**; this
 * one only words the explanation and the reason, and the two change together.
 */
export const MIN_POEMS = 10;

export const LEVEL_NAME: Record<1 | 2 | 3, string> = {
  3: "آشنا",
  2: "خوش‌ساخت",
  1: "کم‌پشتوانه",
};

/** What each name means, said once above the list and in each ⓘ. */
export const LEVEL_SAYS: Record<1 | 2 | 3, string> = {
  3: "دست‌کم در ده سروده با همین خوانش آمده است.",
  2: "کم آمده یا نیامده، ولی دستورهایش بارها واژه‌ای داده‌اند که در پیکره هست.",
  1: "کم آمده یا نیامده، و یکی از دستورهایش به‌ندرت چنین واژه‌ای داده است.",
};

export const NOT_KNOWN = "سنجیده نشده";

/**
 * Where a level sorts: familiar, well-formed, not known, weakly backed.
 *
 * **`_ranked` in murfulu/api/generate.py says the same** (`level.order`):
 * steps 1 and 2 are sorted here, a deep answer there. *Not known* sits above
 * weakly backed, because silence must not sink a word below one that was
 * measured and found weak. An older API sends no level, and every form then
 * ties here and the order below decides, as it did before.
 */
export function levelOrder(level: FormLevel | undefined): number {
  switch (level?.level) {
    case 3:
      return 0;
    case 2:
      return 1;
    case 1:
      return 3;
    default:
      return 2;
  }
}
