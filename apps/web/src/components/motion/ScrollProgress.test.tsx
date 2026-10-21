import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { resetGsap } from "../../lib/gsap";
import { allowMotion } from "../../test/utils";
import { ScrollProgress } from "./ScrollProgress";

afterEach(() => resetGsap());

/** A document twice the height of the window, scrolled to `y`. */
function scrolledTo(y: number) {
  vi.spyOn(document.documentElement, "scrollHeight", "get").mockReturnValue(2000);
  vi.spyOn(window, "innerHeight", "get").mockReturnValue(1000);
  window.scrollY = y;
  window.dispatchEvent(new Event("scroll"));
}

describe("ScrollProgress", () => {
  it("is decorative: the scrollbar already says the same thing", () => {
    const { container } = render(<ScrollProgress />);
    expect(container.querySelector(".scroll-progress")?.getAttribute("aria-hidden")).toBe("true");
  });

  it("with reduced motion it still reports the position, straight from the scroll", () => {
    render(<ScrollProgress />);
    scrolledTo(500); // half of the 1000px that can be scrolled
    expect(screen.getByTestId("scroll-progress").style.transform).toBe("scaleX(0.5)");
    scrolledTo(1000);
    expect(screen.getByTestId("scroll-progress").style.transform).toBe("scaleX(1)");
  });

  it("never reports more than the whole document", () => {
    render(<ScrollProgress />);
    scrolledTo(99999);
    expect(screen.getByTestId("scroll-progress").style.transform).toBe("scaleX(1)");
  });

  it("with motion the bar is scrubbed by GSAP instead of the listener", async () => {
    allowMotion();
    render(<ScrollProgress />);
    // GSAP sets the starting scale itself; the listener above is not installed at all.
    await waitFor(() => expect(screen.getByTestId("scroll-progress").style.transform).toContain("scale"));
    scrolledTo(500);
    expect(screen.getByTestId("scroll-progress").style.transform).not.toBe("scaleX(0.5)");
  });
});
