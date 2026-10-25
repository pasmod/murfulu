/**
 * The two things a Persian interface gets wrong most often: mixed direction,
 * and numerals.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { Latin } from "./Latin";
import { Num } from "./Num";
import { Term } from "./Term";
import { persianCentury, persianCenturyRange, persianNumber } from "./numbers";

describe("a Latin form inside Persian text", () => {
  it("declares its own direction", () => {
    render(<Latin>Raveš</Latin>);
    expect(screen.getByText("Raveš")).toHaveAttribute("dir", "ltr");
  });

  it("is marked as Persian written in Latin, not as English", () => {
    render(<Latin>Raveš</Latin>);
    expect(screen.getByText("Raveš")).toHaveAttribute("lang", "fa-Latn");
  });

  it("keeps its capital letters", () => {
    // Porsidan the noun and porsidan the verb differ by nothing else.
    render(
      <>
        <Latin>Porsidan</Latin>
        <Latin>porsidan</Latin>
      </>,
    );
    expect(screen.getByText("Porsidan")).toBeInTheDocument();
    expect(screen.getByText("porsidan")).toBeInTheDocument();
  });

  it("keeps an affix and its dash together", () => {
    render(<Latin affix>-ār</Latin>);
    expect(screen.getByText("-ār")).toHaveAttribute("dir", "ltr");
  });
});

describe("numbers", () => {
  it("are written in Persian numerals", () => {
    expect(persianNumber(4)).toBe("۴");
  });

  it("keep Persian grouping past a thousand", () => {
    const written = persianNumber(1738711);
    expect(written).not.toMatch(/[0-9]/);
    expect(written).toContain("۱");
  });

  it("carry their Latin value in the DOM, so a count stays checkable", () => {
    render(<Num value={4813} />);
    expect(screen.getByText("۴٬۸۱۳")).toHaveAttribute("data-value", "4813");
  });

  it("write one century as a century and two as a range", () => {
    expect(persianCentury(5)).toBe("سدهٔ ۵");
    expect(persianCenturyRange(5, 5)).toBe("سدهٔ ۵");
    expect(persianCenturyRange(5, 12)).toBe("سدهٔ ۵ تا ۱۲");
  });
});

describe("a grammar term", () => {
  const term = {
    term: "کارنام",
    explanation: "خودِ کار، که همچون نام به کار می‌رود",
    traditional: "اسم مصدر",
  };

  it("shows nothing until it is asked", () => {
    render(<Term {...term} />);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("explains itself on focus, so it is reachable by keyboard", async () => {
    render(<Term {...term} />);
    await userEvent.tab();
    expect(screen.getByRole("tooltip")).toHaveTextContent(term.explanation);
  });

  it("names the traditional term as well", async () => {
    render(<Term {...term} />);
    await userEvent.tab();
    expect(screen.getByRole("tooltip")).toHaveTextContent("اسم مصدر");
  });

  it("is dismissed with Escape", async () => {
    render(<Term {...term} />);
    await userEvent.tab();
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("is described by its tooltip while the tooltip is open", async () => {
    render(<Term {...term} />);
    const button = screen.getByRole("button", { name: "کارنام" });
    expect(button).not.toHaveAttribute("aria-describedby");
    await userEvent.tab();
    expect(button).toHaveAttribute("aria-describedby");
  });

  it("explains itself on a press, which is all a phone can do", async () => {
    // It did not, from the day it was written until 2026-08-17: a press is
    // enter, then focus, then click, and the click toggled shut what the first
    // two had opened. A phone has no hover to fall back on, so tapping the one
    // component whose whole job is explaining the grammar explained nothing.
    render(<Term {...term} />);
    await userEvent.click(screen.getByRole("button", { name: "کارنام" }));
    expect(screen.getByRole("tooltip")).toHaveTextContent(term.explanation);
  });
});
