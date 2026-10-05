import { useState } from "react";
import { useParams } from "react-router-dom";

import { Bookmark, BookmarkCheck, Gauge } from "lucide-react";

import { FieldError } from "../components/FieldError";
import { Icon } from "../components/Icon";
import { Poster } from "../components/Poster";
import { RateDialog } from "../components/RateDialog";
import { showsLikedAspects } from "../components/RatingInput";
import { EmptyState, ErrorState, Loading, Skeleton } from "../components/States";
import { AxisLegend, TraitAxis, traitLabelKey } from "../components/Traits";
import { useT } from "../i18n";
import { isNotFound } from "../lib/api";
import { imageUrl, releaseYear, score } from "../lib/format";
import { usePrefersReducedMotion } from "../lib/motion";
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
import type { MatchBand, MovieDetail } from "../lib/types";

/** Two columns of three on wide screens. */
const COMPARED = 6;
/** "Why you" names at most this many traits: the match's reasons (top_reasons, n = 3). */
const WHY_TRAITS = 3;

/**
 * The film's strongest traits that "Why you" does not already show, up to COMPARED.
 * The reasons sit on the same axes in the panel above, so they are not repeated.
 */
export function comparedTraits(detail: MovieDetail): TraitKey[] {
  const scores = detail.traits?.scores ?? {};
  const shown = detail.reasons.filter(isTraitKey).slice(0, WHY_TRAITS);
  return [...TRAIT_KEYS]
    .filter((key) => !shown.includes(key))
    .sort((a, b) => (scores[b] ?? 0) - (scores[a] ?? 0))
    .slice(0, COMPARED);
}

/**
 * The user's taste scores, or null while they load or without a taste profile: the API
 * sends `scores: {}` then, and a missing score must not be drawn as a "you" dot at 0.
 */
function tasteScores(scores: Record<string, number> | undefined): Record<string, number> | null {
  return scores && Object.keys(scores).length > 0 ? scores : null;
}

/**
 * The backdrop across the full width; the gradient runs into the page at the bottom and
 * on the left. Without a backdrop, the poster blurred; without either, a plain surface.
 */
function Hero({ detail }: { detail: MovieDetail }) {
  const backdrop = imageUrl(detail.backdrop_path, "w1280");
  const poster = imageUrl(detail.poster_path, "w342");
  return (
    <div className="film-hero" data-testid="film-hero">
      {backdrop ? (
        <img
          className="film-hero-img"
          src={backdrop}
          srcSet={`${imageUrl(detail.backdrop_path, "w780")} 780w, ${backdrop} 1280w`}
          sizes="100vw"
          alt=""
          fetchPriority="high"
        />
      ) : (
        poster && <img className="film-hero-img film-hero-blur" src={poster} alt="" />
      )}
    </div>
  );
}

/** Year, runtime and genres as neutral chips. */
function Tags({ detail }: { detail: MovieDetail }) {
  const t = useT();
  const year = releaseYear(detail);
  const tags = [
    ...(year ? [year] : []),
    ...(detail.runtime_minutes ? [t("common.minutes", { n: detail.runtime_minutes })] : []),
    ...detail.genres,
  ];
  if (!tags.length) return null;
  return (
    <ul className="tags">
      {tags.map((tag) => (
        <li key={tag}>{tag}</li>
      ))}
    </ul>
  );
}

/**
 * The panel's heading, which the sentence under it completes: the band itself ("STRONG
 * MATCH" red, "GOOD MATCH" neutral; FR-5, TZ 1.13), or a neutral kicker without one.
 */
function Kicker({ band }: { band: MatchBand | null }) {
  const t = useT();
  return (
    <h2 className={band ? `why-kicker why-kicker-${band}` : "why-kicker"} id="why-title">
      {band ? t(band === "strong" ? "band.strong" : "band.good") : t("movie.whyKicker")}
    </h2>
  );
}

/**
 * "Why you": the band as the panel's heading, the sentence and up to three reasons on
 * their axes, read as one statement ("STRONG MATCH" -> "It keeps you guessing..."). No
 * number, no ring (FR-5, TZ 1.13): the sentence is the main signal.
 * The sentence's slot is sized before the text arrives, so nothing below it moves; the
 * text then fades in over 200 ms (not with reduced motion). With at most one reason the
 * panel is one column (.why-solo): the axis, if any, under the sentence with its key, so
 * the panel is as tall as its content. No reason: the "suits you overall" sentence at the
 * same size, without axes.
 */
