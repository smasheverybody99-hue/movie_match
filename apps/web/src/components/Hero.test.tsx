import { act, fireEvent, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { movie, rec } from "../dev/fixtures";
import type { Recommendation } from "../lib/types";
import { renderWithProviders } from "../test/utils";
import { Hero, HERO_INTERVAL_MS } from "./Hero";

/** Five top picks: the first with a backdrop, a strong band and a cached sentence. */
function picks(): Recommendation[] {
  return [0, 1, 2, 3, 4].map((i) => ({
    ...rec(movie(i, { backdrop_path: `/b${i}.jpg` }), 94 - i, i === 0 ? "strong" : i === 1 ? "good" : null),
    explanation: i === 0 ? "Twisty, like your favourites." : null,
  }));
}

function motion(reduce: boolean) {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({ matches: reduce, addEventListener: vi.fn(), removeEventListener: vi.fn() })),
  );
}

function renderHero(items = picks(), saved: ReadonlySet<number> = new Set(), onToggleSave = vi.fn()) {
  renderWithProviders(<Hero items={items} saved={saved} onToggleSave={onToggleSave} />);
  return { hero: screen.getByTestId("home-hero"), onToggleSave };
}

const title = () => screen.getByRole("heading", { level: 2 }).textContent;

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("Hero", () => {
  it("shows the first pick: title, year and runtime, band, and its backdrop as the priority image", () => {
    const { hero } = renderHero();
    expect(hero).toHaveAttribute("aria-roledescription", "carousel");
    expect(within(hero).getByRole("link", { name: "The Prestige" })).toHaveAttribute("href", "/movie/1000");
    expect(within(hero).getAllByRole("listitem").map((li) => li.textContent)).toEqual(["2006", "130m"]);
    expect(within(hero).getByText("Strong match")).toHaveClass("match-band-strong");
    const first = hero.querySelector<HTMLImageElement>(".home-hero-img.is-active")!;
    expect(first).toHaveAttribute("src", "https://image.tmdb.org/t/p/w1280/b0.jpg");
    expect(first).toHaveAttribute("fetchpriority", "high");
    expect(screen.getByRole("group", { name: "1 of 5" })).toBeInTheDocument();
  });

  it("loads only the shown slides and the next one", () => {
    const { hero } = renderHero();
    expect(hero.querySelectorAll(".home-hero-img")).toHaveLength(2);
    fireEvent.click(screen.getByRole("button", { name: "Next film" }));
    expect(hero.querySelectorAll(".home-hero-img")).toHaveLength(3);
    expect(hero.querySelectorAll(".home-hero-img")[1]).not.toHaveAttribute("fetchpriority", "high");
  });

  it("opens the cached sentence in place; never asks the API for one", () => {
    renderHero();
    const why = screen.getByRole("button", { name: "Why it suits me?" });
    expect(why).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText("Twisty, like your favourites.")).not.toBeInTheDocument();
    fireEvent.click(why);
    expect(why).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Twisty, like your favourites.")).toHaveAttribute("id", why.getAttribute("aria-controls"));
  });

  it("without a cached sentence, Why links to the film page", () => {
    renderHero();
    fireEvent.click(screen.getByRole("button", { name: "Next film" }));
    expect(screen.getByRole("link", { name: "Why it suits me?" })).toHaveAttribute("href", "/movie/1001");
    expect(screen.getByText("Good match")).toHaveClass("match-band-good");
  });

  it("moves with prev / next, the dots and the arrow keys, wrapping at both ends", () => {
    const { hero } = renderHero();
    fireEvent.click(screen.getByRole("button", { name: "Previous film" }));
    expect(title()).toBe("Wind River");
    fireEvent.click(screen.getByRole("button", { name: "Next film" }));
    expect(title()).toBe("The Prestige");
    fireEvent.click(screen.getByRole("button", { name: "Film 3 of 5" }));
    expect(title()).toBe("Zodiac");
    expect(screen.getByRole("button", { name: "Film 3 of 5" })).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("button", { name: "Film 1 of 5" })).not.toHaveAttribute("aria-current");
    fireEvent.keyDown(hero, { key: "ArrowRight" });
    expect(title()).toBe("Prisoners");
    fireEvent.keyDown(hero, { key: "ArrowLeft" });
    expect(title()).toBe("Zodiac");
  });

  it("rotates every 7 s, and announces nothing while it does", () => {
    motion(false);
    vi.useFakeTimers();
    const { hero } = renderHero();
    expect(hero.querySelector(".home-hero-body")).toHaveAttribute("aria-live", "off");
    act(() => vi.advanceTimersByTime(HERO_INTERVAL_MS - 1));
    expect(title()).toBe("The Prestige");
    act(() => vi.advanceTimersByTime(1));
    expect(title()).toBe("Memento");
  });

  it("holds while the pointer or focus is inside, and after Pause", () => {
    motion(false);
    vi.useFakeTimers();
    const { hero } = renderHero();
    fireEvent.mouseEnter(hero);
    act(() => vi.advanceTimersByTime(HERO_INTERVAL_MS * 2));
    expect(title()).toBe("The Prestige");
    expect(hero.querySelector(".home-hero-body")).toHaveAttribute("aria-live", "polite");
    fireEvent.mouseLeave(hero);

    fireEvent.focus(screen.getByRole("button", { name: "Next film" }));
    act(() => vi.advanceTimersByTime(HERO_INTERVAL_MS * 2));
    expect(title()).toBe("The Prestige");
    fireEvent.blur(screen.getByRole("button", { name: "Next film" }));

    fireEvent.click(screen.getByRole("button", { name: "Pause rotation" }));
    fireEvent.mouseLeave(hero);
    fireEvent.blur(screen.getByRole("button", { name: "Resume rotation" }));
    act(() => vi.advanceTimersByTime(HERO_INTERVAL_MS * 2));
    expect(title()).toBe("The Prestige");
    fireEvent.click(screen.getByRole("button", { name: "Resume rotation" }));
    fireEvent.blur(screen.getByRole("button", { name: "Pause rotation" }));
    act(() => vi.advanceTimersByTime(HERO_INTERVAL_MS));
    expect(title()).toBe("Memento");
  });

  it("with reduced motion: never moves on its own, and has no Pause", () => {
    motion(true);
    vi.useFakeTimers();
    renderHero();
    act(() => vi.advanceTimersByTime(HERO_INTERVAL_MS * 3));
    expect(title()).toBe("The Prestige");
    expect(screen.queryByRole("button", { name: "Pause rotation" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next film" })).toBeInTheDocument();
  });

  it("saves and unsaves the shown film", () => {
    const onToggleSave = vi.fn();
    renderHero(picks(), new Set([1000]), onToggleSave);
    const save = screen.getByRole("button", { name: "Saved" });
    expect(save).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(save);
    expect(onToggleSave).toHaveBeenCalledWith(expect.objectContaining({ id: 1000 }), true);
  });

  it("with one film: no controls; without a backdrop, the poster blurred", () => {
    const one = [rec(movie(0, { poster_path: "/p.jpg" }), 90, null)];
    const { hero } = renderHero(one);
    expect(screen.queryByRole("button", { name: "Next film" })).not.toBeInTheDocument();
    expect(within(hero).queryByText(/match/)).not.toBeInTheDocument();
    expect(hero.querySelector(".home-hero-img")).toHaveClass("film-hero-blur");
  });
});
