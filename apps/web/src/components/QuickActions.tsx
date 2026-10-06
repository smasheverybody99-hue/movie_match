import { useState, type ReactNode } from "react";

import { useT } from "../i18n";
import { useRate, useRatings, useWatchlist, useWatchlistChange } from "../lib/queries";
import type { Movie } from "../lib/types";
import type { QuickActions } from "./MovieCard";
import { RateDialog } from "./RateDialog";
import { showsLikedAspects } from "./RatingInput";

/** The rating dialog for a card's quick Rate; it asks for the current score only when open. */
function QuickRate({ movie, onSave, onClose }: {
  movie: Movie;
  onSave: (value: number, liked: string[]) => void;
  onClose: () => void;
}) {
  const ratings = useRatings();
  const current = ratings.data?.find((r) => r.movie_id === movie.id)?.score ?? null;
  return <RateDialog key={current ?? "none"} title={movie.title} current={current} onSave={onSave} onClose={onClose} />;
}

/**
 * The poster cards' quick Rate and Save, wherever the cards are (Home rows, search
 * results): one rating dialog, the watchlist toggle, and a toast when either fails.
 * `quickFor(movie)` goes to MovieCard's `quick`; render `overlay` once on the page.
 */
export function useQuickActions(): {
  saved: ReadonlySet<number>;
  toggleSave: (movie: Movie, isSaved: boolean) => void;
  quickFor: (movie: Movie) => QuickActions;
  overlay: ReactNode;
} {
  const t = useT();
  const watchlist = useWatchlist();
  const change = useWatchlistChange();
  const rate = useRate();
  const [rating, setRating] = useState<Movie | null>(null);
  const saved = new Set(watchlist.data?.map((item) => item.movie.id) ?? []);
  const toggleSave = (movie: Movie, isSaved: boolean) =>
    change.mutate(isSaved ? { kind: "remove", movieId: movie.id } : { kind: "add", movie });
  const quickFor = (movie: Movie): QuickActions => {
    const isSaved = saved.has(movie.id);
    return { saved: isSaved, onRate: () => setRating(movie), onToggleSave: () => toggleSave(movie, isSaved) };
  };
  const overlay = (
    <>
      {rating && (
        <QuickRate
          movie={rating}
          onClose={() => setRating(null)}
          onSave={(value, liked) => {
            rate.mutate({ movie_id: rating.id, score: value, liked_aspects: showsLikedAspects(value) ? liked : [] });
            setRating(null);
          }}
        />
      )}
      {(rate.isError || change.isError) && (
        <p className="toast" role="alert">
          {rate.isError ? t("movie.rateError") : t("movie.listError")}
        </p>
      )}
    </>
  );
  return { saved, toggleSave, quickFor, overlay };
}
