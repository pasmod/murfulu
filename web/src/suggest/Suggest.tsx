/**
 * A search box that suggests while the reader types.
 *
 * Asked for by the project lead on 2026-11-14: *the search fields all should
 * support auto suggest*. Every box that searches — the word search, the word
 * to build or join or take apart, the word bank, the meanings, the texts —
 * draws itself with this, so they all behave alike.
 *
 * **The pattern is the ARIA combobox with a list** (WAI-ARIA APG, *list
 * autocomplete*): the box keeps the focus the whole time, ↓ and ↑ move through
 * the suggestions, Enter takes the one marked, Escape closes the list, and the
 * marked one is announced through `aria-activedescendant`. A suggestion is
 * never taken without the reader asking: Enter with none marked submits what
 * was typed, exactly as before there were suggestions.
 *
 * **Asked for after a pause, not on every key.** The request goes out once
 * the reader has stopped typing for {@link DELAY} ms, and a request still
 * open when the text moves on is aborted, so a slow answer for «دل» can never
 * land under «دلب».
 *
 * **Only what the reader typed opens the list.** A value written into the box
 * from elsewhere — the address, the query builder, an example button — does
 * not: the list is for the reader at the keyboard, and one opening under a
 * box nobody is typing in reads as the page doing something on its own.
 *
 * On a phone the list is as wide as the box and scrolls inside itself, and
 * every suggestion is a full touch target. A pressed suggestion keeps the
 * focus in the box, so the keyboard stays up.
 */

