/**
 * The feedback affordance: one button in the corner, on every screen, and the
 * panel behind it.
 *
 * It is in the frame rather than on a screen because docs/FRONTEND.md says so
 * — retrofitting it later means touching every component — and because the
 * store it writes to is the evaluation set the scoring weights will be fitted
 * against. Building review early is what makes the score mean anything.
 *
 * **No screenshot, and that is settled rather than pending** — the structured
 * context is the reusable half and is captured in full, while an image would
 * capture whatever else was on the reviewer's screen. See docs/REVIEW.md.
 *
 * **And no key to type in.** The panel used to ask for an API token before it
 * would show the form, because only an expert could leave a linguistic
 * verdict. There is one account and no roles as of 2026-08-17: the site
 * password is the whole of the authentication, so a reader who can see this
 * button can already use it.
 */

import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import { me, type Account } from "../api/feedback";
import { useFeedback, whereWeAre } from "./subject";
import { Form } from "./Form";
import styles from "./Feedback.module.css";

type Stage = "asking" | "form" | "done" | "unreachable";

export function Feedback() {
  const { open, raise, close } = useFeedback();
  const location = useLocation();
  const [account, setAccount] = useState<Account | null>(null);
  const [stage, setStage] = useState<Stage>("asking");
  // Who is calling is asked when the panel opens, not on every page load: the
  // app is readable without an account and most readers never leave feedback.
  useEffect(() => {
    if (!open) return;
    const stop = new AbortController();
    setStage("asking");
    me(stop.signal)
      .then((who) => {
        setAccount(who);
        setStage("form");
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        // One failure left, where there used to be two. A credential problem
        // is no longer possible — the wall in front of the site is the only
        // thing that refuses anyone — so anything that gets here is the store
        // being unreachable.
        setStage("unreachable");
      });
    return () => stop.abort();
  }, [open]);

  return (
    <>
      <button
        type="button"
        className={styles.launcher}
        onClick={() => raise()}
        aria-haspopup="dialog"
      >
        بازخورد
      </button>

      {open ? (
        <div
          className={styles.panel}
          role="dialog"
          aria-modal="false"
          aria-label={`بازخورد دربارهٔ ${open.label}`}
        >
          <header className={styles.head}>
            <h2 className={styles.title}>بازخورد</h2>
            <button type="button" className={styles.close} onClick={close}>
              بستن
            </button>
          </header>

          <p className={styles.about}>
            دربارهٔ: <strong>{open.label}</strong>
          </p>

          {stage === "asking" ? <p className={styles.explain}>یک لحظه…</p> : null}

          {stage === "unreachable" ? (
            <p className={styles.trouble} role="alert">
              انبارِ بازخورد در دسترس نیست. کمی بعد دوباره بیازمایید.
            </p>
          ) : null}

          {stage === "form" && account ? (
            <Form
              subject={open}
              account={account}
              where={whereWeAre(location)}
              onDone={() => setStage("done")}
            />
          ) : null}

          {stage === "done" ? (
            <p className={styles.thanks} role="status">
              ثبت شد. سپاسگزاریم.
            </p>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
