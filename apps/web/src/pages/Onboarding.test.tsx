import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MOVIES, rating } from "../dev/fixtures";
import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import { loadProgress, saveProgress } from "../lib/onboardingStore";
import type { RatingIn } from "../lib/types";
import { navigatedTo, pending, renderWithProviders, TEST_SESSION } from "../test/utils";
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

/** Pick MOVIES[from..to) by tapping their tiles. */
async function pick(to: number, from = 0) {
  for (const movie of MOVIES.slice(from, to)) {
    await userEvent.click(await screen.findByRole("button", { name: movie.title }));
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

  it("keeps continue disabled below 10 picks and enables it at 10", async () => {
    renderWithProviders(<Onboarding />, ROUTE);
    await pick(9);
    expect(screen.getByText("9 / 10 picked")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pick 1 more" })).toBeDisabled();

    await pick(10, 9);
    expect(screen.getByText("10 / 10 picked")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue" })).toBeEnabled();
  });

  it("unpicks a film on a second tap", async () => {
    renderWithProviders(<Onboarding />, ROUTE);
    await pick(1);
    await userEvent.click(screen.getByRole("button", { name: "The Prestige, selected" }));
    expect(screen.getByRole("button", { name: "The Prestige" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByText("0 / 10 picked")).toBeInTheDocument();
  });

  it("counts films already rated towards the 10", async () => {
    ratings.mockResolvedValue([rating(1, 8), rating(2, 7), rating(3, 9), rating(4, 6)]);
    renderWithProviders(<Onboarding />, ROUTE);
    await screen.findByText("4 / 10 picked");
    await pick(5);
    expect(screen.getByRole("button", { name: "Pick 1 more" })).toBeDisabled();
    await pick(6, 5);
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

  it("restores progress after a remount", async () => {
    const first = renderWithProviders(<Onboarding />, ROUTE);
    await pick(3);
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
    renderWithProviders(<Onboarding />, ROUTE);
    await screen.findByRole("heading", { name: "The Prestige" });
    await userEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByRole("heading", { name: "All set!" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "See my recommendations" }));
    expect(await navigatedTo()).toBe("/");
    expect(loadProgress(TEST_SESSION.userId).step).toBe("pick");
  });
});
