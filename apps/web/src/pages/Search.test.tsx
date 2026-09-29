import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MOVIES } from "../dev/fixtures";
import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import { pending, renderWithProviders } from "../test/utils";
import Search from "./Search";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi } = await import("../test/utils");
  return { ...actual, api: mockedApi(actual.api) };
});

const search = vi.mocked(api.searchMovies);
const ROUTE = { route: "/search", path: "/search" };

describe("Search", () => {
  beforeEach(() => {
    search.mockReset();
    search.mockResolvedValue(MOVIES.slice(0, 6));
  });

  it("renders its loading state", () => {
    search.mockReturnValue(pending());
    renderWithProviders(<Search />, ROUTE);
    expect(screen.getByTestId("loading")).toBeInTheDocument();
  });

  it("shows popular films before anything is typed", async () => {
    renderWithProviders(<Search />, ROUTE);
    expect(await screen.findByRole("heading", { name: "Popular films" })).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: /The Prestige/ })).toHaveAttribute("href", "/movie/1000");
  });

  it("searches by title once typing pauses", async () => {
    renderWithProviders(<Search />, ROUTE);
    await screen.findByText("The Prestige");
    await userEvent.type(screen.getByRole("searchbox", { name: "Film title" }), "mem");
    await waitFor(() => expect(search).toHaveBeenLastCalledWith(expect.objectContaining({ q: "mem" })));
    expect(search).not.toHaveBeenCalledWith(expect.objectContaining({ q: "m" }));
    expect(screen.getByRole("heading", { name: "Results" })).toBeInTheDocument();
  });

  it("sends year, runtime and trait filters", async () => {
    renderWithProviders(<Search />, ROUTE);
    await screen.findByText("The Prestige");
    await userEvent.type(screen.getByRole("textbox", { name: "From year" }), "2000");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Length" }), "90");
    await userEvent.click(screen.getByRole("button", { name: "Tone darkness" }));
    await waitFor(() =>
      expect(search).toHaveBeenLastCalledWith(
        expect.objectContaining({ yearFrom: 2000, maxRuntime: 90, traits: ["darkness"], traitMinimum: 70 }),
      ),
    );
  });

  it("renders its empty state with a way to clear the filters", async () => {
    renderWithProviders(<Search />, ROUTE);
    await screen.findByText("The Prestige");
    search.mockResolvedValue([]);
    await userEvent.click(screen.getByRole("button", { name: "Humor" }));
    expect(await screen.findByText(/No films match these filters/)).toBeInTheDocument();

    search.mockResolvedValue(MOVIES.slice(0, 6));
    await userEvent.click(screen.getAllByRole("button", { name: "Clear filters" })[0] as HTMLElement);
    expect(await screen.findByRole("heading", { name: "Popular films" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Humor" })).toHaveAttribute("aria-pressed", "false");
  });

  it("renders its error state with a retry that refetches", async () => {
    search.mockRejectedValueOnce(new ApiError(500, "x"));
    renderWithProviders(<Search />, ROUTE);
    expect(await screen.findByRole("alert")).toHaveTextContent("Search didn't work.");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("The Prestige")).toBeInTheDocument();
    expect(search).toHaveBeenCalledTimes(2);
  });
});
