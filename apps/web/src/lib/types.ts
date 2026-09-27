// Mirrors services/api/app/schemas.py by hand.
// When a Pydantic schema changes, change this file in the same commit.

export interface Movie {
  id: number;
  title: string;
  release_date: string | null;
  runtime_minutes: number | null;
  overview: string | null;
  poster_path: string | null;
}

export interface TraitScores {
  scores: Record<string, number>;
  summary: string | null;
}

export interface MovieDetail extends Movie {
  traits: TraitScores | null;
  genres: string[];
  director: string | null;
  cast: string[];
}

export interface Recommendation {
  movie: Movie;
  /** 0-100, computed from trait distance. */
  match: number;
  /** Trait keys that drove the match, strongest first. */
  reasons: string[];
  explanation: string | null;
}

export interface MovieDna {
  scores: Record<string, number>;
  summary: string | null;
  rating_count: number;
}

export type Lang = "uz" | "en";

export type SectionKey = "for_you" | "because_you_loved" | "under_90" | "outside_usual";

/** One row of recommendations. The client turns `key` into a title in the user's language. */
export interface Section {
  key: SectionKey;
  /** The film in "Because you loved {film}"; null otherwise. */
  seed: Movie | null;
  items: Recommendation[];
}

export interface Recommendations {
  status: "ok" | "not_enough_data";
  /** Ratings still needed before recommendations. */
  ratings_needed: number;
  sections: Section[];
}

export interface Explanation {
  movie_id: number;
  lang: Lang;
  /** Null when it could not be generated; try later. */
  text: string | null;
}

export interface DismissalIn {
  movie_id: number;
}

export interface Me {
  id: string;
  created_at: string;
  rating_count: number;
  ratings_needed: number;
  has_taste_profile: boolean;
  taste_updated_at: string | null;
}

export interface RatingIn {
  movie_id: number;
  /** 0.5 .. 10.0 */
  score: number;
  /** Trait keys, no repeats. */
  liked_aspects?: string[];
}

export interface Rating {
  movie_id: number;
  score: number;
  liked_aspects: string[];
  /** When the score was last set. */
  rated_at: string;
}

export interface WatchlistIn {
  movie_id: number;
}

export interface WatchlistItem {
  movie: Movie;
  added_at: string;
  watched_at: string | null;
}
