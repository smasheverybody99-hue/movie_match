import { fireEvent, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MOVIES, rating } from "../dev/fixtures";
import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import { loadProgress, saveProgress } from "../lib/onboardingStore";
import type { RatingIn, Recommendations } from "../lib/types";
import { createTestQueryClient, navigatedTo, pending, renderWithProviders, TEST_SESSION } from "../test/utils";
import Onboarding from "./Onboarding";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi } = await import("../test/utils");
  return { ...actual, api: mockedApi(actual.api) };
});

const films = vi.mocked(api.onboardingFilms);
const ratings = vi.mocked(api.ratings);
const rate = vi.mocked(api.rate);
const search = vi.mocked(api.searchMovies);

const ROUTE = { route: "/onboarding", path: "/onboarding" };

/**
 * Pick MOVIES[from..to) by tapping their tiles. Each tap costs ~100 ms in jsdom (a role
 * query over the whole grid, then a click), so keep the count low. `signal` is the test's:
 * Vitest does not stop a test that times out, and without the check its remaining taps
 * would land on the next test's screen and fail that test instead.
 */
async function pick(signal: AbortSignal, to: number, from = 0) {
  for (const movie of MOVIES.slice(from, to)) {
    signal.throwIfAborted();
    const tile = await screen.findByRole("button", { name: movie.title });
    signal.throwIfAborted();
    await userEvent.click(tile);
  }
}

function slider(): HTMLInputElement {
  return screen.getByRole("slider", { name: "Score out of 10" });
}

