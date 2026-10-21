import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { resetGsap } from "../../lib/gsap";
import { allowMotion } from "../../test/utils";
import { Tilt } from "./Tilt";

afterEach(() => resetGsap());

function card(): HTMLElement {
  const parent = screen.getByText("poster").parentElement;
  if (!parent) throw new Error("no card");
  return parent;
}

/** jsdom lays nothing out, so the card is given a size to be tilted within. */
function sized(el: HTMLElement) {
  vi.spyOn(el, "getBoundingClientRect").mockReturnValue({
    x: 0, y: 0, top: 0, left: 0, right: 200, bottom: 300, width: 200, height: 300,
    toJSON: () => ({}),
  });
}

function over(el: HTMLElement, x: number, y: number) {
  el.dispatchEvent(new MouseEvent("pointermove", { clientX: x, clientY: y, bubbles: false }));
}

describe("Tilt", () => {
  it("with reduced motion the card never turns", async () => {
    render(
      <Tilt className="movie-card">
        <span>poster</span>
      </Tilt>,
    );
    sized(card());
    over(card(), 10, 10);
    await Promise.resolve();
    expect(card().style.transform).toBe("");
  });

  it("on a touch screen the card never turns", async () => {
    allowMotion({ finePointer: false });
    render(
      <Tilt className="movie-card">
        <span>poster</span>
      </Tilt>,
    );
    await waitFor(() => expect(card()).toBeTruthy());
    sized(card());
    over(card(), 10, 10);
    await Promise.resolve();
    expect(card().style.transform).toBe("");
  });

  it("turns towards the pointer and back to flat", async () => {
    allowMotion();
    render(
      <Tilt className="movie-card" max={8}>
        <span>poster</span>
      </Tilt>,
    );
    const el = card();
    sized(el);
    // The top-left corner is the largest turn on both axes. The pointer keeps moving
    // until something answers it: the listener goes on with the GSAP chunk.
    await waitFor(() => {
      over(el, 0, 0);
      expect(el.style.transform).toMatch(/rotate[XY]\(/);
    });
    el.dispatchEvent(new MouseEvent("pointerleave"));
    await waitFor(() => expect(el.style.transform).not.toMatch(/rotate[XY]\(-?[1-9]/));
  });

  it("renders one box with the class it was given, so the card's own CSS still applies", () => {
    render(
      <Tilt className="movie-card has-quick">
        <span>poster</span>
      </Tilt>,
    );
    expect(card().className).toBe("movie-card has-quick");
    expect(card().tagName).toBe("DIV");
  });
});
