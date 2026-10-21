import { useLayoutEffect, useRef, type CSSProperties, type ReactNode } from "react";

import { useGsapEffect } from "../../lib/gsap";
import { usePrefersReducedMotion } from "../../lib/motion";

/** How a block arrives. `rise` is the default everywhere; the rest are for one-offs. */
export type RevealEffect = "rise" | "fade" | "blur" | "scale";

/** Where a block starts, per effect. `y` is the travel in px (0 for the still effects). */
function startVars(effect: RevealEffect, y: number): gsap.TweenVars {
  switch (effect) {
    case "fade":
      return { opacity: 0 };
    case "blur":
      return { opacity: 0, filter: "blur(10px)" };
    case "scale":
      return { opacity: 0, scale: 0.94 };
    default:
      return { opacity: 0, y };
  }
}

function endVars(effect: RevealEffect): gsap.TweenVars {
  const end: gsap.TweenVars = { opacity: 1, y: 0, scale: 1, filter: "blur(0px)" };
  if (effect === "fade") return { opacity: 1 };
  if (effect === "blur") return { opacity: 1, filter: "blur(0px)" };
  if (effect === "scale") return { opacity: 1, scale: 1 };
  delete end.filter;
  delete end.scale;
  return end;
}

export interface RevealProps {
  children: ReactNode;
  /** The element this renders; `li` and `section` keep a list or a landmark intact. */
  as?: "div" | "section" | "li" | "ul" | "article";
  className?: string;
  style?: CSSProperties;
  effect?: RevealEffect;
  /** Travel for `rise`, in px. */
  y?: number;
  duration?: number;
  delay?: number;
  /** Seconds between direct children. Above 0 the children arrive, not the box. */
  stagger?: number;
  /** ScrollTrigger's `start`. The default fires a little before the block is in view. */
  start?: string;
  /** Animate on mount instead of on scroll: for a block that is already on screen. */
  immediate?: boolean;
  /** `aria-labelledby`, for a `section` that is named by a heading inside it. */
  labelledBy?: string;
}

/**
 * A block that arrives when it is scrolled to: opacity, and a short rise (React Bits'
 * "Animated Content", on GSAP ScrollTrigger).
 *
 * Only `transform`, `opacity` and `filter` move, and the block keeps its box from the
 * first paint, so nothing reflows and CLS stays 0. It happens once per mount, never
 * again on a re-render.
 *
 * The starting state is set before the first paint — as an inline style for the block
 * itself, in a layout effect for staggered children — so there is no flash of finished
 * content first. With reduced motion none of it is applied and the block is simply
 * there; the same undo runs if the GSAP chunk fails to arrive, so a visitor is never
 * left looking at something invisible.
 */
export function Reveal({
  children,
  as = "div",
  className,
  style,
  effect = "rise",
  y = 24,
  duration = 0.7,
  delay = 0,
  stagger = 0,
  start = "top 88%",
  immediate = false,
  labelledBy,
}: RevealProps) {
  // One tag type inside, whichever tag is rendered: the props of the four are the same
  // here (class, style, children), and a union would make the ref unassignable to any.
  const Tag = as as "div";
  const ref = useRef<HTMLDivElement>(null);
  const reduce = usePrefersReducedMotion();
  const hides = !reduce && stagger <= 0;

  // Staggered children cannot be hidden from the render (they are the caller's elements),
  // so they are hidden here instead — before the browser paints, not after.
  useLayoutEffect(() => {
    if (reduce || stagger <= 0 || !ref.current) return;
    for (const child of ref.current.children) {
      if (child instanceof HTMLElement) child.style.opacity = "0";
    }
  }, [reduce, stagger]);

  const clear = () => {
    const el = ref.current;
    if (!el) return;
    el.style.opacity = "";
    for (const child of el.children) {
      if (child instanceof HTMLElement) child.style.opacity = "";
    }
  };

  useGsapEffect(
    ref,
    ({ gsap }) => {
      const el = ref.current;
      if (!el) return;
      const targets: Element[] = stagger > 0 ? [...el.children] : [el];
      if (targets.length === 0) return;
      gsap.fromTo(
        targets,
        startVars(effect, y),
        {
          ...endVars(effect),
          duration,
          delay,
          stagger,
          ease: "power3.out",
          // `force3D` promotes the element for the length of the tween and then lets it
          // go. A `will-change` of our own would instead stay on every element for ever
          // — on a feed that is a live layer per poster row, for one 0.7 s arrival.
          force3D: true,
          // Every inline style this leaves behind goes, transform included: one left on
          // the block would become the containing block for the page's fixed bars.
          clearProps: "transform,scale,filter",
          scrollTrigger: immediate ? undefined : { trigger: el, start, once: true },
        },
      );
    },
    [effect, y, duration, delay, stagger, start, immediate],
    clear,
  );

  return (
    <Tag
      ref={ref}
      className={className}
      style={hides ? { ...style, opacity: 0 } : style}
      aria-labelledby={labelledBy}
    >
      {children}
    </Tag>
  );
}
