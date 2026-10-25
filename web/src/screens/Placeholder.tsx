/**
 * A screen that is not built yet.
 *
 * It is not a blank page and not a spinner. docs/FRONTEND.md asks empty states
 * to say what to do next, so each one carries the screen's purpose, the thing
 * the reader would do here, and which task builds it — the app is a working
 * artefact under construction and saying so is more useful than pretending.
 *
 * Tasks 7.2 to 7.8 replace these one at a time.
 */

import { useEffect } from "react";

import type { Screen } from "../shell/screens";
import styles from "./Placeholder.module.css";

export interface PlaceholderProps {
  screen: Screen;
}

export function Placeholder({ screen }: PlaceholderProps) {
  useEffect(() => {
    document.title = `${screen.title} — مورفولو`;
  }, [screen.title]);

  return (
    <article className={styles.screen}>
      <h1>{screen.title}</h1>
      <p className={styles.purpose}>{screen.purpose}</p>

      <div className={styles.empty}>
        <p className={styles.invitation}>{screen.invitation}</p>
        <p className={styles.pending}>
          این صفحه هنوز ساخته نشده است. کار {screen.task}.
        </p>
      </div>
    </article>
  );
}
