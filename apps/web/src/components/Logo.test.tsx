import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

import { COMPACT_BELOW, COMPACT_RAYS, ENVELOPE, FULL_RAYS, Logo } from "./Logo";

const PUBLIC = path.resolve(__dirname, "../../public");

describe("Logo", () => {
  it("draws 14 rays and the outline through their tips at 40px and up", () => {
    const { container } = render(<Logo size={48} />);
    const svg = container.querySelector("svg")!;
    expect(svg.dataset.variant).toBe("full");
    expect(svg.querySelectorAll("line")).toHaveLength(14);
    const outline = svg.querySelector("polygon")!;
    expect(outline.getAttribute("points")).toBe(ENVELOPE);
    // the outline's corners are exactly the rays' tips
    expect(ENVELOPE.split(" ")).toEqual(FULL_RAYS.map(([, , x, y]) => `${x},${y}`));
    expect(outline.getAttribute("fill-opacity")).toBe("0.07");
    expect(outline.getAttribute("stroke-opacity")).toBe("0.4");
  });

  it("switches to 8 thick rays without the outline below 40px, whatever was asked for", () => {
    const { container } = render(<Logo size={32} variant="full" />);
    const svg = container.querySelector("svg")!;
    expect(svg.dataset.variant).toBe("compact");
    expect(svg.querySelectorAll("line")).toHaveLength(8);
    expect(svg.querySelector("polygon")).toBeNull();
    expect(svg.querySelector("g")!.getAttribute("stroke-width")).toBe("9");
  });

  it("changes drawing at 40px: 39 is compact, 40 is full", () => {
    const at = (size: number) => render(<Logo size={size} />).container.querySelector("svg")!.dataset.variant;
    expect(at(39)).toBe("compact");
    expect(at(40)).toBe("full");
    expect(COMPACT_BELOW).toBe(40);
  });

  it("can be compact at a large size (inline loading marks)", () => {
    const { container } = render(<Logo size={64} variant="compact" />);
    expect(container.querySelector("svg")!.dataset.variant).toBe("compact");
  });

  it("is sized in px on the 120 grid", () => {
    const { container } = render(<Logo size={48} />);
    const svg = container.querySelector("svg")!;
    expect(svg.getAttribute("width")).toBe("48");
    expect(svg.getAttribute("height")).toBe("48");
    expect(svg.getAttribute("viewBox")).toBe("0 0 120 120");
  });

  it("is an image with the given name, or decorative without one", () => {
    render(<Logo size={32} title="Movie Match" />);
    expect(screen.getByRole("img", { name: "Movie Match" })).toBeInTheDocument();

    const { container } = render(<Logo size={32} />);
    const decorative = container.querySelector("svg")!;
    expect(decorative).toHaveAttribute("aria-hidden", "true");
    expect(decorative).not.toHaveAttribute("role");
  });

  it("takes its colour from where it sits: currentColor only, no colour of its own", () => {
    const { container } = render(<Logo size={48} />);
    const markup = container.innerHTML;
    expect(markup).not.toMatch(/#[0-9a-f]{3,6}\b|rgb\(/i);
    expect(container.querySelector("svg")!.getAttribute("stroke")).toBe("currentColor");
    expect(container.querySelector("polygon")!.getAttribute("fill")).toBe("currentColor");
  });

  it("favicon.svg is the compact mark: dark rays on a light tab, light on a dark one", () => {
    const favicon = readFileSync(path.join(PUBLIC, "favicon.svg"), "utf8");
    const lines = [...favicon.matchAll(/<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)"\/>/g)];
    expect(lines.map((m) => m.slice(1, 5).map(Number))).toEqual(COMPACT_RAYS.map((r) => [...r]));
    // the token values: --bg by default, --text when the browser is dark
    expect(favicon).toMatch(/g\{stroke:#0a0a0a\}@media \(prefers-color-scheme:dark\)\{g\{stroke:#f5f5f5\}\}/);
    expect(favicon).not.toMatch(/e63950/i); // never red
  });

  it("the manifest lists the 192 and 512 icons and no display mode", () => {
    const manifest = JSON.parse(readFileSync(path.join(PUBLIC, "manifest.webmanifest"), "utf8"));
    expect(manifest.icons.map((i: { sizes: string }) => i.sizes)).toEqual(["192x192", "512x512"]);
    expect(manifest).not.toHaveProperty("display");
    expect(manifest.background_color).toBe("#0a0a0a");
  });
});
