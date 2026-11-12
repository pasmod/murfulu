/**
 * The one line a screen shows while its answer is on the way.
 *
 * Most screens showed nothing at all between the heading and the answer, so a
 * slow request looked the same as a broken one. The word bank already said
 * «در حال خواندن…»; this is that sentence, in one place, for the others.
 *
 * **It is a status message, so it says so** (`role="status"`, WCAG 4.1.3): a
 * reader who cannot see the screen has to be told the answer is on its way
 * without focus being moved to the sentence. A review on 2026-11-13 caught the
 * first version, which left the role off so that tests looking for a screen's
 * error by that role would not find this line instead.
 *
 * **It holds back for a moment, and that is why the two do not collide.** Most
 * answers arrive faster than a reader can read the sentence, and a word that
 * flashes and goes is worse than a short blank — for a screen reader as much
 * as for an eye, which would otherwise hear it on every change of screen. So
 * nothing is rendered until the wait has lasted `HOLD_MS`; a screen's error
 * line and its answer both replace it, never stand beside it.
 */

import { useEffect, useState } from "react";

import page from "../styles/page.module.css";

/** How long a wait has to last before it is worth saying anything. */
const HOLD_MS = 300;

export function Waiting(): React.ReactElement | null {
  const [due, setDue] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setDue(true), HOLD_MS);
    return () => window.clearTimeout(timer);
  }, []);

  if (!due) return null;

  return (
    <p className={page.waiting} role="status">
      در حال خواندن…
    </p>
  );
}
