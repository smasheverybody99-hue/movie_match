import { onlineManager, useQuery } from "@tanstack/react-query";
import { act, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { renderWithProviders } from "../test/utils";
import { OfflineBanner } from "./Layout";
import { QueryView } from "./States";

function Probe({ fetcher }: { fetcher: () => Promise<string> }) {
  const query = useQuery({ queryKey: ["probe"], queryFn: fetcher });
  return (
    <QueryView query={query} skeleton={<p>skeleton</p>} error="It failed.">
      {(data) => <p>{data}</p>}
    </QueryView>
  );
}

function setBrowserOnline(online: boolean) {
  vi.spyOn(navigator, "onLine", "get").mockReturnValue(online);
  act(() => {
    window.dispatchEvent(new Event(online ? "online" : "offline"));
    onlineManager.setOnline(online);
  });
}

describe("offline", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    act(() => onlineManager.setOnline(true));
  });

  it("shows the offline message, not a skeleton forever, when nothing is cached", async () => {
    setBrowserOnline(false);
    const fetcher = vi.fn(async () => "fresh");
    renderWithProviders(<Probe fetcher={fetcher} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("You're offline");
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("keeps showing cached content while offline", async () => {
    const fetcher = vi.fn(async () => "cached content");
    const { queryClient } = renderWithProviders(<Probe fetcher={fetcher} />);
    expect(await screen.findByText("cached content")).toBeInTheDocument();
    setBrowserOnline(false);
    await act(() => queryClient.invalidateQueries());
    expect(screen.getByText("cached content")).toBeInTheDocument();
  });

  it("shows the offline banner only while offline", () => {
    renderWithProviders(<OfflineBanner />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    setBrowserOnline(false);
    expect(screen.getByRole("status")).toHaveTextContent("Offline. Showing saved content.");
    setBrowserOnline(true);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
