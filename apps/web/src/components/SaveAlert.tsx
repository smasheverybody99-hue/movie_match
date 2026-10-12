import { useT } from "../i18n";
import type { UnsavedRating } from "../lib/ratingQueue";

/**
 * Scores the server has not taken: named, with Try again. Fixed above the foot bar (or the
 * bottom navigation), so it appears without moving the page (CLS 0); it stays until the
 * scores are saved. Used in onboarding and in the app shell, where queued scores keep
 * being sent after onboarding.
 */
export function SaveAlert({ failed, onRetry }: { failed: readonly UnsavedRating[]; onRetry: () => void }) {
  const t = useT();
  if (failed.length === 0) return null;
  return (
    <div className="save-alert" role="alert">
      <span>{t("onboarding.rate.unsaved", { titles: failed.map((u) => u.title).join(", ") })}</span>
      <button type="button" className="btn btn-secondary btn-sm" onClick={onRetry}>
        {t("common.retry")}
      </button>
    </div>
  );
}
