/**
 * The Movie Match mark, taken from the Movie DNA chart (docs/ui.md, "Logo"). One family,
 * two drawings on the same 120 × 120 grid:
 * - full (40px and up): 14 rays from an empty centre, one per trait, and the faint
 *   outline through their tips, like the DNA page's shape;
 * - compact (below 40px: the sidebar and top bar, favicon, inline loading): 8 thicker
 *   rays, no outline, so it still reads at 16px.
 * Below 40px it is always compact: at 32px the 14 rays already run together (seen in
 * the sidebar, 2026-10-09), so the size picks the drawing, not the other way round.
 * Neutral only: everything is currentColor (the outline at 7% fill, 40% stroke), so the
 * place it sits in gives the colour. Never red (docs/ui.md, 1).
 */

/** Below this size (px) the compact drawing is used. */
export const COMPACT_BELOW = 40;

type Ray = readonly [number, number, number, number];

/** [x1, y1, x2, y2]: from the inner circle (r 14) out to the tip, clockwise from 12 o'clock. */
export const FULL_RAYS: readonly Ray[] = [
  [60, 46, 60, 16.8],
  [66.07, 47.39, 74.06, 30.81],
  [70.95, 51.27, 90.1, 36],
  [73.65, 56.89, 86.91, 53.86],
  [73.65, 63.11, 104.16, 70.08],
  [70.95, 68.73, 87.68, 82.07],
  [66.07, 72.61, 73.15, 87.3],
  [60, 74, 60, 100.5],
  [53.93, 72.61, 48.76, 83.33],
  [49.05, 68.73, 30.68, 83.38],
  [46.35, 63.11, 27.15, 67.5],
  [46.35, 56.89, 17.2, 50.23],
  [49.05, 51.27, 37.33, 41.92],
  [53.93, 47.39, 42.86, 24.41],
];

/** The outline: through every full ray's tip, in the same order. */
export const ENVELOPE = FULL_RAYS.map(([, , x, y]) => `${x},${y}`).join(" ");

export const COMPACT_RAYS: readonly Ray[] = [
  [60, 44, 60, 12.3],
  [71.31, 48.69, 84.54, 35.46],
  [76, 60, 102.6, 60],
  [71.31, 71.31, 81.5, 81.5],
  [60, 76, 60, 106.2],
  [48.69, 71.31, 33.41, 86.59],
  [44, 60, 27.4, 60],
  [48.69, 48.69, 30.87, 30.87],
];

export function Logo({
  size,
  variant,
  title,
  className,
}: {
  size: number;
  variant?: "full" | "compact";
  /** The accessible name. Without one the mark is decorative (aria-hidden). */
  title?: string;
  className?: string;
}) {
  const kind = size < COMPACT_BELOW ? "compact" : (variant ?? "full");
  const rays = kind === "full" ? FULL_RAYS : COMPACT_RAYS;
  return (
    <svg
      className={className ? `logo ${className}` : "logo"}
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      data-variant={kind}
      {...(title ? { role: "img", "aria-label": title } : { "aria-hidden": true })}
    >
      {kind === "full" && (
        <polygon
          points={ENVELOPE}
          fill="currentColor"
          fillOpacity={0.07}
          strokeOpacity={0.4}
          strokeWidth={1.6}
          strokeLinejoin="round"
        />
      )}
      <g strokeWidth={kind === "full" ? 6 : 9}>
        {rays.map(([x1, y1, x2, y2]) => (
          <line key={`${x2},${y2}`} x1={x1} y1={y1} x2={x2} y2={y2} />
        ))}
      </g>
    </svg>
  );
}
