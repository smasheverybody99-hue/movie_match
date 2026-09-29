import { useEffect, useState, type CSSProperties } from "react";

import { useT, type MessageKey } from "../i18n";
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

/** The film as the bar (coloured by strength), the user's taste as a tick on it. */
export function TraitCompare({
  trait,
  taste,
  film,
}: {
  trait: TraitKey;
  taste: number;
  film: number;
}) {
  const t = useT();
  const you = Math.round(taste);
  const it = Math.round(film);
  return (
    <div className="trait-row">
      <div className="trait-label">
        <span>{t(traitLabelKey(trait))}</span>
        <span className="trait-value">
          <span className="visually-hidden">{t("movie.compareYou")} </span>
          {you}
          {" · "}
          <span className="visually-hidden">{t("movie.compareFilm")} </span>
          {it}
        </span>
      </div>
      <div className="bar compare" aria-hidden="true">
        <i className={`band-${traitBand(film)}`} style={{ width: `${it}%` }} />
        <i className="taste-tick" style={{ left: `${you}%` }} />
      </div>
    </div>
  );
}

/** Conic ring with the percentage inside. Fills from 0 on first show. */
export function MatchRing({ value, size = 84 }: { value: number; size?: number }) {
  const t = useT();
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const frame = requestAnimationFrame(() => setShown(value));
    return () => cancelAnimationFrame(frame);
  }, [value]);
  const style = { "--p": shown, "--size": `${size}px` } as CSSProperties;
  return (
    <div className="ring" style={style} role="img" aria-label={t("common.matchLabel", { n: value })}>
      <div className="ring-inner" aria-hidden="true">
        <span className="ring-value">{value}%</span>
        <span className="ring-label">{t("common.matchWord")}</span>
      </div>
    </div>
  );
}
