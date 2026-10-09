import { describe, expect, it } from "vitest";

import { preconnectLinks } from "./preconnect";

describe("preconnectLinks", () => {
  it("gives one crossorigin preconnect per origin, without the path", () => {
    expect(
      preconnectLinks(["https://api.example.com/", "https://abcd.supabase.co/auth/v1"]),
    ).toEqual([
      {
        tag: "link",
        attrs: { rel: "preconnect", href: "https://api.example.com", crossorigin: true },
        injectTo: "head",
      },
      {
        tag: "link",
        attrs: { rel: "preconnect", href: "https://abcd.supabase.co", crossorigin: true },
        injectTo: "head",
      },
    ]);
  });

  it("gives no link for an empty, missing or malformed URL (CI and test builds)", () => {
    expect(preconnectLinks([undefined, "", "  ", "not a url"])).toEqual([]);
  });

  it("does not repeat an origin", () => {
    expect(preconnectLinks(["https://x.example.com/a", "https://x.example.com/b"])).toHaveLength(1);
  });
});
