import type { Movie, MovieDetail } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

/** Set once the user signs in. Supabase issues the token; the API verifies it. */
let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new ApiError(response.status, detail || response.statusText);
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => request<{ status: string; trait_dimensions: number }>("/health"),
  searchMovies: (q: string) =>
    request<Movie[]>(`/movies?q=${encodeURIComponent(q)}`),
  getMovie: (id: number) => request<MovieDetail>(`/movies/${id}`),
};
