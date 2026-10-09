import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TASTE } from "../dev/fixtures";
import { TRAIT_KEYS } from "../lib/traits";
import { renderWithProviders } from "../test/utils";
import { DnaFlower, lines, rayAngle, rayLength, rayOpacity, shapePoints } from "./DnaFlower";

describe("DnaFlower", () => {
  it("is one image with the summary as its label", () => {
    renderWithProviders(<DnaFlower scores={TASTE} label="Movie DNA chart. Strongest: Plot twists 91." />);
    expect(screen.getByRole("img", { name: "Movie DNA chart. Strongest: Plot twists 91." })).toBe(
      screen.getByTestId("dna-flower"),
    );
  });

  it("draws one ray per trait, in traits.json order, with its value", () => {
    renderWithProviders(<DnaFlower scores={TASTE} label="x" />);
    const rays = TRAIT_KEYS.map((key) => screen.getByTestId(`ray-${key}`));
    expect(rays).toHaveLength(14);
    expect(rays.map((r) => Number(r.dataset.value))).toEqual(TRAIT_KEYS.map((key) => TASTE[key]));
  });

  it("makes length linear in the value, from the inner circle to the 100 ring", () => {
    expect(rayLength(0)).toBe(40);
    expect(rayLength(100)).toBe(170);
    expect(rayLength(50)).toBe(105); // the 50 ring sits exactly half way
    expect(rayLength(80) - rayLength(40)).toBeCloseTo(rayLength(40) - rayLength(0)); // equal steps
    expect(rayLength(140)).toBe(170); // clamped
  });

  it("gives each trait the same angle for everyone: the first at 12 o'clock, then clockwise", () => {
    expect(rayAngle(0)).toBeCloseTo(-Math.PI / 2);
    expect(rayAngle(7)).toBeCloseTo(Math.PI / 2); // half way round: 6 o'clock
  });

  it("lights the three strongest fully, the rest by value but never below 0.4", () => {
    expect(rayOpacity(10, true)).toBe(1);
    expect(rayOpacity(0, false)).toBe(0.4);
    expect(rayOpacity(100, false)).toBeCloseTo(0.85);
    renderWithProviders(<DnaFlower scores={TASTE} label="x" />);
    // TASTE: plot_twist 91, psychological_complexity 88, mystery 84 are the top three
    const top = [...document.querySelectorAll(".dna-label.is-top")].map((l) => l.closest("g")!.dataset.testid);
    expect(top.sort()).toEqual(["ray-mystery", "ray-plot_twist", "ray-psychological_complexity"]);
    const strongRay = screen.getByTestId("ray-plot_twist").querySelector("line")!;
    expect(strongRay.style.opacity).toBe("1");
  });

  it("draws one closed outline through the 14 ray tips, on the same fixed scale", () => {
    renderWithProviders(<DnaFlower scores={TASTE} label="x" />);
    const points = screen.getByTestId("dna-shape").getAttribute("points")!.split(" ");
    expect(points).toHaveLength(14);
    // the first trait points straight up: its tip is rayLength(value) above the centre
    const [x, y] = points[0]!.split(",").map(Number);
    expect(x).toBeCloseTo(0, 0);
    expect(y).toBeCloseTo(-rayLength(TASTE.psychological_complexity!), 0);
    // each tip is exactly where its ray ends
    const ray = screen.getByTestId("ray-plot_twist").querySelector("line")!;
    expect(points[1]).toBe(`${Number(ray.getAttribute("x2")).toFixed(1)},${Number(ray.getAttribute("y2")).toFixed(1)}`);
    // a value of 100 sits on the 100 ring for everyone
    expect(shapePoints({ psychological_complexity: 100 }).split(" ")[0]).toBe("0.0,-170.0");
  });

  it("names every trait, splitting a long name over two lines", () => {
    renderWithProviders(<DnaFlower scores={TASTE} label="x" />);
    expect(document.querySelectorAll(".dna-label")).toHaveLength(14);
    const long = screen.getByTestId("ray-emotional_intensity").querySelectorAll("tspan");
    expect([...long].map((s) => s.textContent)).toEqual(["Emotional", "intensity"]);
  });
});

describe("DnaFlower labels", () => {
  it("puts a label of 12 characters or more on two lines, at the space nearest the middle", () => {
    expect(lines("Накал эмоций")).toEqual(["Накал", "эмоций"]); // 12: one line ran past a phone
    expect(lines("Emotional intensity")).toEqual(["Emotional", "intensity"]);
    expect(lines("Plot twists")).toEqual(["Plot twists"]); // 11
    expect(lines("Динамичность")).toEqual(["Динамичность"]); // one word stays whole
  });
});
