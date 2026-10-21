import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { resetGsap } from "../../lib/gsap";
import { allowMotion } from "../../test/utils";
import { Reveal } from "./Reveal";

afterEach(() => resetGsap());

/** The element Reveal rendered: the one the children sit in. */
function box(): HTMLElement {
  const parent = screen.getByText("content").parentElement;
  if (!parent) throw new Error("no box");
  return parent;
}

describe("Reveal", () => {
  it("with reduced motion the block is simply there", () => {
    render(
      <Reveal>
        <p>content</p>
      </Reveal>,
    );
    expect(box().style.opacity).toBe("");
  });

  it("starts hidden before the first paint and ends visible", async () => {
    allowMotion();
    render(
      <Reveal immediate duration={0.05}>
        <p>content</p>
      </Reveal>,
    );
    // Hidden from the render itself, not from an effect: no flash of finished content.
    expect(box().style.opacity).toBe("0");
    await waitFor(() => expect(Number(box().style.opacity || "1")).toBeGreaterThan(0.9));
  });

  it("leaves no transform behind, which would trap the page's fixed bars", async () => {
    allowMotion();
    render(
      <Reveal immediate duration={0.05} y={40}>
        <p>content</p>
      </Reveal>,
    );
    // The travel is written as a transform the moment the tween is built, and clearProps
    // takes it back once the tween is done: the second wait is the end of the animation.
    await waitFor(() => expect(box().style.transform).toContain("translate3d"));
    await waitFor(() => expect(box().style.transform).toBe(""));
    expect(box().style.opacity).toBe("1");
    // And nothing asked for a compositor layer that outlives the tween.
    expect(box().style.willChange).toBe("");
  });

  it("staggers its children, hiding each one before the paint", async () => {
    allowMotion();
    render(
      <Reveal stagger={0.01} immediate duration={0.05}>
        <p>content</p>
        <p>second</p>
      </Reveal>,
    );
    const children = [...box().children] as HTMLElement[];
    expect(children.map((c) => c.style.opacity)).toEqual(["0", "0"]);
    // The box itself is never hidden in this mode: its children are.
    expect(box().style.opacity).toBe("");
    await waitFor(() => {
      for (const child of children) expect(Number(child.style.opacity || "1")).toBeGreaterThan(0.9);
    });
  });

  it("keeps the tag and the heading a section is named by", () => {
    render(
      <Reveal as="section" labelledBy="title" className="panel">
        <h2 id="title">content</h2>
      </Reveal>,
    );
    const section = screen.getByRole("region", { name: "content" });
    expect(section.tagName).toBe("SECTION");
    expect(section.className).toBe("panel");
  });
});
