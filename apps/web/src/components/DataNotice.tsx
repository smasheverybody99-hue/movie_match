import type { ReactNode } from "react";

import { useT } from "../i18n";
import { useAuth } from "../lib/auth";
import { useAcceptDataNotice, useMe } from "../lib/queries";
import { ErrorState, SavingLabel } from "./States";

/**
 * The closed alpha's data notice (ADR 0004, the free-tier exception of 2026-11-17).
 *
 * The assistant and the explanations run on Gemini's free tier, where Google may use what
 * it is sent. Every tester accepts this once after signing in, before any screen that
 * could send something; the acceptance is stored on the server (users.data_notice_accepted_at).
 * Declining signs the viewer out (user decision, 2026-11-17). When the API stops asking
 * for it (DATA_NOTICE_REQUIRED=false, on the paid tier) nobody sees it.
 *
 * A browser that has seen this account accept goes straight through while /me loads,
 * so the notice costs a round trip only the first time.
 */
const STORAGE_KEY = "mm.dataNotice.v1.";

function remembered(userId: string): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY + userId) === "accepted";
  } catch {
    return false;
  }
}

function remember(userId: string): void {
  try {
    localStorage.setItem(STORAGE_KEY + userId, "accepted");
  } catch {
    // Storage blocked: the notice is only checked again, never shown again once accepted.
  }
}

export function DataNoticeGate({ children, loading }: { children: ReactNode; loading: ReactNode }) {
  const t = useT();
  const { session } = useAuth();
  const me = useMe();
  const userId = session?.userId ?? "";
  const data = me.data;

  if (data !== undefined) {
    if (!data.data_notice_required || data.data_notice_accepted_at !== null) {
      if (data.data_notice_accepted_at !== null) remember(userId);
      return <>{children}</>;
    }
    return <DataNotice onAccepted={() => remember(userId)} />;
  }
  if (remembered(userId)) return <>{children}</>;
  if (me.isError) return <ErrorState message={t("notice.error")} onRetry={() => void me.refetch()} />;
  return <>{loading}</>;
}

function DataNotice({ onAccepted }: { onAccepted: () => void }) {
  const t = useT();
  const { signOut } = useAuth();
  const accept = useAcceptDataNotice();
  return (
    <main className="page data-notice" id="main" aria-labelledby="notice-title">
      <h1 className="screen-title" id="notice-title">
        {t("notice.title")}
      </h1>
      <p>{t("notice.body")}</p>
      <p className="muted">{t("notice.busy")}</p>
      {accept.isError && <p role="alert">{t("notice.saveError")}</p>}
      <div className="data-notice-actions">
        <button
          type="button"
          className="btn btn-primary"
          aria-disabled={accept.isPending || undefined}
          onClick={() => {
            if (!accept.isPending) accept.mutate(undefined, { onSuccess: onAccepted });
          }}
        >
          <SavingLabel saving={accept.isPending}>{t("notice.accept")}</SavingLabel>
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => void signOut()}>
          {t("notice.decline")}
        </button>
      </div>
    </main>
  );
}

/** One line on the assistant screen while the notice applies. */
export function AssistantDataReminder() {
  const t = useT();
  const me = useMe();
  if (!me.data?.data_notice_required) return null;
  return <p className="meta assistant-reminder">{t("notice.assistantReminder")}</p>;
}
