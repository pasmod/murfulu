/**
 * The feedback affordance.
 *
 * What is tested is what docs/REVIEW.md insists on and what the store under it
 * enforces, so the interface cannot quietly disagree with either:
 *
 * - it is on **every** screen, not on a screen of its own
 * - the category is chosen first and the form adapts
 * - a linguistic verdict is offered only to an expert, and asked for **before**
 *   a note is written rather than refused after it
 * - the record names no author, and carries the context the screen was showing
 * - nothing edits or withdraws a record, because nothing can
 */

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { renderApp } from "../test/render";

const EXPERT = { username: "murfulu", may_leave_a_verdict: true };
// The API says `true` for everyone since 2026-08-17 — one account, no roles.
// This stands for an API that says otherwise, which is why the flag was kept
// rather than removed: the screen must still honour a `no` if one ever comes.
const REFUSED = { username: "murfulu", may_leave_a_verdict: false };

/** One rule, so a row exists to be judged on its own. */
const RULES = {
  rule_pack_version: "1",
  count: 1,
  corpus_version: "v1",
  measured_rules: 1,
  word_classes: [],
  rules: [
    {
      id: "V-010",
      family: "V",
      kind: "suffix",
      affix: "-ār",
      affix_fa: "ار",
      input_types: ["karbon1"],
      output_types: ["karnam"],
      semantic_tags: [],
      strength: "typical",
      examples: [],
      label_fa: null,
      explanation_fa: null,
      active: true,
      needs_expert_check: false,
      productivity: null,
    },
  ],
};

/** Open the panel on one rule rather than on the page listing them. */
async function judgeTheRule() {
  await userEvent.click(
    await screen.findByRole("button", { name: /داوری دربارهٔ دستور V-010/ }),
  );
  return screen.findByRole("dialog");
}

