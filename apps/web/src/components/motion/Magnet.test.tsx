import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { resetGsap } from "../../lib/gsap";
import { allowMotion } from "../../test/utils";
import { Magnet } from "./Magnet";

afterEach(() => resetGsap());

function wrapper(): HTMLElement {
  const parent = screen.getByRole("button").parentElement;
  if (!parent) throw new Error("no wrapper");
  return parent;
}

function pointerAt(x: number, y: number) {
  window.dispatchEvent(new MouseEvent("pointermove", { clientX: x, clientY: y }));
}

describe("Magnet", () => {
  it("with reduced motion the pointer moves nothing", async () => {
    render(
      <Magnet>
        <button type="button">Continue</button>
      </Magnet>,
    );
    pointerAt(4, 4);
    await Promise.resolve();
    expect(wrapper().style.transform).toBe("");
  });

  it("on a touch screen the pointer moves nothing", async () => {
    allowMotion({ finePointer: false });
    render(
      <Magnet>
        <button type="button">Continue</button>
      </Magnet>,
    );
    await waitFor(() => expect(wrapper()).toBeTruthy());
    pointerAt(4, 4);
    await Promise.resolve();
    expect(wrapper().style.transform).toBe("");
  });

  it("leans towards a pointer that comes close, and settles back", async () => {
    allowMotion();
    render(
      <Magnet strength={0.5}>
        <button type="button">Continue</button>
      </Magnet>,
    );
    // The listener goes on once the GSAP chunk is in, so the pointer keeps moving until
    // something answers it.
    await waitFor(() => {
      pointerAt(20, 0);
      expect(wrapper().style.transform).toContain("translate");
    });
    // Away again: it returns to where the layout put it.
    pointerAt(5000, 5000);
    await waitFor(() => expect(wrapper().style.transform).toMatch(/translate3d\(0px, 0px/));
  });

  it("keeps the button reachable: the wrapper is only a box around it", () => {
    render(
      <Magnet className="full">
        <button type="button">Continue</button>
      </Magnet>,
    );
    expect(wrapper().className).toBe("magnet full");
    expect(screen.getByRole("button", { name: "Continue" })).toBeTruthy();
  });
});
