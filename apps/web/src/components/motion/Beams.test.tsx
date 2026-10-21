import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { resetGsap } from "../../lib/gsap";
import { allowMotion } from "../../test/utils";
import { Beams } from "./Beams";

afterEach(() => resetGsap());

function beams(container: HTMLElement): HTMLElement[] {
  return [...container.querySelectorAll<HTMLElement>(".beam")];
}

describe("Beams", () => {
  it("is decorative: hidden from assistive technology and reads nothing out", () => {
    const { container } = render(<Beams />);
    const box = container.querySelector(".beams");
    expect(box?.getAttribute("aria-hidden")).toBe("true");
    expect(box?.textContent).toBe("");
    expect(screen.queryByRole("img")).toBeNull();
  });

  it("with reduced motion the beams are still there, simply still", () => {
    const { container } = render(<Beams />);
    expect(beams(container)).toHaveLength(3);
    for (const beam of beams(container)) expect(beam.style.transform).toBe("");
  });

  it("drifts each beam once the chunk is in", async () => {
    allowMotion();
    const { container } = render(<Beams />);
    await waitFor(() => expect(beams(container)[0]?.style.transform).toContain("translate"));
  });

  it("takes the class it is given, so a screen can place it", () => {
    const { container } = render(<Beams className="welcome-beams" />);
    expect(container.querySelector(".beams")?.className).toBe("beams welcome-beams");
  });
});
