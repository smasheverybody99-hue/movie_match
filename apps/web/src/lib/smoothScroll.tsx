import { useEffect, type ReactNode } from "react";

import { loadGsap } from "./gsap";
import { usePrefersReducedMotion } from "./motion";

/** Scroll feel (docs/ui.md, "Harakat v3"): long enough to glide, short enough to obey. */
export const LENIS_OPTIONS = { duration: 1.05, wheelMultiplier: 0.9, touchMultiplier: 1.6 } as const;

/** How long the document's height has to hold still before everything is re-measured. */
const REFRESH_DELAY_MS = 150;

/**
 * Lenis (darkroomengineering/lenis, MIT) over the whole document, with GSAP driving its
 * frames so a scrubbed ScrollTrigger and the scroll position can never disagree by a
 * frame.
 *
 * Lenis sets the real scroll position rather than transforming a wrapper, so the sticky
 * side bar, the sticky top bar and the fixed bottom nav keep working untouched.
 *
 * It is also where the whole app's scroll-driven animations are re-measured when the
 * document changes height, which it does on every screen as the data arrives.
 *
 * It is skipped entirely with reduced motion: the chunk is not even fetched and the
 * browser's own scrolling is left alone. Anything with `data-lenis-prevent` (the Home
 * rows, the rating dialog) keeps its native scrolling, so a horizontal swipe is never
 * smoothed into the page.
 */
export function SmoothScroll({ children }: { children: ReactNode }) {
  const reduce = usePrefersReducedMotion();

  useEffect(() => {
    if (reduce) return;
    let live = true;
    let stop: (() => void) | null = null;

    void loadGsap().then(
      ({ gsap, ScrollTrigger }) => {
        if (!live) return;
        const parts: (() => void)[] = [];

        // The page grows after it is first measured: a feed's rows and a film's panels
        // arrive with their data. Every scroll-driven animation is positioned against the
        // document's height, so each of those changes has to be re-measured — without
        // this, a bar that fills over the whole page is set up against an empty one and
        // never moves. Debounced, because a refresh re-measures every trigger at once.
        if (typeof ResizeObserver === "function") {
          let timer: ReturnType<typeof setTimeout> | null = null;
          const observer = new ResizeObserver(() => {
            if (timer) clearTimeout(timer);
            timer = setTimeout(() => ScrollTrigger.refresh(), REFRESH_DELAY_MS);
          });
          observer.observe(document.body);
          parts.push(() => {
            if (timer) clearTimeout(timer);
            observer.disconnect();
          });
        }

        void import("lenis").then((lenisModule) => {
          if (!live) {
            for (const part of parts) part();
            return;
          }
          const lenis = new lenisModule.default({ ...LENIS_OPTIONS, autoRaf: false });
          const update = () => ScrollTrigger.update();
          const frame = (time: number) => lenis.raf(time * 1000); // gsap counts seconds, Lenis ms
          lenis.on("scroll", update);
          gsap.ticker.add(frame);
          parts.push(() => {
            gsap.ticker.remove(frame);
            lenis.off("scroll", update);
            lenis.destroy();
          });
        });

        stop = () => {
          for (const part of parts) part();
          parts.length = 0;
        };
      },
      () => {
        // No chunk, no smooth scroll: the browser's own scrolling was never taken away.
      },
    );

    return () => {
      live = false;
      stop?.();
    };
  }, [reduce]);

  return <>{children}</>;
}
