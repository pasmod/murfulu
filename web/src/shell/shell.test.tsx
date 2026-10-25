/** The frame: navigation, routing, and the way in for a keyboard. */

import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { renderApp } from "../test/render";
import { NAVIGATION, SCREENS } from "./screens";

describe("the shell", () => {
  it("offers every screen that belongs in the menu", () => {
    renderApp();
    for (const screenInMenu of NAVIGATION) {
      expect(
        screen.getByRole("link", { name: screenInMenu.label }),
      ).toBeInTheDocument();
    }
  });

  it("says what each screen does, not only what it is called", () => {
    // The project lead, going through the app on 2026-08-17: *the names do not
    // say what they do*. ساخت، ترکیب and تحلیل are three nouns a reader who
    // has not used the app cannot tell apart.
    renderApp();
    const nav = screen.getByRole("navigation", { name: "بخش‌های اصلی" });
    for (const screenInMenu of NAVIGATION) {
      expect(nav).toHaveTextContent(screenInMenu.gloss);
    }
  });

  it("gives every screen a gloss short enough for a menu", () => {
    // A sentence here would wrap the row and push the page sideways at 320px.
    // `purpose` is the sentence; this is the short form.
    for (const screenInMenu of SCREENS) {
      expect(screenInMenu.gloss.trim()).not.toBe("");
      expect(screenInMenu.gloss.length).toBeLessThanOrEqual(30);
      expect(screenInMenu.gloss).toMatch(/[؀-ۿ]/);
    }
  });

  it("keeps the gloss out of the link's name and in its description", () => {
    // Both in the name gives one long run and no name at all; the gloss
    // dropped entirely would tell a screen reader less than the screen shows.
    renderApp();
    const link = screen.getByRole("link", { name: "ترکیب" });
    const described = link.getAttribute("aria-describedby");
    expect(described).toBeTruthy();
    expect(document.getElementById(described!)).toHaveTextContent(
      "دو واژه، یک واژهٔ تازه",
    );
  });

  it("keeps word detail out of the menu, because it is reached from a result", () => {
    renderApp();
    expect(screen.queryByRole("link", { name: "واژه" })).not.toBeInTheDocument();
  });

  it("starts a keyboard user at the skip link", async () => {
    renderApp();
    await userEvent.tab();
    expect(screen.getByRole("link", { name: "رفتن به محتوای اصلی" })).toHaveFocus();
  });

  it("marks the screen you are on", async () => {
    renderApp("/rules");
    const current = screen.getByRole("link", { name: "دستورها" });
    expect(current).toHaveAttribute("aria-current", "page");
  });

  it("names its navigation, so a screen reader can announce it", () => {
    renderApp();
    expect(screen.getByRole("navigation", { name: "بخش‌های اصلی" })).toBeInTheDocument();
  });

  it("sends an unknown address back to search rather than to a dead end", () => {
    renderApp("/nothing-here");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("جست‌وجو");
  });
});

describe("every screen", () => {
  it.each(SCREENS.map((one) => [one.label, one]))(
    "%s says what it is for",
    (_label, one) => {
      renderApp(one.path.replace(":wordId", "روش:Raveš"));
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(one.title);

      // A screen still waiting to be built says what it is for and what the
      // reader would do here. A built one shows the thing itself — the word
      // detail screen leads with the word, not with a description of itself —
      // so this follows the marker rather than a list that would go stale.
      const pending = screen.queryByText(/این صفحه هنوز ساخته نشده است/);
      if (pending) {
        expect(screen.getByText(one.purpose)).toBeInTheDocument();
        expect(screen.getByText(one.invitation)).toBeInTheDocument();
      }
    },
  );

  it("has exactly one first-level heading", () => {
    renderApp("/build");
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  it("is written in Persian only — no English reaches the reader", () => {
    for (const one of SCREENS) {
      for (const text of [one.label, one.title, one.purpose, one.invitation]) {
        expect(text).not.toMatch(/[A-Za-z]/);
      }
    }
  });
});
