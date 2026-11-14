/**
 * The suggesting box on its own: the combobox pattern, the keys, the pause
 * before asking, and that an old answer never lands under new letters.
 */

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { type Source, type Suggestion, Suggest } from "./Suggest";

const WORDS = ["دل", "دلبر", "دلدار", "دلیر"];

const fromList: Source<Suggestion> = (text) =>
  WORDS.filter((one) => one.startsWith(text.trim())).map((one) => ({ key: one, text: one }));

function Box({
  source = fromList,
  onPick = () => undefined,
  onSubmit = () => undefined,
  initial = "",
  atEndOnly = false,
}: {
  source?: Source<Suggestion>;
  onPick?: (one: Suggestion) => void;
  onSubmit?: (value: string) => void;
  initial?: string;
  atEndOnly?: boolean;
}) {
  const [value, setValue] = useState(initial);
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(value);
      }}
    >
      <label htmlFor="box">واژه</label>
      <Suggest
        id="box"
        value={value}
        onChange={setValue}
        source={source}
        listLabel="پیشنهادها"
        atEndOnly={atEndOnly}
        onPick={(one) => {
          setValue(one.text);
          onPick(one);
        }}
      />
      <button type="button" onClick={() => setValue("دلیر")}>
        از بیرون
      </button>
    </form>
  );
}

function box() {
  return screen.getByRole("combobox", { name: "واژه" });
}

