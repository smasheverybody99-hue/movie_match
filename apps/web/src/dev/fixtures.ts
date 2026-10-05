/**
 * Hand-written API responses: used by the component tests and by the dev-only mock
 * API (`VITE_MOCK_API=1 npm run dev`). Shapes follow src/lib/types.ts exactly.
 */
import { TRAIT_KEYS } from "../lib/traits";
import type {
  MatchBand,
  Movie,
  MovieDetail,
  MovieDna,
  Rating,
  Recommendation,
  Recommendations,
  WatchlistItem,
} from "../lib/types";

const TITLES: [string, string, number][] = [
  ["The Prestige", "2006-10-20", 130],
  ["Memento", "2000-10-11", 113],
  ["Zodiac", "2007-03-02", 157],
  ["Prisoners", "2013-09-20", 153],
  ["Wind River", "2017-08-04", 107],
  ["The Machinist", "2004-10-22", 101],
  ["Enemy", "2013-09-08", 91],
  ["Coherence", "2013-09-19", 89],
  ["The Guilty", "2018-06-14", 88],
  ["Shutter Island", "2010-02-19", 138],
  ["Arrival", "2016-11-11", 116],
  ["Heat", "1995-12-15", 170],
  ["Amélie", "2001-04-25", 122],
  ["Spirited Away", "2001-07-20", 125],
  ["Oldboy", "2003-11-21", 120],
  ["Parasite", "2019-05-30", 132],
  ["Before Sunrise", "1995-01-27", 101],
  ["Mad Max: Fury Road", "2015-05-15", 120],
  ["Paddington 2", "2017-11-10", 103],
  ["The Grand Budapest Hotel", "2014-03-07", 99],
  ["Nightcrawler", "2014-10-31", 117],
  ["Gone Girl", "2014-10-03", 149],
  ["Whiplash", "2014-10-10", 107],
  ["Her", "2013-12-18", 126],
];

export function movie(i: number, patch: Partial<Movie> = {}): Movie {
  const [title, release_date, runtime_minutes] = TITLES[i % TITLES.length] ?? ["Film", null, null];
  return {
    id: 1000 + i,
    title,
    release_date,
    runtime_minutes,
    overview: `${title}: a hand-written overview for the fixtures.`,
    poster_path: null,
    ...patch,
  };
}

export const MOVIES: Movie[] = TITLES.map((_, i) => movie(i));

/** A deterministic trait vector per film, 0..100. */
export function scoresFor(id: number): Record<string, number> {
  return Object.fromEntries(TRAIT_KEYS.map((key, i) => [key, (id * 37 + i * 23) % 101]));
}

export const TASTE: Record<string, number> = Object.fromEntries(
  TRAIT_KEYS.map((key, i) => [key, [88, 91, 84, 80, 72, 55, 30, 35, 48, 40, 69, 62, 74, 66][i] ?? 50]),
);

export function detail(m: Movie, patch: Partial<MovieDetail> = {}): MovieDetail {
  return {
    ...m,
    backdrop_path: null,
    traits: { scores: scoresFor(m.id), summary: null },
    genres: ["Drama", "Mystery"],
    director: "Christopher Nolan",
    cast: ["Hugh Jackman", "Christian Bale"],
    match: 94,
    band: "strong",
    reasons: ["psychological_complexity", "plot_twist", "mystery"],
    ...patch,
  };
}

export function rec(m: Movie, match: number, band: MatchBand | null = null): Recommendation {
  return { movie: m, match, band, reasons: ["mystery", "plot_twist"], explanation: null };
}

/** As the API bands a feed: the first two of "For you" strong (red stays rare), then good. */
function bandAt(i: number): MatchBand | null {
  return i < 2 ? "strong" : i < 5 ? "good" : null;
}

export const RECOMMENDATIONS: Recommendations = {
  status: "ok",
  ratings_needed: 0,
  sections: [
    {
      key: "for_you",
      seed: null,
      items: MOVIES.slice(0, 6).map((m, i) => rec(m, 94 - i * 2, bandAt(i))),
    },
    {
      key: "because_you_loved",
      seed: movie(9),
      items: MOVIES.slice(6, 11).map((m, i) => rec(m, 87 - i * 2, i < 2 ? "good" : null)),
    },
    {
      key: "under_90",
      seed: null,
      items: [rec(movie(7), 83), rec(movie(8), 79)],
    },
    { key: "outside_usual", seed: null, items: [] },
  ],
};

export const DNA: MovieDna = {
  scores: TASTE,
  summary: null,
  rating_count: 14,
  ratings_needed: 0,
  average_rating: 7.64,
  top_genre: "Drama",
};

export function rating(movieId: number, score: number): Rating {
  return { movie_id: movieId, score, liked_aspects: [], rated_at: "2026-09-29T10:00:00Z" };
}

export function watchItem(m: Movie, patch: Partial<WatchlistItem> = {}): WatchlistItem {
  return { movie: m, added_at: "2026-09-28T10:00:00Z", watched_at: null, match: 85, band: "good", ...patch };
}

export const WATCHLIST: WatchlistItem[] = [
  watchItem(movie(5), { match: 88, band: "strong" }),
  watchItem(movie(4), { match: 85, band: "good" }),
  watchItem(movie(8), { match: 81, band: "good" }),
  watchItem(movie(6), { match: 79, band: null }),
  watchItem(movie(11), { match: null, band: null, watched_at: "2026-09-20T10:00:00Z" }),
];
