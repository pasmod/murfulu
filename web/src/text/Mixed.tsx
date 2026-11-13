/**
 * A Persian sentence that carries Latin inside it, with every Latin run set
 * apart as an island of its own direction.
 *
 * **Why this exists.** The rule pack's sentences are written with the affix in
 * Latin — «از کنون‌کاربن با پسوند -ande کارنده‌کاربهر ساخته می‌شود» — and
 * were printed as plain text. Inside a right-to-left line the dash of `-ande`
 * belongs to neither side, takes the paragraph's direction and lands on the
 * far side of the letters: the reader saw «ande-», a prefix, where the rule
 * adds a suffix. Measured in the browser on 2026-11-13 for -ā, -ande, -ān,
 * -ār and -gar on the build screen. FRONTEND.md asked for bidi isolation on
 * every mixed cell; these sentences had none.
 *
 * Each run of Latin words — with its dashes, digits and the spaces between
 * them, so a phrase like *Kārboné do* stays in its own order — becomes a
 * {@link Latin} island. Everything else is left as written: the strings are
 * the rule pack's, and nothing here rewords them.
 */

import { Fragment } from "react";

import { Latin } from "./Latin";
import { splitLatin } from "./latinRuns";

export function Mixed({ children }: { children: string }) {
  return (
    <>
      {splitLatin(children).map((part, index) =>
        part.latin ? (
          <Latin key={index}>{part.text}</Latin>
        ) : (
          <Fragment key={index}>{part.text}</Fragment>
        ),
      )}
    </>
  );
}
