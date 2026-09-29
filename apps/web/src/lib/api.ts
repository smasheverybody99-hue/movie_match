import type {
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

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  } catch (cause) {
    throw new ApiError(0, cause instanceof Error ? cause.message : "Network error");
  }

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

export const api = {
  health: () => request<{ status: string; trait_dimensions: number }>("/health"),

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
};

export type Api = typeof api;
