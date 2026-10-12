import { fireEvent, render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { I18nProvider } from "../i18n";
import { movie } from "../dev/fixtures";
import type { Lang } from "../lib/types";
import { Poster } from "./Poster";

const ARRIVAL = movie(0, { title: "Arrival", release_date: "2016-11-11", genres: ["Drama", "Science Fiction"], poster_path: "/x.jpg" });

function renderPoster(lang: Lang = "en", m = ARRIVAL) {
  return render(
    <I18nProvider lang={lang}>
      <Poster movie={m} />
    </I18nProvider>,
  );
}

describe("Poster", () => {
  it("keeps the title, year and first genre under the image, for while it loads or if it never does", () => {
    const { getByTestId, container } = renderPoster();
    const fallback = getByTestId("poster-fallback");
    expect(fallback).toHaveAttribute("data-title", "Arrival");
    expect(fallback).toHaveAttribute("data-meta", "2016 · Drama");
    expect(fallback).toHaveAttribute("aria-hidden", "true"); // the card prints the title already
    expect(container.querySelector("img")).toHaveAttribute("src", "https://image.tmdb.org/t/p/w342/x.jpg");
  });

  it("names the genre in the interface language", () => {
    expect(renderPoster("ru").getByTestId("poster-fallback")).toHaveAttribute("data-meta", "2016 · Драма");
  });

  it("drops a failed image and leaves the fallback", () => {
    const { container, getByTestId } = renderPoster();
    fireEvent.error(container.querySelector("img")!);
    expect(container.querySelector("img")).toBeNull();
    expect(getByTestId("poster-fallback")).toHaveAttribute("data-title", "Arrival");
  });

  it("without a year or genre shows only the title", () => {
    const bare = movie(0, { title: "Untitled", release_date: null, genres: [], poster_path: null });
    const { getByTestId, container } = renderPoster("en", bare);
    expect(getByTestId("poster-fallback")).not.toHaveAttribute("data-meta");
    expect(container.querySelector("img")).toBeNull();
  });
});
