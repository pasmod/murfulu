/**
 * The one line a screen shows while its answer is on the way.
 *
 * Most screens showed nothing at all between the heading and the answer, so a
 * slow request looked the same as a broken one. The word bank already said
 * «در حال خواندن…»; this is that sentence, in one place, for the others.
 *
 * Not `role="status"`: every screen's error line has that role, and the tests
 * and a screen reader both find the error by it. This line is replaced by the
 * answer a moment later and has nothing to announce.
 */

import page from "../styles/page.module.css";

export function Waiting(): React.ReactElement {
  return <p className={page.waiting}>در حال خواندن…</p>;
}
