import { beforeEach, describe, expect, it } from "vitest";

import { allowMotion } from "../test/utils";
import { loadGsap, resetGsap } from "./gsap";

// ScrollTrigger asks the browser about media queries as it registers. Nothing loads GSAP
// without one: an app with no matchMedia reads the motion preference as "reduce"
// (lib/motion.ts) and never gets this far.
beforeEach(() => {
  allowMotion();
  resetGsap();
});

describe("loadGsap", () => {
  it("hands out one GSAP with both plugins registered", async () => {
    const bundle = await loadGsap();
    expect(typeof bundle.gsap.to).toBe("function");

    // Registered, so a tween's `scrollTrigger` is acted on rather than warned about.
    const box = document.createElement("div");
    document.body.append(box);
    const tween = bundle.gsap.to(box, { opacity: 0, scrollTrigger: { trigger: box } });
    expect(bundle.ScrollTrigger.getAll()).not.toHaveLength(0);
    tween.scrollTrigger?.kill();
    tween.kill();
    box.remove();

    // And a line of text can be split into letters, then put back as it was.
    const line = document.createElement("p");
    line.textContent = "Movie Match";
    document.body.append(line);
    const split = new bundle.SplitText(line, { type: "chars" });
    expect(split.chars.length).toBe("MovieMatch".length);
    split.revert();
    expect(line.textContent).toBe("Movie Match");
    line.remove();
  });

  it("loads once, however many components ask", async () => {
    const [first, second] = await Promise.all([loadGsap(), loadGsap()]);
    expect(first).toBe(second);
    expect(await loadGsap()).toBe(first);
  });
});
