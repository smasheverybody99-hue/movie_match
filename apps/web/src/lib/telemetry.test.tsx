import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi, type MockInstance } from "vitest";

import { ApiError, api, setAccessToken } from "./api";
import {
  FLUSH_AT,
  FLUSH_EVERY_MS,
  SHOWN_AFTER_MS,
  flush,
  queued,
  startTelemetry,
  track,
  useShownRef,
} from "./telemetry";

const shown = (movie_id: number) => ({ type: "recommendation_shown" as const, movie_id, source: "for_you" as const });

describe("telemetry", () => {
  let send: MockInstance<typeof api.sendEvents>;

  beforeEach(() => {
    vi.useFakeTimers();
    setAccessToken("token");
    send = vi.spyOn(api, "sendEvents").mockResolvedValue({ recorded: 1 });
  });

  afterEach(() => {
    vi.useRealTimers();
    setAccessToken(null);
    send.mockRestore();
  });

  it("sends nothing at once: one batch after ten seconds", async () => {
    track(shown(1));
    track({ type: "recommendation_clicked", movie_id: 1, source: "for_you" });
    track({ type: "onboarding_step", step: "pick" });
    expect(send).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(FLUSH_EVERY_MS);
    expect(send).toHaveBeenCalledTimes(1);
    const [batch, keepalive] = send.mock.calls[0]!;
    expect(batch.map((e) => e.type)).toEqual([
      "recommendation_shown",
      "recommendation_clicked",
      "onboarding_step",
    ]);
    expect(keepalive).toBe(false);
    expect(Number.isNaN(Date.parse(batch[0]!.at))).toBe(false);
    expect(queued()).toEqual([]);
  });

  it("goes at twenty waiting, without the timer", async () => {
    for (let i = 1; i <= FLUSH_AT; i++) track(shown(i));
    await vi.advanceTimersByTimeAsync(0);
    expect(send).toHaveBeenCalledTimes(1);
    expect(send.mock.calls[0]![0]).toHaveLength(FLUSH_AT);
  });

  it("counts a film shown once per source, a click every time", async () => {
    track(shown(1));
    track(shown(1));
    track({ type: "recommendation_shown", movie_id: 1, source: "assistant" });
    track({ type: "recommendation_clicked", movie_id: 1, source: "for_you" });
    track({ type: "recommendation_clicked", movie_id: 1, source: "for_you" });
    expect(queued().map((e) => e.type)).toEqual([
      "recommendation_shown",
      "recommendation_shown",
      "recommendation_clicked",
      "recommendation_clicked",
    ]);
  });

  it("keeps a batch that did not arrive and sends it again", async () => {
    send.mockRejectedValueOnce(new ApiError(0, "offline"));
    track(shown(1));
    await vi.advanceTimersByTimeAsync(FLUSH_EVERY_MS);
    expect(queued()).toHaveLength(1);
    await vi.advanceTimersByTimeAsync(FLUSH_EVERY_MS);
    expect(send).toHaveBeenCalledTimes(2);
    expect(queued()).toEqual([]);
  });

  it("drops a batch the API refuses as malformed instead of sending it forever", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    send.mockRejectedValueOnce(new ApiError(422, "bad"));
    track(shown(1));
    await vi.advanceTimersByTimeAsync(FLUSH_EVERY_MS);
    expect(queued()).toEqual([]);
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it("waits while signed out", async () => {
    setAccessToken(null);
    track(shown(1));
    await vi.advanceTimersByTimeAsync(FLUSH_EVERY_MS);
    expect(send).not.toHaveBeenCalled();
    setAccessToken("token");
    await vi.advanceTimersByTimeAsync(FLUSH_EVERY_MS);
    expect(send).toHaveBeenCalledTimes(1);
  });

  it("sends with keepalive when the page is hidden", async () => {
    const stop = startTelemetry();
    track(shown(1));
    window.dispatchEvent(new Event("pagehide"));
    await vi.advanceTimersByTimeAsync(0);
    expect(send).toHaveBeenCalledWith(expect.any(Array), true);
    stop();
  });

  it("flush with nothing waiting sends nothing", async () => {
    await flush();
    expect(send).not.toHaveBeenCalled();
  });
});

describe("useShownRef", () => {
  type Callback = (entries: Partial<IntersectionObserverEntry>[]) => void;
  let observed: Callback | null = null;
  const disconnect = vi.fn();

  beforeEach(() => {
    vi.useFakeTimers();
    observed = null;
    vi.stubGlobal(
      "IntersectionObserver",
      class {
        constructor(callback: Callback) {
          observed = callback;
        }
        observe() {}
        disconnect = disconnect;
      },
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  function Card() {
    const ref = useShownRef<HTMLDivElement>(42, "under_90");
    return <div ref={ref}>card</div>;
  }

  it("records a card at least half in view for a second", () => {
    render(<Card />);
    act(() => observed!([{ isIntersecting: true, intersectionRatio: 0.6 }]));
    act(() => vi.advanceTimersByTime(SHOWN_AFTER_MS - 1));
    expect(queued()).toEqual([]);
    act(() => vi.advanceTimersByTime(1));
    expect(queued()).toEqual([expect.objectContaining({ type: "recommendation_shown", movie_id: 42, source: "under_90" })]);
    expect(disconnect).toHaveBeenCalled();
  });

  it("does not record a card scrolled past within the second", () => {
    render(<Card />);
    act(() => observed!([{ isIntersecting: true, intersectionRatio: 0.8 }]));
    act(() => vi.advanceTimersByTime(SHOWN_AFTER_MS / 2));
    act(() => observed!([{ isIntersecting: false, intersectionRatio: 0 }]));
    act(() => vi.advanceTimersByTime(SHOWN_AFTER_MS * 2));
    expect(queued()).toEqual([]);
  });

  it("does not record a card less than half in view", () => {
    render(<Card />);
    act(() => observed!([{ isIntersecting: true, intersectionRatio: 0.3 }]));
    act(() => vi.advanceTimersByTime(SHOWN_AFTER_MS * 2));
    expect(queued()).toEqual([]);
  });
});
