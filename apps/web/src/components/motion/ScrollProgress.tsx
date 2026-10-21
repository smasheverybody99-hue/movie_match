import { useEffect, useRef } from "react";

import { useGsapEffect } from "../../lib/gsap";
import { usePrefersReducedMotion } from "../../lib/motion";

/** How far down the document the viewport has travelled, 0 to 1. */
function progress(): number {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  return scrollable > 0 ? Math.min(1, Math.max(0, window.scrollY / scrollable)) : 0;
}

/**
 * A hairline across the top of the window that fills as the page is scrolled.
 *
 * It reports a position rather than animating anything, so it is there with reduced
 * motion too — set straight from the scroll position by a listener, with no library and
 * no easing. With motion it is a scrubbed ScrollTrigger instead, which follows Lenis's
 * eased position frame by frame.
 *
 * Decorative: the same position is in the scrollbar, so it is hidden from assistive
 * technology rather than announced twice.
 */
export function ScrollProgress() {
  const ref = useRef<HTMLDivElement>(null);
  const bar = useRef<HTMLDivElement>(null);
  const reduce = usePrefersReducedMotion();

  useEffect(() => {
    if (!reduce) return;
    const set = () => {
      if (bar.current) bar.current.style.transform = `scaleX(${progress()})`;
    };
    set();
    window.addEventListener("scroll", set, { passive: true });
    window.addEventListener("resize", set);
    return () => {
      window.removeEventListener("scroll", set);
      window.removeEventListener("resize", set);
    };
  }, [reduce]);

  useGsapEffect(ref, ({ gsap, ScrollTrigger }) => {
    if (!bar.current) return;
    gsap.fromTo(
      bar.current,
      { scaleX: 0 },
      {
        scaleX: 1,
        ease: "none",
        // The whole page, as two scroll positions rather than a trigger element: the
        // document grows as rows and panels load, and `end` is read again on every
        // refresh, so the bar still reaches 1 at the foot of the page it ends up being.
        scrollTrigger: { start: 0, end: () => ScrollTrigger.maxScroll(window), scrub: 0.25 },
      },
    );
  });

  return (
    <div ref={ref} className="scroll-progress" aria-hidden="true">
      <div ref={bar} className="scroll-progress-bar" data-testid="scroll-progress" />
    </div>
  );
}
