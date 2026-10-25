/**
 * The two ways into the search that are not typing.
 *
 * The screen used to offer a box and four examples. That is enough for a
 * reader willing to learn a syntax and nothing at all for the writer of J1,
 * who has a German word and does not know `type:` exists — and the facet
 * panel, which teaches the syntax properly, only appears once a search has
 * already worked.
 *
 * What is tested here is the thing that makes both safe to have: **they write
 * the query, they do not replace it**. A control that rebuilt the string from
 * its own state would quietly drop whatever the reader had typed.
 */

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { renderApp } from "../../test/render";

const WORD_CLASSES = [
  { name: "karnam", label_fa: "کارنام", label_is_traditional: false },
  { name: "nam", label_fa: "نام", label_is_traditional: false },
];

const EMPTY_SEARCH = {
  query: "",
  index: "word_types",
  total: 0,
  returned: 0,
  facets: {},
  formed_with_affix: [],
  string_match_only: [],
};

/** Answers by path, because the builder asks `/rules` and the screen `/search`. */
function api({ classes = true } = {}) {
  return vi.fn().mockImplementation((url: string) => {
    const path = String(url).replace("/api", "").split("?")[0];
    const body =
      path === "/rules"
        ? classes
          ? { word_classes: WORD_CLASSES }
          : {}
        : EMPTY_SEARCH;
    return Promise.resolve({
      ok: true,
      status: 200,
      statusText: "",
      json: async () => body,
    } as Response);
  });
}

/** What is in the search box right now. */
function box() {
  return screen.getByLabelText("جست‌وجوی واژه") as HTMLInputElement;
}

/**
 * The syntax guide's panel, which the ⓘ opens.
 *
 * Scoped, because the same query string can appear in two places — the
 * builder writes `count:1` into the box while the guide lists it as a row —
 * and a bare `getByText` cannot say which was clicked.
 */
function guidePanel() {
  return document.getElementById("syntax-guide")!;
}

/**
 * Open the syntax guide.
 *
 * It was a full-width grey bar reading «راهنمای نحو» until 2026-08-18, when
 * the project lead asked for information to be an ⓘ rather than something
 * that looks like an action.
 */
async function openGuide() {
  await userEvent.click(screen.getByRole("button", { name: "راهنمای نحو" }));
}

/**
 * Reach the filters, the way a reader does.
 *
 * They are open from 2026-08-18 — the project lead asked for them visible —
 * so nothing has to be unfolded. What still happens on arrival is the one
 * request the screen makes: the word-class list is fetched when a reader
 * first reaches that control, never on load, because *the screen asks nothing
 * until there is a query* and a test says so.
 */
async function openBuilder() {
  const type = screen.queryByLabelText("گونه");
  if (type) await userEvent.click(type);
}

