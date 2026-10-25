/**
 * The questions screen.
 *
 * What matters here is not that the questions appear. It is that **a reader is
 * told they cannot answer before they write one**, that the question is shown
 * in Persian and in no other version, and that the evidence is downloadable —
 * because a question about the grammar document cannot be answered until that
 * document is in front of the reader, and sending him to a shared drive to find
 * it is the thing this screen replaces.
 */

import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Question, Questions as QuestionList } from "../../api/questions";
import { renderApp } from "../../test/render";

function question(over: Partial<Question> = {}): Question {
  return {
    reference: "L13",
    question_fa: "آیا میان دو همخوان مصوت e می‌آید؟ همخوان یعنی حرفی که صدادار نیست.",
    question_latin: null,
    question_en: null,
    files: [],
    context: { from_document: "šāhvār against šāhevār, and twenty more." },
    state: "open",
    blocks_work: false,
    origin: "document",
    asked_at: null,
    ruling: null,
    rulings: 0,
    ...over,
  };
}

function answer(over: Partial<QuestionList> = {}): QuestionList {
  return {
    count: 1,
    answering_as: "expert-1",
    questions: [question()],
    ...over,
  };
}

describe("the questions screen", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function serve(body: QuestionList) {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(body), { status: 200 })),
    );
  }

  it("shows the Persian as the question, and it is the only version", async () => {
    serve(answer());
    renderApp("/questions");
    expect(
      await screen.findByText(/همخوان یعنی حرفی که صدادار نیست/),
    ).toBeInTheDocument();
  });

  it("sets a question as the paragraphs it was written in", async () => {
    // The text is context, then measurement, then what we did, then the
    // question. Poured into one <p> it is a wall, and the one person who has
    // to answer it would not read to the end.
    serve(
      answer({
        questions: [
          question({
            question_fa: "بند نخست، زمینه.\n\nبند دوم، اندازه‌گیری.\n\nبند سوم، پرسش.",
          }),
        ],
      }),
    );
    renderApp("/questions");
    expect(await screen.findByText("بند نخست، زمینه.")).toBeInTheDocument();
    expect(screen.getByText("بند دوم، اندازه‌گیری.")).toBeInTheDocument();
    expect(screen.getByText("بند سوم، پرسش.")).toBeInTheDocument();
  });

  it("offers the evidence as a download, with what it is beside it", async () => {
    // A question that names the grammar document cannot be answered until the
    // document is in front of the reader.
    serve(
      answer({
        questions: [
          question({
            files: [
              {
                filename: "قواعد-مصدر.docx",
                description_fa: "سند قواعد مصدر و لاتین‌نویسی.",
                byte_size: 13004,
                href: "/questions/L13/files/قواعد-مصدر.docx",
              },
            ],
          }),
        ],
      }),
    );
    renderApp("/questions");
    const link = await screen.findByRole("link", { name: "قواعد-مصدر.docx" });
    expect(link).toHaveAttribute("href", "/api/questions/L13/files/قواعد-مصدر.docx");
    expect(screen.getByText("سند قواعد مصدر و لاتین‌نویسی.")).toBeInTheDocument();
  });

  it("shows nothing where a question has no attachment", async () => {
    serve(answer());
    renderApp("/questions");
    await screen.findByText(/همخوان یعنی/);
    // Scoped to download links: the navigation has links of its own.
    expect(document.querySelector("a[download]")).toBeNull();
  });

  it("puts Persian evidence on the screen with the question", async () => {
    serve(
      answer({
        questions: [
          question({
            context: { from_document: "بیست‌ویک واژه که هر دو املا را دارند." },
          }),
        ],
      }),
    );
    renderApp("/questions");
    await userEvent.click(await screen.findByText("شواهد"));
    expect(screen.getByText(/بیست‌ویک واژه/)).toBeInTheDocument();
  });

  it("does not show evidence written in English", async () => {
    // It was imported from our own Markdown and arrived as left-to-right
    // prose inside a right-to-left page — unreadable to the one person the
    // screen is for. The files stay; they are the evidence that matters.
    serve(answer());
    renderApp("/questions");
    await screen.findByText(/همخوان یعنی/);
    expect(screen.queryByText("شواهد")).toBeNull();
  });

  it("marks a question that is stopping work", async () => {
    serve(answer({ questions: [question({ blocks_work: true, state: "blocked" })] }));
    renderApp("/questions");
    expect(await screen.findAllByText("کار را متوقف کرده")).not.toHaveLength(0);
  });

  it("tells a reader they cannot answer, before they write one", async () => {
    serve(answer({ answering_as: null }));
    renderApp("/questions");
    expect(await screen.findByText(/پاسخ دادن برای شما باز نیست/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "ثبت پاسخ" })).toBeNull();
  });

  it("offers the box to someone who may answer", async () => {
    serve(answer());
    renderApp("/questions");
    expect(
      await screen.findByRole("button", { name: "ثبت پاسخ" }),
    ).toBeInTheDocument();
  });

  it("will not send an empty ruling", async () => {
    serve(answer());
    renderApp("/questions");
    const send = await screen.findByRole("button", { name: "ثبت پاسخ" });
    expect(send).toBeDisabled();
  });

  it("shows the ruling that stands, and says when the answer changed", async () => {
    serve(
      answer({
        questions: [
          question({
            state: "answered",
            rulings: 2,
            ruling: {
              ruling_fa: "بله.",
              ruling_latin: null,
              ruling_en: null,
              affects: null,
              supersedes_earlier: true,
              ruled_at: null,
            },
          }),
        ],
      }),
    );
    renderApp("/questions");
    // The screen opens on the unanswered, so the answered ones are reached
    // through their own box at the top.
    await userEvent.click(
      await screen.findByRole("button", { name: /پاسخ داده شده/ }),
    );
    expect(await screen.findByText("بله.")).toBeInTheDocument();
    expect(screen.getByText(/پاسخ تغییر کرده/)).toBeInTheDocument();
  });

  it("counts the questions by state, and each count is the filter", async () => {
    // The screen had one checkbox and no figures: how many there are, how many
    // are answered and how many are stopping work had to be counted by hand.
    serve(
      answer({
        questions: [
          question({ reference: "L1" }),
          question({ reference: "L2", state: "answered" }),
        ],
      }),
    );
    renderApp("/questions");
    const boxes = await screen.findByRole("button", { name: /همهٔ پرسش‌ها/ });
    expect(boxes.textContent).toMatch(/۲/);
    expect(screen.getByRole("button", { name: /پاسخ داده شده/ }).textContent).toMatch(
      /۱/,
    );
    // It opens on the unanswered, so L2 is not on screen until its box is hit.
    expect(screen.queryByText("L2")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: /همهٔ پرسش‌ها/ }));
    // One question at a time now, so the box shows the first of the two and
    // the second is one step away.
    expect(await screen.findByText("L1")).toBeInTheDocument();
    await userEvent.click(screen.getAllByRole("button", { name: "پرسش بعدی" })[0]!);
    expect(await screen.findByText("L2")).toBeInTheDocument();
  });

  it("shows one question at a time, and says which one", async () => {
    // Sixteen questions on one page was a scroll minutes long, with nothing
    // on it saying where a reader was.
    serve(
      answer({
        questions: [
          question({ reference: "L1" }),
          question({ reference: "L2" }),
          question({ reference: "L3" }),
        ],
      }),
    );
    renderApp("/questions");
    expect(await screen.findByText("L1")).toBeInTheDocument();
    expect(screen.queryByText("L2")).toBeNull();
    const bars = screen.getAllByRole("navigation", { name: "رفتن میان پرسش‌ها" });
    expect(bars[0]!.textContent).toMatch(/پرسش ۱ از ۳/);
  });

  it("walks forwards and back through them", async () => {
    serve(
      answer({
        questions: [question({ reference: "L1" }), question({ reference: "L2" })],
      }),
    );
    renderApp("/questions");
    await screen.findByText("L1");

    await userEvent.click(screen.getAllByRole("button", { name: "پرسش بعدی" })[0]!);
    expect(await screen.findByText("L2")).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: "پرسش پیشین" })[0]!);
    expect(await screen.findByText("L1")).toBeInTheDocument();
  });

  it("does not offer a step past either end", async () => {
    serve(
      answer({
        questions: [question({ reference: "L1" }), question({ reference: "L2" })],
      }),
    );
    renderApp("/questions");
    await screen.findByText("L1");
    expect(screen.getAllByRole("button", { name: "پرسش پیشین" })[0]!).toBeDisabled();

    await userEvent.click(screen.getAllByRole("button", { name: "پرسش بعدی" })[0]!);
    await screen.findByText("L2");
    expect(screen.getAllByRole("button", { name: "پرسش بعدی" })[0]!).toBeDisabled();
  });

  it("stays on the question just answered, though the filter would drop it", async () => {
    // The screen opens on the unanswered. Answering one makes it answered,
    // and a filter applied blindly would drop it from the list and move the
    // reader to a different question — so the ruling just written would
    // vanish before it could be read back.
    const ruled = {
      ruling_fa: "بله، همان است.",
      ruling_latin: null,
      ruling_en: null,
      affects: null,
      supersedes_earlier: false,
      ruled_at: null,
    };
    const before = answer({
      questions: [question({ reference: "L1" }), question({ reference: "L2" })],
    });
    const after = answer({
      questions: [
        question({ reference: "L1", state: "answered", rulings: 1, ruling: ruled }),
        question({ reference: "L2" }),
      ],
    });
    let sent = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: unknown, init?: RequestInit) => {
        if (init?.method === "POST") {
          sent = true;
          return new Response("{}", { status: 201 });
        }
        return new Response(JSON.stringify(sent ? after : before), { status: 200 });
      }),
    );

    renderApp("/questions");
    await screen.findByText("L1");
    await userEvent.type(
      screen.getByPlaceholderText("پاسخ خود را به فارسی بنویسید."),
      "بله، همان است.",
    );
    await userEvent.click(screen.getByRole("button", { name: "ثبت پاسخ" }));

    expect(await screen.findByText("بله، همان است.")).toBeInTheDocument();
    expect(screen.getByText("L1")).toBeInTheDocument();
  });

  it("opens on the question the address names", async () => {
    // A question is a thing to point at: /questions?q=L2 must open on L2.
    serve(
      answer({
        questions: [question({ reference: "L1" }), question({ reference: "L2" })],
      }),
    );
    renderApp("/questions?q=L2");
    expect(await screen.findByText("L2")).toBeInTheDocument();
    expect(screen.queryByText("L1")).toBeNull();
  });

  it("asks for a token rather than showing an empty screen", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("{}", { status: 401 })),
    );
    renderApp("/questions");
    await waitFor(() =>
      expect(screen.getByText(/کلید دسترسی/)).toBeInTheDocument(),
    );
  });
});

