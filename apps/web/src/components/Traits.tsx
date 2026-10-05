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

/**
 * The key to the two dots on a TraitAxis: you a filled circle, the film an outlined one.
 * Laid out as an axis row with an empty name cell, so it sits directly above the first
 * axis and starts where the axes start.
 */
export function AxisLegend() {
  const t = useT();
  return (
    <div className="axis-row axis-legend-row" aria-hidden="true">
      <span className="axis-name" />
      <p className="axis-legend">
        <span className="key-you">{t("movie.compareYou")}</span>
        <span className="key-film">{t("movie.compareFilm")}</span>
      </p>
    </div>
  );
}

/** The least distance between the two dots' centres, in px: a 12px dot plus 8px clear. */
export const DOT_GAP = 20;

/**
 * Where the two dots sit on the axis, as CSS lengths. Each sits at its value unless the
 * two would be closer than DOT_GAP px on screen; then both move apart from their midpoint
 * to exactly DOT_GAP, and stay inside the axis. Pure CSS (min/max/clamp), so it holds at
 * any width without measuring. The true values stay in the printed numbers and the label.
 */
export function axisPositions(you: number, film: number): { you: string; film: string } {
  const lo = Math.min(you, film);
  const hi = Math.max(you, film);
  const mid = (lo + hi) / 2;
  const half = DOT_GAP / 2;
  const low = `clamp(0px, min(${lo}%, ${mid}% - ${half}px), 100% - ${DOT_GAP}px)`;
  const high = `clamp(${DOT_GAP}px, max(${hi}%, ${mid}% + ${half}px), 100%)`;
  return you <= film ? { you: low, film: high } : { you: high, film: low };
}

/**
 * One trait on one 0-100 axis: the user's taste as a filled dot with its number above,
 * the film as an outlined dot with its number below, the distance between them as a line.
 * Shape, not shade, tells them apart: both are white. A number near 0 or 100 is pushed
 * inwards so it stays inside. Screen readers get one label with both values. A taste not
 * known yet (null) leaves its dot out rather than drawing it at 0.
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
  const name = t(traitLabelKey(trait));
  const values = [
    ...(you === null ? [] : [`${t("movie.compareYou")} ${you}`]),
    `${t("movie.compareFilm")} ${it}`,
  ].join(", ");
  const at = you === null ? { film: `${it}%` } : axisPositions(you, it);
  const style = { "--film": at.film, ...("you" in at ? { "--you": at.you } : {}) } as CSSProperties;
  return (
    <div className="axis-row" data-testid={`axis-${trait}`}>
      <span className="axis-name" aria-hidden="true">
        {name}
      </span>
      <div className="axis-plot" role="img" aria-label={`${name}: ${values}`} title={values} style={style}>
        {you !== null && (
          <>
            <span className="axis-num you">{you}</span>
            <i className="axis-gap" />
            <i className="axis-dot you" data-value={you} />
          </>
        )}
        <i className="axis-dot film" data-value={it} />
        <span className="axis-num film">{it}</span>
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
        {/* A hidden copy of the final value fixes the box's width, so the count never moves it. */}
        <span className="ring-value">
          <span className="ring-ghost">{value}%</span>
          <span className="ring-count">{counted}%</span>
        </span>
        <span className="ring-label">{t("common.matchWord")}</span>
      </div>
    </div>
  );
}
