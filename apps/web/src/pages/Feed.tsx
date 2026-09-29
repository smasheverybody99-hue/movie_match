import { Navigate } from "react-router-dom";

import { MovieCard } from "../components/MovieCard";
import { CardRowSkeleton, EmptyState, QueryView, Skeleton } from "../components/States";
import { useT } from "../i18n";
import { useRecommendations } from "../lib/queries";
import type { Section } from "../lib/types";

function SectionTitle({ section }: { section: Section }) {
  const t = useT();
  if (section.key === "because_you_loved") {
    return <>{t("feed.section.because_you_loved", { title: section.seed?.title ?? "" })}</>;
  }
  return <>{t(`feed.section.${section.key}`)}</>;
}

function FeedSkeleton() {
  return (
    <>
      {[0, 1, 2].map((i) => (
        <div key={i}>
          <Skeleton className="skeleton-line" style={{ width: 180, height: 16, margin: "24px 0 12px" }} />
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
              <ul className="row-scroll" style={{ listStyle: "none", margin: 0, padding: 0 }}>
                {section.items.map((item) => (
                  <li key={item.movie.id}>
                    <MovieCard movie={item.movie} match={item.match} />
                  </li>
                ))}
              </ul>
            </section>
          ));
        }}
      </QueryView>
    </>
  );
}
