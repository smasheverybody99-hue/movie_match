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

/** Uzbek labels for display. Keys must cover every trait. */
export const TRAIT_LABELS_UZ: Record<TraitKey, string> = {
  psychological_complexity: "Psixologik murakkablik",
  plot_twist: "Syujet burilishi",
  mystery: "Sirlilik",
  character_depth: "Personaj chuqurligi",
  emotional_intensity: "Hissiy zichlik",
  pacing: "Temp",
  humor: "Hazil",
  romance: "Romantika",
  action: "Ekshn",
  violence: "Zo'ravonlik",
  visual_style: "Vizual uslub",
  realism: "Realizm",
  darkness: "Qorong'ulik",
  ending_ambiguity: "Ochiq tugash",
};

/** Bar colour band. Strength, not quality — see the design system. */
export function traitBand(score: number): "strong" | "medium" | "weak" {
  if (score >= 80) return "strong";
  if (score >= 50) return "medium";
  return "weak";
}
