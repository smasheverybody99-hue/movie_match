import type { Translate } from "../i18n";
import type { Movie } from "./types";

const TMDB_IMAGES = "https://image.tmdb.org/t/p";

/** TMDB image URL for a stored path, or null. Sizes are TMDB's fixed widths. */
export function imageUrl(
  path: string | null,
  size: "w185" | "w342" | "w780" | "w1280",
): string | null {
  return path ? `${TMDB_IMAGES}/${size}${path}` : null;
}

export function releaseYear(movie: Pick<Movie, "release_date">): string | null {
  return movie.release_date ? movie.release_date.slice(0, 4) : null;
}

/** "2010 · 138m": whatever of year and runtime is known. */
export function movieMeta(movie: Movie, t: Translate): string {
  const parts: string[] = [];
  const year = releaseYear(movie);
  if (year) parts.push(year);
  if (movie.runtime_minutes) parts.push(t("common.minutes", { n: movie.runtime_minutes }));
  return parts.join(" · ");
}

/** Up to two initials for a poster placeholder. */
export function initials(title: string): string {
  const words = title.split(/\s+/).filter((w) => /\p{L}|\p{N}/u.test(w));
  return words
    .slice(0, 2)
    .map((w) => [...w][0] ?? "")
    .join("")
    .toUpperCase();
}

/** One decimal, the way scores are shown: 8 -> "8.0". */
export function score(value: number): string {
  return value.toFixed(1);
}
