import { useEffect, useState } from "react";

const REDUCE = "(prefers-reduced-motion: reduce)";

/**
 * True when the user asked for less motion, or when it cannot be known (no matchMedia,
 * as in tests): then nothing animates and every value shows at once. The CSS rule in
 * app.css covers transitions and keyframes; this covers motion driven from JS.
 */
export function usePrefersReducedMotion(): boolean {
  const [reduce, setReduce] = useState(() =>
    typeof window.matchMedia === "function" ? window.matchMedia(REDUCE).matches : true,
  );
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const query = window.matchMedia(REDUCE);
    const update = () => setReduce(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return reduce;
}

/** Counts from 0 up to `target` over `ms` (ease-out), once per target; at once if reduced. */
export function useCountUp(target: number, ms = 600): number {
  const reduce = usePrefersReducedMotion();
  const [value, setValue] = useState(reduce ? target : 0);
  useEffect(() => {
    if (reduce) {
      setValue(target);
      return;
    }
    let frame = 0;
    const start = performance.now();
    const step = (now: number) => {
      // A frame can be stamped slightly before `start`: clamp, or the first value is negative.
      const progress = Math.min(Math.max((now - start) / ms, 0), 1);
      setValue(Math.round(target * (1 - (1 - progress) ** 3)));
      if (progress < 1) frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [target, ms, reduce]);
  return value;
}
