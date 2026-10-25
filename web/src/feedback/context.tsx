/**
 * The provider that holds what is being judged.
 *
 * The types, the hooks and the context object are in `subject.ts`; this file
 * exports one component and nothing else.
 */

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";

import { APP, FeedbackContext, type Handle, type Subject } from "./subject";

export function FeedbackProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState<Subject | null>(null);
  const [screen, setScreen] = useState<Subject | null>(null);
  const location = useLocation();

  // A screen's subject belongs to that screen. Carrying it across would let a
  // reader comment on the word they were looking at a moment ago while the
  // rules page is on screen, and the record would name the wrong thing.
  useEffect(() => {
    setScreen(null);
    setOpen(null);
  }, [location.pathname]);

  const value = useMemo<Handle>(
    () => ({
      open,
      screen: screen ?? APP,
      raise: (subject?: Subject) => setOpen(subject ?? screen ?? APP),
      close: () => setOpen(null),
      declare: setScreen,
    }),
    [open, screen],
  );

  return (
    <FeedbackContext.Provider value={value}>{children}</FeedbackContext.Provider>
  );
}
