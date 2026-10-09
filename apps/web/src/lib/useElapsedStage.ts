import { useEffect, useState } from "react";

/**
 * How many of `thresholds` (ms since mount, ascending) have passed: 0 at first, then 1, 2 …
 * Pass a module-level array: a new array on every render restarts the clock.
 */
export function useElapsedStage(thresholds: readonly number[]): number {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const timers = thresholds.map((ms, i) => setTimeout(() => setStage(i + 1), ms));
    return () => timers.forEach(clearTimeout);
  }, [thresholds]);
  return stage;
}
