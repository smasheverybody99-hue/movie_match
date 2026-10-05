import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { usePrefersReducedMotion } from "./motion";

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
  });
});
