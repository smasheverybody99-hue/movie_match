import { useT } from "../i18n";
import type { MatchBand } from "../lib/types";
import { shownBand } from "./MatchBand";

/**
 * The heading a sentence completes, on the film page and in the Home hero: "STRONG MATCH"
 * in red for the user's closest films, otherwise the neutral "YOU AND THIS FILM". Used
 * only where a film's band is shown; plain section labels stay `.eyebrow`.
 */
export function Kicker({ band, as: Tag = "h2", id }: { band: MatchBand | null | undefined; as?: "h2" | "p"; id?: string }) {
  const t = useT();
  const strong = shownBand(band) === "strong";
  return (
    <Tag className={strong ? "kicker kicker-strong" : "kicker"} id={id}>
      {strong ? t("band.strongHeading") : t("movie.whyKicker")}
    </Tag>
  );
}
