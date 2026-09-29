import { describe, expect, it } from "vitest";

import sharedSpec from "../../../../packages/shared/traits.json";
import { TRAIT_KEYS } from "../lib/traits";
import { en } from "./en";
import { format, translate } from "./index";
import { uz } from "./uz";

describe("dictionaries", () => {
  it("every key in uz exists in en", () => {
    const missing = Object.keys(uz).filter((key) => !(key in en));
    expect(missing).toEqual([]);
  });

  it("every key in en exists in uz", () => {
    const extra = Object.keys(en).filter((key) => !(key in uz));
    expect(extra).toEqual([]);
  });

  it("no string is empty", () => {
    for (const dict of [uz, en]) {
      for (const [key, value] of Object.entries(dict)) {
        expect(value.trim(), key).not.toBe("");
      }
    }
  });

  it("both languages use the same placeholders in each string", () => {
    const names = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const key of Object.keys(uz) as (keyof typeof uz)[]) {
      expect(names(en[key]), key).toEqual(names(uz[key]));
    }
  });

  it("has a label for every trait, equal to packages/shared/traits.json", () => {
    for (const dimension of sharedSpec.dimensions) {
      const key = `trait.${dimension.key}` as keyof typeof uz;
      expect(uz[key], dimension.key).toBe(dimension.label_uz);
      expect(en[key], dimension.key).toBe(dimension.label_en);
    }
    expect(sharedSpec.dimensions.map((d) => d.key)).toEqual([...TRAIT_KEYS]);
  });
});

describe("format", () => {
  it("fills placeholders and leaves unknown ones", () => {
    expect(format("{a} and {b}", { a: 1 })).toBe("1 and {b}");
  });

  it("translates in the requested language", () => {
    expect(translate("en", "feed.section.because_you_loved", { title: "Heat" })).toBe(
      "Because you loved Heat",
    );
    expect(translate("uz", "feed.section.because_you_loved", { title: "Heat" })).toBe(
      "Heat yoqqani uchun",
    );
  });
});
