import type { LucideIcon } from "lucide-react";

/**
 * Every icon in the app goes through here: lucide-react, neutral (currentColor), one
 * stroke width. Icons are decoration — the text or aria-label next to them carries the
 * meaning — so they are hidden from screen readers. No emoji anywhere (design brief v2;
 * `noEmoji.test.ts` enforces it).
 */
export function Icon({ as: Glyph, size = 20 }: { as: LucideIcon; size?: number }) {
  return <Glyph className="icon" size={size} strokeWidth={1.75} aria-hidden="true" focusable="false" />;
}
