import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DNA } from "../dev/fixtures";
import { translate } from "../i18n";
import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import { pending, renderWithProviders } from "../test/utils";
import Dna, { sortedTraits, summarize } from "./Dna";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi } = await import("../test/utils");
  return { ...actual, api: mockedApi(actual.api) };
});

const dna = vi.mocked(api.dna);
const ROUTE = { route: "/dna", path: "/dna" };

describe("Dna", () => {
  beforeEach(() => {
    dna.mockReset();
    dna.mockResolvedValue(DNA);
  });

  it("renders its loading state", () => {
    dna.mockReturnValue(pending());
    renderWithProviders(<Dna />, ROUTE);
    expect(screen.getByTestId("loading")).toBeInTheDocument();
  });

  it("below 10 ratings shows the 'rate more' screen, not empty bars", async () => {
    dna.mockResolvedValue({ ...DNA, scores: {}, rating_count: 7, ratings_needed: 3 });
    renderWithProviders(<Dna />, ROUTE);
    expect(await screen.findByText("Rate 3 more films to unlock your Movie DNA.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Rate films" })).toHaveAttribute("href", "/onboarding");
    expect(screen.queryByRole("meter")).not.toBeInTheDocument();
    expect(screen.queryByTestId("dna-bars")).not.toBeInTheDocument();
  });

  it("with 10 ratings but no liked film, says what is missing instead of empty bars", async () => {
    dna.mockResolvedValue({ ...DNA, scores: {}, rating_count: 10, ratings_needed: 0 });
    renderWithProviders(<Dna />, ROUTE);
    expect(await screen.findByText(/No liked films yet/)).toBeInTheDocument();
    expect(screen.queryByRole("meter")).not.toBeInTheDocument();
  });

  it("renders its error state with a retry that refetches", async () => {
    dna.mockRejectedValueOnce(new ApiError(500, "x"));
    renderWithProviders(<Dna />, ROUTE);
    expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't load your Movie DNA.");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByTestId("dna-bars")).toBeInTheDocument();
    expect(dna).toHaveBeenCalledTimes(2);
  });

  it("renders all 14 bars sorted by strength, the summary and the stats", async () => {
    renderWithProviders(<Dna />, ROUTE);
    const bars = within(await screen.findByTestId("dna-bars")).getAllByRole("meter");
    expect(bars).toHaveLength(14);
    const values = bars.map((bar) => Number(bar.getAttribute("aria-valuenow")));
    expect(values).toEqual([...values].sort((a, b) => b - a));
    expect(bars[0]).toHaveAccessibleName("Plot twists"); // 91, the highest in the fixture

    expect(screen.getByText("“You prefer films strong in Plot twists, Psychological and Mystery.”")).toBeInTheDocument();
    const stats = screen.getByRole("region", { name: "Stats" });
    expect(within(stats).getByText("14")).toBeInTheDocument();
    expect(within(stats).getByText("7.6")).toBeInTheDocument();
    expect(within(stats).getByText("Drama")).toBeInTheDocument();
  });

  it("in Russian: traits in lower case inside the sentence, a decimal comma, the genre translated", async () => {
    renderWithProviders(<Dna />, { ...ROUTE, lang: "ru" });
    expect(
      await screen.findByText("“Вам ближе всего фильмы, в которых сильны сюжетные повороты, психологизм и загадочность.”"),
    ).toBeInTheDocument();
    const stats = screen.getByRole("region", { name: "Статистика" });
    expect(within(stats).getByText("7,6")).toBeInTheDocument();
    expect(within(stats).getByText("Драма")).toBeInTheDocument();
    expect(screen.getByText("В цифрах")).toBeInTheDocument();
  });

  it("shows the chart first, and the exact values behind Numbers, closed until opened", async () => {
    renderWithProviders(<Dna />);
    const chart = await screen.findByRole("img", {
      name: "Movie DNA chart. Strongest: Plot twists 91, Psychological 88, Mystery 84.",
    });
    expect(chart).toHaveClass("dna-flower");
    const numbers = screen.getByText("Numbers").closest("details")!;
    expect(numbers).not.toHaveAttribute("open");
    expect(numbers).toContainElement(screen.getByTestId("dna-bars"));
    await userEvent.click(screen.getByText("Numbers"));
    expect(numbers).toHaveAttribute("open");
    // the chart comes before the stats and the numbers
    const stats = screen.getByRole("region", { name: "Stats" });
    expect(chart.compareDocumentPosition(stats) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(stats.compareDocumentPosition(numbers) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("shares a text summary by copying it where the share sheet is missing", async () => {
    const writeText = vi.fn(async () => {});
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
    renderWithProviders(<Dna />, ROUTE);
    await userEvent.click(await screen.findByRole("button", { name: /Share/ }));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("My Movie DNA: Plot twists 91"));
    expect(screen.getByRole("status")).toHaveTextContent("Copied");
  });
});

describe("summary helpers", () => {
  it("sorts strongest first and ignores unknown keys", () => {
    expect(sortedTraits({ humor: 10, darkness: 90, sparkle: 99 })).toEqual([
      ["darkness", 90],
      ["humor", 10],
    ]);
  });

  it("prefers the API's summary when there is one", () => {
    const t = (key: Parameters<typeof translate>[1], vars?: Record<string, string | number>) =>
      translate("en", key, vars);
    expect(summarize({ ...DNA, summary: "Given." }, t, "en")).toBe("Given.");
  });
});
