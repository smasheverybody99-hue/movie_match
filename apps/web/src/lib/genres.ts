import type { MessageKey, Translate } from "../i18n";

/** TMDB's genre names, as the API sends them (English, from ingestion). */
const GENRE_KEYS: Readonly<Record<string, MessageKey>> = {
  Action: "genre.action",
  Adventure: "genre.adventure",
  Animation: "genre.animation",
  Comedy: "genre.comedy",
  Crime: "genre.crime",
  Documentary: "genre.documentary",
  Drama: "genre.drama",
  Family: "genre.family",
  Fantasy: "genre.fantasy",
  History: "genre.history",
  Horror: "genre.horror",
  Music: "genre.music",
  Mystery: "genre.mystery",
  Romance: "genre.romance",
  "Science Fiction": "genre.science_fiction",
  Thriller: "genre.thriller",
  "TV Movie": "genre.tv_movie",
  War: "genre.war",
  Western: "genre.western",
};

/**
 * A genre in the interface language. TMDB has a fixed list, so it is translated like a
 * label; a name TMDB adds later is shown as sent until it gets a key.
 */
export function genreLabel(name: string, t: Translate): string {
  const key = GENRE_KEYS[name];
  return key ? t(key) : name;
}

export const KNOWN_GENRES = Object.keys(GENRE_KEYS);
