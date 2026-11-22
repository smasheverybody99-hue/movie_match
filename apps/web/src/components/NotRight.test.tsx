import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { movie } from "../dev/fixtures";
import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import { useHiddenCards } from "../lib/hiddenCards";
import { pending, renderWithProviders } from "../test/utils";
import { MovieCard } from "./MovieCard";
import { WrongNoticeToast } from "./NotRight";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi } = await import("../test/utils");
  return { ...actual, api: mockedApi(actual.api) };
});

const markWrong = vi.mocked(api.markWrong);
const FILMS = [movie(1, { title: "Arrival" }), movie(2, { title: "Heat" })];

/** A row of recommendation cards the way Home shows them: hidden ones leave. */
function Row() {
  const { hidden } = useHiddenCards();
  return (
    <>
      <ul>
        {FILMS.filter((m) => !hidden.has(m.id)).map((m) => (
          <li key={m.id}>
            <MovieCard movie={m} source="under_90" />
          </li>
        ))}
      </ul>
      <WrongNoticeToast />
    </>
  );
}

function card(title: string): HTMLElement {
  const link = screen.getByRole("link", { name: new RegExp(title) });
  return link.closest(".movie-card") as HTMLElement;
}

describe("Not right?", () => {
  beforeEach(() => {
    markWrong.mockReset();
  });

  it("is a quiet button on each recommendation, closed at first", () => {
    renderWithProviders(<Row />);
    const button = within(card("Arrival")).getByRole("button", { name: "Not right for me: Arrival" });
    expect(button).toHaveTextContent("Not right?");
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("group", { name: "What's wrong with it?" })).not.toBeInTheDocument();
  });

  it("opens four reasons, a way to skip them and a way back", async () => {
    renderWithProviders(<Row />);
    await userEvent.click(screen.getByRole("button", { name: "Not right for me: Arrival" }));
    const panel = screen.getByRole("group", { name: "What's wrong with it?" });
    expect(within(panel).getAllByRole("button").map((b) => b.textContent)).toEqual([
      "I've seen it",
      "Not my genre",
      "Too old",
      "Other",
      "Just hide it",
      "Cancel",
    ]);
    await userEvent.click(within(panel).getByRole("button", { name: "Cancel" }));
    expect(screen.getByRole("button", { name: "Not right for me: Arrival" })).toBeInTheDocument();
    expect(markWrong).not.toHaveBeenCalled();
  });

  it("sends the reason, takes the card out of the view at once and says thanks", async () => {
    markWrong.mockReturnValue(pending());
    renderWithProviders(<Row />);
    await userEvent.click(screen.getByRole("button", { name: "Not right for me: Arrival" }));
    await userEvent.click(screen.getByRole("button", { name: "Too old" }));
    expect(markWrong).toHaveBeenCalledWith({ movie_id: 1001, source: "under_90", reason: "too_old" });
    expect(screen.queryByRole("link", { name: /Arrival/ })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Heat/ })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Thanks, noted. Arrival is hidden for now.");
  });

  it("sends no reason when skipped", async () => {
    markWrong.mockResolvedValue(undefined);
    renderWithProviders(<Row />);
    await userEvent.click(screen.getByRole("button", { name: "Not right for me: Heat" }));
    await userEvent.click(screen.getByRole("button", { name: "Just hide it" }));
    expect(markWrong).toHaveBeenCalledWith({ movie_id: 1002, source: "under_90", reason: null });
  });

  it("brings the card back and says so when the press does not arrive", async () => {
    markWrong.mockRejectedValue(new ApiError(0, "offline"));
    renderWithProviders(<Row />);
    await userEvent.click(screen.getByRole("button", { name: "Not right for me: Arrival" }));
    await userEvent.click(screen.getByRole("button", { name: "I've seen it" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't send that about Arrival. It's back — try again.");
    await waitFor(() => expect(screen.getByRole("link", { name: /Arrival/ })).toBeInTheDocument());
  });

  it("is not on a card that is not a recommendation (search results)", () => {
    renderWithProviders(<MovieCard movie={FILMS[0]!} />);
    expect(screen.queryByRole("button", { name: /Not right/ })).not.toBeInTheDocument();
  });
});
