import { describe, expect, it } from "vitest";

/**
 * No emoji in the interface: icons come from lucide-react through <Icon> (design brief
 * v2, docs/ui.md). This reads every source file and the stylesheets, including the
 * dictionaries, so an emoji cannot come back through a string or a CSS `content`.
 */
const SOURCES = import.meta.glob(["./**/*.{ts,tsx,css}", "!./**/*.test.{ts,tsx}"], {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

// Pictographs, plus the dingbats that were used as icons before (★ ✓ ✔ ✕ ✖ ⚠ ↗).
const EMOJI = /[\p{Extended_Pictographic}★✓✔✕✖⚠↗]/u;

describe("no emoji", () => {
  it("reads the source files", () => {
    expect(Object.keys(SOURCES).length).toBeGreaterThan(20);
    expect(Object.keys(SOURCES)).toContain("./components/Layout.tsx");
  });

  it.each(Object.entries(SOURCES))("%s has none", (_path, text) => {
    const found = text.split("\n").flatMap((line, i) => (EMOJI.test(line) ? [`${i + 1}: ${line.trim()}`] : []));
    expect(found).toEqual([]);
  });
});
