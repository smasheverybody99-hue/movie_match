import { useEffect, useState } from "react";

import { useT } from "../i18n";
import { clearWrongNotice, useHiddenCards } from "../lib/hiddenCards";
import { useMarkWrong } from "../lib/queries";
import type { EventSource, FeedbackReason, Movie } from "../lib/types";

/** The chips, in the order the user approved (2026-11-17). */
export const REASONS: readonly FeedbackReason[] = ["seen", "not_my_genre", "too_old", "other"];

/**
 * "Not right?" under a recommendation (Phase 5): a reason from four chips, or none. The
 * card leaves this view at once; the press is stored for the alpha and changes nothing
 * the engine picks. If it does not arrive, the card comes back and the page says so
 * (`WrongNoticeToast`).
 */
export function NotRight({ movie, source }: { movie: Movie; source: EventSource }) {
  const t = useT();
  const mark = useMarkWrong();
  const [open, setOpen] = useState(false);
  const send = (reason: FeedbackReason | null) => {
    setOpen(false);
    mark.mutate({ movie, source, reason });
  };

  if (!open) {
    return (
      <button
        type="button"
        className="link-btn not-right"
        aria-label={t("wrong.openLabel", { title: movie.title })}
        aria-expanded={false}
        onClick={() => setOpen(true)}
      >
        {t("wrong.open")}
      </button>
    );
  }
  return (
    <div className="not-right-panel" role="group" aria-label={t("wrong.question")}>
      <p className="not-right-question">{t("wrong.question")}</p>
      <div className="chip-row">
        {REASONS.map((reason) => (
          <button key={reason} type="button" className="chip" onClick={() => send(reason)}>
            {t(`wrong.reason.${reason}`)}
          </button>
        ))}
      </div>
      <div className="not-right-foot">
        <button type="button" className="link-btn" onClick={() => send(null)}>
          {t("wrong.skip")}
        </button>
        <button type="button" className="link-btn" onClick={() => setOpen(false)}>
          {t("wrong.cancel")}
        </button>
      </div>
    </div>
  );
}

const NOTICE_MS = 4000;

/** Once per page that shows NotRight: the thanks, or that the press did not arrive. */
export function WrongNoticeToast() {
  const t = useT();
  const { notice } = useHiddenCards();
  useEffect(() => {
    if (notice === null) return;
    const timer = setTimeout(clearWrongNotice, NOTICE_MS);
    return () => clearTimeout(timer);
  }, [notice]);
  useEffect(() => clearWrongNotice, []);
  if (notice === null) return null;
  return notice.kind === "error" ? (
    <p className="toast" role="alert">
      {t("wrong.error", { title: notice.title })}
    </p>
  ) : (
    <p className="toast" role="status">
      {t("wrong.thanks", { title: notice.title })}
    </p>
  );
}
