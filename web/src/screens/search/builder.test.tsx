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

import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { useNavigate } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { renderApp, renderWithRouter } from "../../test/render";

const WORD_CLASSES = [
  {
    name: "karnam",
    label_fa: "کارنام",
    label_is_traditional: false,
    traditional_fa: "اسم مصدر",
  },
  { name: "nam", label_fa: "نام", label_is_traditional: false, traditional_fa: "اسم" },
  {
    name: "nedayi",
    label_fa: "ندایی",
    label_is_traditional: true,
    traditional_fa: "ندایی",
  },
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
        : path === "/corpus/centuries"
          ? { first: 4, last: 14 }
          : EMPTY_SEARCH;
    return Promise.resolve({
      ok: true,
      status: 200,
      statusText: "",
      json: async () => body,
    } as Response);
  });
}

/** The browser's Back, as a button that leaves the focus where it is. */
function Back() {
  const go = useNavigate();
  return (
    <button type="button" onClick={() => go(-1)}>
      back
    </button>
  );
}

/** What is in the search box right now. */
function box() {
  return screen.getByLabelText("جست‌وجوی واژه") as HTMLInputElement;
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
    expect(screen.getByLabelText("این واژه از کجاست")).toBeVisible();
    expect(screen.getByLabelText("جور بسامد")).toBeVisible();
    // And the box is still the one clear action beside them.
    expect(screen.getByRole("button", { name: "جست‌وجو" })).toBeVisible();
  });

  it("asks for the word classes only when a reader reaches that control", () => {
    // The rule the folded panel was protecting, kept without the fold: the
    // word classes are fetched when that select is reached rather than when
    // the screen loads. The one thing asked on arrival is the corpus's range
    // of centuries, which fills the century fields (2026-11-20).
    renderApp("/");
    const asked = vi.mocked(fetch).mock.calls.map((call) => String(call[0]));
    expect(asked).toEqual(["/api/corpus/centuries"]);
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
    // The linguist's term, and the traditional one in brackets beside it —
    // asked for by the project lead on 2026-11-20.
    expect(
      await within(type).findByRole("option", { name: "کارنام (اسم مصدر)" }),
    ).toBeInTheDocument();
    // Never twice where the label already is the traditional term.
    expect(within(type).getByRole("option", { name: "ندایی" })).toBeInTheDocument();
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

  it("shows what it wrote in the box itself, and nowhere else", async () => {
    // A line under the filters repeated the query after «می‌نویسد:». The box
    // above already shows it, and the project lead asked on 2026-11-20 what
    // the line meant; it went.
    renderApp("/");
    await openBuilder();
    await userEvent.selectOptions(await screen.findByLabelText("این واژه از کجاست"), "corpus");
    expect(box()).toHaveValue("in:corpus");
    expect(screen.queryByText("in:corpus")).not.toBeInTheDocument();
    expect(screen.queryByText("می‌نویسد:")).not.toBeInTheDocument();
  });

  it("says where a word comes from in a sentence a reader can answer", async () => {
    renderApp("/");
    const origin = screen.getByLabelText("این واژه از کجاست");
    for (const name of ["در متن‌ها آمده", "در واژه‌نامه هست", "ساختهٔ دستور، هنوز دیده نشده"]) {
      expect(within(origin).getByRole("option", { name })).toBeInTheDocument();
    }
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
    await userEvent.selectOptions(await screen.findByLabelText("این واژه از کجاست"), "corpus");
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
    expect(await screen.findByLabelText("این واژه از کجاست")).toBeVisible();
    // It is on the screen until the list is asked for; once the answer comes
    // back empty it takes itself away rather than standing there useless.
    await waitFor(() =>
      expect(screen.queryByLabelText("گونه")).not.toBeInTheDocument(),
    );
  });
});

