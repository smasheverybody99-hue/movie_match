import { useT } from "../i18n";
import type { MatchBand as Band } from "../lib/types";

/**
 * The band the UI shows (FR-5, TZ 1.16): "strong" only, the user's few closest films.
 * The API still sends "good" (ordering, and so the decision is easy to undo), but it is
 * not drawn: on Home it appeared on 68% of the pages (0.15 share), so it told nothing apart.
 */
export function shownBand(band: Band | null | undefined): "strong" | null {
  return band === "strong" ? "strong" : null;
}

/** "Strong match" as a red pill (posters, watchlist rows); nothing otherwise. */
export function MatchBand({ band, className = "" }: { band: Band | null | undefined; className?: string }) {
  const t = useT();
  if (!shownBand(band)) return null;
  return <span className={`match-band match-band-strong ${className}`.trim()}>{t("band.strong")}</span>;
}