describe("Onboarding", () => {
  beforeEach(() => {
    localStorage.clear();
    films.mockReset();
    ratings.mockReset();
    rate.mockReset();
    search.mockReset();
    films.mockResolvedValue(MOVIES);
    ratings.mockResolvedValue([]);
    rate.mockImplementation(async (body: RatingIn) => rating(body.movie_id, body.score));
    search.mockResolvedValue([]);
  });

  it("renders its loading state", () => {
    films.mockReturnValue(pending());
    renderWithProviders(<Onboarding />, ROUTE);
    expect(screen.getByTestId("loading")).toBeInTheDocument();
  });

  it("renders its empty state with a way forward", async () => {
    films.mockResolvedValue([]);
    renderWithProviders(<Onboarding />, ROUTE);
    expect(await screen.findByText("No films here yet. Try searching by title.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Search films" }));
    expect(screen.getByRole("searchbox", { name: "Search films" })).toHaveFocus();
  });

  it("renders its error state with a retry that refetches", async () => {
    films.mockRejectedValueOnce(new ApiError(500, "boom"));
    renderWithProviders(<Onboarding />, ROUTE);
    expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't load films.");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("button", { name: "The Prestige" })).toBeInTheDocument();
    expect(films).toHaveBeenCalledTimes(2);
  });

  it("renders the films to pick from the API", async () => {
    renderWithProviders(<Onboarding />, ROUTE);
    expect(await screen.findByRole("button", { name: "Memento" })).toBeInTheDocument();
    expect(films).toHaveBeenCalledWith(60, 0);
  });

  it("keeps continue disabled below 10 picks and enables it at 10", async ({ signal }) => {
    // Eight picks already made; the taps that cross the threshold are the ones under test.
    saveProgress(TEST_SESSION.userId, { step: "pick", picks: MOVIES.slice(0, 8), index: 0, offset: 0 });
    renderWithProviders(<Onboarding />, ROUTE);
    await screen.findByText("8 / 10 picked");
    await pick(signal, 9, 8);
    expect(screen.getByText("9 / 10 picked")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pick 1 more" })).toBeDisabled();

    await pick(signal, 10, 9);
    expect(screen.getByText("10 / 10 picked")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue" })).toBeEnabled();
  });

  it("unpicks a film on a second tap", async ({ signal }) => {
    renderWithProviders(<Onboarding />, ROUTE);
    await pick(signal, 1);
    await userEvent.click(screen.getByRole("button", { name: "The Prestige, selected" }));
    expect(screen.getByRole("button", { name: "The Prestige" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByText("0 / 10 picked")).toBeInTheDocument();
  });

  it("counts films already rated towards the 10", async ({ signal }) => {
    ratings.mockResolvedValue([rating(1, 8), rating(2, 7), rating(3, 9), rating(4, 6)]);
    saveProgress(TEST_SESSION.userId, { step: "pick", picks: MOVIES.slice(0, 4), index: 0, offset: 0 });
    renderWithProviders(<Onboarding />, ROUTE);
    await screen.findByText("8 / 10 picked");
    await pick(signal, 5, 4);
    expect(screen.getByRole("button", { name: "Pick 1 more" })).toBeDisabled();
    await pick(signal, 6, 5);
    expect(screen.getByRole("button", { name: "Continue" })).toBeEnabled();
  });

  it("loads the next films when none of these have been seen", async () => {
    renderWithProviders(<Onboarding />, ROUTE);
    await screen.findByRole("button", { name: "Memento" });
    await userEvent.click(screen.getByRole("button", { name: "I haven't seen any of these" }));
    expect(films).toHaveBeenLastCalledWith(60, 60);
  });

  it("shows liked-aspect chips above 8.0 and not below", async () => {
    saveProgress(TEST_SESSION.userId, { step: "rate", picks: MOVIES.slice(0, 10), index: 0, offset: 0 });
    renderWithProviders(<Onboarding />, ROUTE);
    await screen.findByRole("heading", { name: "How much did you like it?" });

    fireEvent.change(slider(), { target: { value: "7.5" } });
    expect(screen.queryByTestId("liked-aspects")).not.toBeInTheDocument();
    fireEvent.change(slider(), { target: { value: "8" } });
    expect(screen.queryByTestId("liked-aspects")).not.toBeInTheDocument();

    fireEvent.change(slider(), { target: { value: "8.5" } });
    expect(screen.getByTestId("liked-aspects")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "What did you like?" })).toBeInTheDocument();
  });

  it("sends the score and the chosen aspects, then moves to the next film", async () => {
    saveProgress(TEST_SESSION.userId, { step: "rate", picks: MOVIES.slice(0, 10), index: 0, offset: 0 });
    renderWithProviders(<Onboarding />, ROUTE);
    await screen.findByRole("heading", { name: "The Prestige" });

    fireEvent.change(slider(), { target: { value: "9.5" } });
    await userEvent.click(screen.getByRole("button", { name: "Plot twists" }));
    await userEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(rate).toHaveBeenCalledWith({ movie_id: 1000, score: 9.5, liked_aspects: ["plot_twist"] });
    expect(await screen.findByRole("heading", { name: "Memento" })).toBeInTheDocument();
    expect(screen.getByText("2 / 10")).toBeInTheDocument();
    // The next film starts afresh: default score, no aspects.
    expect(slider().value).toBe("7");
    expect(screen.queryByTestId("liked-aspects")).not.toBeInTheDocument();
  });

  it("takes whole-number scores from the keyboard", async () => {
    saveProgress(TEST_SESSION.userId, { step: "rate", picks: MOVIES.slice(0, 10), index: 0, offset: 0 });
    renderWithProviders(<Onboarding />, ROUTE);
    await screen.findByRole("heading", { name: "The Prestige" });
    await userEvent.keyboard("9");
    expect(slider().value).toBe("9");
    await userEvent.keyboard("0");
    expect(slider().value).toBe("10");
  });

  it("stays on the film and says so when the rating fails", async () => {
    rate.mockRejectedValueOnce(new ApiError(0, "Failed to fetch"));
    saveProgress(TEST_SESSION.userId, { step: "rate", picks: MOVIES.slice(0, 10), index: 0, offset: 0 });
    renderWithProviders(<Onboarding />, ROUTE);
    await userEvent.click(await screen.findByRole("button", { name: "Next" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't save the score.");
    expect(screen.getByRole("heading", { name: "The Prestige" })).toBeInTheDocument();
  });

  it("restores progress after a remount", async ({ signal }) => {
    const first = renderWithProviders(<Onboarding />, ROUTE);
    await pick(signal, 3);
    expect(screen.getByText("3 / 10 picked")).toBeInTheDocument();
    first.unmount();

    renderWithProviders(<Onboarding />, ROUTE);
    expect(await screen.findByText("3 / 10 picked")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "The Prestige, selected" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(loadProgress(TEST_SESSION.userId).picks.map((m) => m.id)).toEqual([1000, 1001, 1002]);
  });

  it("while a rating saves, Next says so inside, stays enabled and a second press sends nothing", async () => {
    rate.mockReturnValue(pending());
    saveProgress(TEST_SESSION.userId, { step: "rate", picks: MOVIES.slice(0, 10), index: 0, offset: 0 });
    renderWithProviders(<Onboarding />, ROUTE);
    const next = await screen.findByRole("button", { name: "Next" });
    await userEvent.click(next);

    expect(next).not.toBeDisabled();
    expect(next).toHaveAttribute("aria-disabled", "true");
    expect(within(next).getByTestId("saving")).toHaveTextContent("Saving…");
    await userEvent.click(next);
    expect(rate).toHaveBeenCalledTimes(1);
  });

  it("restores the rating position after a remount", async () => {
    saveProgress(TEST_SESSION.userId, { step: "rate", picks: MOVIES.slice(0, 10), index: 0, offset: 0 });
    const first = renderWithProviders(<Onboarding />, ROUTE);
    await userEvent.click(await screen.findByRole("button", { name: "Next" }));
    await screen.findByRole("heading", { name: "Memento" });
    first.unmount();

    renderWithProviders(<Onboarding />, ROUTE);
    expect(await screen.findByRole("heading", { name: "Memento" })).toBeInTheDocument();
  });

  it("finishes after the tenth rating and goes to the feed", async () => {
    ratings.mockResolvedValue(MOVIES.slice(10, 19).map((m) => rating(m.id, 8)));
    saveProgress(TEST_SESSION.userId, { step: "rate", picks: MOVIES.slice(0, 1), index: 0, offset: 0 });
    // A feed cached before the ratings ("rate 10 more", in both languages) must not survive.
    const queryClient = createTestQueryClient();
    const stale = { status: "not_enough_data", ratings_needed: 10, sections: [] } satisfies Recommendations;
    queryClient.setQueryData(["recommendations", "en"], stale);
    queryClient.setQueryData(["recommendations", "ru"], stale);
    renderWithProviders(<Onboarding />, { ...ROUTE, queryClient });
    await screen.findByRole("heading", { name: "The Prestige" });
    await userEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByRole("heading", { name: "All set!" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "See my recommendations" }));
    expect(await navigatedTo()).toBe("/");
    expect(loadProgress(TEST_SESSION.userId).step).toBe("pick");
    expect(queryClient.getQueryData(["recommendations", "en"])).toBeUndefined();
    expect(queryClient.getQueryData(["recommendations", "ru"])).toBeUndefined();
  });
});
