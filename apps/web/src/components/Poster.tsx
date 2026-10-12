import { useState } from "react";

import { useT } from "../i18n";
import { imageUrl, releaseYear } from "../lib/format";
import { genreLabel } from "../lib/genres";
import type { MatchBand as Band, Movie } from "../lib/types";
import { MatchBand } from "./MatchBand";

interface PosterProps {
  movie: Pick<Movie, "title" | "poster_path" | "release_date" | "genres">;
  size?: "w185" | "w342";
  /** The match band; only "strong" is shown on a poster (top-left, red), so it stays rare. */
  band?: Band | null;
  /** Decorative when the title is printed next to it (the default), so it isn't read twice. */
  describe?: boolean;
  eager?: boolean;
}

/**
 * 2:3 poster. Under the image, always: the title, the year and the first genre, so the card
 * says what it is while the image loads, when it fails, or when it cannot be reached at all
 * (image.tmdb.org refuses connections from some networks, Kazakhstan and parts of Russia
 * measured 2026-10-12; tester 1 saw black squares). The image covers it once it arrives.
 */
export function Poster({ movie, size = "w342", band, describe = false, eager }: PosterProps) {
  const t = useT();
  const [failed, setFailed] = useState(false);
  const src = failed ? null : imageUrl(movie.poster_path, size);
  const year = releaseYear(movie);
  const genre = movie.genres[0] ? genreLabel(movie.genres[0], t) : null;
  const meta = [year, genre].filter(Boolean).join(" · ");
  return (
    <div className="poster">
      {/* Drawn by CSS from these attributes: the title is already the card's text, so it is
          neither read out nor found by find-in-page a second time. */}
      <span
        className="poster-fallback"
        aria-hidden="true"
        data-testid="poster-fallback"
        data-title={movie.title}
        data-meta={meta || undefined}
      />
      {src && (
        <img
          src={src}
          alt={describe ? t("common.poster", { title: movie.title }) : ""}
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          onError={() => setFailed(true)}
        />
      )}
      {band === "strong" && <MatchBand band={band} className="badge" />}
    </div>
  );
}
