import type { ReactNode } from "react";

/**
 * A slow sheen travelling across text (React Bits' "Shiny Text"), as a gradient clipped
 * to the glyphs. CSS only: the global reduced-motion rule in app.css already stops it,
 * and it costs nothing to load.
 *
 * The darkest point of the gradient is --muted, so the words stay readable the whole way
 * through; where the clip is not supported the text keeps its own colour (app.css).
 */
export function ShinyText({ children, className }: { children: ReactNode; className?: string }) {
  return <span className={className ? `shiny-text ${className}` : "shiny-text"}>{children}</span>;
}
