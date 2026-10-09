import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes, useSearchParams } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { renderWithProviders } from "../test/utils";
import { AppShell } from "./Layout";

function SearchProbe() {
  const [params] = useSearchParams();
  return <p data-testid="q">{params.get("q")}</p>;
}

function shellAt(route: string) {
  return renderWithProviders(
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<p>home</p>} />
        <Route path="search" element={<SearchProbe />} />
      </Route>
    </Routes>,
    { route, path: "/*", lang: "en" },
  );
}

describe("AppShell", () => {
  it("names every section, with an svg icon and no emoji", () => {
    shellAt("/");
    const [sidebar] = screen.getAllByRole("navigation", { name: "Main sections" });
    const links = within(sidebar as HTMLElement).getAllByRole("link");
    expect(links.map((a) => a.textContent)).toEqual(["Home", "Search", "Movie DNA", "Watchlist"]);
    for (const link of links) {
      expect(link.querySelector("svg[aria-hidden='true']")).not.toBeNull();
    }
  });

  it("opens the search screen with what was typed in the pill", async () => {
    shellAt("/");
    const pill = screen.getByRole("search");
    await userEvent.type(within(pill).getByRole("searchbox", { name: "Film title" }), "heat{Enter}");
    expect(await screen.findByTestId("q")).toHaveTextContent("heat");
  });

  it("steps aside on the search screen, which has its own field", () => {
    shellAt("/search");
    expect(screen.queryByRole("search")).toBeNull();
  });

  it("fades a new page in as new content; the shell itself is not part of it", async () => {
    shellAt("/");
    const home = screen.getByText("home").closest(".page-enter");
    expect(home).not.toBeNull();
    // the navigation sits outside the fading content
    const [sidebar] = screen.getAllByRole("navigation", { name: "Main sections" });
    expect(home).not.toContainElement(sidebar as HTMLElement);

    await userEvent.click(within(sidebar as HTMLElement).getByRole("link", { name: "Search" }));
    const search = (await screen.findByTestId("q")).closest(".page-enter");
    expect(search).not.toBeNull();
    expect(search).not.toBe(home); // a new element: the fade runs again
  });
});
