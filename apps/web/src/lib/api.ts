import type {
  AssistantCard,
  AssistantChatIn,
  AssistantEvent,
  AssistantLimit,
  Explanation,
  Lang,
  Me,
  Movie,
  MovieDetail,
  MovieDna,
  Rating,
  RatingIn,
  Recommendations,
  WatchlistItem,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

/** Set on every Supabase session change. Supabase issues the token; the API verifies it. */
let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

/**
 * Any failed request. `status` is the HTTP status, or 0 when the request never got an
 * answer (offline, API down, CORS). Screens branch on the status, never on `message`:
 * the message is for logs, not for users.
 */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

/** The assistant's 429: today's messages are used up until `limit.resets_at` (FR-8). */
export class AssistantLimitError extends ApiError {
  constructor(readonly limit: AssistantLimit) {
    super(429, limit.detail);
    this.name = "AssistantLimitError";
  }
}

async function send(path: string, init: RequestInit): Promise<Response> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  try {
    return await fetch(`${BASE_URL}${path}`, { ...init, headers });
  } catch (cause) {
    throw new ApiError(0, cause instanceof Error ? cause.message : "Network error");
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await send(path, init);

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new ApiError(response.status, detail || response.statusText);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function json(method: string, body: unknown): RequestInit {
  return { method, body: JSON.stringify(body) };
}

export interface SearchParams {
  q?: string;
  yearFrom?: number;
  yearTo?: number;
  maxRuntime?: number;
  /** Trait keys; each means "scores at least `traitMinimum`". */
  traits?: readonly string[];
  traitMinimum?: number;
  limit?: number;
}

export function searchQuery(params: SearchParams): string {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.yearFrom !== undefined) query.set("year_from", String(params.yearFrom));
  if (params.yearTo !== undefined) query.set("year_to", String(params.yearTo));
  if (params.maxRuntime !== undefined) query.set("max_runtime", String(params.maxRuntime));
  for (const key of params.traits ?? []) query.append("trait", `${key}:${params.traitMinimum ?? 70}`);
  query.set("limit", String(params.limit ?? 40));
  return query.toString();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isLimit(value: unknown): value is AssistantLimit {
  return isRecord(value) && typeof value.resets_at === "string" && typeof value.limit === "number";
}

/**
 * One SSE block (`event: name` + `data: json`) as an AssistantEvent, or null for anything
 * this client does not know: a newer API may add events, and an old client skips them.
 */
export function toAssistantEvent(name: string, data: unknown): AssistantEvent | null {
  if (!isRecord(data)) return null;
  switch (name) {
    case "text":
      return typeof data.text === "string" ? { type: "text", text: data.text } : null;
    case "card":
      return isRecord(data.movie) && typeof data.match === "number"
        ? { type: "card", card: data as unknown as AssistantCard }
        : null;
    case "followups":
      return Array.isArray(data.items)
        ? { type: "followups", items: data.items.filter((i): i is string => typeof i === "string") }
        : null;
    case "refusal":
      return data.reason === "off_topic" || data.reason === "leak" ? { type: "refusal", reason: data.reason } : null;
    case "error":
      return { type: "error", reason: data.reason === "blocked" ? "blocked" : "failed" };
    case "done":
      return { type: "done" };
    default:
      return null;
  }
}

/** Complete SSE blocks out of `buffer`, and what is left of it (a block still arriving). */
export function readSse(buffer: string): { events: AssistantEvent[]; rest: string } {
  const normalised = buffer.replace(/\r\n/g, "\n");
  const blocks = normalised.split("\n\n");
  const rest = blocks.pop() ?? "";
  const events: AssistantEvent[] = [];
  for (const block of blocks) {
    let name = "message";
    const data: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) name = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    let parsed: unknown = null;
    try {
      parsed = JSON.parse(data.join("\n"));
    } catch {
      continue;
    }
    const event = toAssistantEvent(name, parsed);
    if (event) events.push(event);
  }
  return { events, rest };
}

/**
 * POST /assistant/chat. Calls `onEvent` for every event as it arrives and resolves when
 * the stream ends. Throws AssistantLimitError on the daily cap, ApiError otherwise.
 */
async function assistantChat(
  body: AssistantChatIn,
  onEvent: (event: AssistantEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await send("/assistant/chat", { ...json("POST", body), signal });
  if (response.status === 429) {
    const limit: unknown = await response.json().catch(() => null);
    if (isLimit(limit)) throw new AssistantLimitError(limit);
  }
  if (!response.ok || !response.body) {
    const detail = await response.text().catch(() => "");
    throw new ApiError(response.status, detail || response.statusText);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const { events, rest } = readSse(done ? `${buffer}\n\n` : buffer);
      buffer = rest;
      events.forEach(onEvent);
      if (done) return;
    }
  } catch (cause) {
    if (cause instanceof ApiError) throw cause;
    throw new ApiError(0, cause instanceof Error ? cause.message : "Stream broke");
  }
}

export const api = {
  health: () => request<{ status: string; trait_dimensions: number; commit: string | null }>("/health"),

  searchMovies: (params: SearchParams) => request<Movie[]>(`/movies?${searchQuery(params)}`),
  getMovie: (id: number) => request<MovieDetail>(`/movies/${id}`),

  me: () => request<Me>("/me"),
  dna: () => request<MovieDna>("/me/dna"),
  deleteAccount: () => request<void>("/me", { method: "DELETE" }),

  onboardingFilms: (limit: number, offset: number) =>
    request<Movie[]>(`/onboarding/films?limit=${limit}&offset=${offset}`),

  ratings: () => request<Rating[]>("/ratings"),
  rate: (body: RatingIn) => request<Rating>("/ratings", json("POST", body)),
  unrate: (movieId: number) => request<void>(`/ratings/${movieId}`, { method: "DELETE" }),

  watchlist: () => request<WatchlistItem[]>("/watchlist"),
  addToWatchlist: (movieId: number) =>
    request<WatchlistItem>("/watchlist", json("POST", { movie_id: movieId })),
  removeFromWatchlist: (movieId: number) =>
    request<void>(`/watchlist/${movieId}`, { method: "DELETE" }),
  markWatched: (movieId: number) =>
    request<WatchlistItem>(`/watchlist/${movieId}/watched`, { method: "POST" }),

  recommendations: (lang: Lang) => request<Recommendations>(`/recommendations?lang=${lang}`),
  explanation: (movieId: number, lang: Lang) =>
    request<Explanation>(`/recommendations/${movieId}/explanation?lang=${lang}`),
  dismiss: (movieId: number) => request<void>("/dismissals", json("POST", { movie_id: movieId })),

  assistantChat,
};

export type Api = typeof api;