beforeEach(() => {
  vi.stubGlobal("fetch", api());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the builder", () => {
  it("is on the screen without being asked for", async () => {
    // It was folded behind «ساختن جست‌وجو» and a reader had to know to press
    // it. The project lead asked for the filters visible on 2026-08-18.
    renderApp("/");
    expect(screen.getByLabelText("جور الگو")).toBeVisible();
    expect(screen.getByLabelText("کجا پیدا شده")).toBeVisible();
    expect(screen.getByLabelText("جور بسامد")).toBeVisible();
    // And the box is still the one clear action beside them.
    expect(screen.getByRole("button", { name: "جست‌وجو" })).toBeVisible();
  });

  it("still asks the API nothing until a reader reaches the one control that needs it", () => {
    // The rule the folded panel was protecting, kept without the fold: the
    // word classes are the only thing here that needs the API, and they are
    // fetched when that select is reached rather than when the screen loads.
    renderApp("/");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("writes a word class into the box as the syntax for it", async () => {
    renderApp("/");
    await openBuilder();
    const type = await screen.findByLabelText("گونه");
    await userEvent.selectOptions(type, "karnam");
    expect(box()).toHaveValue("type:karnam");
  });

  it("labels the classes from the rule pack, never from the component", async () => {
    renderApp("/");
    await openBuilder();
    const type = await screen.findByLabelText("گونه");
    expect(within(type).getByRole("option", { name: "کارنام" })).toBeInTheDocument();
  });

  it("replaces a choice instead of asking for both", async () => {
    renderApp("/");
    await openBuilder();
    const type = await screen.findByLabelText("گونه");
    await userEvent.selectOptions(type, "karnam");
    await userEvent.selectOptions(type, "nam");
    expect(box()).toHaveValue("type:nam");
  });

  it("takes the term away again when the reader clears the control", async () => {
    renderApp("/");
    await openBuilder();
    const type = await screen.findByLabelText("گونه");
    await userEvent.selectOptions(type, "karnam");
    await userEvent.selectOptions(type, "");
    expect(box()).toHaveValue("");
  });

  it("writes a pattern in the shape that was chosen", async () => {
    renderApp("/");
    await openBuilder();
    await userEvent.type(screen.getByLabelText("الگوی حرفی"), "nā");
    expect(box()).toHaveValue("*nā");

    await userEvent.selectOptions(screen.getByLabelText("جور الگو"), "starts");
    expect(box()).toHaveValue("nā*");
  });

  it("keeps a term it has no control for", async () => {
    // The reason it edits the query rather than composing one: `tag:ja` is a
    // real search and the builder has no control for it.
    renderApp("/?q=tag%3Aja");
    await openBuilder();
    await waitFor(() => expect(box()).toHaveValue("tag:ja"));
    await userEvent.selectOptions(await screen.findByLabelText("گونه"), "karnam");
    expect(box()).toHaveValue("tag:ja type:karnam");
  });

  it("shows the query it has written, which is how the syntax is learnt", async () => {
    renderApp("/");
    await openBuilder();
    await userEvent.selectOptions(await screen.findByLabelText("کجا پیدا شده"), "corpus");
    expect(screen.getByText("in:corpus")).toBeVisible();
  });

  it("does not run the search on every keystroke", async () => {
    renderApp("/");
    await openBuilder();
    await userEvent.type(screen.getByLabelText("الگوی حرفی"), "nā");
    const searches = vi
      .mocked(fetch)
      .mock.calls.filter((call) => String(call[0]).includes("/search"));
    expect(searches).toHaveLength(0);
  });

  it("runs what it built when the reader asks for it", async () => {
    renderApp("/");
    await openBuilder();
    await userEvent.selectOptions(await screen.findByLabelText("کجا پیدا شده"), "corpus");
    await userEvent.click(screen.getByRole("button", { name: "جست‌وجو" }));
    await waitFor(() => {
      const last = vi.mocked(fetch).mock.calls.at(-1);
      expect(String(last?.[0])).toContain("in%3Acorpus");
    });
  });

  it("loses one control rather than the screen when the API is a version behind", async () => {
    // The build screen was taken down once by exactly this — a field the
    // running container did not serve yet. See api/generate.ts.
    vi.stubGlobal("fetch", api({ classes: false }));
    renderApp("/");
    await openBuilder();
    expect(await screen.findByLabelText("کجا پیدا شده")).toBeVisible();
    // It is on the screen until the list is asked for; once the answer comes
    // back empty it takes itself away rather than standing there useless.
    await waitFor(() =>
      expect(screen.queryByLabelText("گونه")).not.toBeInTheDocument(),
    );
  });
});

describe("the syntax reference", () => {
  it("names the operators the interface never showed", async () => {
    renderApp("/");
    await openGuide();
    const reference = within(guidePanel());
    for (const query of ["stem1:goft", "tag:ja", "rule:V-010", "century:10-13"]) {
      expect(reference.getByText(query)).toBeVisible();
    }
  });

  it("runs a row when it is clicked", async () => {
    renderApp("/");
    await openGuide();
    await userEvent.click(within(guidePanel()).getByText("count:1"));
    await waitFor(() => {
      const last = vi.mocked(fetch).mock.calls.at(-1);
      expect(String(last?.[0])).toContain("count%3A1");
    });
    expect(box()).toHaveValue("count:1");
  });
});
