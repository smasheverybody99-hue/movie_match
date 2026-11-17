import { Bookmark, BookmarkCheck, Gauge } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { useT } from "../i18n";
import { movieMeta } from "../lib/format";
import { track, useShownRef } from "../lib/telemetry";
import type { EventSource, MatchBand, Movie } from "../lib/types";
import { Icon } from "./Icon";
import { NotRight } from "./NotRight";
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
  band,
  quick,
  source,
}: {
  movie: Movie;
  band?: MatchBand | null;
  quick?: QuickActions;
  /** A recommendation from here: its showing and its click go to the alpha's telemetry. */
  source?: EventSource;
}) {
  const t = useT();
  const meta = movieMeta(movie, t);
  return (
    <TrackedCard movieId={movie.id} source={source} className={quick ? "movie-card has-quick" : "movie-card"}>
      <Link
        to={`/movie/${movie.id}`}
        className="card-link"
        onClick={source ? () => track({ type: "recommendation_clicked", movie_id: movie.id, source }) : undefined}
      >
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
      {source && <NotRight movie={movie} source={source} />}
    </TrackedCard>
  );
}

/** The card's box; with a source, it reports its first second in view (lib/telemetry.ts). */
function TrackedCard({
  movieId,
  source,
  className,
  children,
}: {
  movieId: number;
  source?: EventSource;
  className: string;
  children: ReactNode;
}) {
  if (!source) return <div className={className}>{children}</div>;
  return (
    <ShownCard movieId={movieId} source={source} className={className}>
      {children}
    </ShownCard>
  );
}

function ShownCard({
  movieId,
  source,
  className,
  children,
}: {
  movieId: number;
  source: EventSource;
  className: string;
  children: ReactNode;
}) {
  const ref = useShownRef<HTMLDivElement>(movieId, source);
  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