/**
 * The multiple-choice form, asked for on 2026-10-18: options as radios, a
 * free-text box always beside them, one submit. A ruling is an option, text,
 * or both — the submit stays shut only when it is neither.
 */
describe("answering by choosing an option", () => {
  const CHOICES = [
    { id: "document", text_fa: "املای سند درست است.", suggested: false, settles: true },
    { id: "karbon", text_fa: "خوانش کربن درست است.", suggested: true, settles: true },
    { id: "unsure", text_fa: "نمی‌دانم و باید بیشتر بررسی کنم.", suggested: false, settles: false },
  ];

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function serveAndRecord(body: QuestionList): RequestInit[] {
    const posted: RequestInit[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: unknown, init?: RequestInit) => {
        if (init?.method === "POST") {
          posted.push(init);
          return new Response("{}", { status: 201 });
        }
        return new Response(JSON.stringify(body), { status: 200 });
      }),
    );
    return posted;
  }

  it("offers every option, and the box is there without choosing one", async () => {
    serveAndRecord(answer({ questions: [question({ choices: CHOICES })] }));
    renderApp("/questions");
    expect(await screen.findByRole("radio", { name: /املای سند درست است/ })).toBeInTheDocument();
    expect(screen.getAllByRole("radio")).toHaveLength(3);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("marks only the option the documents propose", async () => {
    serveAndRecord(answer({ questions: [question({ choices: CHOICES })] }));
    renderApp("/questions");
    const marks = await screen.findAllByText("پیشنهاد ما");
    expect(marks).toHaveLength(1);
    expect(screen.getByRole("radio", { name: /خوانش کربن/ })).toBeInTheDocument();
  });

  it("sends an option alone", async () => {
    const posted = serveAndRecord(answer({ questions: [question({ choices: CHOICES })] }));
    renderApp("/questions");
    const send = await screen.findByRole("button", { name: "ثبت پاسخ" });
    expect(send).toBeDisabled();
    await userEvent.click(screen.getByRole("radio", { name: /املای سند/ }));
    expect(send).toBeEnabled();
    await userEvent.click(send);
    await waitFor(() => expect(posted).toHaveLength(1));
    const body = JSON.parse(String(posted[0]?.body));
    expect(body.choice_id).toBe("document");
    expect(body.ruling_fa).toBe("");
  });

  it("sends text alone, and both together", async () => {
    const posted = serveAndRecord(answer({ questions: [question({ choices: CHOICES })] }));
    renderApp("/questions");
    const box = await screen.findByRole("textbox");
    await userEvent.type(box, "بستگی دارد.");
    await userEvent.click(screen.getByRole("button", { name: "ثبت پاسخ" }));
    await waitFor(() => expect(posted).toHaveLength(1));
    expect(JSON.parse(String(posted[0]?.body))).toMatchObject({
      choice_id: null,
      ruling_fa: "بستگی دارد.",
    });

    await userEvent.click(screen.getByRole("radio", { name: /خوانش کربن/ }));
    await userEvent.type(screen.getByRole("textbox"), "جز در یک واژه.");
    await userEvent.click(screen.getByRole("button", { name: "ثبت پاسخ" }));
    await waitFor(() => expect(posted).toHaveLength(2));
    expect(JSON.parse(String(posted[1]?.body))).toMatchObject({
      choice_id: "karbon",
      ruling_fa: "جز در یک واژه.",
    });
  });

  it("shows the chosen option of an answer, and his words only when he wrote any", async () => {
    serveAndRecord(
      answer({
        questions: [
          question({
            state: "answered",
            rulings: 1,
            choices: CHOICES,
            ruling: {
              ruling_fa: "املای سند درست است.",
              choice_id: "document",
              choice_fa: "املای سند درست است.",
              ruling_latin: null,
              ruling_en: null,
              affects: null,
              supersedes_earlier: false,
              ruled_at: null,
            },
          }),
        ],
      }),
    );
    renderApp("/questions");
    await userEvent.click(await screen.findByRole("button", { name: /پاسخ داده شده/ }));
    expect(await screen.findByText("گزینهٔ برگزیده")).toBeInTheDocument();
    expect(screen.queryByText("نوشتهٔ شما")).toBeNull();
  });

  it("does not show the options as evidence", async () => {
    serveAndRecord(
      answer({
        questions: [question({ choices: CHOICES, context: { choices: CHOICES, covers: ["L18"] } })],
      }),
    );
    renderApp("/questions");
    await screen.findByRole("radio", { name: /املای سند/ });
    expect(screen.queryByText("شواهد")).toBeNull();
  });
});
