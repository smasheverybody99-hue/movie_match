import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RECOMMENDATIONS, movie, rating, rec, watchItem } from "../dev/fixtures";
import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import type { Recommendations } from "../lib/types";
import { createTestQueryClient, navigatedTo, pending, renderWithProviders } from "../test/utils";
import Feed from "./Feed";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi: mocked } = await import("../test/utils");
  return { ...actual, api: mocked(actual.api) };
});

const recommendations = vi.mocked(api.recommendations);
const watchlist = vi.mocked(api.watchlist);
const ratings = vi.mocked(api.ratings);
const rate = vi.mocked(api.rate);
const add = vi.mocked(api.addToWatchlist);
const remove = vi.mocked(api.removeFromWatchlist);

describe("Feed", () => {
  beforeEach(() => {
    for (const fn of [recommendations, watchlist, ratings, rate, add, remove]) fn.mockReset();
    watchlist.mockResolvedValue([]);
    ratings.mockResolvedValue([]);
  });

  it("renders its loading state", () => {
    recommendations.mockReturnValue(pending());
    renderWithProviders(<Feed />);
    expect(screen.getByTestId("loading")).toBeInTheDocument();
  });

  describe("first load", () => {
    function motion(reduce: boolean) {
      vi.stubGlobal(
        "matchMedia",
        vi.fn(() => ({ matches: reduce, addEventListener: vi.fn(), removeEventListener: vi.fn() })),
      );
    }
    afterEach(() => {
      vi.useRealTimers();
      vi.unstubAllGlobals();
    });

    it("spins the mark and changes its words at 5 s and 15 s, the last about the server waking", async () => {
      vi.useFakeTimers();
      motion(false);
      recommendations.mockReturnValue(pending());
      renderWithProviders(<Feed />);
      await act(async () => {}); // the session settles

      const loading = screen.getByTestId("loading");
      expect(loading).toHaveAttribute("role", "status");
      expect(loading).toHaveAttribute("aria-live", "polite");
      const mark = within(loading).getByRole("img", { name: "Loading" });
      expect(mark).toHaveAttribute("data-variant", "full");
      expect(mark).toHaveAttribute("width", "72");
      expect(mark).toHaveClass("logo-spin");
      expect(loading).toHaveTextContent("Picking your films…");

      act(() => vi.advanceTimersByTime(4999));
      expect(loading).toHaveTextContent("Picking your films…");
      act(() => vi.advanceTimersByTime(1));
      expect(loading).toHaveTextContent("Still looking…");
      act(() => vi.advanceTimersByTime(9999));
      expect(loading).toHaveTextContent("Still looking…");
      act(() => vi.advanceTimersByTime(1));
      expect(loading).toHaveTextContent("The server is waking up, just a moment…");
    });

    it("with reduced motion the mark stands still and only the words remain", async () => {
      vi.useFakeTimers();
      motion(true);
      recommendations.mockReturnValue(pending());
      renderWithProviders(<Feed />);
      await act(async () => {});
      const loading = screen.getByTestId("loading");
      expect(within(loading).getByRole("img", { name: "Loading" })).not.toHaveClass("logo-spin");
      expect(loading).toHaveTextContent("Picking your films…");
      act(() => vi.advanceTimersByTime(15000));
      expect(loading).toHaveTextContent("The server is waking up, just a moment…");
    });

    it("speaks Uzbek and Russian too", async () => {
      recommendations.mockReturnValue(pending());
      const uz = renderWithProviders(<Feed />, { lang: "uz" });
      await act(async () => {});
      expect(screen.getByTestId("loading")).toHaveTextContent("Filmlaringiz tanlanmoqda…");
      uz.unmount();
      renderWithProviders(<Feed />, { lang: "ru" });
      await act(async () => {});
      expect(screen.getByTestId("loading")).toHaveTextContent("Подбираем ваши фильмы…");
    });
  });

  it("renders sections; For you continues after the hero's five, so no film shows twice", async () => {
    recommendations.mockResolvedValue(RECOMMENDATIONS);
    renderWithProviders(<Feed />);

    expect(await screen.findByRole("heading", { name: "For you" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Because you loved Shutter Island" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Under 90 minutes" })).toBeInTheDocument();

    // the fixtures' For you has six: five in the hero, the sixth starts the row
    expect(within(screen.getByTestId("home-hero")).getByRole("heading", { name: "The Prestige" })).toBeInTheDocument();
    const forYou = screen.getByRole("region", { name: "For you" });
    const first = within(forYou).getAllByRole("link")[0];
    expect(first).toHaveAttribute("href", "/movie/1005");
    expect(within(forYou).queryByText("The Prestige")).not.toBeInTheDocument();
    expect(within(forYou).queryByText("Memento")).not.toBeInTheDocument();
    expect(recommendations).toHaveBeenCalledWith("en");
  });

  it("does not render a section that has no items at all", async () => {
    recommendations.mockResolvedValue(RECOMMENDATIONS);
    renderWithProviders(<Feed />);
    await screen.findByRole("heading", { name: "For you" });
    // outside_usual is in the response with an empty list
    expect(screen.queryByRole("heading", { name: "Outside your usual taste" })).not.toBeInTheDocument();
    // three rows and the hero
    expect(screen.getAllByRole("region")).toHaveLength(4);
    expect(screen.getByRole("region", { name: "Top picks for you" })).toBeInTheDocument();
  });

  it("shows the band, never the number: red only for strong, nothing on a card for good", async () => {
    const data: Recommendations = {
      status: "ok",
      ratings_needed: 0,
      sections: [
        {
          key: "for_you",
          seed: null,
          // five for the hero, then the row: strong, good, none
          items: [0, 1, 2, 3, 4].map((i) => rec(movie(i), 95 - i, "strong")).concat([
            rec(movie(5), 91, "strong"),
            rec(movie(6), 88, "good"),
            rec(movie(7), 73, null),
          ]),
        },
      ],
    };
    recommendations.mockResolvedValue(data);
    renderWithProviders(<Feed />);
    await screen.findByRole("heading", { name: "For you" });
    // on the cards: strong only
    const row = screen.getByRole("region", { name: "For you" });
    expect(within(row).getAllByText("Strong match")).toHaveLength(1);
    expect(within(row).queryByText("Good match")).not.toBeInTheDocument();
    // the hero's kicker for the first pick: the same red kicker as the film page
    expect(within(screen.getByTestId("home-hero")).getByText("Strong match")).toHaveClass("kicker-strong");
    expect(screen.queryByText(/\d+%/)).not.toBeInTheDocument();
  });

  it("puts the top five of For you in the hero, and never asks for an explanation", async () => {
    const data: Recommendations = {
      ...RECOMMENDATIONS,
      sections: RECOMMENDATIONS.sections.map((s) =>
        s.key === "for_you" ? { ...s, items: [0, 1, 2, 3, 4, 5, 6].map((i) => rec(movie(i), 94 - i)) } : s,
      ),
    };
    recommendations.mockResolvedValue(data);
    renderWithProviders(<Feed />);
    const hero = await screen.findByTestId("home-hero");
    expect(within(hero).getByRole("heading", { level: 2, name: "The Prestige" })).toBeInTheDocument();
    expect(within(hero).getAllByRole("button", { name: /^Film \d of 5$/ })).toHaveLength(5);
    expect(vi.mocked(api.explanation)).not.toHaveBeenCalled();
  });

  it("with five or fewer in For you: all in the hero, and no For you row", async () => {
    recommendations.mockResolvedValue({
      ...RECOMMENDATIONS,
      sections: RECOMMENDATIONS.sections.map((s) => (s.key === "for_you" ? { ...s, items: s.items.slice(0, 5) } : s)),
    });
    renderWithProviders(<Feed />);
    expect(await screen.findByTestId("home-hero")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "For you" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Under 90 minutes" })).toBeInTheDocument();
  });

  it("has no hero when For you is empty", async () => {
    recommendations.mockResolvedValue({
      ...RECOMMENDATIONS,
      sections: RECOMMENDATIONS.sections.map((s) => (s.key === "for_you" ? { ...s, items: [] } : s)),
    });
    renderWithProviders(<Feed />);
    await screen.findByRole("heading", { name: "Under 90 minutes" });
    expect(screen.queryByTestId("home-hero")).not.toBeInTheDocument();
  });

  it("renders its empty state with a call to action when nothing matches", async () => {
    recommendations.mockResolvedValue({
      status: "ok",
      ratings_needed: 0,
      sections: [{ key: "for_you", seed: null, items: [] }],
    });
    renderWithProviders(<Feed />);
    expect(await screen.findByText(/No recommendations for you yet/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Search films" })).toHaveAttribute("href", "/search");
  });

  it("asks for more ratings below 10, with a link back to onboarding", async () => {
    recommendations.mockResolvedValue({ status: "not_enough_data", ratings_needed: 4, sections: [] });
    renderWithProviders(<Feed />);
    expect(await screen.findByText("Rate 4 more films to get recommendations.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Keep rating" })).toHaveAttribute("href", "/onboarding");
  });

  it("sends a user with no ratings to onboarding", async () => {
    recommendations.mockResolvedValue({ status: "not_enough_data", ratings_needed: 10, sections: [] });
    renderWithProviders(<Feed />);
    expect(await navigatedTo()).toBe("/onboarding");
  });

  it("waits for the fresh feed instead of acting on a cached 'rate 10 more'", async () => {
    // The F3 defect: cached before the ratings, shown while the new feed loads, it sent
    // a user who had just finished onboarding straight back to it.
    let resolve: (value: Recommendations) => void = () => {};
    recommendations.mockReturnValue(new Promise<Recommendations>((r) => (resolve = r)));
    const queryClient = createTestQueryClient();
    queryClient.setQueryData(["recommendations", "en"], {
      status: "not_enough_data",
      ratings_needed: 10,
      sections: [],
    } satisfies Recommendations);
    renderWithProviders(<Feed />, { queryClient });

    expect(screen.getByTestId("loading")).toBeInTheDocument();
    expect(screen.queryByTestId("location")).not.toBeInTheDocument();
    resolve(RECOMMENDATIONS);
    expect(await screen.findByRole("heading", { name: "For you" })).toBeInTheDocument();
    expect(screen.queryByTestId("location")).not.toBeInTheDocument();
  });

  it("renders its error state with a retry that refetches", async () => {
    recommendations.mockRejectedValueOnce(new ApiError(503, "upstream timeout"));
    recommendations.mockResolvedValueOnce(RECOMMENDATIONS);
    renderWithProviders(<Feed />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Couldn't load recommendations.");
    expect(alert).not.toHaveTextContent("503");
    expect(alert).not.toHaveTextContent("upstream");

    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "For you" })).toBeInTheDocument();
    expect(recommendations).toHaveBeenCalledTimes(2);
  });

  it("uses the chosen language for titles and for the request", async () => {
    recommendations.mockResolvedValue(RECOMMENDATIONS);
    renderWithProviders(<Feed />, { lang: "uz" });
    expect(await screen.findByRole("heading", { name: "Shutter Island yoqqani uchun" })).toBeInTheDocument();
    expect(recommendations).toHaveBeenCalledWith("uz");
  });

  it("puts a neutral icon before each row's title", async () => {
    recommendations.mockResolvedValue(RECOMMENDATIONS);
    renderWithProviders(<Feed />);
    const title = await screen.findByRole("heading", { name: "For you" });
    const icon = title.querySelector("svg");
    expect(icon).toHaveAttribute("aria-hidden", "true");
  });

  it("gives each card quick Rate and Save buttons beside its link, not inside it", async () => {
    recommendations.mockResolvedValue(RECOMMENDATIONS);
    renderWithProviders(<Feed />);
    const rateButton = await screen.findByRole("button", { name: "Rate Enemy" });
    const saveButton = screen.getByRole("button", { name: "Save Enemy" });
    expect(saveButton).toHaveAttribute("aria-pressed", "false");
    expect(rateButton.closest("a")).toBeNull();
    expect(saveButton.closest("a")).toBeNull();
    // the card's link still opens the film page
    expect(screen.getAllByRole("link", { name: /Enemy/ })[0]).toHaveAttribute("href", "/movie/1006");
  });

  it("rates from the card through the rating dialog, starting at the current score", async () => {
    recommendations.mockResolvedValue(RECOMMENDATIONS);
    ratings.mockResolvedValue([rating(1006, 6)]);
    rate.mockImplementation(async (body) => rating(body.movie_id, body.score));
    renderWithProviders(<Feed />);
    await userEvent.click(await screen.findByRole("button", { name: "Rate Enemy" }));
    const dialog = await screen.findByRole("dialog", { name: "Rate Enemy" });
    await waitFor(() => expect(within(dialog).getByRole("slider")).toHaveValue("6"));
    fireEvent.change(within(dialog).getByRole("slider"), { target: { value: "8" } });
    await userEvent.click(within(dialog).getByRole("button", { name: "Save rating" }));
    expect(rate).toHaveBeenCalledWith({ movie_id: 1006, score: 8, liked_aspects: [] });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("saves from the card at once, and takes it off for a film already on the list", async () => {
    recommendations.mockResolvedValue(RECOMMENDATIONS);
    watchlist.mockResolvedValue([watchItem(movie(10))]);
    add.mockReturnValue(pending());
    remove.mockReturnValue(pending());
    renderWithProviders(<Feed />);

    const enemy = await screen.findByRole("button", { name: "Save Enemy" });
    await userEvent.click(enemy);
    expect(add).toHaveBeenCalledWith(1006);
    expect(enemy).toHaveAttribute("aria-pressed", "true"); // before the server answers

    const arrival = screen.getByRole("button", { name: "Save Arrival" });
    await waitFor(() => expect(arrival).toHaveAttribute("aria-pressed", "true"));
    await userEvent.click(arrival);
    expect(remove).toHaveBeenCalledWith(1010);
  });

  it("says so when a quick save fails, and rolls the button back", async () => {
    recommendations.mockResolvedValue(RECOMMENDATIONS);
    add.mockRejectedValue(new ApiError(500, "no"));
    renderWithProviders(<Feed />);
    const button = await screen.findByRole("button", { name: "Save Enemy" });
    await userEvent.click(button);
    expect(await screen.findByRole("alert")).toHaveTextContent("Your watchlist didn't change. Try again.");
    expect(button).toHaveAttribute("aria-pressed", "false");
  });

  describe("row scrolling", () => {
    const size = (name: "scrollWidth" | "clientWidth", value: number) =>
      vi.spyOn(HTMLElement.prototype, name, "get").mockReturnValue(value);
    afterEach(() => vi.restoreAllMocks());

    it("shows Next while there is more to the right, and scrolls by most of a screen", async () => {
      size("scrollWidth", 2000);
      size("clientWidth", 1000);
      const scrollBy = vi.fn();
      HTMLElement.prototype.scrollBy = scrollBy;
      recommendations.mockResolvedValue(RECOMMENDATIONS);
      renderWithProviders(<Feed />);
      const forYou = await screen.findByRole("region", { name: "For you" });
      // at the start: no Previous
      expect(within(forYou).queryByRole("button", { name: "Previous films" })).not.toBeInTheDocument();
      await userEvent.click(within(forYou).getByRole("button", { name: "Next films" }));
      // reduced motion in tests (no matchMedia): an instant jump
      expect(scrollBy).toHaveBeenCalledWith({ left: 800, behavior: "auto" });
    });

    it("shows neither button when the row fits", async () => {
      size("scrollWidth", 900);
      size("clientWidth", 1000);
      recommendations.mockResolvedValue(RECOMMENDATIONS);
      renderWithProviders(<Feed />);
      const forYou = await screen.findByRole("region", { name: "For you" });
      expect(within(forYou).queryByRole("button", { name: /films$/ })).not.toBeInTheDocument();
    });
  });
});
