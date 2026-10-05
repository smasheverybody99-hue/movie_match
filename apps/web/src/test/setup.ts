import "@testing-library/jest-dom/vitest";

import { cleanup, configure } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// findBy* / waitFor give up after this long (the library's default is 1000 ms). A wait here
// is for an exact role, name or text, and on an idle machine it is met at the first check.
// But a busy worker can stall for over a second (measured: the 1000 ms timer fired 1373 ms
// late while the mocked response sat resolved and unrendered), and on expiry waitFor fails
// without one last check, so the overdue timer beats the render already queued behind it.
// A passing wait returns as soon as it is met, so the longer limit costs nothing when green.
configure({ asyncUtilTimeout: 3000 });

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
