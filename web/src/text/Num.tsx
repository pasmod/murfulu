/**
 * A number on screen. Always Persian numerals; never a bare `{count}`.
 *
 * The element carries the Latin value in `data-value` so a test — and anyone
 * reading the DOM — can still see what the figure is.
 */

import { persianNumber } from "./numbers";

export interface NumProps {
  value: number;
  className?: string;
}

export function Num({ value, className }: NumProps) {
  return (
    <span className={className} data-value={String(value)}>
      {persianNumber(value)}
    </span>
  );
}
