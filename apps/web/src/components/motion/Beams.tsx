import { useRef } from "react";

import { useGsapEffect } from "../../lib/gsap";

/** How many beams cross the box. Three reads as light; more reads as a pattern. */
const BEAMS = [0, 1, 2];

/**
 * Light drifting behind a screen (React Bits' "Beams" / "Light Rays", as gradients
 * rather than a WebGL canvas, so it costs one paint and no second library).
 *
 * Monochrome by the colour rule (docs/ui.md 1): white at a few percent, over --bg. It
 * carries no information, so it is hidden from assistive technology, and it sits behind
 * everything with `pointer-events: none`.
 *
 * Each beam drifts on its own slow loop. With reduced motion the beams are simply still
 * — the look stays, the movement goes — and the GSAP chunk is never fetched.
 */
export function Beams({ className }: { className?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useGsapEffect(ref, ({ gsap }) => {
    const beams = ref.current?.querySelectorAll(".beam");
    if (!beams || beams.length === 0) return;
    beams.forEach((beam, i) => {
      gsap.to(beam, {
        xPercent: i % 2 === 0 ? 14 : -14,
        yPercent: i === 1 ? -8 : 6,
        rotate: i % 2 === 0 ? 3 : -3,
        opacity: 0.55,
        duration: 13 + i * 5,
        ease: "sine.inOut",
        repeat: -1,
        yoyo: true,
        delay: i * 1.5,
      });
    });
  });

  return (
    <div ref={ref} className={className ? `beams ${className}` : "beams"} aria-hidden="true">
      {BEAMS.map((i) => (
        <span key={i} className="beam" data-beam={i} />
      ))}
    </div>
  );
}
