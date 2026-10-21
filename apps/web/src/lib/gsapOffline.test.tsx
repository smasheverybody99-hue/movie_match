import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Reveal } from "../components/motion/Reveal";
import { allowMotion } from "../test/utils";

// The GSAP chunk cannot be fetched: an offline visit to a page whose chunk was never
// cached. A component that hid itself for an animation that is now never coming has to
// undo that, or the visitor is left looking at nothing.
vi.mock("gsap", () => {
  throw new Error("chunk unavailable");
});

describe("a motion chunk that never arrives", () => {
  it("leaves the content visible instead of hidden", async () => {
    allowMotion();
    render(
      <Reveal immediate>
        <p>content</p>
      </Reveal>,
    );
    const box = screen.getByText("content").parentElement;
    expect(box?.style.opacity).toBe("0");
    await waitFor(() => expect(box?.style.opacity).toBe(""));
  });

  it("leaves staggered children visible too", async () => {
    allowMotion();
    render(
      <Reveal immediate stagger={0.05}>
        <p>first</p>
        <p>second</p>
      </Reveal>,
    );
    await waitFor(() => {
      expect(screen.getByText("first").style.opacity).toBe("");
      expect(screen.getByText("second").style.opacity).toBe("");
    });
  });
});
