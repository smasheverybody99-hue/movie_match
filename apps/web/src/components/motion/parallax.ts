import { useGsapEffect } from "../../lib/gsap";

export interface ParallaxOptions {
  /** Which elements inside the box move; the box itself when it is left out. */
  selector?: string;
  /** Total travel over the whole scroll, as a share of the element's height. */
  distance?: number;
  /** The scale it is held at, so the travel never uncovers an edge. */
  zoom?: number;
}

/**
 * Holds a backdrop slightly behind the page as it scrolls away (GSAP ScrollTrigger,
 * scrubbed, so Lenis's eased position and the image agree frame by frame).
 *
 * The image is held a little larger than its box for the whole scroll, so the travel can
 * never reveal an edge, and both heroes clip their contents anyway. Scrubbed motion is
 * driven by the scroll position, not by a clock, so it cannot run on after a flick.
 * Nothing but `transform` moves, so no text reflows.
 */
export function useParallax(
  ref: { current: HTMLElement | null },
  { selector, distance = 14, zoom = 1.14 }: ParallaxOptions = {},
): void {
  useGsapEffect(
    ref,
    ({ gsap }) => {
      const box = ref.current;
      if (!box) return;
      const targets = selector ? [...box.querySelectorAll(selector)] : [box];
      if (targets.length === 0) return;
      gsap.fromTo(
        targets,
        { yPercent: -distance / 2, scale: zoom },
        {
          yPercent: distance / 2,
          scale: zoom,
          ease: "none",
          scrollTrigger: { trigger: box, start: "top top", end: "bottom top", scrub: true },
        },
      );
    },
    [selector, distance, zoom],
  );
}
