/**
 * The *busy* state of the two screens that run a request on demand.
 *
 * Both cancel the request in flight when the question changes, and a cancelled
 * request settles like any other. It used to take the screen's *busy* state
 * with it, although the request that replaced it had only just started: the
 * button read as ready, and the waiting line never showed.
 *
 * Strict mode is the shortest way to that state — it runs each effect twice,
 * so the first request is cancelled on the spot and the second stays out —
 * and it is also exactly how the fault showed in development.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StrictMode } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";

/** A request that never answers, and fails the way the browser does when it is cancelled. */
function neverAnswering() {
  return vi.fn(
    (_url: string, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => {
          reject(new DOMException("The operation was aborted.", "AbortError"));
        });
      }),
  );
}

function renderStrict(route: string) {
  return render(
    <StrictMode>
      <MemoryRouter initialEntries={[route]}>
        <App />
      </MemoryRouter>
    </StrictMode>,
  );
}

beforeEach(() => {
  vi.stubGlobal("fetch", neverAnswering());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("building a word", () => {
  const route = `/build?word=${encodeURIComponent("رفتن")}`;

  it("stays busy while the request that replaced a cancelled one is still out", async () => {
    renderStrict(route);
    const button = await screen.findByRole("button", { name: "در حال ساخت" });
    expect(button).toBeDisabled();
  });

  it("is ready again when the word is taken away mid-request", async () => {
    renderStrict(route);
    await screen.findByRole("button", { name: "در حال ساخت" });

    // The menu's own link to this screen clears the word from the address.
    await userEvent.click(screen.getByRole("link", { name: "ساخت" }));

    const button = await screen.findByRole("button", { name: "بساز" });
    expect(button).toBeEnabled();
  });
});

describe("searching", () => {
  const route = `/?q=${encodeURIComponent("*نا")}`;

  it("stays busy while the request that replaced a cancelled one is still out", async () => {
    renderStrict(route);
    const button = await screen.findByRole("button", { name: "در حال جست‌وجو" });
    expect(button).toBeDisabled();
  });

  it("is ready again when the query is taken away mid-request", async () => {
    renderStrict(route);
    await screen.findByRole("button", { name: "در حال جست‌وجو" });

    await userEvent.click(screen.getByRole("link", { name: "جست‌وجو" }));

    const button = await screen.findByRole("button", { name: "جست‌وجو" });
    expect(button).toBeEnabled();
  });
});
