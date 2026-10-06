import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { WATCHLIST, movie, watchItem } from "../dev/fixtures";
import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import { pending, renderWithProviders } from "../test/utils";
import Watchlist, { inGroup } from "./Watchlist";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi } = await import("../test/utils");
  return { ...actual, api: mockedApi(actual.api) };
});

const list = vi.mocked(api.watchlist);
const markWatched = vi.mocked(api.markWatched);
const remove = vi.mocked(api.removeFromWatchlist);

const ROUTE = { route: "/watchlist", path: "/watchlist" };

function rowTitles(): string[] {
  return screen.queryAllByRole("listitem").map((row) => within(row).getByRole("link").textContent ?? "");
}

describe("Watchlist", () => {
  beforeEach(() => {
    for (const fn of [list, markWatched, remove]) fn.mockReset();
    list.mockResolvedValue(WATCHLIST);
  });

  it("renders its loading state", () => {
    list.mockReturnValue(pending());
    renderWithProviders(<Watchlist />, ROUTE);
    expect(screen.getByTestId("loading")).toBeInTheDocument();
  });

  it("renders its empty state with a link to search", async () => {
    list.mockResolvedValue([]);
    renderWithProviders(<Watchlist />, ROUTE);
    expect(await screen.findByText(/Your watchlist is empty/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Search films" })).toHaveAttribute("href", "/search");
  });

  it("renders its error state with a retry that refetches", async () => {
    list.mockRejectedValueOnce(new ApiError(500, "x"));
    renderWithProviders(<Watchlist />, ROUTE);
    expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't load your watchlist.");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("The Machinist")).toBeInTheDocument();
    expect(list).toHaveBeenCalledTimes(2);
  });

  it("renders rows with the API's match band, unwatched films under Watch next", async () => {
    renderWithProviders(<Watchlist />, ROUTE);
    await screen.findByText("The Machinist");
    expect(rowTitles()).toEqual(["The Machinist", "Wind River", "The Guilty", "Enemy"]);
    expect(screen.getAllByText("Strong match")).toHaveLength(1);
    // "good" comes from the API but is not drawn (TZ 1.16)
    expect(screen.queryByText("Good match")).not.toBeInTheDocument();
    expect(screen.queryByText(/\d+%/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Watch next" })).toHaveAttribute("aria-pressed", "true");
  });

  it("filters the list with the group chips", async () => {
    renderWithProviders(<Watchlist />, ROUTE);
    await screen.findByText("The Machinist");

    await userEvent.click(screen.getByRole("button", { name: /Under 90 min/ }));
    expect(screen.getByRole("button", { name: /Under 90 min/ })).toHaveAttribute("aria-pressed", "true");
    expect(rowTitles()).toEqual(["The Guilty"]); // 88 minutes; Enemy is 91

    await userEvent.click(screen.getByRole("button", { name: "Watched" }));
    expect(rowTitles()).toEqual(["Heat"]);
  });

  it("removes the row from Watch next when it is marked watched", async () => {
    const watched = watchItem(movie(5), { match: 88, watched_at: "2026-09-29T12:00:00Z" });
    let answer!: (item: typeof watched) => void;
    markWatched.mockReturnValue(new Promise((resolve) => (answer = resolve)));
    renderWithProviders(<Watchlist />, ROUTE);
    await screen.findByText("The Machinist");

    await userEvent.click(screen.getByRole("button", { name: "Mark The Machinist as watched" }));
    // gone before the server has answered
    await waitFor(() => expect(rowTitles()).not.toContain("The Machinist"));
    expect(markWatched).toHaveBeenCalledWith(1005);

    list.mockResolvedValue([...WATCHLIST.slice(1), watched]); // what the refetch returns
    answer(watched);
    await waitFor(() => expect(list).toHaveBeenCalledTimes(2));
    expect(rowTitles()).not.toContain("The Machinist");

    await userEvent.click(screen.getByRole("button", { name: "Watched" }));
    expect(rowTitles()).toContain("The Machinist");
  });

  it("puts a row back when marking it watched fails", async () => {
    markWatched.mockRejectedValue(new ApiError(0, "offline"));
    renderWithProviders(<Watchlist />, ROUTE);
    await screen.findByText("The Machinist");
    await userEvent.click(screen.getByRole("button", { name: "Mark The Machinist as watched" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("That change wasn't saved.");
    await waitFor(() => expect(rowTitles()).toContain("The Machinist"));
  });

  it("removes a film", async () => {
    remove.mockImplementation(async () => {
      list.mockResolvedValue(WATCHLIST.filter((i) => i.movie.title !== "Wind River"));
    });
    renderWithProviders(<Watchlist />, ROUTE);
    await screen.findByText("Wind River");
    await userEvent.click(screen.getByRole("button", { name: "Remove Wind River from the watchlist" }));
    await waitFor(() => expect(rowTitles()).not.toContain("Wind River"));
    expect(remove).toHaveBeenCalledWith(1004);
  });

  it("says so when a group is empty", async () => {
    list.mockResolvedValue([watchItem(movie(11))]); // Heat, 170 minutes, unwatched
    renderWithProviders(<Watchlist />, ROUTE);
    await screen.findByText("Heat");
    await userEvent.click(screen.getByRole("button", { name: /Under 90 min/ }));
    expect(screen.getByText("No films in this group.")).toBeInTheDocument();
  });
});

describe("inGroup", () => {
  it("puts a short unwatched film in Watch next and Under 90, not Watched", () => {
    const item = watchItem(movie(8)); // 88 minutes
    expect(inGroup(item, "next")).toBe(true);
    expect(inGroup(item, "short")).toBe(true);
    expect(inGroup(item, "watched")).toBe(false);
  });

  it("leaves a film of unknown length out of Under 90", () => {
    expect(inGroup(watchItem(movie(8, { runtime_minutes: null })), "short")).toBe(false);
  });
});