describe("the number fields", () => {
  /** A field by its label, as an input. */
  function field(name: string) {
    return screen.getByLabelText(name) as HTMLInputElement;
  }

  it("open filled, in Persian digits and right to left, without writing anything", async () => {
    // The project lead, 2026-11-20: the digits were Latin, the fields empty
    // and left to right. Filled with what the search covers when nothing is
    // asked, so the reader only moves them.
    renderApp("/");
    await waitFor(() => expect(field("سده از")).toHaveValue("۴"));
    expect(field("سده تا")).toHaveValue("۱۴");
    expect(field("بسامد در پیکره")).toHaveValue("۰");
    expect(screen.getByLabelText("جور بسامد")).toHaveValue("gt");
    for (const name of ["سده از", "سده تا", "بسامد در پیکره"]) {
      expect(field(name)).toHaveAttribute("dir", "rtl");
    }
    // Shown is not written: a search that asks nothing of them stays open
    // to words with no count and no century.
    expect(box()).toHaveValue("");
  });

  it("writes a century range once the reader moves one end, from the corpus's own range", async () => {
    renderApp("/");
    await waitFor(() => expect(field("سده از")).toHaveValue("۴"));
    await userEvent.clear(field("سده از"));
    await userEvent.type(field("سده از"), "۱۰");
    expect(box()).toHaveValue("century:10-14");
    expect(field("سده از")).toHaveValue("۱۰");
  });

  it("takes the century away again when the range is the whole corpus", async () => {
    renderApp("/?q=century%3A10-14");
    await waitFor(() => expect(field("سده از")).toHaveValue("۱۰"));
    await userEvent.clear(field("سده از"));
    await userEvent.type(field("سده از"), "4");
    expect(box()).toHaveValue("");
  });

  it("never writes a range that runs backwards while it is being retyped", async () => {
    renderApp("/?q=century%3A4-12");
    await waitFor(() => expect(field("سده تا")).toHaveValue("۱۲"));
    await userEvent.clear(field("سده تا"));
    await userEvent.type(field("سده تا"), "1");
    // «۴ تا ۱» is not a query; the box keeps the last one that was.
    expect(field("سده تا")).toHaveValue("۱");
    expect(box()).not.toHaveValue("century:4-1");
    await userEvent.type(field("سده تا"), "3");
    expect(box()).toHaveValue("century:4-13");
  });

  it("writes a frequency from either keyboard's digits, and shows them in Persian", async () => {
    renderApp("/");
    await userEvent.clear(field("بسامد در پیکره"));
    await userEvent.type(field("بسامد در پیکره"), "10");
    expect(box()).toHaveValue("count:>10");
    expect(field("بسامد در پیکره")).toHaveValue("۱۰");
  });

  it("keeps the caret where the reader typed, so a digit in the middle stays there", async () => {
    renderApp("/?q=count%3A%3E123");
    await waitFor(() => expect(field("بسامد در پیکره")).toHaveValue("۱۲۳"));
    await userEvent.type(field("بسامد در پیکره"), "45", {
      initialSelectionStart: 1,
      initialSelectionEnd: 1,
    });
    expect(field("بسامد در پیکره")).toHaveValue("۱۴۵۲۳");
    expect(box()).toHaveValue("count:>14523");
  });

  it("keeps an exact frequency exact while its figure is retyped", async () => {
    renderApp("/?q=count%3A10");
    await waitFor(() => expect(field("بسامد در پیکره")).toHaveValue("۱۰"));
    await userEvent.clear(field("بسامد در پیکره"));
    await userEvent.type(field("بسامد در پیکره"), "20");
    expect(box()).toHaveValue("count:20");
    expect(screen.getByLabelText("جور بسامد")).toHaveValue("eq");
  });

  it("drops the frequency when the field is left empty", async () => {
    renderApp("/?q=count%3A10");
    await waitFor(() => expect(field("بسامد در پیکره")).toHaveValue("۱۰"));
    await userEvent.clear(field("بسامد در پیکره"));
    // What is submitted is what the field shows: no frequency.
    expect(box()).toHaveValue("");
    await userEvent.tab();
    expect(field("بسامد در پیکره")).toHaveValue("۰");
    expect(screen.getByLabelText("جور بسامد")).toHaveValue("gt");
  });

  it("lets the century filter go when there is no corpus range and an end is emptied", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          statusText: "",
          json: async () => ({ first: null, last: null, ...EMPTY_SEARCH }),
        } as Response),
      ),
    );
    renderApp("/?q=century%3A10-13");
    await waitFor(() => expect(field("سده از")).toHaveValue("۱۰"));
    await userEvent.clear(field("سده از"));
    expect(box()).toHaveValue("");
  });

  it("keeps the lower end when the upper is retyped after a search from its field", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          statusText: "",
          json: async () => ({ first: null, last: null, ...EMPTY_SEARCH }),
        } as Response),
      ),
    );
    renderApp("/?q=century%3A10-13");
    await waitFor(() => expect(field("سده تا")).toHaveValue("۱۳"));
    await userEvent.clear(field("سده تا"));
    await userEvent.type(field("سده تا"), "14{Enter}");
    await waitFor(() =>
      expect(
        vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("century%3A10-14")),
      ).toBe(true),
    );
    await userEvent.clear(field("سده تا"));
    await userEvent.type(field("سده تا"), "15");
    expect(box()).toHaveValue("century:10-15");
  });

  it("lets go of a held end when the filter is taken away", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          statusText: "",
          json: async () => ({ first: null, last: null, ...EMPTY_SEARCH }),
        } as Response),
      ),
    );
    renderApp("/?q=century%3A10-13");
    await waitFor(() => expect(field("سده تا")).toHaveValue("۱۳"));
    await userEvent.clear(field("سده تا"));
    await userEvent.type(field("سده تا"), "1");
    await userEvent.clear(field("سده تا"));
    await userEvent.tab();
    expect(box()).toHaveValue("");
    expect(field("سده تا")).toHaveValue("");
    expect(field("سده تا")).not.toHaveAttribute("aria-invalid");
  });

  it("shows the search's figure when the search changes under a focused field", async () => {
    // Submitted from the field, then the Back button: the field must follow
    // the search it is showing, not keep the figure typed into it.
    renderWithRouter(
      <>
        <App />
        <Back />
      </>,
      "/?q=count%3A10",
    );
    await waitFor(() => expect(field("بسامد در پیکره")).toHaveValue("۱۰"));
    await userEvent.clear(field("بسامد در پیکره"));
    await userEvent.type(field("بسامد در پیکره"), "20{Enter}");
    await waitFor(() =>
      expect(
        vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("count%3A20")),
      ).toBe(true),
    );
    expect(field("بسامد در پیکره")).toHaveFocus();
    // A click that leaves the focus where it is, as the browser's Back does.
    fireEvent.click(screen.getByRole("button", { name: "back" }));
    await waitFor(() => expect(box()).toHaveValue("count:10"));
    expect(field("بسامد در پیکره")).toHaveValue("۱۰");
  });

  it("holds an end that runs the range backwards until the other end is moved", async () => {
    // «۱۰ تا ۱۳» to «۴ تا ۹», upper end first: the «۹» is no range yet.
    renderApp("/?q=century%3A10-13");
    await waitFor(() => expect(field("سده از")).toHaveValue("۱۰"));
    await userEvent.clear(field("سده تا"));
    await userEvent.type(field("سده تا"), "9");
    // Emptied, the end stood for the corpus's last century; «۱۰ تا ۹» is
    // not written.
    expect(box()).toHaveValue("century:10-14");
    await userEvent.tab();
    expect(field("سده تا")).toHaveValue("۹");
    expect(field("سده تا")).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText("سدهٔ آغاز از سدهٔ پایان بزرگ‌تر است.")).toBeVisible();
    // The form will not run a search while the range on screen is no search.
    expect((field("سده تا") as HTMLInputElement).validity.valid).toBe(false);
    expect(field("سده تا").closest("form")!.checkValidity()).toBe(false);
    await userEvent.clear(field("سده از"));
    await userEvent.type(field("سده از"), "4");
    expect(box()).toHaveValue("century:4-9");
    expect(field("سده تا")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByText("سدهٔ آغاز از سدهٔ پایان بزرگ‌تر است.")).toBeNull();
  });

  it("holds both ends while the range still runs backwards", async () => {
    renderApp("/?q=century%3A11-13");
    await waitFor(() => expect(field("سده از")).toHaveValue("۱۱"));
    await userEvent.clear(field("سده از"));
    await userEvent.type(field("سده از"), "18");
    await userEvent.clear(field("سده تا"));
    await userEvent.type(field("سده تا"), "17");
    expect(field("سده از")).toHaveValue("۱۸");
    await userEvent.clear(field("سده تا"));
    await userEvent.type(field("سده تا"), "19");
    expect(box()).toHaveValue("century:18-19");
  });

  it("forgets a held comparison when the Back button changes the search", async () => {
    renderWithRouter(
      <>
        <App />
        <Back />
      </>,
      "/?q=bar*",
    );
    await userEvent.clear(box());
    await userEvent.type(box(), "count:10{Enter}");
    await waitFor(() => expect(field("بسامد در پیکره")).toHaveValue("۱۰"));
    await userEvent.clear(field("بسامد در پیکره"));
    fireEvent.click(screen.getByRole("button", { name: "back" }));
    await waitFor(() => expect(box()).toHaveValue("bar*"));
    expect(screen.getByLabelText("جور بسامد")).toHaveValue("gt");
    await userEvent.type(field("بسامد در پیکره"), "5");
    expect(box()).toHaveValue("bar* count:>5");
  });

  it("keeps the untouched end of a century range after the Back button", async () => {
    renderWithRouter(
      <>
        <App />
        <Back />
      </>,
      "/",
    );
    await waitFor(() => expect(field("سده تا")).toHaveValue("۱۴"));
    await userEvent.click(field("سده از"));
    await userEvent.clear(field("سده از"));
    await userEvent.type(field("سده از"), "10");
    await userEvent.clear(field("سده تا"));
    await userEvent.type(field("سده تا"), "13{Enter}");
    await waitFor(() => expect(box()).toHaveValue("century:10-13"));
    fireEvent.click(screen.getByRole("button", { name: "back" }));
    await waitFor(() => expect(field("سده از")).toHaveValue("۴"));
    // Only the upper end is moved: the lower stays the corpus's own.
    await userEvent.clear(field("سده تا"));
    await userEvent.type(field("سده تا"), "12");
    expect(box()).toHaveValue("century:4-12");
  });

  it("reads a range written in Persian digits, and edits it", async () => {
    renderApp("/?q=century%3A%DB%B1%DB%B0-%DB%B1%DB%B3");
    await waitFor(() => expect(field("سده از")).toHaveValue("۱۰"));
    expect(field("سده تا")).toHaveValue("۱۳");
    await userEvent.clear(field("سده از"));
    await userEvent.type(field("سده از"), "11");
    expect(box()).toHaveValue("century:11-13");
  });

  it("takes a two-digit century when there is no corpus range to fill from", async () => {
    // An API without the route, or one that is down: the fields open empty.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) =>
        Promise.resolve({
          ok: !String(url).includes("/corpus/centuries"),
          status: String(url).includes("/corpus/centuries") ? 404 : 200,
          statusText: "",
          json: async () => EMPTY_SEARCH,
        } as Response),
      ),
    );
    renderApp("/");
    expect(field("سده از")).toHaveValue("");
    await userEvent.type(field("سده از"), "10");
    expect(box()).toHaveValue("century:10");
    // One century is a range of one: the other end shows it too.
    expect(field("سده تا")).toHaveValue("۱۰");
    await userEvent.clear(field("سده تا"));
    await userEvent.type(field("سده تا"), "13");
    expect(box()).toHaveValue("century:10-13");
  });

  it("leaves the frequency out of the query while it says «بیش از ۰»", async () => {
    renderApp("/?q=count%3A%3E5");
    await waitFor(() => expect(field("بسامد در پیکره")).toHaveValue("۵"));
    await userEvent.clear(field("بسامد در پیکره"));
    await userEvent.type(field("بسامد در پیکره"), "۰");
    expect(box()).toHaveValue("");
  });
});
