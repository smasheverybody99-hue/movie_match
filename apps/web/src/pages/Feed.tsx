import { ChevronLeft, ChevronRight, Compass, Heart, Sparkles, Timer, type LucideIcon } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { Hero, HERO_COUNT } from "../components/Hero";
import { Icon } from "../components/Icon";
import { MovieCard } from "../components/MovieCard";
import { useQuickActions } from "../components/QuickActions";
import { CardRowSkeleton, EmptyState, Loading, QueryView, Skeleton } from "../components/States";
import { useT } from "../i18n";
import { usePrefersReducedMotion } from "../lib/motion";
import { useRecommendations } from "../lib/queries";
import type { Section, SectionKey } from "../lib/types";

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

function FeedSkeleton() {
  return (
    <>
      {/* The hero's box, so the rows do not jump when it arrives. */}
      <div className="home-hero" />
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
 * / — the hero (the top 5 of "For you"), then sections with reasons (design system, home
 * feed); the For you row continues from the 6th film, so nothing shows twice. A section without items is not rendered at all; the band on each card is the
 * API's, never recomputed here.
 */
export default function Feed() {
  const t = useT();
  const query = useRecommendations();
  const { saved, toggleSave, quickFor, overlay } = useQuickActions();

  return (
    <>
      <h1 className="visually-hidden">{t("nav.home")}</h1>
      <QueryView query={query} skeleton={<FeedSkeleton />} error={t("feed.error")}>
        {(data) => {
          if (data.status === "not_enough_data") {
            // A cached "rate N more" can be older than the latest ratings: while the feed is
            // being fetched again, wait for it instead of acting on old numbers (F3 item 1).
            if (query.isFetching) return <Loading><FeedSkeleton /></Loading>;
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
          const forYou = sections.find((s) => s.key === "for_you");
          const heroItems = forYou ? forYou.items.slice(0, HERO_COUNT) : [];
          // The hero's films are not repeated in the For you row: it starts at the 6th.
          const rows = sections
            .map((s) => (s.key === "for_you" ? { ...s, items: s.items.slice(HERO_COUNT) } : s))
            .filter((s) => s.items.length > 0);
          if (sections.length === 0) {
            return (
              <EmptyState
                message={t("feed.empty")}
                action={{ label: t("feed.emptyCta"), to: "/search" }}
              />
            );
          }
          return (
            <>
              {heroItems.length > 0 && <Hero items={heroItems} saved={saved} onToggleSave={toggleSave} />}
              {rows.map((section) => (
            <section key={section.key} className="feed-section" aria-labelledby={`section-${section.key}`}>
              <h2 className="section-title" id={`section-${section.key}`}>
                <SectionTitle section={section} />
              </h2>
              <Row>
                {section.items.map((item) => (
                  <li key={item.movie.id}>
                    <MovieCard movie={item.movie} band={item.band} quick={quickFor(item.movie)} />
                  </li>
                ))}
              </Row>
            </section>
              ))}
            </>
          );
        }}
      </QueryView>
      {overlay}
    </>
  );
}
