import { useRef, type ReactNode } from "react";

import { useGsapEffect } from "../../lib/gsap";

/** Only where there is a real pointer to be drawn towards: never on touch. */
const FINE_POINTER = "(hover: hover) and (pointer: fine)";

export interface MagnetProps {
  children: ReactNode;
  className?: string;
  /** How far it leans, as a share of the pointer's distance from the centre. */
  strength?: number;
  /** How close the pointer has to come, in px beyond the element's own box. */
  radius?: number;
}

/**
 * A control that leans towards the pointer as it approaches, and settles back when it
 * leaves (React Bits' "Magnet", on GSAP's quickTo).
 *
 * Pointer only, and never on touch: a finger has no "approach". It moves the wrapper by
 * a few px of `transform`, so the control keeps its place in the layout and whatever is
 * inside keeps its own hover and focus styles.
 */
export function Magnet({ children, className, strength = 0.3, radius = 90 }: MagnetProps) {
  const ref = useRef<HTMLSpanElement>(null);

  useGsapEffect(
    ref,
    ({ gsap }) => {
      const el = ref.current;
      if (!el || !window.matchMedia(FINE_POINTER).matches) return;
      const toX = gsap.quickTo(el, "x", { duration: 0.45, ease: "power3.out" });
      const toY = gsap.quickTo(el, "y", { duration: 0.45, ease: "power3.out" });
      const move = (event: PointerEvent) => {
        const box = el.getBoundingClientRect();
        const dx = event.clientX - (box.left + box.width / 2);
        const dy = event.clientY - (box.top + box.height / 2);
        const near =
          Math.abs(dx) < box.width / 2 + radius && Math.abs(dy) < box.height / 2 + radius;
        toX(near ? dx * strength : 0);
        toY(near ? dy * strength : 0);
      };
      const rest = () => {
        toX(0);
        toY(0);
      };
      window.addEventListener("pointermove", move, { passive: true });
      window.addEventListener("pointerleave", rest);
      return () => {
        window.removeEventListener("pointermove", move);
        window.removeEventListener("pointerleave", rest);
      };
    },
    [strength, radius],
  );

  return (
    <span ref={ref} className={className ? `magnet ${className}` : "magnet"}>
      {children}
    </span>
  );
}
