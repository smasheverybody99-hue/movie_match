import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuthFailure } from "../lib/supabase";
import { fakeAuthClient, renderWithProviders } from "../test/utils";
import Welcome from "./Welcome";

const ROUTE = { route: "/welcome", path: "/welcome" };

describe("Welcome", () => {
  it("offers Google, Apple and email", async () => {
    renderWithProviders(<Welcome />, { ...ROUTE, auth: fakeAuthClient(null) });
    expect(screen.getByRole("heading", { level: 1, name: "Movie Match" })).toBeInTheDocument();
    for (const name of ["Continue with Google", "Continue with Apple", "Continue with email"]) {
      expect(screen.getByRole("button", { name })).toBeInTheDocument();
    }
  });

  it("starts the provider's sign-in", async () => {
    const auth = fakeAuthClient(null);
    renderWithProviders(<Welcome />, { ...ROUTE, auth });
    await userEvent.click(await screen.findByRole("button", { name: "Continue with Google" }));
    expect(auth.signInWithOAuth).toHaveBeenCalledWith("google");
  });

  it("says a provider is not switched on, in words, not the SDK's message", async () => {
    const auth = fakeAuthClient(null);
    vi.mocked(auth.signInWithOAuth).mockRejectedValue(
      new AuthFailure("provider_disabled", "Unsupported provider: provider is not enabled"),
    );
    renderWithProviders(<Welcome />, { ...ROUTE, auth });
    await userEvent.click(await screen.findByRole("button", { name: "Continue with Apple" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("This sign-in method isn't switched on yet.");
    expect(alert).not.toHaveTextContent("Unsupported provider");
  });

  it("checks the email, then sends a magic link", async () => {
    const auth = fakeAuthClient(null);
    renderWithProviders(<Welcome />, { ...ROUTE, auth });
    await userEvent.click(screen.getByRole("button", { name: "Continue with email" }));
    const input = screen.getByRole("textbox", { name: "Your email" });

    await userEvent.type(input, "not-an-email");
    await userEvent.click(screen.getByRole("button", { name: "Send me a sign-in link" }));
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText(/Enter a full email address/)).toBeInTheDocument();
    expect(auth.signInWithEmail).not.toHaveBeenCalled();

    await userEvent.clear(input);
    await userEvent.type(input, "me@example.com");
    await userEvent.click(screen.getByRole("button", { name: "Send me a sign-in link" }));
    expect(auth.signInWithEmail).toHaveBeenCalledWith("me@example.com");
    expect(await screen.findByRole("status")).toHaveTextContent("We sent a link to me@example.com");
  });

  it("explains when sign-in is not configured instead of failing silently", () => {
    renderWithProviders(<Welcome />, { ...ROUTE, auth: null });
    expect(screen.getByRole("alert")).toHaveTextContent("Sign-in is unavailable right now. Try again later.");
    expect(screen.getByRole("button", { name: "Continue with Google" })).toBeDisabled();
  });

  it("is in Uzbek by default", () => {
    renderWithProviders(<Welcome />, { ...ROUTE, auth: fakeAuthClient(null), lang: "uz" });
    expect(screen.getByRole("button", { name: "Google bilan davom etish" })).toBeInTheDocument();
  });
});
