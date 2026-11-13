/**
 * What a reader sees beside each kind of unit. The words are ours and
 * unconfirmed until the linguist rules (docs/FOR_THE_LINGUIST.md L39).
 */

import type { TextUnit } from "../../api/texts";

export const KIND: Record<TextUnit["kind"], string> = {
  couplet: "بیت",
  half: "مصراع",
  prose: "نثر",
  line: "سطر",
  note: "یادداشت سرچشمه",
};
