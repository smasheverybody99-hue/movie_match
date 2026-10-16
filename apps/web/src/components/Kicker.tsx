import { useT, type MessageKey } from "../i18n";
import type { MatchBand, TraitSide } from "../lib/types";
import { shownBand } from "./MatchBand";

/**
 * The heading a sentence completes, on the film page and in the Home hero. It names what
 * the sentence under it is (TZ 1.25): why the film suits the viewer, or how it differs.
 *
 * Red "STRONG MATCH" holds for one of the viewer's closest films (FR-5) unless the sentence
 * under it contradicts that: a strong film described by its *differences* gets the neutral
 * difference heading, because red over "this film differs from you" is the pairing that
 * TZ 1.23/1.24 removed from the recommendation row. No catalogue film is in that state
 * today; a bigger catalogue will produce one.
 *
 * Silence is not a contradiction: with nothing named there is no sentence, but the band is
 * still true - and a film with nothing named is one that sits closest to the taste on all
 * 14 traits, so it is among the best matches there are. It keeps the red heading. Used only
 * where a film's band or side is shown; plain section labels stay `.eyebrow`.
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
  const strong = shownBand(band) === "strong" && side !== "difference";
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
