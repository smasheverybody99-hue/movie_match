import { useEffect, useState, type CSSProperties } from "react";

import { useT, type MessageKey } from "../i18n";
import { useCountUp, usePrefersReducedMotion } from "../lib/motion";
import { traitBand, type TraitKey } from "../lib/traits";

export function traitLabelKey(key: TraitKey): MessageKey {
  return `trait.${key}`;
}

/** One trait: label, value, a bar coloured by strength (not quality). */
export function TraitBar({ trait, value }: { trait: TraitKey; value: number }) {
  const t = useT();
  const rounded = Math.round(value);
  return (
    <div className="trait-row">
      <div className="trait-label">
        <span>{t(traitLabelKey(trait))}</span>
        <span className="trait-value">{rounded}</span>
      </div>
      <div
        className="bar"
        role="meter"
        aria-label={t(traitLabelKey(trait))}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={rounded}
      >
        <i className={`band-${traitBand(value)}`} style={{ width: `${rounded}%` }} />
      </div>
    </div>
  );
}

/** The key to the two dots on a TraitAxis: you grey, the film white. Decorative. */
export function AxisLegend() {
  const t = useT();
  return (
    <p className="axis-legend" aria-hidden="true">
      <span className="key-you">{t("movie.compareYou")}</span>
      <span className="key-film">{t("movie.compareFilm")}</span>
    </p>
  );
}

/**
 * One trait on one 0-100 axis: the user's taste as a grey dot, the film as a white one,
 * the distance between them as a line. Both numbers are printed too; screen readers get
 * them as words. A taste not known yet (null) leaves its dot out rather than at 0, so the
 * dot appears instead of jumping.
 */
export function TraitAxis({
  trait,
  taste,
  film,
}: {
  trait: TraitKey;
  taste: number | null;
  film: number;
}) {
  const t = useT();
  const you = taste === null ? null : Math.round(taste);
  const it = Math.round(film);
  return (
    <div className="axis-row" data-testid={`axis-${trait}`}>
      <div className="axis-label">
        <span>{t(traitLabelKey(trait))}</span>
        <span className="axis-values">
          <span className="key-you">
            <span className="visually-hidden">{t("movie.compareYou")} </span>
            {you ?? "–"}
          </span>
          <span className="key-film">
            <span className="visually-hidden">{t("movie.compareFilm")} </span>
            {it}
          </span>
        </span>
      </div>
      <div className="axis" aria-hidden="true">
        {you !== null && (
          <>
            <i className="axis-gap" style={{ left: `${Math.min(you, it)}%`, width: `${Math.abs(it - you)}%` }} />
            <i className="axis-dot you" data-value={you} style={{ left: `${you}%` }} />
          </>
        )}
        <i className="axis-dot film" data-value={it} style={{ left: `${it}%` }} />
      </div>
    </div>
  );
}

/**
 * Conic ring with the percentage inside. Fills from 0 on first show while the number
 * counts up with it; with reduced motion both show the value at once. Screen readers get
 * the final value from the label, never the count.
 */
export function MatchRing({ value, size }: { value: number; size?: number }) {
  const t = useT();
  const reduce = usePrefersReducedMotion();
  const counted = useCountUp(value);
  const [shown, setShown] = useState(reduce ? value : 0);
  useEffect(() => {
    if (reduce) {
      setShown(value);
      return;
    }
    const frame = requestAnimationFrame(() => setShown(value));
    return () => cancelAnimationFrame(frame);
  }, [value, reduce]);
  // Without `size` the stylesheet sets it (the film page's ring is larger on wide screens).
  const style = { "--p": shown, ...(size ? { "--size": `${size}px` } : {}) } as CSSProperties;
  return (
    <div className="ring" style={style} data-p={shown} role="img" aria-label={t("common.matchLabel", { n: value })}>
      <div className="ring-inner" aria-hidden="true">
        <span className="ring-value">{counted}%</span>
        <span className="ring-label">{t("common.matchWord")}</span>
      </div>
    </div>
  );
}
