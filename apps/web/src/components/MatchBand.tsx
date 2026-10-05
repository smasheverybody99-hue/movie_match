import { useT } from "../i18n";
import type { MatchBand as Band } from "../lib/types";

/**
 * The match as the user sees it (FR-5, TZ 1.13): a band, not a number. "Strong" is red,
 * the product's one red, kept rare (the user's few closest films in the catalogue);
 * "good" is neutral. Nothing for a film outside both bands.
 */
export function MatchBand({ band, className = "" }: { band: Band | null | undefined; className?: string }) {
  const t = useT();
  if (!band) return null;
  return (
    <span className={`match-band match-band-${band} ${className}`.trim()}>
      {t(band === "strong" ? "band.strong" : "band.good")}
    </span>
  );
}
