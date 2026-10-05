import { Bookmark, BookmarkCheck, Gauge } from "lucide-react";
import { Link } from "react-router-dom";

import { useT } from "../i18n";
import { movieMeta } from "../lib/format";
import type { Movie } from "../lib/types";
import { Icon } from "./Icon";
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
 */
export function MovieCard({
  movie,
  match,
  quick,
}: {
  movie: Movie;
  match?: number | null;
  quick?: QuickActions;
}) {
  const t = useT();
  const meta = movieMeta(movie, t);
  return (
    <div className={quick ? "movie-card has-quick" : "movie-card"}>
      <Link to={`/movie/${movie.id}`} className="card-link">
        <Poster title={movie.title} path={movie.poster_path} match={match} />
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
    </div>
  );
}
