import { ChevronLeft, ChevronRight, Compass, Heart, Sparkles, Timer, type LucideIcon } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { Icon } from "../components/Icon";
import { MovieCard } from "../components/MovieCard";
import { RateDialog } from "../components/RateDialog";
import { showsLikedAspects } from "../components/RatingInput";
import { CardRowSkeleton, EmptyState, QueryView, Skeleton } from "../components/States";
import { useT } from "../i18n";
import { usePrefersReducedMotion } from "../lib/motion";
import { useRate, useRatings, useRecommendations, useWatchlist, useWatchlistChange } from "../lib/queries";
import type { Movie, Section, SectionKey } from "../lib/types";

/** A neutral icon before each row's title (docs/ui.md, 2). */
const SECTION_ICONS: Record<SectionKey, LucideIcon> = {
  for_you: Sparkles,
  because_you_loved: Heart,
  under_90: Timer,
  outside_usual: Compass,
};

function SectionTitle({ section }: { section: Section }) {
  const t = useT();
  const text =
    section.key === "because_you_loved"
      ? t("feed.section.because_you_loved", { title: section.seed?.title ?? "" })
      : t(`feed.section.${section.key}`);
  return (
    <>
      <Icon as={SECTION_ICONS[section.key]} />
      {text}
    </>
  );
}

/**
 * One horizontal row of posters. On wide screens with a mouse, previous / next buttons
 * scroll it by most of its width (no wheel needed) and hide at either end; on touch the
 * row is swiped and the buttons never show. Reduced motion: the jump is instant.
 */
function Row({ children }: { children: ReactNode }) {
  const t = useT();
  const reduce = usePrefersReducedMotion();
  const ref = useRef<HTMLUListElement>(null);
  const [edges, setEdges] = useState({ start: true, end: true });
  useEffect(() => {
    const list = ref.current;
    if (!list) return;
    const update = () =>
      setEdges({
        start: list.scrollLeft <= 1,
        end: list.scrollLeft + list.clientWidth >= list.scrollWidth - 1,
      });
    update();
    list.addEventListener("scroll", update, { passive: true });
    const resize = typeof ResizeObserver === "function" ? new ResizeObserver(update) : null;
    resize?.observe(list);
    return () => {
      list.removeEventListener("scroll", update);
      resize?.disconnect();
    };
  }, []);
  const scroll = (direction: 1 | -1) => {
    const list = ref.current;
    list?.scrollBy({ left: direction * list.clientWidth * 0.8, behavior: reduce ? "auto" : "smooth" });
  };
  return (
    <div className="row">
      <button
        type="button"
        className="row-arrow prev"
        hidden={edges.start}
        aria-label={t("feed.scrollPrev")}
        onClick={() => scroll(-1)}
      >
        <Icon as={ChevronLeft} />
      </button>
      <ul className="row-scroll" ref={ref}>
        {children}
      </ul>
      <button
        type="button"
        className="row-arrow next"
        hidden={edges.end}
        aria-label={t("feed.scrollNext")}
        onClick={() => scroll(1)}
      >
        <Icon as={ChevronRight} />
      </button>
    </div>
  );
}

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

function FeedSkeleton() {
  return (
    <>
      {[0, 1, 2].map((i) => (
        <div key={i} className="feed-section">
          <Skeleton className="section-title skeleton-title" />
          <CardRowSkeleton />
        </div>
      ))}
    </>
  );
}

/**
 * / — sections with reasons (design system, home feed). A section without items is not
 * rendered at all; the match on each card is the API's number, never recomputed here.
 */
export default function Feed() {
  const t = useT();
  const query = useRecommendations();
  const watchlist = useWatchlist();
  const change = useWatchlistChange();
  const rate = useRate();
  const [rating, setRating] = useState<Movie | null>(null);
  const saved = new Set(watchlist.data?.map((item) => item.movie.id) ?? []);

  return (
    <>
      <h1 className="visually-hidden">{t("nav.home")}</h1>
      <QueryView query={query} skeleton={<FeedSkeleton />} error={t("feed.error")}>
        {(data) => {
          if (data.status === "not_enough_data") {
            // A user who has rated nothing yet belongs in onboarding, not on an empty feed.
            if (data.ratings_needed >= 10) return <Navigate to="/onboarding" replace />;
            return (
              <EmptyState
                message={t("feed.notEnough", { n: data.ratings_needed })}
                action={{ label: t("feed.notEnoughCta"), to: "/onboarding" }}
              />
            );
          }
          const sections = data.sections.filter((s) => s.items.length > 0);
          if (sections.length === 0) {
            return (
              <EmptyState
                message={t("feed.empty")}
                action={{ label: t("feed.emptyCta"), to: "/search" }}
              />
            );
          }
          return sections.map((section) => (
            <section key={section.key} className="feed-section" aria-labelledby={`section-${section.key}`}>
              <h2 className="section-title" id={`section-${section.key}`}>
                <SectionTitle section={section} />
              </h2>
              <Row>
                {section.items.map((item) => {
                  const isSaved = saved.has(item.movie.id);
                  return (
                    <li key={item.movie.id}>
                      <MovieCard
                        movie={item.movie}
                        match={item.match}
                        quick={{
                          saved: isSaved,
                          onRate: () => setRating(item.movie),
                          onToggleSave: () =>
                            change.mutate(
                              isSaved
                                ? { kind: "remove", movieId: item.movie.id }
                                : { kind: "add", movie: item.movie },
                            ),
                        }}
                      />
                    </li>
                  );
                })}
              </Row>
            </section>
          ));
        }}
      </QueryView>
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
}
