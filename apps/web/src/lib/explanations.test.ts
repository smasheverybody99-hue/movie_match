import { beforeEach, describe, expect, it } from "vitest";

import { explanationsOff, noteExplanation, resetExplanations } from "./explanations";

describe("explanationsOff", () => {
  beforeEach(resetExplanations);

  it("starts asking", () => {
    expect(explanationsOff()).toBeNull();
  });

  it("stops asking for the rest of the session once the API settles it", () => {
    for (const reason of ["no_generator", "daily_cap", "no_taste"] as const) {
      resetExplanations();
      noteExplanation(reason);
      expect(explanationsOff()).toBe(reason);
      // and it stays settled: a later per-film answer does not reopen it
      noteExplanation("no_reasons");
      expect(explanationsOff()).toBe(reason);
    }
  });

  it("keeps asking after answers that are about one film", () => {
    for (const reason of ["no_traits", "no_reasons", "rejected"] as const) {
      noteExplanation(reason);
      expect(explanationsOff()).toBeNull();
    }
  });

  it("allows one failure, then stops: a timeout costs up to ten seconds a film", () => {
    noteExplanation("failed");
    expect(explanationsOff()).toBeNull();
    noteExplanation("failed");
    expect(explanationsOff()).toBe("failed");
  });

  it("counts failures in a row, not in total", () => {
    noteExplanation("failed");
    noteExplanation(null); // a sentence arrived, so the provider is answering
    noteExplanation("failed");
    expect(explanationsOff()).toBeNull();
  });

  it("treats a missing reason like a sentence", () => {
    noteExplanation("failed");
    noteExplanation(undefined);
    noteExplanation("failed");
    expect(explanationsOff()).toBeNull();
  });
});
