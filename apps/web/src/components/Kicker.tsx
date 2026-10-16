import { useT, type MessageKey } from "../i18n";
import type { MatchBand, TraitSide } from "../lib/types";
import { shownBand } from "./MatchBand";

/**
 * The heading a sentence completes, on the film page and in the Home hero. It names what
 * the sentence under it is (TZ 1.25): why the film suits the viewer, or how it differs.
 *
 * Red "STRONG MATCH" needs both: one of the viewer's closest films (FR-5) *and* a sentence
 * saying why it suits them. A strong film described by its differences gets the neutral
 * difference heading instead - red over "this film differs from you" is the pairing that
 * TZ 1.23/1.24 removed from the recommendation row, and the heading must not bring it back.
 * No catalogue film is in that state today; a bigger catalogue will produce one.
 *
 * With nothing named there is no sentence to name, so the heading stays the neutral
 * "YOU AND THIS FILM" whatever the band. Used only where a film's band or side is shown;
 * plain section labels stay `.eyebrow`.
 */
export function Kicker({
  band,
  side = null,
  as: Tag = "h2",
  id,
}: {
  band: MatchBand | null | undefined;
  side?: TraitSide | null;
  as?: "h2" | "p";
  id?: string;
}) {
  const t = useT();
  const strong = shownBand(band) === "strong" && side === "reason";
  const key: MessageKey = strong
    ? "band.strongHeading"
    : side === "reason"
      ? "movie.whyKickerReason"
      : side === "difference"
        ? "movie.whyKickerDifference"
        : "movie.whyKicker";
  return (
    <Tag className={strong ? "kicker kicker-strong" : "kicker"} id={id}>
      {t(key)}
    </Tag>
  );
}
