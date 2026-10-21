import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { resetGsap } from "../../lib/gsap";
import { allowMotion } from "../../test/utils";
import { SplitText } from "./SplitText";

afterEach(() => resetGsap());

describe("SplitText", () => {
  it("with reduced motion it is one plain line of text", () => {
    render(<SplitText as="h1" text="Movie Match" />);
    const heading = screen.getByRole("heading", { name: "Movie Match" });
    expect(heading.querySelectorAll("span")).toHaveLength(0);
    expect(heading.style.opacity).toBe("");
  });

  it("splits into letters and still reads as the whole line", async () => {
    allowMotion();
    render(<SplitText as="h1" text="Movie Match" duration={0.05} immediate />);
    const heading = screen.getByRole("heading");
    await waitFor(() => expect(heading.querySelectorAll(".split-char").length).toBeGreaterThan(5));
    // The pieces are hidden from assistive technology and the whole line is the label,
    // so a screen reader reads the title, not a column of letters.
    expect(screen.getByRole("heading", { name: "Movie Match" })).toBe(heading);
    expect(heading.querySelector(".split-char")?.getAttribute("aria-hidden")).toBe("true");
    // The letters are real text, so find-in-page still matches the title.
    expect(heading.textContent).toBe("Movie Match");
  });

  it("puts the text back as it was when it goes away", async () => {
    allowMotion();
    const { unmount } = render(<SplitText as="h2" text="Movie DNA" duration={0.05} immediate />);
    const heading = screen.getByRole("heading");
    await waitFor(() => expect(heading.querySelectorAll(".split-char").length).toBeGreaterThan(3));
    unmount();
    expect(heading.querySelectorAll(".split-char")).toHaveLength(0);
  });

  it("hides the unsplit line until the letters are ready", () => {
    allowMotion();
    render(<SplitText as="p" text="A sentence" immediate />);
    expect(screen.getByText("A sentence").style.opacity).toBe("0");
  });
});
