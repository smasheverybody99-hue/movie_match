import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Dialog } from "../components/Dialog";
import { Poster } from "../components/Poster";
import { RatingInput, showsLikedAspects } from "../components/RatingInput";
import { EmptyState, ErrorState, Loading, Skeleton } from "../components/States";
import { MatchRing, TraitCompare, traitLabelKey } from "../components/Traits";
import { useT } from "../i18n";
import { isNotFound } from "../lib/api";
import { imageUrl, movieMeta, score } from "../lib/format";
import {
  useDna,
  useExplanation,
  useMovie,
  useRate,
  useRatings,
  useWatchlist,
  useWatchlistChange,
} from "../lib/queries";
import { isTraitKey, TRAIT_KEYS, type TraitKey } from "../lib/traits";
import type { MovieDetail } from "../lib/types";

const COMPARED = 5;

/** The match's reasons first, then the film's strongest traits, up to COMPARED. */
export function comparedTraits(detail: MovieDetail): TraitKey[] {
  const scores = detail.traits?.scores ?? {};
  const reasons = detail.reasons.filter(isTraitKey);
  const rest = [...TRAIT_KEYS]
    .filter((key) => !reasons.includes(key))
    .sort((a, b) => (scores[b] ?? 0) - (scores[a] ?? 0));
  return [...reasons, ...rest].slice(0, COMPARED);
}

function Why({ detail }: { detail: MovieDetail }) {
  const t = useT();
  const explanation = useExplanation(detail.id, detail.match !== null);
  if (detail.match === null) {
    return <p className="why-text muted">{t("movie.noMatch")}</p>;
  }
  const fallback = t("movie.whyYouFallback", {
    traits: detail.reasons
      .filter(isTraitKey)
      .map((key) => t(traitLabelKey(key)))
      .join(", "),
  });
  return (
    <div className="why">
      <MatchRing value={detail.match} />
      <div style={{ flex: 1 }}>
        <p className="eyebrow">{t("movie.whyYou")}</p>
        {explanation.isPending ? (
          <Loading>
            <div data-testid="explanation-skeleton">
              <Skeleton className="skeleton-line" />
              <Skeleton className="skeleton-line" style={{ width: "70%" }} />
            </div>
          </Loading>
        ) : (
          <p className="why-text">{explanation.data?.text ?? fallback}</p>
        )}
      </div>
    </div>
  );
}

function Compare({ detail }: { detail: MovieDetail }) {
  const t = useT();
  const dna = useDna();
  const film = detail.traits?.scores;
  if (!film) return <p className="muted">{t("movie.traitsPending")}</p>;
  const taste = dna.data?.scores ?? {};
  return (
    <section className="panel" aria-labelledby="compare-title">
      <h2 className="eyebrow" id="compare-title">
        {t("movie.compareTitle")}
      </h2>
      {comparedTraits(detail).map((key) => (
        <TraitCompare key={key} trait={key} taste={taste[key] ?? 0} film={film[key] ?? 0} />
      ))}
    </section>
  );
}

function RateDialog({
  detail,
  current,
  onSave,
  onClose,
}: {
  detail: MovieDetail;
  current: number | null;
  onSave: (value: number, aspects: TraitKey[]) => void;
  onClose: () => void;
}) {
  const t = useT();
  const [value, setValue] = useState(current ?? 7);
  const [aspects, setAspects] = useState<TraitKey[]>([]);
  return (
    <Dialog title={t("movie.rateDialog", { title: detail.title })} onClose={onClose}>
      <RatingInput value={value} onChange={setValue} aspects={aspects} onAspectsChange={setAspects} />
      <div className="foot-actions" style={{ marginTop: 16 }}>
        <button type="button" className="btn btn-ghost" onClick={onClose}>
          {t("common.cancel")}
        </button>
        <button type="button" className="btn btn-primary" onClick={() => onSave(value, aspects)}>
          {t("movie.rateSave")}
        </button>
      </div>
    </Dialog>
  );
}

