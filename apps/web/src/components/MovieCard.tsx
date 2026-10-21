import { Bookmark, BookmarkCheck, Gauge } from "lucide-react";
import { Link } from "react-router-dom";

import { useT } from "../i18n";
import { movieMeta } from "../lib/format";
import type { MatchBand, Movie } from "../lib/types";
import { Icon } from "./Icon";
import { Tilt } from "./motion";
import { Poster } from "./Poster";

/** Quick actions over the poster (Home rows): Rate opens the rating dialog, Save toggles. */
export interface QuickActions {
  saved: boolean;
  onRate: () => void;
  onToggleSave: () => void;
}

/**
 * Poster, title (two lines at most), year · runtime. Links to the film page.
 * With `quick`: on hover (a fine pointer only) or keyboard focus the poster lifts (8%, shadow)
 * and two icon buttons appear over it. They sit beside the link, not inside it (no button
 * in a link). On touch there is no hover: a tap opens the film page.
 *
 * The card also turns a few degrees towards the pointer (Tilt). That rotation is on the
 * card, while the lift is a CSS transition on the poster inside it, so the two compose
 * instead of overwriting one another. Neither happens on touch or with reduced motion.
 */
export function MovieCard({
  movie,
  band,
  quick,
}: {
  movie: Movie;
  band?: MatchBand | null;
  quick?: QuickActions;
}) {
  const t = useT();
  const meta = movieMeta(movie, t);
  return (
    <Tilt className={quick ? "movie-card has-quick" : "movie-card"} max={6}>
      <Link to={`/movie/${movie.id}`} className="card-link">
        <Poster movie={movie} band={band} />
        <div className="movie-card-title">{movie.title}</div>
        {meta && <div className="meta">{meta}</div>}
      </Link>
      {quick && (
        <div className="card-quick">
          <button
            type="button"
            className="quick-btn"
            aria-label={t("movie.rateDialog", { title: movie.title })}
            title={t("movie.rate")}
            onClick={quick.onRate}
          >
            <Icon as={Gauge} size={24} />
          </button>
          <button
            type="button"
            className="quick-btn"
            aria-label={t("feed.quickSave", { title: movie.title })}
            aria-pressed={quick.saved}
            title={quick.saved ? t("movie.onList") : t("movie.saveToList")}
            onClick={quick.onToggleSave}
          >
            <Icon as={quick.saved ? BookmarkCheck : Bookmark} size={24} />
          </button>
        </div>
      )}
    </Tilt>
  );
}
