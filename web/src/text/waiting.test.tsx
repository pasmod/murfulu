/**
 * The waiting line: silent for a short wait, a status message for a long one.
 */

import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Waiting } from "./Waiting";

describe("the waiting line", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("says nothing while the wait is still short", () => {
    render(<Waiting />);
    act(() => {
      vi.advanceTimersByTime(250);
    });
    // Nothing at all — not an empty status either, which a test or a screen
    // reader looking for the screen's error by that role would find first.
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("is a status message once the wait has lasted", () => {
    render(<Waiting />);
    act(() => {
      vi.advanceTimersByTime(300);
    });
    // By role, so it reaches a reader who cannot see the screen (WCAG 4.1.3).
    expect(screen.getByRole("status")).toHaveTextContent("در حال خواندن…");
  });

  it("does not speak after the answer has replaced it", () => {
    const { unmount } = render(<Waiting />);
    unmount();
    // The timer is cleared with the component: no state is set on something
    // that is no longer on the screen.
    expect(vi.getTimerCount()).toBe(0);
  });
});
