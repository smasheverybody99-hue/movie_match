import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useCountUp, usePrefersReducedMotion } from "./motion";

function mediaQuery(reduce: boolean) {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: reduce,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
}

describe("motion", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("follows prefers-reduced-motion", () => {
    mediaQuery(true);
    expect(renderHook(() => usePrefersReducedMotion()).result.current).toBe(true);
    mediaQuery(false);
    expect(renderHook(() => usePrefersReducedMotion()).result.current).toBe(false);
  });

  it("treats an unknown preference as reduced: nothing moves", () => {
    vi.stubGlobal("matchMedia", undefined);
    expect(renderHook(() => usePrefersReducedMotion()).result.current).toBe(true);
    expect(renderHook(() => useCountUp(82)).result.current).toBe(82);
  });

  it("shows the final number at once when motion is reduced", () => {
    mediaQuery(true);
    expect(renderHook(() => useCountUp(82)).result.current).toBe(82);
  });

  it("counts up from 0 and ends exactly on the target", () => {
    mediaQuery(false);
    vi.useFakeTimers({ toFake: ["requestAnimationFrame", "cancelAnimationFrame", "performance"] });
    const { result } = renderHook(() => useCountUp(82, 600));
    expect(result.current).toBe(0);
    act(() => vi.advanceTimersByTime(300));
    expect(result.current).toBeGreaterThan(0);
    expect(result.current).toBeLessThan(82);
    act(() => vi.advanceTimersByTime(400));
    expect(result.current).toBe(82);
  });
});
