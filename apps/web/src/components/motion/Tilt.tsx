import { useRef, type ReactNode } from "react";

import { useGsapEffect } from "../../lib/gsap";

const FINE_POINTER = "(hover: hover) and (pointer: fine)";

export interface TiltProps {
  children: ReactNode;
  className?: string;
  /** The largest rotation on either axis, in degrees. */
  max?: number;
}

/**
 * A card that turns a few degrees towards the pointer, as if it were lying under glass
 * (React Bits' "Tilted Card", on GSAP's quickTo).
 *
 * The rotation goes on this box, never on the poster inside: the poster's own scale on
 * hover and focus is a CSS transition (app.css, .has-quick), and two writers on one
 * `transform` would fight. Pointer only — a touch has no hover, and tapping a card opens
 * the film.
 */
export function Tilt({ children, className, max = 7 }: TiltProps) {
  const ref = useRef<HTMLDivElement>(null);

  useGsapEffect(
    ref,
    ({ gsap }) => {
      const el = ref.current;
      if (!el || !window.matchMedia(FINE_POINTER).matches) return;
      const settings = { duration: 0.4, ease: "power3.out", transformPerspective: 900 };
      const toX = gsap.quickTo(el, "rotationX", settings);
      const toY = gsap.quickTo(el, "rotationY", settings);
      const move = (event: PointerEvent) => {
        const box = el.getBoundingClientRect();
        if (box.width === 0 || box.height === 0) return;
        const x = (event.clientX - box.left) / box.width - 0.5;
        const y = (event.clientY - box.top) / box.height - 0.5;
        toX(-y * max * 2);
        toY(x * max * 2);
      };
      const rest = () => {
        toX(0);
        toY(0);
      };
      el.addEventListener("pointermove", move, { passive: true });
      el.addEventListener("pointerleave", rest);
      return () => {
        el.removeEventListener("pointermove", move);
        el.removeEventListener("pointerleave", rest);
      };
    },
    [max],
  );

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
