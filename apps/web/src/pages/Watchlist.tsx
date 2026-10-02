import { CircleCheck, ListVideo, Timer, type LucideIcon } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { FieldError } from "../components/FieldError";
import { Icon } from "../components/Icon";
import { Poster } from "../components/Poster";
import { EmptyState, QueryView, Skeleton } from "../components/States";
import { useT, type MessageKey } from "../i18n";
import { movieMeta } from "../lib/format";
import { useWatchlist, useWatchlistChange } from "../lib/queries";
import type { WatchlistItem } from "../lib/types";

/**
 * Groups computed from what every item already carries. The trait-based smart groups
 * (Challenging, Light, Hidden gems) are Phase 8 (`app/services/watchlist_groups.py`,
 * TZ §2 item 12); these three need no traits.
 */
export type Group = "next" | "short" | "watched";

export const GROUPS: { key: Group; label: MessageKey; icon: LucideIcon }[] = [
  { key: "next", label: "watchlist.group.next", icon: ListVideo },
  { key: "short", label: "watchlist.group.short", icon: Timer },
  { key: "watched", label: "watchlist.group.watched", icon: CircleCheck },
];

export function inGroup(item: WatchlistItem, group: Group): boolean {
  switch (group) {
    case "next":
      return item.watched_at === null;
    case "short":
      return item.watched_at === null && item.movie.runtime_minutes !== null && item.movie.runtime_minutes <= 90;
    case "watched":
      return item.watched_at !== null;
  }
}

function ListSkeleton() {
  return (
    <ul className="list">
      {Array.from({ length: 5 }, (_, i) => (
        <li key={i} className="list-row">
          <Skeleton className="poster" style={{ width: 52 }} />
          <div style={{ flex: 1 }}>
            <Skeleton className="skeleton-line" style={{ width: "60%" }} />
            <Skeleton className="skeleton-line" style={{ width: "35%" }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

type Change = { kind: "watched" | "remove"; movieId: number };

function Row({ item, onChange }: { item: WatchlistItem; onChange: (change: Change) => void }) {
  const t = useT();
  const { movie } = item;
  return (
    <li className="list-row">
      <Poster title={movie.title} path={movie.poster_path} size="w185" />
      <div className="list-row-meta">
        <Link to={`/movie/${movie.id}`} className="list-row-title">
          {movie.title}
        </Link>
        <span className="meta">{movieMeta(movie, t)}</span>
      </div>
      {item.match !== null && (
        <span className="match" aria-label={t("common.matchLabel", { n: item.match })}>
          {item.match}%
        </span>
      )}
      <div className="row-actions">
        {item.watched_at === null && (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            aria-label={t("watchlist.markWatchedLabel", { title: movie.title })}
            onClick={() => onChange({ kind: "watched", movieId: movie.id })}
          >
            {t("watchlist.markWatched")}
          </button>
        )}
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          aria-label={t("watchlist.removeLabel", { title: movie.title })}
          onClick={() => onChange({ kind: "remove", movieId: movie.id })}
        >
          {t("watchlist.remove")}
        </button>
      </div>
    </li>
  );
}

/** /watchlist — group chips on top, rows below; marking watched moves a row out of "Watch next". */
export default function Watchlist() {
  const t = useT();
  const query = useWatchlist();
  const change = useWatchlistChange();
  const [group, setGroup] = useState<Group>("next");

  return (
    <>
      <h1 className="screen-title">{t("watchlist.title")}</h1>
      <QueryView query={query} skeleton={<ListSkeleton />} error={t("watchlist.error")}>
        {(items) => {
          if (items.length === 0) {
            return (
              <EmptyState message={t("watchlist.empty")} action={{ label: t("watchlist.emptyCta"), to: "/search" }} />
            );
          }
          const shown = items.filter((item) => inGroup(item, group));
          return (
            <>
              <div className="chip-scroll" role="group" aria-label={t("watchlist.groups")} style={{ marginBottom: 12 }}>
                {GROUPS.map((g) => (
                  <button
                    key={g.key}
                    type="button"
                    className="chip"
                    aria-pressed={group === g.key}
                    onClick={() => setGroup(g.key)}
                  >
                    <Icon as={g.icon} size={16} /> {t(g.label)}
                  </button>
                ))}
              </div>
              {change.isError && (
                <FieldError>{t("watchlist.actionError")}</FieldError>
              )}
              {shown.length === 0 ? (
                <p className="muted">{t("watchlist.emptyGroup")}</p>
              ) : (
                <ul className="list">
                  {shown.map((item) => (
                    <Row key={item.movie.id} item={item} onChange={(c) => change.mutate(c)} />
                  ))}
                </ul>
              )}
            </>
          );
        }}
      </QueryView>
    </>
  );
}
