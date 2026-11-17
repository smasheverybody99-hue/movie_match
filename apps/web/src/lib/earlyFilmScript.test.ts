import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BACKDROP_SIZES, backdropSrcSet, earlyFilmScript, earlyFilmTag } from "./earlyFilmScript";

const API = "https://api.example.com/";

/** Runs the inline script as the browser would, on this path. */
function runAt(path: string): void {
  window.history.replaceState({}, "", path);
  new Function(earlyFilmScript(API)!)();
}

function preloads(): HTMLLinkElement[] {
  return [...document.head.querySelectorAll<HTMLLinkElement>('link[rel="preload"][as="image"]')];
}

function answer(body: unknown, ok = true) {
  return vi.fn().mockResolvedValue({ ok, json: () => Promise.resolve(body) });
}

describe("the early film script", () => {
  beforeEach(() => {
    delete window.__mmEarlyFilm;
    for (const link of preloads()) link.remove();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    window.history.replaceState({}, "", "/");
  });

  it("asks for the film with a plain GET (no headers, so no preflight) and preloads the hero's own srcset", async () => {
    const fetch = answer({ id: 7, backdrop_path: "/b.jpg", poster_path: "/p.jpg", match: null });
    vi.stubGlobal("fetch", fetch);
    runAt("/movie/7");
    expect(fetch).toHaveBeenCalledWith("https://api.example.com/movies/7");
    expect(window.__mmEarlyFilm?.id).toBe(7);
    // Only the hero's two paths are kept.
    expect(await window.__mmEarlyFilm?.film).toEqual({ backdrop_path: "/b.jpg", poster_path: "/p.jpg" });
    const [link] = preloads();
    expect(link?.getAttribute("imagesrcset")).toBe(backdropSrcSet("/b.jpg"));
    expect(link?.getAttribute("imagesizes")).toBe(BACKDROP_SIZES);
    expect(link?.getAttribute("fetchpriority")).toBe("high");
  });

  it("preloads nothing without a backdrop, and keeps the poster for the blurred hero", async () => {
    vi.stubGlobal("fetch", answer({ backdrop_path: null, poster_path: "/p.jpg" }));
    runAt("/movie/7/");
    expect(await window.__mmEarlyFilm?.film).toEqual({ backdrop_path: null, poster_path: "/p.jpg" });
    expect(preloads()).toHaveLength(0);
  });

  it("gives a sensitive film no preload and no early hero", async () => {
    vi.stubGlobal("fetch", answer({ backdrop_path: "/b.jpg", poster_path: "/p.jpg", sensitive: true }));
    runAt("/movie/7");
    expect(await window.__mmEarlyFilm?.film).toBeNull();
    expect(preloads()).toHaveLength(0);
  });

  it("gives null, and no preload, when the request fails or is refused", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    runAt("/movie/7");
    expect(await window.__mmEarlyFilm?.film).toBeNull();
    vi.stubGlobal("fetch", answer({ detail: "not found" }, false));
    runAt("/movie/8");
    expect(await window.__mmEarlyFilm?.film).toBeNull();
    expect(preloads()).toHaveLength(0);
  });

  it("does nothing off a film page", () => {
    const fetch = answer({});
    vi.stubGlobal("fetch", fetch);
    for (const path of ["/", "/movie/abc", "/movie/7/more", "/watchlist"]) runAt(path);
    expect(fetch).not.toHaveBeenCalled();
    expect(window.__mmEarlyFilm).toBeUndefined();
  });

  it("is built only with a real API URL, at the top of <head>", () => {
    expect(earlyFilmTag(undefined)).toEqual([]);
    expect(earlyFilmTag("  ")).toEqual([]);
    expect(earlyFilmTag("not a url")).toEqual([]);
    expect(earlyFilmTag(API)).toEqual([
      { tag: "script", children: earlyFilmScript(API), injectTo: "head-prepend" },
    ]);
  });
});