describe("a box that suggests", () => {
  it("is a combobox that opens a named list after a pause in typing", async () => {
    render(<Box />);
    expect(box()).toHaveAttribute("aria-expanded", "false");
    await userEvent.type(box(), "دل");
    const list = await screen.findByRole("listbox", { name: "پیشنهادها" });
    expect(box()).toHaveAttribute("aria-expanded", "true");
    expect(box()).toHaveAttribute("aria-controls", list.id);
    expect(box()).toHaveAttribute("aria-autocomplete", "list");
    expect(screen.getAllByRole("option").map((one) => one.textContent)).toEqual(WORDS);
    // Nothing is marked until the reader asks.
    expect(box()).not.toHaveAttribute("aria-activedescendant");
  });

  it("asks once for a run of keys, not once a key", async () => {
    const source = vi.fn(fromList);
    render(<Box source={source} />);
    await userEvent.type(box(), "دلب");
    await screen.findByRole("listbox");
    expect(source).toHaveBeenCalledTimes(1);
    expect(source.mock.calls[0]![0]).toBe("دلب");
  });

  it("moves with the arrow keys, round the ends, and says which is marked", async () => {
    render(<Box />);
    await userEvent.type(box(), "دل");
    await screen.findByRole("listbox");
    await userEvent.keyboard("{ArrowDown}");
    const options = screen.getAllByRole("option");
    expect(box()).toHaveAttribute("aria-activedescendant", options[0]!.id);
    expect(options[0]).toHaveAttribute("aria-selected", "true");
    await userEvent.keyboard("{ArrowUp}");
    expect(box()).toHaveAttribute("aria-activedescendant", options[3]!.id);
    await userEvent.keyboard("{ArrowDown}");
    expect(box()).toHaveAttribute("aria-activedescendant", options[0]!.id);
  });

  it("takes the marked one on Enter and does not submit the form", async () => {
    const onPick = vi.fn();
    const onSubmit = vi.fn();
    render(<Box onPick={onPick} onSubmit={onSubmit} />);
    await userEvent.type(box(), "دل");
    await screen.findByRole("listbox");
    await userEvent.keyboard("{ArrowDown}{ArrowDown}{Enter}");
    expect(onPick).toHaveBeenCalledWith(expect.objectContaining({ text: "دلبر" }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(box()).toHaveValue("دلبر");
    expect(box()).toHaveAttribute("aria-expanded", "false");
    // A taken suggestion does not reopen the list for its own letters.
    await act(() => new Promise((done) => setTimeout(done, 300)));
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("submits what was typed on Enter when nothing is marked", async () => {
    const onPick = vi.fn();
    const onSubmit = vi.fn();
    render(<Box onPick={onPick} onSubmit={onSubmit} />);
    await userEvent.type(box(), "دل");
    await screen.findByRole("listbox");
    await userEvent.keyboard("{Enter}");
    expect(onSubmit).toHaveBeenCalledWith("دل");
    expect(onPick).not.toHaveBeenCalled();
    expect(box()).toHaveAttribute("aria-expanded", "false");
  });

  it("closes on Escape and keeps what was typed", async () => {
    render(<Box />);
    await userEvent.type(box(), "دل");
    await screen.findByRole("listbox");
    await userEvent.keyboard("{ArrowDown}{Escape}");
    expect(box()).toHaveAttribute("aria-expanded", "false");
    expect(box()).not.toHaveAttribute("aria-activedescendant");
    expect(box()).toHaveValue("دل");
  });

  it("takes a suggestion pressed with the pointer and keeps the focus in the box", async () => {
    const onPick = vi.fn();
    render(<Box onPick={onPick} />);
    await userEvent.type(box(), "دل");
    await screen.findByRole("listbox");
    await userEvent.click(screen.getByRole("option", { name: "دلدار" }));
    expect(onPick).toHaveBeenCalledWith(expect.objectContaining({ text: "دلدار" }));
    expect(box()).toHaveFocus();
    expect(box()).toHaveValue("دلدار");
  });

  it("does not open for a value written in from elsewhere", async () => {
    const source = vi.fn(fromList);
    render(<Box source={source} />);
    await userEvent.click(screen.getByRole("button", { name: "از بیرون" }));
    expect(box()).toHaveValue("دلیر");
    await act(() => new Promise((done) => setTimeout(done, 300)));
    expect(source).not.toHaveBeenCalled();
    expect(box()).toHaveAttribute("aria-expanded", "false");
  });

  it("never shows an old answer under new letters", async () => {
    let release: (() => void) | undefined;
    const source: Source<Suggestion> = (text, signal) =>
      text === "د"
        ? new Promise((resolve, reject) => {
            release = () => resolve([{ key: "old", text: "کهنه" }]);
            signal.addEventListener("abort", () =>
              reject(new DOMException("stopped", "AbortError")),
            );
          })
        : fromList(text, signal);
    render(<Box source={source} />);
    await userEvent.type(box(), "د");
    await waitFor(() => expect(release).toBeDefined());
    await userEvent.type(box(), "لب");
    await screen.findByRole("option", { name: "دلبر" });
    await act(async () => release?.());
    expect(screen.queryByRole("option", { name: "کهنه" })).toBeNull();
  });

  it("stays shut when the suggestions cannot be had", async () => {
    render(<Box source={() => Promise.reject(new Error("down"))} />);
    await userEvent.type(box(), "دل");
    await act(() => new Promise((done) => setTimeout(done, 300)));
    expect(box()).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("option")).toBeNull();
  });

  it("opens again with ArrowDown after Escape, without asking again", async () => {
    const source = vi.fn(fromList);
    render(<Box source={source} />);
    await userEvent.type(box(), "دل");
    await screen.findByRole("listbox");
    await userEvent.keyboard("{Escape}{ArrowDown}");
    expect(box()).toHaveAttribute("aria-expanded", "true");
    expect(box()).toHaveAttribute("aria-activedescendant", screen.getAllByRole("option")[0]!.id);
    expect(source).toHaveBeenCalledTimes(1);
  });

  it("forgets the marked one when the letters change, so Enter searches what was typed", async () => {
    const onPick = vi.fn();
    const onSubmit = vi.fn();
    render(<Box onPick={onPick} onSubmit={onSubmit} />);
    await userEvent.type(box(), "دل");
    await screen.findByRole("listbox");
    await userEvent.keyboard("{ArrowDown}{ArrowDown}");
    await userEvent.type(box(), "ی");
    expect(box()).not.toHaveAttribute("aria-activedescendant");
    await userEvent.keyboard("{Enter}");
    expect(onPick).not.toHaveBeenCalled();
    expect(onSubmit).toHaveBeenCalledWith("دلی");
  });

  it("gives the box back when the caret moves", async () => {
    const onPick = vi.fn();
    render(<Box onPick={onPick} />);
    await userEvent.type(box(), "دل");
    await screen.findByRole("listbox");
    await userEvent.keyboard("{ArrowDown}{ArrowLeft}");
    expect(box()).not.toHaveAttribute("aria-activedescendant");
    await userEvent.keyboard("{Enter}");
    expect(onPick).not.toHaveBeenCalled();
  });

  it("leaves an Enter to an input method that is composing", async () => {
    const onPick = vi.fn();
    render(<Box onPick={onPick} />);
    await userEvent.type(box(), "دل");
    await screen.findByRole("listbox");
    await userEvent.keyboard("{ArrowDown}");
    fireEvent.keyDown(box(), { key: "Enter", keyCode: 229 });
    expect(onPick).not.toHaveBeenCalled();
    expect(box()).toHaveAttribute("aria-expanded", "true");
  });

  it("asks nothing for an edit inside the text when it finishes only the end", async () => {
    const source = vi.fn(fromList);
    render(<Box source={source} atEndOnly initial="دل دل" />);
    const input = box() as HTMLInputElement;
    await userEvent.click(input);
    input.setSelectionRange(1, 1);
    await userEvent.type(input, "ب", { initialSelectionStart: 1, initialSelectionEnd: 1 });
    expect(input).toHaveValue("دبل دل");
    await act(() => new Promise((done) => setTimeout(done, 300)));
    expect(source).not.toHaveBeenCalled();
    await userEvent.type(input, "ب", { initialSelectionStart: 6, initialSelectionEnd: 6 });
    await waitFor(() => expect(source).toHaveBeenCalledTimes(1));
  });

  it("takes nothing for the end when the caret has gone back into the text", async () => {
    const onPick = vi.fn();
    const onSubmit = vi.fn();
    render(<Box atEndOnly onPick={onPick} onSubmit={onSubmit} />);
    await userEvent.type(box(), "دل");
    await screen.findByRole("listbox");
    const input = box() as HTMLInputElement;
    await userEvent.keyboard("{ArrowLeft}");
    fireEvent.select(input);
    expect(box()).toHaveAttribute("aria-expanded", "false");
    await userEvent.keyboard("{ArrowDown}{Enter}");
    expect(onPick).not.toHaveBeenCalled();
    expect(onSubmit).toHaveBeenCalledWith("دل");
  });
});
