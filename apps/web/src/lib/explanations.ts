import type { ExplanationReason } from "./types";

/**
 * Whether asking for another "why you" sentence is still worth it in this session.
 *
 * The API answers a missing sentence with a reason (app/services/explain.py). Three of
 * them will not change while the tab is open - nothing can generate, this user's daily
 * allowance is used up, or they have no taste profile yet - so after one of those the
 * film page stops asking and stops showing "Writing the explanation…": the indicator
 * promised a sentence that was never coming, which is what a tester reported on
 * 2026-10-13.
 *
 * `failed` is different. One timeout is bad luck, so the next film still asks; two in a
 * row is the provider being down, and then asking again only buys another wait of up to
 * the API's ten seconds per film.
 */
const SETTLED: readonly ExplanationReason[] = ["no_generator", "daily_cap", "no_taste"];
const FAILURES_ALLOWED = 2;

let off: ExplanationReason | null = null;
let failures = 0;

/** The reason no sentence is coming, or null while one still might. */
export function explanationsOff(): ExplanationReason | null {
  return off;
}

/** Called with every answer: a sentence, or the reason there is none. */
export function noteExplanation(reason: ExplanationReason | null | undefined): void {
  if (!reason) {
    failures = 0; // a sentence arrived, so the provider is answering
    return;
  }
  if (SETTLED.includes(reason)) {
    off = reason;
    return;
  }
  if (reason === "failed" && ++failures >= FAILURES_ALLOWED) off = reason;
  // "no_traits", "nothing_named" and "rejected" are about one film, not the session.
}

/** Tests, and a fresh sign-in: forget what this session learned. */
export function resetExplanations(): void {
  off = null;
  failures = 0;
}
