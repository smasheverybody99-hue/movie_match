import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { resetGsap } from "../../lib/gsap";
import { allowMotion } from "../../test/utils";
import { CountUp } from "./CountUp";

afterEach(() => resetGsap());

/**
 * A count that is deliberately far too slow to finish during the test, so what is
 * asserted is a step on the way and never a race with the end of it.
 */
const SLOW = 30;

describe("CountUp", () => {
  it("with reduced motion the final number is there at once (docs/ui.md 7)", () => {
    render(<CountUp value={45} />);
    expect(screen.getByTestId("count-up").textContent).toBe("45");
  });

  it("starts below the value and counts towards it", async () => {
    allowMotion();
    render(<CountUp value={45} duration={SLOW} immediate />);
    const span = screen.getByTestId("count-up");
    await waitFor(() => expect(Number(span.textContent)).toBeLessThan(45));
    expect(Number(span.textContent)).toBeGreaterThanOrEqual(0);
  });

  it("lands exactly on the value", async () => {
    allowMotion();
    render(<CountUp value={45} duration={0.05} immediate />);
    await waitFor(() => expect(screen.getByTestId("count-up").textContent).toBe("45"));
  });

  it("writes every step through the caller's format", async () => {
    allowMotion();
    render(<CountUp value={4} duration={SLOW} format={(n) => `${n.toFixed(1)} of 5`} immediate />);
    const span = screen.getByTestId("count-up");
    await waitFor(() => expect(span.textContent).toMatch(/^[0-3]\.\d of 5$/));
  });
});
