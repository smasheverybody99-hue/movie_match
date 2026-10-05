/**
 * DEV ONLY: an in-memory API and a signed-in fake session, so the screens can be
 * walked through in a browser without Supabase keys or a scored catalogue.
 *
 *   VITE_MOCK_API=1 npm run dev
 *
 * main.tsx imports this only when `import.meta.env.DEV` and the flag are both set, so
 * it never reaches a production bundle. Controls, in the browser console:
 *   localStorage["mm.mock.scenario"] = "new" | "active"   (then reload)
 *   localStorage["mm.mock.down"] = "1"                     (every request fails)
 *   localStorage["mm.mock.signedOut"] = "1"                (start at /welcome)
 *   localStorage["mm.mock.explain"] = "none" | "long"      (no AI text / a 2-sentence one)
 * Posters and backdrops are real TMDB paths (images.ts). Reasons vary by film id: three,
 * one, or none (id % 4 == 3, the "suits you overall" case).
 */
import type { AuthClient, Session } from "../lib/supabase";
import type { Movie, MovieDetail, Rating, WatchlistItem } from "../lib/types";
import { DNA, MOVIES as PLAIN, RECOMMENDATIONS as PLAIN_RECS, TASTE, WATCHLIST as PLAIN_LIST, detail, rating, rec, scoresFor } from "./fixtures";
import { TMDB_PATHS } from "./images";

function withImages(m: Movie): Movie {
  return { ...m, poster_path: TMDB_PATHS[m.title]?.poster ?? null };
}

const MOVIES = PLAIN.map(withImages);
const WATCHLIST = PLAIN_LIST.map((i) => ({ ...i, movie: withImages(i.movie) }));
const RECOMMENDATIONS = {
  ...PLAIN_RECS,
  sections: PLAIN_RECS.sections.map((s) => ({
    ...s,
    seed: s.seed && withImages(s.seed),
    // "For you" carries 12 here (the fixtures have 6), so a row overflows on wide screens.
    items: (s.key === "for_you" ? PLAIN.slice(0, 12).map((m, i) => rec(m, 94 - i * 2, i < 2 ? "strong" : i < 6 ? "good" : null)) : s.items).map((r) => ({
      ...r,
      movie: withImages(r.movie),
    })),
  })),
};

/** Stand-ins for the AI text, at its measured typical length (~30 tokens) and at two sentences. */
const EXPLANATION = {
  typical: "It keeps you guessing the way your favourites do, and the pieces only click into place in the last act.",
  long:
    "It keeps you guessing the way your favourites do, and the pieces only click into place in the last act. Its rivalry plays out in layers of misdirection, more than most films attempt.",
};

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

