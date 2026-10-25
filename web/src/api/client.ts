/**
 * Talking to the API.
 *
 * One place, so no screen writes a URL and no screen invents an error
 * message. Everything goes to `/api` on this origin — the dev server proxies
 * it, nginx proxies it in the container, and the app never learns where the
 * API actually lives.
 *
 * **The failures are the interesting part.** docs/FRONTEND.md asks error
 * states to say what to do next, never just what failed, and this project has
 * two failures that mean very different things and would otherwise look the
 * same: the search index has not been built yet (503) and the query itself is
 * unreadable (400). One is "come back after the ingest"; the other is "you
 * wrote something I cannot parse". They are separate types here.
 */

export const BASE = "/api";

/** Why a request did not produce an answer. */
export type Trouble =
  /** The query could not be read. The message names what is wrong with it. */
  | "unreadable-query"
  /** The index or the store is not there yet. Nothing is wrong with the query. */
  | "not-built"
  /** Nothing by that name. */
  | "missing"
  /** No token, or one the API does not know. */
  | "unidentified"
  /** A working token, on an account that may not do this. */
  | "not-allowed"
  /** Anything else: the network, a bug, the API being down. */
  | "unreachable";

/**
 * A fault named by the API, rather than described by it.
 *
 * The search parser's messages are English and the interface used to print
 * them under a Persian heading. It now sends the fault by name and the parts
 * of it, and the screen writes the Persian — see `Search.tsx`. `said` is the
 * English, kept for the console and for a developer reading a network tab.
 */
export interface Reason {
  code: string;
  facts: Record<string, string>;
  said: string;
}

export class ApiError extends Error {
  readonly trouble: Trouble;
  readonly status: number;
  /** Set when the API named the fault. Absent on anything older or simpler. */
  readonly reason: Reason | null;

  constructor(
    trouble: Trouble,
    status: number,
    message: string,
    reason: Reason | null = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.trouble = trouble;
    this.status = status;
    this.reason = reason;
  }
}

function troubleFor(status: number): Trouble {
  if (status === 400 || status === 422) return "unreadable-query";
  if (status === 401) return "unidentified";
  // Kept apart from 401 on purpose. "I do not know you" and "I know you and
  // this is not yours" are different sentences to a reader, and the second
  // one must not read as a broken token.
  if (status === 403) return "not-allowed";
  if (status === 404) return "missing";
  if (status === 503) return "not-built";
  return "unreachable";
}

/** Whether a `detail` object is the API naming a fault rather than describing one. */
function isReason(detail: unknown): detail is Reason {
  return (
    typeof detail === "object" &&
    detail !== null &&
    typeof (detail as Reason).code === "string"
  );
}

async function detail(
  response: Response,
): Promise<{ message: string; reason: Reason | null }> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return { message: body.detail, reason: null };
    }
    if (isReason(body.detail)) {
      return { message: body.detail.said, reason: body.detail };
    }
    return { message: JSON.stringify(body.detail ?? ""), reason: null };
  } catch {
    return { message: response.statusText, reason: null };
  }
}

async function send<T>(url: string, init: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (reason) {
    if (reason instanceof DOMException && reason.name === "AbortError") throw reason;
    throw new ApiError("unreachable", 0, String(reason));
  }

  if (!response.ok) {
    const said = await detail(response);
    throw new ApiError(
      troubleFor(response.status),
      response.status,
      said.message,
      said.reason,
    );
  }
  return (await response.json()) as T;
}

/** One GET, with the query string built from the parts that are set. */
export async function get<T>(
  path: string,
  params: Record<string, string | number | undefined> = {},
  signal?: AbortSignal,
  headers: Record<string, string> = {},
): Promise<T> {
  const query = new URLSearchParams();
  for (const [name, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") query.set(name, String(value));
  }
  const suffix = query.toString();
  const url = `${BASE}${path}${suffix ? `?${suffix}` : ""}`;
  return send<T>(url, {
    signal,
    headers: { accept: "application/json", ...headers },
  });
}

/**
 * One POST. Only the review store takes writes, and every one of them needs a
 * token — which is why the headers are a parameter rather than a default.
 */
export async function post<T>(
  path: string,
  body: unknown,
  headers: Record<string, string> = {},
  signal?: AbortSignal,
): Promise<T> {
  return send<T>(`${BASE}${path}`, {
    method: "POST",
    signal,
    headers: {
      accept: "application/json",
      "content-type": "application/json",
      ...headers,
    },
    body: JSON.stringify(body),
  });
}
