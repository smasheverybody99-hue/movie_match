import type { UseQueryResult } from "@tanstack/react-query";
import type { CSSProperties, ReactNode } from "react";
import { Link } from "react-router-dom";

import { useT } from "../i18n";
import { usePrefersReducedMotion } from "../lib/motion";
import { Logo } from "./Logo";

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

/**
 * A loading state with the mark (docs/ui.md, "Loading"): `spin` (2.4 s a turn) for a whole
 * screen, `pulse` (opacity 1 → 0.45 → 1, 1.6 s) inline. The words are a polite live region,
 * so a change of text is heard. With reduced motion the mark stands still; the words stay.
 */
export function LoadingMark({
  size,
  motion,
  text,
  variant,
  className,
  testId = "loading",
}: {
  size: number;
  motion: "spin" | "pulse";
  text: string;
  variant?: "full" | "compact";
  className?: string;
  testId?: string;
}) {
  const t = useT();
  const reduce = usePrefersReducedMotion();
  return (
    <div
      className={className ? `loading-mark ${className}` : "loading-mark"}
      role="status"
      aria-live="polite"
      data-testid={testId}
    >
      <Logo
        size={size}
        variant={variant}
        title={t("common.loading")}
        className={reduce ? "loading-logo" : `loading-logo logo-${motion}`}
      />
      {/* Keyed by the words: a new message is a new node, not centred text moving (CLS). */}
      <span className="loading-text" key={text}>
        {text}
      </span>
    </div>
  );
}

/**
 * A save button's label (docs/ui.md "Loading", decision A): while `saving`, the pulsing
 * compact mark and "Saving…" take the label's place inside the button. Three layers share
 * one grid cell: the label, an invisible copy of the saving note that keeps the width, and
 * the note itself. So the button is as wide as the wider of the two at all times, and
 * nothing moves when a save starts or ends (CLS 0). The button is not disabled: the
 * caller sets aria-disabled and ignores a second press.
 */
export function SavingLabel({ saving, children }: { saving: boolean; children: ReactNode }) {
  const t = useT();
  const reduce = usePrefersReducedMotion();
  return (
    <span className="saving-stack">
      <span className={saving ? "saving-label is-hidden" : "saving-label"}>{children}</span>
      <span className="saving-note is-hidden" aria-hidden="true">
        <span className="saving-mark-box" />
        {t("common.saving")}
      </span>
      <span className="saving-note" role="status" aria-live="polite" data-testid="saving">
        {saving && (
          <>
            <Logo
              size={20}
              variant="compact"
              title={t("common.loading")}
              className={reduce ? "loading-logo" : "loading-logo logo-pulse"}
            />
            {t("common.saving")}
          </>
        )}
      </span>
    </span>
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
 * - first load -> `loading` if given (a LoadingMark, its own live region), else `skeleton`
 * - failed with nothing cached -> `error` + retry (refetch)
 * - data (fresh, cached, or stale after a failed refetch) -> `children(data)`
 */
export function QueryView<T>({
  query,
  skeleton,
  loading,
  error,
  children,
}: {
  query: UseQueryResult<T>;
  skeleton?: ReactNode;
  loading?: ReactNode;
  error: string;
  children: (data: T) => ReactNode;
}) {
  const t = useT();
  if (query.data !== undefined) return <>{children(query.data)}</>;
  if (query.isPending && query.fetchStatus === "paused") {
    return <ErrorState message={t("common.offlineNoCache")} onRetry={() => void query.refetch()} />;
  }
  if (query.isPending) return loading ?? <Loading>{skeleton}</Loading>;
  return <ErrorState message={error} onRetry={() => void query.refetch()} />;
}
