import { useT } from "../i18n";
import { TRAIT_KEYS, type TraitKey } from "../lib/traits";
import { traitLabelKey } from "./Traits";

/** Geometry in viewBox units (the SVG is at most 480px wide, docs/ui.md 6). */
const VIEW = 300; // viewBox x: -300..300 (the side labels need the width)
const VIEW_Y = 225; // y: -225..225 (labels above and below reach ~215; a square left bands empty)
const INNER = 40; // the empty centre: rays start here, so 14 of them do not crowd
const OUTER = 170; // value 100
const LABEL = 186; // labels start just outside the 100 ring
const STRONGEST = 3;

/** Where a value ends on its ray: linear in the value, from the inner circle to OUTER. */
export function rayLength(value: number): number {
  return INNER + (Math.min(Math.max(value, 0), 100) / 100) * (OUTER - INNER);
}

/** Each trait keeps one angle for everyone (traits.json order), from 12 o'clock, clockwise. */
export function rayAngle(index: number): number {
  return -Math.PI / 2 + (index * 2 * Math.PI) / TRAIT_KEYS.length;
}

/**
 * A ray's brightness: the three strongest fully white, the rest by their value (0.4 at
 * 0, 0.85 at 100), so the shape is never flat white (docs/ui.md 6, decision 1). 0.4 is
 * the floor: white at 0.4 on --bg is ~3.5:1, above the 3:1 for graphics (WCAG 1.4.11).
 */
export function rayOpacity(value: number, strongest: boolean): number {
  return strongest ? 1 : 0.4 + 0.45 * (Math.min(Math.max(value, 0), 100) / 100);
}

/** The closed outline through every ray's tip, in traits.json order ("x,y x,y ..."). */
export function shapePoints(scores: Partial<Record<TraitKey, number>>): string {
  return TRAIT_KEYS.map((key, i) => {
    const r = rayLength(scores[key] ?? 0);
    const a = rayAngle(i);
    return `${(r * Math.cos(a)).toFixed(1)},${(r * Math.sin(a)).toFixed(1)}`;
  }).join(" ");
}

/**
 * A label of 12 characters or more on two lines, split at the space nearest its middle.
 * 12, not 13: ru "Накал эмоций" on one line ran past a 390px screen when it was among
 * the strongest (the larger size).
 */
export function lines(label: string): string[] {
  if (label.length < 12 || !label.includes(" ")) return [label];
  const mid = label.length / 2;
  let best = -1;
  for (let i = label.indexOf(" "); i !== -1; i = label.indexOf(" ", i + 1)) {
    if (best === -1 || Math.abs(i - mid) < Math.abs(best - mid)) best = i;
  }
  return [label.slice(0, best), label.slice(best + 1)];
}

/**
 * Movie DNA as a radial chart: one ray per trait from the centre, length linear in the
 * value, at an angle fixed for everyone, so two people's shapes compare at a glance.
 * Monochrome (DNA is not a match, so no red). Faint rings at 50 and 100 make lengths
 * readable; the 100 ring is the same for everyone, so shapes compare. A faint closed
 * outline through the ray tips (filled at 6% white) turns 14 rays into one shape; it
 * fades in after the rays. Labels: all 14 on wide screens; below 640px only the three strongest (the
 * fully white rays), the rest are in the Numbers list beside it. Rays grow from the
 * centre one after another on first paint (CSS; none with reduced motion).
 * The SVG is one image with a summary label; the exact values are the Numbers list.
 */
export function DnaFlower({ scores, label }: { scores: Partial<Record<TraitKey, number>>; label: string }) {
  const t = useT();
  const strongest = new Set(
    [...TRAIT_KEYS].sort((a, b) => (scores[b] ?? 0) - (scores[a] ?? 0)).slice(0, STRONGEST),
  );
  return (
    <svg
      className="dna-flower"
      viewBox={`${-VIEW} ${-VIEW_Y} ${2 * VIEW} ${2 * VIEW_Y}`}
      role="img"
      aria-label={label}
      data-testid="dna-flower"
    >
      <circle className="dna-ring" r={rayLength(50)} />
      <circle className="dna-ring" r={OUTER} />
      <polygon className="dna-shape" data-testid="dna-shape" points={shapePoints(scores)} />
      {TRAIT_KEYS.map((key, i) => {
        const value = scores[key] ?? 0;
        const angle = rayAngle(i);
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        const top = strongest.has(key);
        const end = rayLength(value);
        // Left half: the text ends at the ray; right half: starts there; top and bottom: centred.
        const anchor = Math.abs(cos) < 0.2 ? "middle" : cos > 0 ? "start" : "end";
        const text = lines(t(traitLabelKey(key)));
        const lineHeight = top ? 24 : 18;
        // Above the centre the block grows upwards, below it downwards.
        const firstY = LABEL * sin + (sin < -0.2 ? -(text.length - 1) * lineHeight : sin > 0.2 ? lineHeight * 0.7 : 0);
        return (
          <g key={key} data-testid={`ray-${key}`} data-value={Math.round(value)}>
            <line
              className="dna-ray"
              style={{ opacity: rayOpacity(value, top), animationDelay: `${i * 40}ms` }}
              x1={INNER * cos}
              y1={INNER * sin}
              x2={end * cos}
              y2={end * sin}
            />
            <text
              className={top ? "dna-label is-top" : "dna-label"}
              x={LABEL * cos}
              y={firstY}
              textAnchor={anchor}
              dominantBaseline="middle"
            >
              {text.map((part, n) => (
                <tspan key={n} x={LABEL * cos} dy={n === 0 ? 0 : lineHeight}>
                  {part}
                </tspan>
              ))}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
