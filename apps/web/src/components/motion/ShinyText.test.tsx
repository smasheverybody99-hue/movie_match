import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ShinyText } from "./ShinyText";

describe("ShinyText", () => {
  it("leaves the words in the page, so they are read and found as text", () => {
    render(<ShinyText>Taste, not genres</ShinyText>);
    expect(screen.getByText("Taste, not genres")).toBeTruthy();
  });

  it("is CSS only: the sheen is a class, so the global reduced-motion rule stops it", () => {
    const { container } = render(<ShinyText className="brand-name">Movie Match</ShinyText>);
    expect(container.firstElementChild?.className).toBe("shiny-text brand-name");
    expect(container.querySelector(".shiny-text")?.tagName).toBe("SPAN");
  });
});
