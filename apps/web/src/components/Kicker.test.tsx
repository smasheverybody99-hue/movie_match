import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { I18nProvider } from "../i18n";
import type { Lang, MatchBand, TraitSide } from "../lib/types";
import { Kicker } from "./Kicker";

function heading(band: MatchBand | null, side: TraitSide | null, lang: Lang = "en") {
  const { container } = render(
    <I18nProvider lang={lang}>
      <Kicker band={band} side={side} />
    </I18nProvider>,
  );
  const el = container.querySelector(".kicker")!;
  return { text: el.textContent, red: el.classList.contains("kicker-strong") };
}

describe("Kicker", () => {
  it("names a reason sentence, red only for the closest films", () => {
    expect(heading("strong", "reason")).toEqual({ text: "Strong match", red: true });
    expect(heading("good", "reason")).toEqual({ text: "Why it suits you", red: false });
    expect(heading(null, "reason")).toEqual({ text: "Why it suits you", red: false });
  });

  it("names a difference sentence, never in red", () => {
    expect(heading("good", "difference")).toEqual({ text: "How it differs", red: false });
    expect(heading(null, "difference")).toEqual({ text: "How it differs", red: false });
  });

  // The pairing TZ 1.23/1.24 removed from the recommendation row: red "STRONG MATCH" above a
  // sentence saying the film is unlike the viewer. No catalogue film is in this state yet.
  it("drops the red heading when a closest film is described by its differences", () => {
    expect(heading("strong", "difference")).toEqual({ text: "How it differs", red: false });
  });

  // Silence is not a contradiction: there is no sentence, but the band is still true, and a
  // film with nothing named is the one closest to the taste on all 14 traits.
  it("keeps the red heading for a closest film with nothing named", () => {
    expect(heading("strong", null)).toEqual({ text: "Strong match", red: true });
  });

  it("stays neutral with nothing named outside the strong band", () => {
    for (const band of ["good", null] as const) {
      expect(heading(band, null), String(band)).toEqual({ text: "You and this film", red: false });
    }
  });

  it("translates every heading", () => {
    expect(heading(null, "reason", "uz").text).toBe("Nega sizga mos keladi");
    expect(heading(null, "difference", "uz").text).toBe("Nimasi boshqacha");
    expect(heading(null, "reason", "ru").text).toBe("Чем вам подходит");
    expect(heading(null, "difference", "ru").text).toBe("Чем отличается");
    expect(heading("strong", "reason", "ru").text).toBe("Больше всего подходит");
  });
});
