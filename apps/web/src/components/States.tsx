import type { UseQueryResult } from "@tanstack/react-query";
import type { CSSProperties, ReactNode } from "react";
import { Link } from "react-router-dom";

import { useT } from "../i18n";

/** Grey blocks in the shape of the content. Never a spinner (design system, states). */
export function Skeleton({ className = "", style }: { className?: string; style?: CSSProperties }) {
  return <div className={`skeleton ${className}`} style={style} aria-hidden="true" />;
}

/** Wraps a screen's skeleton so assistive tech hears "loading" once, not a pile of divs. */
export function Loading({ children }: { children: ReactNode }) {
  const t = useT();
  return (
    <div role="status" aria-busy="true" data-testid="loading">
      <span className="visually-hidden">{t("common.loading")}</span>
      {children}
    </div>
  );
}

export function CardRowSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="row-scroll">
      {Array.from({ length: count }, (_, i) => (
        <div key={i}>
          <Skeleton className="poster" />
          <Skeleton className="skeleton-line" style={{ width: "80%" }} />
        </div>
      ))}
    </div>
  );
}

/** What happened + one way out. Never a status code or a raw error message. */
export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  const t = useT();
  return (
    <div className="state" role="alert">
      <p>{message}</p>
      <button type="button" className="btn btn-secondary" onClick={onRetry}>
        {t("common.retry")}
      </button>
    </div>
  );
}

/** One sentence of why, one action. */
export function EmptyState({
  message,
  action,
}: {
  message: string;
  action?: { label: string; to: string } | { label: string; onClick: () => void };
}) {
  return (
    <div className="state" data-testid="empty">
      <p>{message}</p>
      {action &&
        ("to" in action ? (
          <Link to={action.to} className="btn btn-primary">
            {action.label}
          </Link>
        ) : (
          <button type="button" className="btn btn-primary" onClick={action.onClick}>
            {action.label}
          </button>
        ))}
    </div>
  );
}

/**
 * The four states of a screen from one query:
 * - offline with nothing cached -> the offline message, with a retry
 * - first load -> `skeleton`
 * - failed with nothing cached -> `error` + retry (refetch)
 * - data (fresh, cached, or stale after a failed refetch) -> `children(data)`
 */
export function QueryView<T>({
  query,
  skeleton,
  error,
  children,
}: {
  query: UseQueryResult<T>;
  skeleton: ReactNode;
  error: string;
  children: (data: T) => ReactNode;
}) {
  const t = useT();
  if (query.data !== undefined) return <>{children(query.data)}</>;
  if (query.isPending && query.fetchStatus === "paused") {
    return <ErrorState message={t("common.offlineNoCache")} onRetry={() => void query.refetch()} />;
  }
  if (query.isPending) return <Loading>{skeleton}</Loading>;
  return <ErrorState message={error} onRetry={() => void query.refetch()} />;
}
