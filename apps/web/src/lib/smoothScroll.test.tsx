import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { allowMotion } from "../test/utils";
import { loadGsap, resetGsap } from "./gsap";
import { SmoothScroll } from "./smoothScroll";

/** Every ResizeObserver made while a test runs, so one can be fired by hand. */
const observers: (() => void)[] = [];

/** jsdom has no ResizeObserver; Lenis and the refresh below both want one. */
function observersAvailable() {
  observers.length = 0;
  vi.stubGlobal(
    "ResizeObserver",
    class {
      constructor(callback: () => void) {
        observers.push(callback);
      }
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  );
}

afterEach(() => {
  resetGsap();
  document.documentElement.className = "";
});

describe("SmoothScroll", () => {
  it("passes the app through untouched", () => {
    render(
      <SmoothScroll>
        <p>the app</p>
      </SmoothScroll>,
    );
    expect(screen.getByText("the app")).toBeTruthy();
  });

  it("with reduced motion the browser's own scrolling is left alone", async () => {
    render(
      <SmoothScroll>
        <p>the app</p>
      </SmoothScroll>,
    );
    await Promise.resolve();
    expect(document.documentElement.classList.contains("lenis")).toBe(false);
  });

  it("takes the scroll over once the chunk is in, and hands it back on the way out", async () => {
    allowMotion();
    observersAvailable();
    const { unmount } = render(
      <SmoothScroll>
        <p>the app</p>
      </SmoothScroll>,
    );
    // Lenis marks the document, which is what the CSS in app.css hangs off.
    await waitFor(() => expect(document.documentElement.classList.contains("lenis")).toBe(true));
    unmount();
    await waitFor(() => expect(document.documentElement.classList.contains("lenis")).toBe(false));
  });

  it("re-measures the scroll animations when the page grows", async () => {
    allowMotion();
    observersAvailable();
    const { ScrollTrigger } = await loadGsap();
    const refresh = vi.spyOn(ScrollTrigger, "refresh").mockImplementation(() => ScrollTrigger);
    render(
      <SmoothScroll>
        <p>the app</p>
      </SmoothScroll>,
    );
    // A feed's rows and a film's panels arrive after the first measurement. Without this
    // every scroll-driven animation stays set up against the empty page it started on.
    await waitFor(() => expect(observers).not.toHaveLength(0));
    refresh.mockClear();
    for (const fire of observers) fire();
    await waitFor(() => expect(refresh).toHaveBeenCalled());
    refresh.mockRestore();
  });
});