function Actions({ detail }: { detail: MovieDetail }) {
  const t = useT();
  const ratings = useRatings();
  const watchlist = useWatchlist();
  const change = useWatchlistChange();
  const rate = useRate();
  const [rating, setRating] = useState(false);
  const mine = ratings.data?.find((r) => r.movie_id === detail.id) ?? null;
  const saved = watchlist.data?.some((i) => i.movie.id === detail.id) ?? false;

  return (
    <>
      {mine && (
        <p className="meta" data-testid="my-rating">
          {t("movie.yourRating", { score: score(mine.score) })}
        </p>
      )}
      {rate.isError && (
        <p className="field-error" role="alert">
          {t("movie.rateError")}
        </p>
      )}
      {change.isError && (
        <p className="field-error" role="alert">
          {t("movie.listError")}
        </p>
      )}
      <div className="film-actions">
        <button type="button" className="btn btn-primary" onClick={() => setRating(true)} disabled={rate.isPending}>
          ★ {mine ? t("movie.yourRating", { score: score(mine.score) }) : t("movie.rate")}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          aria-pressed={saved}
          onClick={() =>
            change.mutate(saved ? { kind: "remove", movieId: detail.id } : { kind: "add", movie: detail })
          }
        >
          🔖 {saved ? t("movie.onList") : t("movie.saveToList")}
        </button>
      </div>
      {rating && (
        <RateDialog
          detail={detail}
          current={mine?.score ?? null}
          onClose={() => setRating(false)}
          onSave={(value, aspects) => {
            // Optimistic: the new score shows at once and rolls back if the request fails.
            rate.mutate({
              movie_id: detail.id,
              score: value,
              liked_aspects: showsLikedAspects(value) ? aspects : [],
            });
            setRating(false);
          }}
        />
      )}
    </>
  );
}

function MovieSkeleton() {
  return (
    <Loading>
      <Skeleton style={{ height: 200, borderRadius: 0 }} />
      <div className="film-head">
        <Skeleton className="poster" style={{ width: 96 }} />
        <div style={{ flex: 1 }}>
          <Skeleton className="skeleton-line" style={{ height: 22, width: "70%" }} />
          <Skeleton className="skeleton-line" style={{ width: "40%" }} />
        </div>
      </div>
      <Skeleton style={{ height: 110 }} />
    </Loading>
  );
}

/** /movie/:id — match and "why you" above the overview (design system, film page). */
export default function MoviePage() {
  const t = useT();
  const params = useParams();
  const id = Number(params.id);
  const query = useMovie(Number.isInteger(id) ? id : 0);

  if (!Number.isInteger(id) || id <= 0 || isNotFound(query.error)) {
    return <EmptyState message={t("movie.notFound")} action={{ label: t("movie.notFoundCta"), to: "/" }} />;
  }
  if (query.data === undefined) {
    if (query.isPending && query.fetchStatus !== "paused") return <MovieSkeleton />;
    return (
      <ErrorState
        message={query.fetchStatus === "paused" ? t("common.offlineNoCache") : t("movie.error")}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const detail = query.data;
  const backdrop = imageUrl(detail.backdrop_path, "w1280");
  return (
    <article>
      <div className={backdrop ? "backdrop" : "backdrop empty"}>{backdrop && <img src={backdrop} alt="" fetchPriority="high" />}</div>
      <div className="film-head">
        <Poster title={detail.title} path={detail.poster_path} describe eager />
        <div>
          <h1 className="film-title">{detail.title}</h1>
          <p className="meta" style={{ margin: "4px 0 0" }}>
            {[movieMeta(detail, t), detail.genres.join(", ")].filter(Boolean).join(" · ")}
          </p>
        </div>
      </div>

      <div className="film-grid">
        <div style={{ display: "grid", gap: 16 }}>
          <section className="panel panel-elev">
            <Why detail={detail} />
          </section>
          <Compare detail={detail} />
        </div>
        <div style={{ display: "grid", gap: 16 }}>
          {detail.overview && (
            <section>
              <h2 className="eyebrow">{t("movie.overview")}</h2>
              <p style={{ margin: 0 }}>{detail.overview}</p>
            </section>
          )}
          {(detail.director || detail.cast.length > 0) && (
            <dl className="facts">
              {detail.director && (
                <>
                  <dt>{t("movie.director")}</dt>
                  <dd>{detail.director}</dd>
                </>
              )}
              {detail.cast.length > 0 && (
                <>
                  <dt>{t("movie.cast")}</dt>
                  <dd>{detail.cast.join(", ")}</dd>
                </>
              )}
            </dl>
          )}
          <p>
            <Link to="/" className="link-btn">
              {t("nav.back")}
            </Link>
          </p>
        </div>
      </div>
      <Actions detail={detail} />
    </article>
  );
}
