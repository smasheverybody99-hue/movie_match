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
