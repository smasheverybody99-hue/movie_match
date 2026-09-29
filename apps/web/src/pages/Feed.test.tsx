import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RECOMMENDATIONS, movie, rec } from "../dev/fixtures";
import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import type { Recommendations } from "../lib/types";
import { navigatedTo, pending, renderWithProviders } from "../test/utils";
import Feed from "./Feed";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi: mocked } = await import("../test/utils");
  return { ...actual, api: mocked(actual.api) };
});

const recommendations = vi.mocked(api.recommendations);

describe("Feed", () => {
  beforeEach(() => {
    recommendations.mockReset();
  });

  it("renders its loading state", () => {
    recommendations.mockReturnValue(pending());
    renderWithProviders(<Feed />);
    expect(screen.getByTestId("loading")).toBeInTheDocument();
  });

  it("renders sections with their reasons, and the API's match on each card", async () => {
    recommendations.mockResolvedValue(RECOMMENDATIONS);
    renderWithProviders(<Feed />);

    expect(await screen.findByRole("heading", { name: "For you" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Because you loved Shutter Island" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Under 90 minutes" })).toBeInTheDocument();

    const forYou = screen.getByRole("region", { name: "For you" });
    const first = within(forYou).getAllByRole("link")[0];
    expect(first).toHaveAttribute("href", "/movie/1000");
    expect(within(first as HTMLElement).getByText("94%")).toBeInTheDocument();
    expect(within(first as HTMLElement).getByText("The Prestige")).toBeInTheDocument();
    expect(recommendations).toHaveBeenCalledWith("en");
  });

  it("does not render a section that has no items at all", async () => {
    recommendations.mockResolvedValue(RECOMMENDATIONS);
    renderWithProviders(<Feed />);
    await screen.findByRole("heading", { name: "For you" });
    // outside_usual is in the response with an empty list
    expect(screen.queryByRole("heading", { name: "Outside your usual taste" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("region")).toHaveLength(3);
  });

  it("shows the match number exactly as the API sent it", async () => {
    const data: Recommendations = {
      status: "ok",
      ratings_needed: 0,
      sections: [{ key: "for_you", seed: null, items: [rec(movie(2), 73)] }],
    };
    recommendations.mockResolvedValue(data);
    renderWithProviders(<Feed />);
    expect(await screen.findByLabelText("73% match")).toHaveTextContent("73%");
  });

  it("renders its empty state with a call to action when nothing matches", async () => {
    recommendations.mockResolvedValue({
      status: "ok",
      ratings_needed: 0,
      sections: [{ key: "for_you", seed: null, items: [] }],
    });
    renderWithProviders(<Feed />);
    expect(await screen.findByText(/No film matches you above 60%/)).toBeInTheDocument();
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
});