function Why({ detail }: { detail: MovieDetail }) {
  const t = useT();
  const reduce = usePrefersReducedMotion();
  const dna = useDna();
  const reasons = detail.reasons.filter(isTraitKey).slice(0, WHY_TRAITS);
  // With no reason the API writes no text (explain.py), so there is nothing to ask for.
  const asks = detail.match !== null && reasons.length > 0;
  const explanation = useExplanation(detail.id, asks);
  if (detail.match === null) {
    return (
      <section className="panel why why-solo" aria-labelledby="why-title">
        <Kicker band={null} />
        <p className="muted" style={{ margin: 0 }}>
          {t("movie.noMatch")}
        </p>
      </section>
    );
  }
  const sentence = reasons.length
    ? (explanation.data?.text ??
      t("movie.whyYouFallback", { traits: reasons.map((key) => t(traitLabelKey(key))).join(", ") }))
    : t("movie.whyYouGeneral");
  const film = detail.traits?.scores ?? {};
  const taste = tasteScores(dna.data?.scores);
  return (
    <section className={reasons.length > 1 ? "panel why" : "panel why why-solo"} aria-labelledby="why-title">
      <div className="why-main">
        <Kicker band={detail.band} />
        {/* Space is reserved only while text can still arrive; otherwise it fits the sentence. */}
        <div className={asks ? "why-slot why-reserve" : "why-slot"} data-testid="why-slot">
          {asks && explanation.isPending ? (
            <Loading>
              <div className="why-skel-lines" data-testid="explanation-skeleton">
                <Skeleton className="why-skel" />
                <Skeleton className="why-skel" />
                <Skeleton className="why-skel" style={{ width: "60%" }} />
              </div>
            </Loading>
          ) : (
            <p className={reduce ? "why-text" : "why-text why-in"}>{sentence}</p>
          )}
        </div>
      </div>
      {reasons.length > 0 && (
        <div className="why-traits" data-testid="why-traits">
          <AxisLegend />
          {reasons.map((key) => (
            <TraitAxis key={key} trait={key} taste={taste ? (taste[key] ?? 0) : null} film={film[key] ?? 0} />
          ))}
        </div>
      )}
    </section>
  );
}

/** True when "Why you" draws axes (and so carries the page's one legend). */
function whyHasAxes(detail: MovieDetail): boolean {
  return detail.match !== null && detail.reasons.some(isTraitKey);
}

function Compare({ detail }: { detail: MovieDetail }) {
  const t = useT();
  const dna = useDna();
  const film = detail.traits?.scores;
  if (!film) return <p className="muted">{t("movie.traitsPending")}</p>;
  const taste = tasteScores(dna.data?.scores);
  return (
    <section className="panel compare" aria-labelledby="compare-title">
      {/* "Other" only when Why you shows reasons: otherwise these are the film's top traits. */}
      <h2 className="eyebrow" id="compare-title">
        {whyHasAxes(detail) ? t("movie.compareOther") : t("movie.compareTop")}
      </h2>
      {!whyHasAxes(detail) && <AxisLegend />}
      <div className="compare-axes">
        {comparedTraits(detail).map((key) => (
          <TraitAxis key={key} trait={key} taste={taste ? (taste[key] ?? 0) : null} film={film[key] ?? 0} />
        ))}
      </div>
    </section>
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
        <FieldError>{t("movie.rateError")}</FieldError>
      )}
      {change.isError && (
        <FieldError>{t("movie.listError")}</FieldError>
      )}
      <div className="film-actions">
        <button type="button" className="btn btn-secondary" onClick={() => setRating(true)} disabled={rate.isPending}>
          <Icon as={Gauge} /> {mine ? t("movie.yourRating", { score: score(mine.score) }) : t("movie.rate")}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          aria-pressed={saved}
          onClick={() =>
            change.mutate(saved ? { kind: "remove", movieId: detail.id } : { kind: "add", movie: detail })
          }
        >
          <Icon as={saved ? BookmarkCheck : Bookmark} /> {saved ? t("movie.onList") : t("movie.saveToList")}
        </button>
      </div>
      {rating && (
        <RateDialog
          title={detail.title}
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

/** The page's shape while it loads: hero, poster and title, the "Why you" panel. */
function MovieSkeleton() {
  return (
    <Loading>
      <div className="film-hero" />
      <div className="film-head">
        <Skeleton className="poster" />
        <div className="film-head-text" style={{ flex: 1 }}>
          <Skeleton className="skeleton-line" style={{ height: 28, width: "70%" }} />
          <Skeleton className="skeleton-line" style={{ width: "40%" }} />
        </div>
      </div>
      <div className="panel why why-solo">
        <div className="why-main">
          <Skeleton className="why-kicker why-kicker-skel" />
          <div className="why-slot">
            <Skeleton className="why-skel" />
            <Skeleton className="why-skel" style={{ width: "60%" }} />
          </div>
        </div>
      </div>
    </Loading>
  );
}

/** /movie/:id — backdrop hero, then the match and "why you" above the overview (docs/ui.md, 5). */
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
  return (
    <article className="film-page">
      <Hero detail={detail} />
      <header className="film-head">
        <Poster title={detail.title} path={detail.poster_path} describe eager />
        <div className="film-head-text">
          <h1 className="film-title">{detail.title}</h1>
          <Tags detail={detail} />
          <Actions detail={detail} />
        </div>
      </header>

      <Why detail={detail} />

      {(detail.overview || detail.director || detail.cast.length > 0) && (
        <section className="film-about" aria-labelledby="overview-title">
          <h2 className="eyebrow" id="overview-title">
            {t("movie.overview")}
          </h2>
          <div className="film-about-body">
            {detail.overview && <p className="film-overview">{detail.overview}</p>}
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
          </div>
        </section>
      )}

      <Compare detail={detail} />
    </article>
  );
}
