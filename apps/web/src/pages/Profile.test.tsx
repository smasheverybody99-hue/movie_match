import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { renderWithProviders, TEST_SESSION } from "../test/utils";
import Profile from "./Profile";

const ROUTE = { route: "/profile", path: "/profile" };

describe("Profile — language", () => {
  afterEach(() => localStorage.clear());

  /** Waits for the signed-in session, so no state update lands after the test. */
  async function signedIn() {
    await screen.findByText(TEST_SESSION.email ?? "");
  }

  it("offers English, O'zbek and Русский in that order, English chosen", async () => {
    renderWithProviders(<Profile />, { ...ROUTE, lang: "en" });
    await signedIn();
    const group = screen.getByRole("group", { name: "Language" });
    const buttons = within(group).getAllByRole("button");
    expect(buttons.map((b) => b.textContent)).toEqual(["English", "O'zbek", "Русский"]);
    expect(buttons.map((b) => b.getAttribute("aria-pressed"))).toEqual(["true", "false", "false"]);
    expect(buttons.map((b) => b.getAttribute("lang"))).toEqual(["en", "uz", "ru"]);
  });

  it("switches the interface and remembers the choice", async () => {
    renderWithProviders(<Profile />, { ...ROUTE, lang: "en" });
    await signedIn();
    await userEvent.click(screen.getByRole("button", { name: "Русский" }));

    expect(screen.getByRole("heading", { level: 1, name: "Профиль" })).toBeInTheDocument();
    const group = screen.getByRole("group", { name: "Язык" });
    expect(within(group).getByRole("button", { name: "Русский" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(localStorage.getItem("mm.lang")).toBe("ru");
  });

  it("shows the language names the same way in Uzbek", async () => {
    renderWithProviders(<Profile />, { ...ROUTE, lang: "uz" });
    await signedIn();
    const group = screen.getByRole("group", { name: "Til" });
    expect(within(group).getAllByRole("button").map((b) => b.textContent)).toEqual([
      "English",
      "O'zbek",
      "Русский",
    ]);
  });
});
