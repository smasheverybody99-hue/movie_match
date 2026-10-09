import type { HtmlTagDescriptor } from "vite";

/**
 * Build time only (vite.config.ts): `<link rel="preconnect">` for the API and Supabase, so
 * the browser opens those connections while the bundle is still loading instead of after.
 * Both are fetched with CORS and no cookies, so the link carries `crossorigin` (anonymous):
 * without it the browser opens a separate connection the fetch cannot use.
 * An empty or malformed URL (CI, tests) gives no link rather than an empty one.
 */
export function preconnectLinks(urls: readonly (string | undefined)[]): HtmlTagDescriptor[] {
  const origins = new Set<string>();
  for (const url of urls) {
    if (!url?.trim()) continue;
    try {
      origins.add(new URL(url.trim()).origin);
    } catch {
      // not a URL: nothing to connect to
    }
  }
  return [...origins].map((href) => ({
    tag: "link",
    attrs: { rel: "preconnect", href, crossorigin: true },
    injectTo: "head",
  }));
}
