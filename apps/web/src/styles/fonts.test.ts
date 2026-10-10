import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const WEB = path.resolve(__dirname, "../..");
const FONTS = path.join(WEB, "public/fonts");
const css = readFileSync(path.join(__dirname, "fonts.css"), "utf8");
const tokens = readFileSync(path.join(__dirname, "tokens.css"), "utf8");
const app = readFileSync(path.join(__dirname, "app.css"), "utf8");
const html = readFileSync(path.join(WEB, "index.html"), "utf8");

const faces = [...css.matchAll(/@font-face \{([^}]*)\}/g)].map((m) => m[1] ?? "");
const prop = (face: string, name: string) => face.match(new RegExp(`${name}: ([^;]+);`))?.[1];
const webFaces = faces.filter((face) => face.includes("url("));
const fallbackFaces = faces.filter((face) => face.includes("local("));

describe("self-hosted fonts", () => {
  it("are the three families at exactly the weights the app used from Google", () => {
    const ranges = new Map(webFaces.map((face) => [prop(face, "font-family"), prop(face, "font-weight")]));
    expect(Object.fromEntries(ranges)).toEqual({
      '"Playfair Display"': "700 900",
      '"Inter"': "400 800",
      '"JetBrains Mono"': "400 600",
    });
  });

  it("cover Latin and Cyrillic for every family (ru needs Cyrillic, uz is Latin)", () => {
    for (const family of ["playfair-display", "inter", "jetbrains-mono"]) {
      for (const subset of ["latin", "latin-ext", "cyrillic"]) {
        expect(css, `${family} ${subset}`).toMatch(new RegExp(`/fonts/${family}-v\\d+-${subset}\\.woff2`));
      }
    }
  });

  it("swap in and fetch only the scripts a page uses", () => {
    for (const face of webFaces) {
      expect(prop(face, "font-display")).toBe("swap");
      expect(prop(face, "unicode-range")).toBeTruthy();
      expect(prop(face, "src")).toMatch(/^url\("\/fonts\/[\w-]+\.woff2"\) format\("woff2"\)$/);
    }
  });

  it("every referenced file is in public/fonts, and every file there is referenced", () => {
    const referenced = [...css.matchAll(/\/fonts\/([\w-]+\.woff2)/g)].map((m) => m[1]).sort();
    const shipped = readdirSync(FONTS).filter((f) => f.endsWith(".woff2")).sort();
    expect(shipped).toEqual(referenced);
    // the licence travels with the files (SIL OFL 1.1)
    for (const family of ["inter", "playfairdisplay", "jetbrainsmono"]) {
      expect(readFileSync(path.join(FONTS, `OFL-${family}.txt`), "utf8")).toMatch(/SIL Open Font License/);
    }
  });

  it("stand in with metric-matched local fonts while a file loads, so the swap does not move text", () => {
    // regular and bold, Latin and Cyrillic, desktop and Android (Courier New: one face, same ratio)
    expect(fallbackFaces).toHaveLength(13);
    for (const face of fallbackFaces) {
      for (const name of ["size-adjust", "ascent-override", "descent-override", "line-gap-override"]) {
        expect(prop(face, name), `${prop(face, "font-family")} ${name}`).toMatch(/^\d+(\.\d+)?%$/);
      }
    }
    // each stack names its fallbacks straight after the web font, before any generic font
    expect(tokens).toMatch(/--font-head: "Playfair Display", "Playfair Display Fallback", "Playfair Display Fallback Android",/);
    expect(tokens).toMatch(/--font-body: "Inter", "Inter Fallback", "Inter Fallback Android",/);
    expect(app).toMatch(/--font-mono: "JetBrains Mono", "JetBrains Mono Fallback",/);
  });

  it("index.html preloads the two Latin files and no longer talks to Google Fonts", () => {
    const preloads = [...html.matchAll(/<link rel="preload" href="([^"]+)" as="font" type="font\/woff2" crossorigin \/>/g)].map(
      (m) => m[1],
    );
    expect(preloads).toEqual(["/fonts/inter-v20-latin.woff2", "/fonts/playfair-display-v40-latin.woff2"]);
    for (const href of preloads) expect(css).toContain(`url("${href}")`);
    expect(html).not.toMatch(/fonts\.googleapis\.com|fonts\.gstatic\.com/);
    expect(css).not.toMatch(/googleapis|gstatic/);
  });

  it("Cloudflare serves the font files with a year's immutable cache", () => {
    const headers = readFileSync(path.join(WEB, "public/_headers"), "utf8");
    expect(headers).toMatch(/^\/fonts\/\*\n {2}Cache-Control: public, max-age=31536000, immutable$/m);
  });
});
