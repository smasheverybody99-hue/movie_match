import { useRef, type CSSProperties } from "react";

import { useGsapEffect } from "../../lib/gsap";
import { usePrefersReducedMotion } from "../../lib/motion";

export interface SplitTextProps {
  text: string;
  /** The element rendered. A heading keeps its level; `span` goes inside a link. */
  as?: "h1" | "h2" | "h3" | "p" | "span";
  className?: string;
  style?: CSSProperties;
  /** What moves: letters for a short line, words for a sentence, lines for a block. */
  by?: "chars" | "words" | "lines";
  /** Seconds between pieces. */
  stagger?: number;
  duration?: number;
  delay?: number;
  /** Animate on mount rather than when scrolled to. */
  immediate?: boolean;
}

const PIECE_CLASS = { chars: "split-char", words: "split-word", lines: "split-line" } as const;

/**
 * A line of text that arrives piece by piece, each one rising out of its own mask
 * (React Bits' "Split Text", on GSAP's SplitText plugin).
 *
 * The text is rendered as plain text and split in place afterwards, so what is in the
 * DOM to begin with — and all there ever is with reduced motion — is the sentence
 * itself. The plugin's `aria: "auto"` puts the whole text back as the element's
 * `aria-label` and hides the pieces from assistive technology, so a screen reader reads
 * one sentence and never a column of letters. Find-in-page still matches: the letters
 * are real text in the page.
 *
 * `mask` wraps each piece in a clipping box, so a letter travels from behind the line
 * instead of sliding over its neighbours. Nothing but `transform` and `opacity` moves;
 * the element keeps its box, so no text below it shifts (CLS 0).
 */
export function SplitText({
  text,
  as = "span",
  className,
  style,
  by = "chars",
  stagger = 0.03,
  duration = 0.9,
  delay = 0,
  immediate = false,
}: SplitTextProps) {
  // One tag type inside: the four tags take the same props here, and a union of them
  // leaves the ref assignable to none.
  const Tag = as as "span";
  const ref = useRef<HTMLSpanElement>(null);
  const reduce = usePrefersReducedMotion();

  const clear = () => {
    if (ref.current) ref.current.style.opacity = "";
  };

  useGsapEffect(
    ref,
    ({ gsap, SplitText: GsapSplitText }) => {
      const el = ref.current;
      if (!el) return;
      const split = new GsapSplitText(el, {
        type: by,
        mask: by,
        aria: "auto",
        charsClass: PIECE_CLASS.chars,
        wordsClass: PIECE_CLASS.words,
        linesClass: PIECE_CLASS.lines,
        autoSplit: by === "lines",
      });
      const pieces = by === "chars" ? split.chars : by === "words" ? split.words : split.lines;
      // The element was hidden from the first paint so the un-split text is never seen;
      // from here each piece carries its own opacity.
      gsap.set(el, { opacity: 1 });
      if (pieces.length > 0) {
        gsap.from(pieces, {
          yPercent: 115,
          opacity: 0,
          duration,
          delay,
          stagger,
          ease: "power3.out",
          force3D: true,
          clearProps: "transform",
          scrollTrigger: immediate ? undefined : { trigger: el, start: "top 92%", once: true },
        });
      }
      // gsap.context runs this when the effect is torn down: the letters go back to
      // being one text node, so React is handed the DOM it rendered.
      return () => split.revert();
    },
    [text, by, stagger, duration, delay, immediate],
    clear,
  );

  return (
    <Tag ref={ref} className={className} style={reduce ? style : { ...style, opacity: 0 }}>
      {text}
    </Tag>
  );
}
