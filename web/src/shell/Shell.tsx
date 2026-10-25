/**
 * The frame every screen sits in: a skip link, the masthead, the navigation
 * and the main region.
 *
 * It also carries the feedback affordance, which docs/FRONTEND.md says has to
 * be on every view from the start: retrofitting it means touching every
 * component.
 *
 * Mobile first. On a narrow screen the navigation is a scrolling row of
 * touch-sized targets under the title; from the first breakpoint it sits
 * beside the title. There is no hamburger — six items fit, and a menu that
 * hides them would make the app harder to learn, which docs/FRONTEND.md says
 * it must not be.
 */

import { NavLink, Outlet } from "react-router-dom";

import { Feedback } from "../feedback/Feedback";
import { FeedbackProvider } from "../feedback/context";
import { NAVIGATION } from "./screens";
import styles from "./Shell.module.css";

export function Shell() {
  return (
    <FeedbackProvider>
      <div className={styles.page}>
        <a className={styles.skip} href="#main">
          رفتن به محتوای اصلی
        </a>

        <header className={styles.masthead}>
          <div className={styles.brand}>
            <span className={styles.name}>مورفولو</span>
            <span className={styles.tagline}>واژه‌سازی فارسی</span>
          </div>

          <nav className={styles.nav} aria-label="بخش‌های اصلی">
            <ul className={styles.navList}>
              {NAVIGATION.map((screen) => (
                <li key={screen.path}>
                  <NavLink
                    to={screen.path}
                    end={screen.path === "/"}
                    // The gloss is the link's *description*, not part of its
                    // name. A screen reader then says «جست‌وجو، پیوند» and the
                    // explanation after it, the way a sighted reader sees a
                    // name with a line under it — where letting both spans
                    // make the name would give one long run and no name at
                    // all. The label is named explicitly for that reason, and
                    // it is the visible text, so WCAG 2.5.3 still holds.
                    aria-label={screen.label}
                    aria-describedby={`says-${screen.path}`}
                    className={({ isActive }) =>
                      isActive
                        ? `${styles.navLink} ${styles.current}`
                        : styles.navLink
                    }
                  >
                    <span className={styles.navName}>{screen.label}</span>
                    {/* What it does, under what it is called. The names are
                        nouns and three of them — ساخت، ترکیب، تحلیل — cannot
                        be told apart by a reader who has not used the app. */}
                    <span className={styles.navGloss} id={`says-${screen.path}`}>
                      {screen.gloss}
                    </span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </header>

        <main id="main" className={styles.main} tabIndex={-1}>
          <Outlet />
        </main>

        {/* Present on every view, never on a screen of its own. */}
        <Feedback />
      </div>
    </FeedbackProvider>
  );
}
