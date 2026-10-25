/**
 * The ⓘ.
 *
 * What is checked here is that it is reachable by everyone, because a tooltip
 * only a mouse can open is a label that only some readers get. The rules are
 * Term's — WCAG 1.4.13 — and this is the second component to follow them, so
 * they are asserted rather than assumed.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { Info } from "./Info";

function anInfo() {
  return render(
    <Info label="واژه‌گونه">واژه‌ها آن‌گونه که خوانده می‌شوند.</Info>,
  );
}

describe("the info mark", () => {
  it("says nothing until it is asked", () => {
    anInfo();
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("is a button, so a keyboard reaches it", async () => {
    anInfo();
    await userEvent.tab();
    expect(screen.getByRole("button")).toHaveFocus();
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
  });

  it("names what it explains, because the mark itself is only a glyph", () => {
    anInfo();
    expect(
      screen.getByRole("button", { name: "واژه‌گونه چیست؟" }),
    ).toBeInTheDocument();
  });

  it("opens on a click, for a reader with neither hover nor a keyboard", async () => {
    anInfo();
    await userEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("tooltip")).toHaveTextContent(
      "واژه‌ها آن‌گونه که خوانده می‌شوند.",
    );
  });

  it("ties the explanation to the control that opened it", async () => {
    anInfo();
    await userEvent.click(screen.getByRole("button"));
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-describedby", screen.getByRole("tooltip").id);
    expect(button).toHaveAttribute("aria-expanded", "true");
  });

  it("closes when the reader moves on, which is how a tap elsewhere dismisses it", async () => {
    // The click handler only ever opens, so this is the dismissal a phone has.
    render(
      <>
        <Info label="واژه‌گونه">واژه‌ها آن‌گونه که خوانده می‌شوند.</Info>
        <button type="button">جای دیگر</button>
      </>,
    );
    await userEvent.click(screen.getByRole("button", { name: /واژه‌گونه/ }));
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "جای دیگر" }));
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("closes on Escape rather than trapping the reader under it", async () => {
    anInfo();
    await userEvent.click(screen.getByRole("button"));
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});
