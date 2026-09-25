import { describe, expect, it } from "vitest";

import sharedSpec from "../../../../packages/shared/traits.json";

import { TRAIT_COUNT, TRAIT_KEYS, TRAIT_LABELS_UZ, traitBand } from "./traits";

interface TraitSpec {
  version: number;
  scale: { min: number; max: number };
  dimensions: { key: string; label_en: string; label_uz: string; description: string }[];
}

/**
 * The web client keeps its own copy of the trait key list. If it drifts from
 * packages/shared/traits.json, every trait score renders against the wrong
 * label and nothing crashes — the UI just quietly lies. This test is what
 * catches that.
 *
 * Imported through Vite rather than read with `new URL(..., import.meta.url)`:
 * Vite rewrites that pattern into an asset URL, which is not a file path.
 */
const spec: TraitSpec = sharedSpec;

describe("trait contract", () => {
  it("has the same keys, in the same order, as the shared spec", () => {
    expect(spec.dimensions.map((d) => d.key)).toEqual([...TRAIT_KEYS]);
  });

  it("has the same number of dimensions", () => {
    expect(TRAIT_COUNT).toBe(spec.dimensions.length);
  });

  it("has an Uzbek label for every trait", () => {
    for (const key of TRAIT_KEYS) {
      expect(TRAIT_LABELS_UZ[key], `missing label for ${key}`).toBeTruthy();
    }
  });

  it("uses a 0-100 scale", () => {
    expect(spec.scale).toEqual({ min: 0, max: 100 });
  });
});

describe("traitBand", () => {
  it("bands by strength at the documented boundaries", () => {
    expect(traitBand(100)).toBe("strong");
    expect(traitBand(80)).toBe("strong");
    expect(traitBand(79)).toBe("medium");
    expect(traitBand(50)).toBe("medium");
    expect(traitBand(49)).toBe("weak");
    expect(traitBand(0)).toBe("weak");
  });
});
