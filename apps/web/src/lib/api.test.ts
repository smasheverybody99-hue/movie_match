import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api, ApiError, isNotFound, searchQuery, setAccessToken } from "./api";

const fetchMock = vi.fn<typeof fetch>();

function lastRequest(): { url: string; init: RequestInit; headers: Headers } {
  const call = fetchMock.mock.calls.at(-1);
  if (!call) throw new Error("fetch was not called");
  const [url, init = {}] = call;
  return { url: String(url), init, headers: new Headers(init.headers) };
}

describe("api", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockReset();
  });

  afterEach(() => {
    setAccessToken(null);
    vi.unstubAllGlobals();
  });

  it("attaches the bearer token", async () => {
    fetchMock.mockResolvedValue(new Response("[]", { status: 200 }));
    setAccessToken("abc.def.ghi");
    await api.ratings();
    expect(lastRequest().headers.get("Authorization")).toBe("Bearer abc.def.ghi");
  });

  it("sends no Authorization header when signed out", async () => {
    fetchMock.mockResolvedValue(new Response("[]", { status: 200 }));
    await api.searchMovies({ q: "heat" });
    expect(lastRequest().headers.has("Authorization")).toBe(false);
  });

  it("throws ApiError with the status on failure", async () => {
    fetchMock.mockResolvedValue(new Response('{"detail":"Movie not found"}', { status: 404 }));
    const error = await api.getMovie(7).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(404);
    expect(isNotFound(error)).toBe(true);
  });

  it("throws ApiError with status 0 when the API cannot be reached", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    const error = await api.me().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(0);
  });

  it("posts JSON and returns the parsed body", async () => {
    const saved = { movie_id: 3, score: 8.5, liked_aspects: [], rated_at: "2026-09-29T10:00:00Z" };
    fetchMock.mockResolvedValue(new Response(JSON.stringify(saved), { status: 200 }));
    await expect(api.rate({ movie_id: 3, score: 8.5 })).resolves.toEqual(saved);
    const { init, headers } = lastRequest();
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(JSON.parse(String(init.body))).toEqual({ movie_id: 3, score: 8.5 });
  });

  it("returns nothing for 204 instead of failing to parse", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));
    await expect(api.removeFromWatchlist(3)).resolves.toBeUndefined();
    expect(lastRequest().init.method).toBe("DELETE");
  });
});

describe("searchQuery", () => {
  it("maps filters to the API's parameters", () => {
    const query = new URLSearchParams(
      searchQuery({
        q: "night",
        yearFrom: 2000,
        yearTo: 2010,
        maxRuntime: 90,
        traits: ["darkness", "mystery"],
        traitMinimum: 70,
      }),
    );
    expect(query.get("q")).toBe("night");
    expect(query.get("year_from")).toBe("2000");
    expect(query.get("year_to")).toBe("2010");
    expect(query.get("max_runtime")).toBe("90");
    expect(query.getAll("trait")).toEqual(["darkness:70", "mystery:70"]);
  });

  it("leaves out what is not set", () => {
    expect(searchQuery({})).toBe("limit=40");
  });
});
