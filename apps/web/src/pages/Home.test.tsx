import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import { renderWithProviders } from "../test/utils";
import Home from "./Home";

// Hoisted by Vitest, so the plain import above receives the mocked module.
// ApiError is kept from the real module: the component and the tests must agree
// on the error type the API layer throws.
vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  return {
    ...actual,
    api: { health: vi.fn(), searchMovies: vi.fn(), getMovie: vi.fn() },
  };
});

const health = vi.mocked(api.health);

describe("Home", () => {
  beforeEach(() => {
    health.mockReset();
  });

  it("shows the loading state while the health check is in flight", () => {
    health.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<Home />);
    expect(screen.getByText(/Tekshirilmoqda/)).toBeInTheDocument();
  });

  it("shows the connected state with the trait count from the API", async () => {
    health.mockResolvedValue({ status: "ok", trait_dimensions: 14 });
    renderWithProviders(<Home />);
    await waitFor(() => {
      expect(screen.getByText(/Ulandi/)).toBeInTheDocument();
    });
    expect(screen.getByText(/14 ta trait/)).toBeInTheDocument();
  });

  it("shows the error state when the API is unreachable", async () => {
    health.mockRejectedValue(new ApiError(503, "Service Unavailable"));
    renderWithProviders(<Home />);
    await waitFor(() => {
      expect(screen.getByText(/Ulanmadi/)).toBeInTheDocument();
    });
  });

  it("always renders the product name", () => {
    health.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<Home />);
    expect(screen.getByText("Movie Match")).toBeInTheDocument();
  });
});