/** One fetch stub answering by path, so a screen and the widget can share it. */
function apiReturning(answers: Record<string, unknown>) {
  return vi.fn().mockImplementation((url: string, init?: RequestInit) => {
    const path = String(url).replace("/api", "").split("?")[0]!;
    const key = `${init?.method ?? "GET"} ${path}`;
    const body = answers[key] ?? answers[path] ?? {};
    const status = body === "401" ? 401 : body === "403" ? 403 : 200;
    return Promise.resolve({
      ok: status === 200,
      status,
      statusText: "",
      json: async () => (status === 200 ? body : { detail: "no" }),
    } as Response);
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the feedback button", () => {
  it("is on every screen, because retrofitting it means touching everything", async () => {
    vi.stubGlobal("fetch", apiReturning({}));
    for (const route of ["/", "/build", "/affixes", "/explain", "/rules", "/corpus"]) {
      const { unmount } = renderApp(route);
      expect(
        await screen.findByRole("button", { name: "بازخورد" }),
      ).toBeInTheDocument();
      unmount();
    }
  });
});

describe("when the caller may grade a word", () => {

  it("chooses the category first and the form adapts", async () => {
    vi.stubGlobal("fetch", apiReturning({ "/me": EXPERT, "/rules": RULES }));
    renderApp("/rules");
    const panel = await judgeTheRule();
    // A graded verdict does not fit "this button does nothing", so it is not
    // on screen until the category asks for it.
    expect(within(panel).queryByText("نیاز به گفت‌وگو")).toBeNull();
    await userEvent.click(within(panel).getByRole("button", { name: /داوری زبانی/ }));
    expect(within(panel).getByText("نیاز به گفت‌وگو")).toBeInTheDocument();

    // And it goes away again for a category that cannot carry one.
    await userEvent.click(within(panel).getByRole("button", { name: /ایراد برنامه/ }));
    expect(within(panel).queryByText("نیاز به گفت‌وگو")).toBeNull();
  });

  it("sends the verdict with the context and no author", async () => {
    const api = apiReturning({
      "/me": EXPERT,
      "/rules": RULES,
      "POST /feedback": { id: 1 },
    });
    vi.stubGlobal("fetch", api);
    renderApp("/rules");
    const panel = await judgeTheRule();
    await userEvent.click(within(panel).getByRole("button", { name: /داوری زبانی/ }));
    await userEvent.click(
      within(panel).getByRole("button", { name: "این دستور نباید اینجا اجرا می‌شد" }),
    );
    await userEvent.type(within(panel).getByLabelText(/یادداشت/), "این واژه نیست");
    await userEvent.click(within(panel).getByRole("button", { name: "ثبت" }));

    await waitFor(() => {
      expect(
        api.mock.calls.some((call: unknown[]) => String(call[0]).includes("/feedback")),
      ).toBe(true);
    });
    const sent = api.mock.calls.find((call: unknown[]) =>
      String(call[0]).includes("/feedback"),
    )!;
    const body = JSON.parse((sent[1] as RequestInit).body as string);
    expect(body.category).toBe("linguistic");
    expect(body.verdict).toBe("wrong");
    expect(body.note).toBe("این واژه نیست");
    // The route where it was said, captured without the screen supplying it.
    expect(body.context.screen).toBe("/rules");
    // And the rule it was said about, not the page listing them.
    expect(body.target_type).toBe("rule");
    expect(body.target_id).toBe("V-010");
    // No author field: the API decides the author and refuses to read one
    // from the body. A record naming the wrong author is worse than none.
    expect(body).not.toHaveProperty("author");
    expect(body).not.toHaveProperty("author_id");
    // And no credential either, since 2026-08-17 — the site password in front
    // of the whole app is the whole of the authentication.
    expect((sent[1] as RequestInit).headers).not.toHaveProperty("authorization");
  });

  it("says the record cannot be taken back", async () => {
    vi.stubGlobal("fetch", apiReturning({ "/me": EXPERT, "/rules": RULES }));
    renderApp("/rules");
    const panel = await judgeTheRule();
    expect(within(panel).getByText(/پس نمی‌گردد و ویرایش نمی‌شود/)).toBeInTheDocument();
  });
});

describe("when the API says the caller may not grade a word", () => {
  // Unreachable through the real API today, and pinned anyway: the flag is the
  // one place the sentence *who may grade a word* lives, and this project has
  // already reversed a decision about roles once.

  it("offers no linguistic verdict, and says why", async () => {
    vi.stubGlobal("fetch", apiReturning({ "/me": REFUSED, "/rules": RULES }));
    renderApp("/rules");
    const panel = await judgeTheRule();
    const graded = within(panel).getByRole("button", { name: /داوری زبانی/ });
    expect(graded).toBeDisabled();
    expect(within(panel).getByText("تنها برای حساب کارشناس")).toBeInTheDocument();
  });

  it("still lets a bug be reported", async () => {
    const api = apiReturning({
      "/me": REFUSED,
      "/rules": RULES,
      "POST /feedback": { id: 2 },
    });
    vi.stubGlobal("fetch", api);
    renderApp("/rules");
    const panel = await judgeTheRule();
    await userEvent.click(within(panel).getByRole("button", { name: /ایراد برنامه/ }));
    await userEvent.type(within(panel).getByLabelText(/یادداشت/), "دکمه کار نمی‌کند");
    await userEvent.click(within(panel).getByRole("button", { name: "ثبت" }));

    await waitFor(() => {
      const sent = api.mock.calls.find((call: unknown[]) =>
        String(call[0]).includes("/feedback"),
      );
      expect(sent).toBeTruthy();
      const body = JSON.parse((sent![1] as RequestInit).body as string);
      expect(body.category).toBe("bug");
      expect(body.verdict).toBeNull();
    });
  });
});

describe("about the app itself", () => {
  it("offers no linguistic verdict, whoever is asking", async () => {
    // Found by running it: the corner button on a screen that declares no
    // subject is about the app, and *is this app good, possible or wrong* is
    // not a question. docs/REVIEW.md maps the app to a bug report.
    vi.stubGlobal("fetch", apiReturning({ "/me": EXPERT }));
    renderApp("/rules");
    await userEvent.click(screen.getByRole("button", { name: "بازخورد" }));

    const panel = await screen.findByRole("dialog");
    expect(within(panel).getByRole("button", { name: /داوری زبانی/ })).toBeDisabled();
    expect(
      within(panel).getByText("داوری زبانی دربارهٔ خودِ برنامه معنا ندارد"),
    ).toBeInTheDocument();
  });
});
