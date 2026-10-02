import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DNA, detail, movie, rating } from "../dev/fixtures";
import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import type { Rating, WatchlistItem } from "../lib/types";
import { pending, renderWithProviders } from "../test/utils";
import MoviePage, { comparedTraits } from "./MoviePage";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi } = await import("../test/utils");
  return { ...actual, api: mockedApi(actual.api) };
});

const getMovie = vi.mocked(api.getMovie);
const explanation = vi.mocked(api.explanation);
const ratings = vi.mocked(api.ratings);
const rate = vi.mocked(api.rate);
const dna = vi.mocked(api.dna);
const watchlist = vi.mocked(api.watchlist);
const add = vi.mocked(api.addToWatchlist);

const FILM = detail(movie(0));
const ROUTE = { route: "/movie/1000", path: "/movie/:id" };

/** A promise the test settles by hand. */
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

async function rateFilm(value: string) {
  await userEvent.click(await screen.findByRole("button", { name: /Rate$/ }));
  const dialog = screen.getByRole("dialog", { name: "Rate The Prestige" });
  fireEvent.change(within(dialog).getByRole("slider"), { target: { value } });
  await userEvent.click(within(dialog).getByRole("button", { name: "Save rating" }));
}

describe("MoviePage", () => {
  beforeEach(() => {
    for (const fn of [getMovie, explanation, ratings, rate, dna, watchlist, add]) fn.mockReset();
    getMovie.mockResolvedValue(FILM);
    explanation.mockResolvedValue({ movie_id: 1000, lang: "en", text: "Twisty and cerebral, like your favourites." });
    ratings.mockResolvedValue([]);
    dna.mockResolvedValue(DNA);
    watchlist.mockResolvedValue([]);
  });

  it("renders its loading state", () => {
    getMovie.mockReturnValue(pending());
    renderWithProviders(<MoviePage />, ROUTE);
    expect(screen.getByTestId("loading")).toBeInTheDocument();
  });

  it("renders the film from the API: match, why, comparison, facts", async () => {
    renderWithProviders(<MoviePage />, ROUTE);
    expect(await screen.findByRole("heading", { level: 1, name: "The Prestige" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "94% match" })).toBeInTheDocument();
    expect(await screen.findByText("Twisty and cerebral, like your favourites.")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Your taste vs this film" })).toBeInTheDocument();
    expect(screen.getByText("Christopher Nolan")).toBeInTheDocument();
    expect(screen.getByText(/2006 · 130m · Drama, Mystery/)).toBeInTheDocument();
    expect(getMovie).toHaveBeenCalledWith(1000);
    expect(explanation).toHaveBeenCalledWith(1000, "en");
  });

  it("shows the explanation skeleton while it loads", async () => {
    const pendingText = deferred<{ movie_id: number; lang: "en"; text: string | null }>();
    explanation.mockReturnValue(pendingText.promise);
    renderWithProviders(<MoviePage />, ROUTE);
    expect(await screen.findByTestId("explanation-skeleton")).toBeInTheDocument();
    // the rest of the page does not wait for it (FR-6)
    expect(screen.getByRole("heading", { level: 1, name: "The Prestige" })).toBeInTheDocument();

    pendingText.resolve({ movie_id: 1000, lang: "en", text: "Now it is here." });
    expect(await screen.findByText("Now it is here.")).toBeInTheDocument();
    expect(screen.queryByTestId("explanation-skeleton")).not.toBeInTheDocument();
  });

  it("falls back to the shared traits when there is no explanation", async () => {
    explanation.mockResolvedValue({ movie_id: 1000, lang: "en", text: null });
    renderWithProviders(<MoviePage />, ROUTE);
    expect(
      await screen.findByText("What you share with it: Psychological, Plot twists, Mystery."),
    ).toBeInTheDocument();
  });

  it("says it suits overall when the match has no standout reason", async () => {
    getMovie.mockResolvedValue(detail(movie(0), { reasons: [] }));
    explanation.mockResolvedValue({ movie_id: 1000, lang: "en", text: null });
    renderWithProviders(<MoviePage />, ROUTE);
    expect(
      await screen.findByText("It suits your taste overall rather than through one standout quality."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/What you share with it/)).not.toBeInTheDocument();
  });

  it("does not ask for an explanation without a match", async () => {
    getMovie.mockResolvedValue(detail(movie(0), { match: null, reasons: [] }));
    renderWithProviders(<MoviePage />, ROUTE);
    expect(await screen.findByText(/Rate 10 films first/)).toBeInTheDocument();
    expect(explanation).not.toHaveBeenCalled();
  });

  it("updates the rating optimistically and rolls it back on a failed request", async () => {
    const request = deferred<Rating>();
    rate.mockReturnValue(request.promise);
    renderWithProviders(<MoviePage />, ROUTE);

    await rateFilm("8.5");
    // shown before the server has answered
    expect(await screen.findByTestId("my-rating")).toHaveTextContent("Your rating: 8.5");
    expect(rate).toHaveBeenCalledWith({ movie_id: 1000, score: 8.5, liked_aspects: [] });

    request.reject(new ApiError(500, "db down"));
    await waitFor(() => expect(screen.queryByTestId("my-rating")).not.toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent("The rating wasn't saved. Try again.");
    expect(screen.getByRole("button", { name: /Rate$/ })).toBeInTheDocument();
  });

  it("rolls back to the previous rating, not to nothing", async () => {
    ratings.mockResolvedValue([rating(1000, 6)]);
    rate.mockRejectedValue(new ApiError(0, "offline"));
    renderWithProviders(<MoviePage />, ROUTE);
    expect(await screen.findByTestId("my-rating")).toHaveTextContent("Your rating: 6.0");

    await userEvent.click(screen.getByRole("button", { name: /Your rating: 6.0/ }));
    const dialog = screen.getByRole("dialog");
    fireEvent.change(within(dialog).getByRole("slider"), { target: { value: "9" } });
    await userEvent.click(within(dialog).getByRole("button", { name: "Save rating" }));

    await screen.findByRole("alert");
    expect(screen.getByTestId("my-rating")).toHaveTextContent("Your rating: 6.0");
  });

  it("keeps a successful rating", async () => {
    rate.mockImplementation(async (body) => rating(body.movie_id, body.score));
    renderWithProviders(<MoviePage />, ROUTE);
    ratings.mockResolvedValue([rating(1000, 9)]); // what the refetch after saving returns
    await rateFilm("9");
    expect(await screen.findByTestId("my-rating")).toHaveTextContent("Your rating: 9.0");
    await waitFor(() => expect(ratings).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("saves to the watchlist optimistically", async () => {
    const request = deferred<WatchlistItem>();
    add.mockReturnValue(request.promise);
    renderWithProviders(<MoviePage />, ROUTE);
    const button = await screen.findByRole("button", { name: /Save$/ });
    await userEvent.click(button);
    expect(screen.getByRole("button", { name: /Saved$/ })).toHaveAttribute("aria-pressed", "true");

    request.reject(new ApiError(500, "no"));
    expect(await screen.findByRole("button", { name: /Save$/ })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("alert")).toHaveTextContent("Your watchlist didn't change.");
  });

  it("renders its empty state for a film that does not exist", async () => {
    getMovie.mockRejectedValue(new ApiError(404, '{"detail":"Movie not found"}'));
    renderWithProviders(<MoviePage />, { route: "/movie/42", path: "/movie/:id" });
    expect(await screen.findByText(/We couldn't find this film/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go home" })).toHaveAttribute("href", "/");
  });

  it("renders its error state with a retry that refetches", async () => {
    getMovie.mockRejectedValueOnce(new ApiError(502, "bad gateway"));
    renderWithProviders(<MoviePage />, ROUTE);
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Couldn't load this film.");
    expect(alert).not.toHaveTextContent("502");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { level: 1, name: "The Prestige" })).toBeInTheDocument();
    expect(getMovie).toHaveBeenCalledTimes(2);
  });
});

describe("comparedTraits", () => {
  it("puts the match's reasons first, then the film's strongest traits", () => {
    const film = detail(movie(0), {
      reasons: ["mystery"],
      traits: {
        summary: null,
        scores: { mystery: 60, darkness: 99, humor: 98, romance: 10, action: 97, pacing: 96 },
      },
    });
    expect(comparedTraits(film)).toEqual(["mystery", "darkness", "humor", "action", "pacing"]);
  });
});
