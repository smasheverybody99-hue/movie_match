import type { gsap as gsapExport } from "gsap";
import type { ScrollTrigger as ScrollTriggerExport } from "gsap/ScrollTrigger";
import type { SplitText as SplitTextExport } from "gsap/SplitText";
import { useEffect, useRef, type DependencyList } from "react";

import { usePrefersReducedMotion } from "./motion";

/**
 * GSAP and Lenis, loaded on demand (docs/ui.md, "Harakat v3").
 *
 * Nothing here is in the main bundle: the first component that actually animates pulls
 * the chunk in. A visitor who asked for less motion never downloads it at all, and
 * neither does a test run, where `usePrefersReducedMotion` reads an unknown preference as
 * "reduce" (lib/motion.ts). That keeps the motion layer free for everyone who cannot use
 * it, and keeps the main chunk the size it was before it existed.
 */
export type Gsap = typeof gsapExport;
export type ScrollTriggerClass = typeof ScrollTriggerExport;
export type SplitTextClass = typeof SplitTextExport;

export interface GsapBundle {
  gsap: Gsap;
  ScrollTrigger: ScrollTriggerClass;
  SplitText: SplitTextClass;
}

let pending: Promise<GsapBundle> | null = null;

/** The one GSAP instance for the app, with the two plugins registered once. */
export function loadGsap(): Promise<GsapBundle> {
  pending ??= Promise.all([import("gsap"), import("gsap/ScrollTrigger"), import("gsap/SplitText")]).then(
    ([core, scroll, split]) => {
      const bundle: GsapBundle = {
        gsap: core.gsap,
        ScrollTrigger: scroll.ScrollTrigger,
        SplitText: split.SplitText,
      };
      bundle.gsap.registerPlugin(bundle.ScrollTrigger, bundle.SplitText);
      // A tab in the background gets no frames; without this, GSAP sees the gap as one
      // enormous delta and jumps every scrubbed animation to its end on return.
      bundle.gsap.ticker.lagSmoothing(500, 33);
      return bundle;
    },
  );
  return pending;
}

/** Tests only: forget the loaded bundle so the next `loadGsap()` starts over. */
export function resetGsap(): void {
  pending = null;
}

/**
 * Builds the animation. Everything created inside runs in a `gsap.context` and is
 * reverted together on cleanup — inline styles included, so no transform is left on an
 * element afterwards (a stray `transform` would become the containing block for the
 * page's fixed bars and dialogs). Anything the context cannot undo by itself (a
 * SplitText, a listener) goes in a cleanup function returned from here.
 */
export type GsapEffect = (bundle: GsapBundle) => void | (() => void);

/**
 * Runs `effect` once the chunk is in, inside a `gsap.context` scoped to `ref`, and
 * reverts it on cleanup or when the motion preference changes.
 *
 * With reduced motion it never loads anything and `onSkip` runs instead — that is where a
 * component undoes whatever it rendered for the animation's starting state. `onSkip` also
 * runs when the chunk fails to load (an offline visit to a page whose chunk was never
 * cached), so a hidden starting state can never be what the visitor is left looking at.
 */
export function useGsapEffect(
  ref: { current: Element | null },
  effect: GsapEffect,
  deps: DependencyList = [],
  onSkip?: () => void,
): void {
  const reduce = usePrefersReducedMotion();
  const latest = useRef({ effect, onSkip });
  latest.current = { effect, onSkip };

  useEffect(() => {
    if (!ref.current) return;
    if (reduce) {
      latest.current.onSkip?.();
      return;
    }
    let live = true;
    let context: { revert: () => void } | null = null;
    void loadGsap().then(
      (bundle) => {
        if (!live || !ref.current) return;
        context = bundle.gsap.context(() => latest.current.effect(bundle), ref.current);
      },
      () => {
        if (live) latest.current.onSkip?.();
      },
    );
    return () => {
      live = false;
      context?.revert();
    };
    // `ref` is stable and both callbacks are read through `latest`, so only the
    // preference and the caller's own deps belong here.
  }, [reduce, ...deps]);
}
