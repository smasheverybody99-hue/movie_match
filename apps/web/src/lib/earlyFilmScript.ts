import type { HtmlTagDescriptor } from "vite";

import type { MovieDetail } from "./types";

/**
 * The film page's largest paint is the backdrop (F3 item 5, measured 2026-11-18). Opened
 * from a link, the page used to reach it in four steps, one after the other: the bundle,
 * the film's request (a preflight, then the GET, both to Singapore), then the image.
 *
 * A small inline script in index.html (build only, vite.config.ts) starts the film's
 * request while the bundle loads: a plain GET of the public `/movies/{id}`, with no
 * Authorization header, so no preflight. When it answers, the script preloads the backdrop
 * with the hero's own srcset and sizes, so the image the page asks for is the one already
 * on its way. The page's skeleton then draws the hero from that answer (useEarlyFilm),
 * while its own signed-in request, with the match and the reasons, is still out.
 *
 * On phones it first preloads the small w300 backdrop the hero paints first (SOFT_MEDIA).
 *
 * Only the hero's two image paths are used from the early answer. A film marked sensitive
 * gets no preload and no early hero: its page shows no image before the viewer agrees.
 */
export type EarlyFilm = Pick<MovieDetail, "backdrop_path" | "poster_path">;

/** What the script leaves on `window.__mmEarlyFilm`. */
export interface EarlyEntry {
  id: number;
  film: Promise<EarlyFilm | null>;
}

export const TMDB_IMAGES = "https://image.tmdb.org/t/p";

/** The hero's srcset for a backdrop path; the preload must match the <img> exactly. */
export function backdropSrcSet(path: string): string {
  return `${TMDB_IMAGES}/w780${path} 780w, ${TMDB_IMAGES}/w1280${path} 1280w`;
}
export const BACKDROP_SIZES = "100vw";

/**
 * Phones get a soft first paint (F3 item 5, the user's option C, 2026-11-22): the w300
 * backdrop, 19 KB against 105 KB for w780, is drawn first and the sharp image covers it
 * when it arrives. It is the same size on screen, so LCP is the soft paint. 640 px is the
 * layout's phone break (app.css); above it the soft layer is the sharp image itself.
 */
export const SOFT_MEDIA = "(max-width: 639px)";
export const SOFT_ABOVE = "(min-width: 640px)";
export function backdropSoft(path: string): string {
  return `${TMDB_IMAGES}/w300${path}`;
}

/**
 * The inline script's source. Plain ES5, no imports: it runs before the bundle. An empty or
 * malformed API URL gives no script.
 */
export function earlyFilmScript(apiUrl: string | undefined): string | null {
  let base: string;
  try {
    base = new URL((apiUrl ?? "").trim()).href.replace(/\/$/, "");
  } catch {
    return null;
  }
  return `(function () {
  var m = /^\\/movie\\/(\\d+)\\/?$/.exec(location.pathname);
  if (!m || typeof fetch !== "function") return;
  var t = ${JSON.stringify(TMDB_IMAGES)};
  window.__mmEarlyFilm = {
    id: Number(m[1]),
    film: fetch(${JSON.stringify(base)} + "/movies/" + m[1])
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (f) {
        if (!f || f.sensitive) return null;
        if (f.backdrop_path) {
          var s = document.createElement("link");
          s.rel = "preload";
          s.setAttribute("as", "image");
          s.setAttribute("href", t + "/w300" + f.backdrop_path);
          s.setAttribute("media", ${JSON.stringify(SOFT_MEDIA)});
          s.setAttribute("fetchpriority", "high");
          document.head.appendChild(s);
          var l = document.createElement("link");
          l.rel = "preload";
          l.setAttribute("as", "image");
          l.setAttribute("imagesrcset", t + "/w780" + f.backdrop_path + " 780w, " + t + "/w1280" + f.backdrop_path + " 1280w");
          l.setAttribute("imagesizes", ${JSON.stringify(BACKDROP_SIZES)});
          l.setAttribute("fetchpriority", "high");
          document.head.appendChild(l);
        }
        return { backdrop_path: f.backdrop_path || null, poster_path: f.poster_path || null };
      })
      .catch(function () { return null; })
  };
})();`;
}

/** Build time only (vite.config.ts): the script as a tag at the top of <head>. */
export function earlyFilmTag(apiUrl: string | undefined): HtmlTagDescriptor[] {
  const children = earlyFilmScript(apiUrl);
  return children ? [{ tag: "script", children, injectTo: "head-prepend" }] : [];
}
