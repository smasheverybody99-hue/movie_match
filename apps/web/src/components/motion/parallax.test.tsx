import { render, waitFor } from "@testing-library/react";
import { useRef } from "react";
import { afterEach, describe, expect, it } from "vitest";

import { resetGsap } from "../../lib/gsap";
import { allowMotion } from "../../test/utils";
import { useParallax } from "./parallax";

afterEach(() => resetGsap());

function Hero({ selector }: { selector?: string }) {
  const box = useRef<HTMLDivElement>(null);
  useParallax(box, { selector });
  return (
    <div ref={box} data-testid="hero" style={{ height: 400 }}>
      <img className="film-hero-img" alt="" data-testid="backdrop" />
      <img className="film-hero-img film-hero-blur" alt="" data-testid="blurred" />
    </div>
  );
}

describe("useParallax", () => {
  it("with reduced motion the backdrop sits where the layout put it", async () => {
    const { getByTestId } = render(<Hero selector=".film-hero-img:not(.film-hero-blur)" />);
    await Promise.resolve();
    expect(getByTestId("backdrop").style.transform).toBe("");
  });

  it("holds the backdrop behind the page, scaled so no edge can show", async () => {
    allowMotion();
    const { getByTestId } = render(<Hero selector=".film-hero-img:not(.film-hero-blur)" />);
    await waitFor(() => expect(getByTestId("backdrop").style.transform).toContain("scale"));
    expect(getByTestId("backdrop").style.transform).toContain("translate");
  });

  it("leaves out whatever the selector excludes: the blurred stand-in has its own transform", async () => {
    allowMotion();
    const { getByTestId } = render(<Hero selector=".film-hero-img:not(.film-hero-blur)" />);
    await waitFor(() => expect(getByTestId("backdrop").style.transform).toContain("scale"));
    expect(getByTestId("blurred").style.transform).toBe("");
  });

  it("moves the box itself when no selector is given", async () => {
    allowMotion();
    const { getByTestId } = render(<Hero />);
    await waitFor(() => expect(getByTestId("hero").style.transform).toContain("scale"));
  });
});
