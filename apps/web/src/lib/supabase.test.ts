import { AuthClient } from "@supabase/auth-js";
import { createClient } from "@supabase/supabase-js";
import { afterEach, describe, expect, it, vi } from "vitest";

import { authClientOptions } from "./supabase";

const URL_ = "https://abcdefghijklmnop.supabase.co";
const KEY = "anon-key-for-tests";

/** The settings a built client actually runs with (protected fields, read at runtime). */
function settingsOf(client: InstanceType<typeof AuthClient>) {
  const c = client as unknown as Record<string, unknown> & { headers: Record<string, string> };
  return {
    storageKey: c.storageKey,
    url: c.url,
    apikey: c.headers.apikey,
    authorization: c.headers.Authorization,
    persistSession: c.persistSession,
    autoRefreshToken: c.autoRefreshToken,
    detectSessionInUrl: c.detectSessionInUrl,
    flowType: c.flowType,
  };
}

describe("authClientOptions", () => {
  afterEach(() => vi.restoreAllMocks());

  it("keeps the storage key saved sessions live under: sb-<project ref>-auth-token", () => {
    expect(authClientOptions(URL_, KEY).storageKey).toBe("sb-abcdefghijklmnop-auth-token");
    expect(authClientOptions(`${URL_}/`, KEY).storageKey).toBe("sb-abcdefghijklmnop-auth-token");
    // auth-js on its own would use another key, and everyone would be signed out
    expect(authClientOptions(URL_, KEY).storageKey).not.toBe("supabase.auth.token");
  });

  it("builds the same auth client createClient did: key, url, headers, flow, session options", () => {
    vi.spyOn(console, "warn").mockImplementation(() => {}); // two clients on one storage key
    const skip = { skipAutoInitialize: true }; // no timers or storage reads in the test
    const before = createClient(URL_, KEY, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, ...skip },
    }).auth;
    const after = new AuthClient({ ...authClientOptions(URL_, KEY), ...skip });

    expect(settingsOf(after)).toEqual(settingsOf(before));
    expect(settingsOf(after)).toEqual({
      storageKey: "sb-abcdefghijklmnop-auth-token",
      url: `${URL_}/auth/v1`,
      apikey: KEY,
      authorization: `Bearer ${KEY}`,
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      flowType: "implicit",
    });
  });
});