import {
  type InputHTMLAttributes,
  type KeyboardEvent,
  type ReactNode,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";

import { persianNumber } from "../text/numbers";
import styles from "./Suggest.module.css";

/** How long typing has to pause before suggestions are asked for. */
export const DELAY = 150;

/** One suggestion: what is said and shown for it, and what it carries. */
export interface Suggestion {
  /** Unique within one list. */
  key: string;
  /** What a screen reader says, and what is shown when there is no `view`. */
  text: string;
  /** How it looks in the list, when that is more than `text`. */
  view?: ReactNode;
}

/** Where suggestions come from: an API call, or a list the screen already has. */
export type Source<T extends Suggestion> = (
  text: string,
  signal: AbortSignal,
) => Promise<T[]> | T[];

export interface SuggestProps<T extends Suggestion>
  extends Omit<
    InputHTMLAttributes<HTMLInputElement>,
    "value" | "onChange" | "role" | "list" | "id"
  > {
  id: string;
  value: string;
  onChange: (value: string) => void;
  source: Source<T>;
  /** A suggestion taken — by Enter on the marked one, a click or a tap. */
  onPick: (suggestion: T) => void;
  /** The list's name for a screen reader. */
  listLabel: string;
  /** The wrapper's class: the box's place in the screen's row. */
  boxClassName?: string;
  /** Fewer letters than this ask for nothing. */
  minLength?: number;
  /**
   * Suggest only while the caret is at the end of the box. For a box whose
   * suggestions finish its last term: with the caret further in, the reader
   * is editing another term, and a suggestion would replace the wrong one.
   */
  atEndOnly?: boolean;
}

function aborted(reason: unknown): boolean {
  return reason instanceof DOMException && reason.name === "AbortError";
}

export function Suggest<T extends Suggestion>({
  id,
  value,
  onChange,
  source,
  onPick,
  listLabel,
  boxClassName,
  className,
  minLength = 1,
  atEndOnly = false,
  onKeyDown,
  onBlur,
  ...input
}: SuggestProps<T>) {
  const [items, setItems] = useState<T[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  /** True from the reader's keystroke until a pick, an Escape or leaving the box. */
  const [armed, setArmed] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = `${useId()}-${id}-suggestions`;
  const optionId = (at: number) => `${listId}-${at}`;

  // The source a screen passes is a fresh function on every render more often
  // than not; reading it through a ref keeps a render from restarting the
  // pause and so postponing the request for as long as the screen redraws.
  const sourceRef = useRef(source);
  useEffect(() => {
    sourceRef.current = source;
  }, [source]);

  useEffect(() => {
    if (!armed) return;
    // The text goes to the source as typed, a last space and all: after a
    // space a word is finished, and that is something a source may use.
    const text = value;
    if (text.trim().length < minLength) {
      setItems([]);
      setOpen(false);
      setActive(-1);
      return;
    }
    const stop = new AbortController();
    const timer = window.setTimeout(() => {
      const box = inputRef.current;
      if (atEndOnly && box && box.selectionStart !== box.value.length) {
        setOpen(false);
        setActive(-1);
        return;
      }
      Promise.resolve()
        .then(() => sourceRef.current(text, stop.signal))
        .then((found) => {
          if (stop.signal.aborted) return;
          setItems(found);
          setActive(-1);
          setOpen(found.length > 0);
        })
        .catch((reason: unknown) => {
          // A suggestion that did not come is no error to show: the box still
          // searches, and the list simply stays shut.
          if (aborted(reason) || stop.signal.aborted) return;
          setItems([]);
          setOpen(false);
        });
    }, DELAY);
    return () => {
      window.clearTimeout(timer);
      stop.abort();
    };
  }, [value, armed, minLength, atEndOnly]);

  const shown = open && items.length > 0;

  // A box near the bottom of the window — the word bank's, under its twelve
  // groups, on a phone — opened its list below the screen's edge. The page
  // moves just enough to show the list, and no more.
  const listRef = useRef<HTMLUListElement>(null);
  useEffect(() => {
    if (shown) listRef.current?.scrollIntoView?.({ block: "nearest" });
  }, [shown]);

  // The marked suggestion stays in view when ↓ walks past the list's edge.
  useEffect(() => {
    if (!open || active < 0) return;
    const marked = listRef.current?.querySelector<HTMLElement>(`[data-at="${active}"]`);
    marked?.scrollIntoView?.({ block: "nearest" });
  }, [open, active]);

  function close() {
    setOpen(false);
    setActive(-1);
  }

  /** False while `atEndOnly` and the caret is somewhere before the end. */
  function caretFits(): boolean {
    const box = inputRef.current;
    return !atEndOnly || !box || box.selectionStart === box.value.length;
  }

  function pick(item: T) {
    close();
    setArmed(false);
    onPick(item);
  }

  function keyDown(event: KeyboardEvent<HTMLInputElement>) {
    onKeyDown?.(event);
    if (event.defaultPrevented) return;
    // Keys pressed while an input method is composing a character belong to
    // it: its Enter confirms the character, and must not take a suggestion.
    if (event.nativeEvent.isComposing || event.keyCode === 229) return;
    const count = items.length;
    // With the caret inside an earlier term, a suggestion for the last one is
    // not for what the reader is editing: the list stays shut, Enter searches.
    if (!caretFits() && (event.key === "ArrowDown" || event.key === "Enter")) {
      close();
      if (event.key === "Enter") setArmed(false);
      return;
    }
    switch (event.key) {
      case "ArrowDown":
        if (!count) return;
        event.preventDefault();
        if (!open) {
          setOpen(true);
          setActive(0);
        } else {
          setActive((at) => (at + 1) % count);
        }
        return;
      case "ArrowUp":
        if (!open || !count) return;
        event.preventDefault();
        setActive((at) => (at <= 0 ? count - 1 : at - 1));
        return;
      case "Enter":
        if (open && active >= 0 && items[active]) {
          event.preventDefault();
          pick(items[active]);
        } else {
          // What was typed is searched for; the list has nothing more to say.
          close();
          setArmed(false);
        }
        return;
      case "Escape":
        // Open, Escape closes the list; shut, it is the browser's own — a
        // search box empties itself.
        if (open) {
          event.preventDefault();
          close();
          setArmed(false);
        }
        return;
      case "Tab":
        close();
        return;
      case "ArrowLeft":
      case "ArrowRight":
      case "Home":
      case "End":
        // The caret moves in the box, so the box has the reader again: no
        // suggestion stays marked, and Enter searches what was typed.
        setActive(-1);
        return;
      default:
    }
  }

  return (
    <div className={[styles.box, boxClassName ?? ""].filter(Boolean).join(" ")}>
      <input
        {...input}
        ref={inputRef}
        id={id}
        className={[styles.input, className ?? ""].filter(Boolean).join(" ")}
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={shown}
        aria-controls={listId}
        aria-activedescendant={shown && active >= 0 ? optionId(active) : undefined}
        autoComplete="off"
        value={value}
        onChange={(event) => {
          setArmed(true);
          // A suggestion marked for the old letters is not one for the new:
          // Enter now searches what was typed until the reader marks again.
          setActive(-1);
          onChange(event.target.value);
        }}
        onKeyDown={keyDown}
        // A caret moved by the pointer, or by keys the list does not answer
        // to, is checked here.
        onSelect={() => {
          if (!caretFits()) close();
        }}
        onBlur={(event) => {
          onBlur?.(event);
          close();
          setArmed(false);
        }}
      />
      <ul
        ref={listRef}
        id={listId}
        role="listbox"
        aria-label={listLabel}
        className={styles.list}
        hidden={!shown}
      >
        {shown
          ? items.map((item, at) => (
              <li
                key={item.key}
                id={optionId(at)}
                data-at={at}
                role="option"
                aria-selected={at === active}
                // Said as `text`: a view is several pieces side by side, and
                // read out as one run they would lose the commas between them.
                aria-label={item.view ? item.text : undefined}
                className={styles.option}
                // Pressed, a suggestion must not take the focus from the box:
                // the box would close the list on losing it before the click
                // lands, and on a phone the keyboard would drop.
                onMouseDown={(event) => event.preventDefault()}
                onMouseMove={() => {
                  if (at !== active) setActive(at);
                }}
                onClick={() => pick(item)}
              >
                {item.view ?? item.text}
              </li>
            ))
          : null}
      </ul>
      {/* How many came, said once. A live region rather than a `status`:
          a screen's own status line is the one its readers listen for. */}
      <span className="visually-hidden" aria-live="polite">
        {shown ? `${persianNumber(items.length)} پیشنهاد` : ""}
      </span>
    </div>
  );
}
