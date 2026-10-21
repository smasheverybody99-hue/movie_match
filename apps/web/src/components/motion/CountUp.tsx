import { useRef } from "react";

import { useGsapEffect } from "../../lib/gsap";

export interface CountUpProps {
  value: number;
  /** How the number is written, e.g. the locale-aware `score` in lib/format. */
  format?: (value: number) => string;
  duration?: number;
  /** Count on mount rather than when scrolled to. */
  immediate?: boolean;
}

/**
 * A number that counts up to its value when it is scrolled to (React Bits' "Count Up").
 *
 * The final number is what is rendered, so it is what a screen reader reads, what a test
 * reads, and what shows with reduced motion (docs/ui.md 7: the last value, at once). The
 * count overwrites the text frame by frame and puts the rendered number back at the end,
 * so nothing but the digits ever differs from the DOM React built.
 *
 * It runs on first mount only — a re-render never restarts it — and the box does not
 * change, because the widest string the count passes through is the final one.
 */
export function CountUp({ value, format = (n) => String(Math.round(n)), duration = 1.1, immediate = false }: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const final = format(value);

  useGsapEffect(
    ref,
    ({ gsap }) => {
      const el = ref.current;
      if (!el || !Number.isFinite(value)) return;
      const counter = { n: 0 };
      gsap.to(counter, {
        n: value,
        duration,
        ease: "power2.out",
        onUpdate: () => {
          el.textContent = format(counter.n);
        },
        onComplete: () => {
          el.textContent = final;
        },
        scrollTrigger: immediate ? undefined : { trigger: el, start: "top 95%", once: true },
      });
    },
    [value, duration, immediate],
  );

  return (
    <span ref={ref} data-testid="count-up">
      {final}
    </span>
  );
}
