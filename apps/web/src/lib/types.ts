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
