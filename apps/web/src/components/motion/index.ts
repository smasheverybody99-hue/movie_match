/**
 * The motion layer (docs/ui.md, "Harakat v3").
 *
 * GSAP (greensock/GSAP) drives everything; Lenis (darkroomengineering/lenis) smooths the
 * scroll that the scrubbed pieces read from (lib/smoothScroll.tsx). The components follow
 * React Bits (DavidHDev/react-bits) — the names in each file say which one — rewritten
 * here on this project's own rules: colours from tokens.css only, nothing that moves
 * layout, a text alternative for anything decorative, and every one of them off with
 * `prefers-reduced-motion: reduce`, where the GSAP chunk is not even fetched.
 */
export { Beams } from "./Beams";
export { CountUp } from "./CountUp";
export { Magnet } from "./Magnet";
export { Reveal } from "./Reveal";
export { ScrollProgress } from "./ScrollProgress";
export { ShinyText } from "./ShinyText";
export { SplitText } from "./SplitText";
export { Tilt } from "./Tilt";
export { useParallax } from "./parallax";
