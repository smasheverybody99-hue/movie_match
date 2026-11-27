import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type * as ApiModule from "../lib/api";
import type * as DownloadModule from "../lib/download";
import { api, ApiError } from "../lib/api";
import { exportFileName, saveJson } from "../lib/download";
import type { DataExport } from "../lib/types";
import { pending, renderWithProviders, TEST_SESSION } from "../test/utils";
import Profile from "./Profile";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi } = await import("../test/utils");
  return { ...actual, api: mockedApi(actual.api) };
});
vi.mock("../lib/download", async () => {
  const actual = await vi.importActual<typeof DownloadModule>("../lib/download");
  return { ...actual, saveJson: vi.fn() };
});

const exportData = vi.mocked(api.exportData);
const save = vi.mocked(saveJson);

const EXPORT: DataExport = {
  format: "movie-match-export/1",
  exported_at: "2026-11-27T12:00:00Z",
  user_id: TEST_SESSION.userId,
  account: { email: TEST_SESSION.email },
  tables: { users: [{ id: TEST_SESSION.userId }], ratings: [] },
  movies: {},
};

async function profile() {
  renderWithProviders(<Profile />, { route: "/profile", path: "/profile", lang: "en" });
  await screen.findByText(TEST_SESSION.email ?? "");
  return screen.getByRole("button", { name: "Download my data" });
}

describe("Profile — download my data", () => {
  beforeEach(() => {
    exportData.mockReset();
    save.mockReset();
  });

  it("asks for nothing until the button is pressed", async () => {
    await profile();
    expect(exportData).not.toHaveBeenCalled();
  });

  it("saves the export as a dated JSON file", async () => {
    exportData.mockResolvedValue(EXPORT);
    await userEvent.click(await profile());
    await waitFor(() => expect(save).toHaveBeenCalledTimes(1));
    const [data, filename] = save.mock.calls[0] ?? [];
    expect(data).toEqual(EXPORT);
    expect(filename).toMatch(/^movie-match-data-\d{4}-\d{2}-\d{2}\.json$/);
  });

  it("can't be pressed twice while the export is being prepared", async () => {
    exportData.mockReturnValue(pending());
    const button = await profile();
    await userEvent.click(button);
    expect(button).toBeDisabled();
  });

  it("says so when the export failed, and saves nothing", async () => {
    exportData.mockRejectedValue(new ApiError(500, "boom"));
    await userEvent.click(await profile());
    expect(await screen.findByText("Couldn't prepare your data. Try again.")).toBeInTheDocument();
    expect(save).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Download my data" })).toBeEnabled();
  });
});

describe("exportFileName", () => {
  it("uses the local date, zero-padded", () => {
    expect(exportFileName(new Date(2026, 0, 5, 23, 30))).toBe("movie-match-data-2026-01-05.json");
  });
});
