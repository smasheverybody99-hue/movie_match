/**
 * The Movie DNA dimensions, as the web client knows them.
 *
 * This list mirrors packages/shared/traits.json. It is written out rather than
 * imported so that the production bundle does not reach outside the app
 * directory; `traits.test.ts` proves the two stay identical.
 *
 * The ORDER is the vector order used by the API. Never reorder.
 */
export const TRAIT_KEYS = [
  "psychological_complexity",
  "plot_twist",
  "mystery",
  "character_depth",
  "emotional_intensity",
  "pacing",
  "humor",
  "romance",
  "action",
  "violence",
  "visual_style",
  "realism",
  "darkness",
  "ending_ambiguity",
] as const;

export type TraitKey = (typeof TRAIT_KEYS)[number];

export const TRAIT_COUNT = TRAIT_KEYS.length;

/** Display labels live in the i18n dictionaries (`trait.<key>`), taken from traits.json. */
export function isTraitKey(value: string): value is TraitKey {
  return (TRAIT_KEYS as readonly string[]).includes(value);
}

/** Bar colour band. Strength, not quality — see the design system. */
export function traitBand(score: number): "strong" | "medium" | "weak" {
  if (score >= 80) return "strong";
  if (score >= 50) return "medium";
  return "weak";
}