function flag(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function json(body: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function install(): AuthClient {
  const scenario = flag("mm.mock.scenario") ?? "active";
  let ratings: Rating[] = scenario === "new" ? [] : MOVIES.slice(10, 24).map((m, i) => rating(m.id, 6 + (i % 5)));
  let watchlist: WatchlistItem[] = scenario === "new" ? [] : [...WATCHLIST];
  const byId = new Map<number, Movie>(MOVIES.map((m) => [m.id, m]));

  function detailOf(id: number): MovieDetail | null {
    const m = byId.get(id);
    if (!m) return null;
    const reasons = [["psychological_complexity", "plot_twist", "mystery"], ["plot_twist", "mystery", "darkness"], ["darkness"], []][id % 4] ?? [];
    return detail(m, {
      backdrop_path: TMDB_PATHS[m.title]?.backdrop ?? null,
      match: ratings.length >= 10 ? 60 + (id % 38) : null,
      // Every third film strong (The Prestige), the next good (Memento), the next none.
      band: ratings.length < 10 ? null : (["strong", "good", null] as const)[(id - 1000) % 3] ?? null,
      reasons,
    });
  }

  async function route(method: string, url: URL, body: unknown): Promise<Response> {
    const path = url.pathname;
    const count = ratings.length;
    const needed = Math.max(10 - count, 0);

    if (path === "/me") {
      return json({ id: "mock-user", created_at: "2026-09-01T00:00:00Z", rating_count: count, ratings_needed: needed, has_taste_profile: count > 0, taste_updated_at: null });
    }
    if (path === "/me/dna") {
      const average = count ? ratings.reduce((s, r) => s + r.score, 0) / count : null;
      return json({ ...DNA, scores: count ? TASTE : {}, rating_count: count, ratings_needed: needed, average_rating: average });
    }
    if (path === "/onboarding/films") {
      const offset = Number(url.searchParams.get("offset") ?? 0);
      const rated = new Set(ratings.map((r) => r.movie_id));
      return json(MOVIES.filter((m) => !rated.has(m.id)).slice(offset % MOVIES.length, (offset % MOVIES.length) + 60));
    }
    if (path === "/ratings" && method === "GET") return json(ratings);
    if (path === "/ratings" && method === "POST") {
      const b = body as { movie_id: number; score: number; liked_aspects?: string[] };
      const r = { ...rating(b.movie_id, b.score), liked_aspects: b.liked_aspects ?? [] };
      ratings = [r, ...ratings.filter((x) => x.movie_id !== b.movie_id)];
      return json(r);
    }
    if (path === "/recommendations") {
      if (count < 10) return json({ status: "not_enough_data", ratings_needed: needed, sections: [] });
      return json(RECOMMENDATIONS);
    }
    const explanation = path.match(/^\/recommendations\/(\d+)\/explanation$/);
    if (explanation) {
      await wait(900);
      const mode = flag("mm.mock.explain");
      const text = mode === "none" ? null : mode === "long" ? EXPLANATION.long : EXPLANATION.typical;
      return json({ movie_id: Number(explanation[1]), lang: url.searchParams.get("lang"), text });
    }
    const movieMatch = path.match(/^\/movies\/(\d+)$/);
    if (movieMatch) {
      const d = detailOf(Number(movieMatch[1]));
      return d ? json(d) : json({ detail: "Movie not found" }, 404);
    }
    if (path === "/movies") {
      const q = (url.searchParams.get("q") ?? "").toLowerCase();
      const maxRuntime = Number(url.searchParams.get("max_runtime") ?? 0);
      const yearFrom = Number(url.searchParams.get("year_from") ?? 0);
      const yearTo = Number(url.searchParams.get("year_to") ?? 9999);
      const traits = url.searchParams.getAll("trait").map((t) => t.split(":"));
      return json(
        MOVIES.filter((m) => m.title.toLowerCase().includes(q))
          .filter((m) => !maxRuntime || (m.runtime_minutes ?? 0) <= maxRuntime)
          .filter((m) => {
            const y = Number((m.release_date ?? "0").slice(0, 4));
            return y >= yearFrom && y <= yearTo;
          })
          .filter((m) => traits.every(([k, min]) => (scoresFor(m.id)[k ?? ""] ?? 0) >= Number(min))),
      );
    }
    if (path === "/watchlist" && method === "GET") return json(watchlist);
    if (path === "/watchlist" && method === "POST") {
      const id = (body as { movie_id: number }).movie_id;
      const m = byId.get(id);
      if (!m) return json({ detail: "Movie not found" }, 404);
      if (!watchlist.some((i) => i.movie.id === id)) {
        watchlist = [{ movie: m, added_at: new Date().toISOString(), watched_at: null, match: 80, band: "good" }, ...watchlist];
      }
      return json(watchlist.find((i) => i.movie.id === id));
    }
    const watched = path.match(/^\/watchlist\/(\d+)\/watched$/);
    if (watched) {
      const id = Number(watched[1]);
      watchlist = watchlist.map((i) => (i.movie.id === id && !i.watched_at ? { ...i, watched_at: new Date().toISOString() } : i));
      return json(watchlist.find((i) => i.movie.id === id));
    }
    const removed = path.match(/^\/watchlist\/(\d+)$/);
    if (removed && method === "DELETE") {
      watchlist = watchlist.filter((i) => i.movie.id !== Number(removed[1]));
      return json(null, 204);
    }
    if (path === "/me" && method === "DELETE") return json(null, 204);
    return json({ detail: "Not found" }, 404);
  }

  const realFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const url = new URL(typeof input === "string" ? input : input instanceof URL ? input.href : input.url);
    if (!url.href.startsWith(BASE_URL)) return realFetch(input, init);
    await wait(250);
    if (flag("mm.mock.down") === "1") throw new TypeError("Failed to fetch");
    const body: unknown = typeof init?.body === "string" ? JSON.parse(init.body) : undefined;
    return route(init?.method ?? "GET", url, body);
  };

  const session: Session = { accessToken: "mock-token", userId: "mock-user", email: "demo@example.com" };
  let current: Session | null = flag("mm.mock.signedOut") === "1" ? null : session;
  const listeners = new Set<(s: Session | null) => void>();
  return {
    getSession: async () => current,
    onChange(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    async signInWithOAuth() {
      current = session;
      listeners.forEach((l) => l(current));
    },
    async signInWithEmail() {},
    async signOut() {
      current = null;
      listeners.forEach((l) => l(null));
    },
  };
}
