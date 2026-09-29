import type { Movie } from "./types";

/**
 * Onboarding progress that survives a reload (FR-3: "a user who leaves mid-way resumes
 * where they were"). Ratings themselves are saved on the server as they are given;
 * this keeps only what the server does not know: the picks, the step, the position.
 * Kept per user, so two accounts in one browser do not share a half-done onboarding.
 */
export type OnboardingStep = "pick" | "rate" | "done";

export interface OnboardingProgress {
  step: OnboardingStep;
  /** Films picked but not rated yet, in pick order. */
  picks: Movie[];
  /** The film being rated: an index into `picks`. */
  index: number;
  /** Which page of onboarding films is showing ("none of these" moves it on). */
  offset: number;
}

export const EMPTY_PROGRESS: OnboardingProgress = { step: "pick", picks: [], index: 0, offset: 0 };

const VERSION = 1;

function storageKey(userId: string): string {
  return `mm.onboarding.v${VERSION}.${userId}`;
}

function isProgress(value: unknown): value is OnboardingProgress {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    (v.step === "pick" || v.step === "rate" || v.step === "done") &&
    Array.isArray(v.picks) &&
    typeof v.index === "number" &&
    typeof v.offset === "number"
  );
}

export function loadProgress(userId: string): OnboardingProgress {
  try {
    const raw = localStorage.getItem(storageKey(userId));
    if (!raw) return EMPTY_PROGRESS;
    const parsed: unknown = JSON.parse(raw);
    return isProgress(parsed) ? parsed : EMPTY_PROGRESS;
  } catch {
    return EMPTY_PROGRESS;
  }
}

export function saveProgress(userId: string, progress: OnboardingProgress): void {
  try {
    localStorage.setItem(storageKey(userId), JSON.stringify(progress));
  } catch {
    // Storage full or blocked: onboarding still works, it just won't resume.
  }
}

export function clearProgress(userId: string): void {
  try {
    localStorage.removeItem(storageKey(userId));
  } catch {
    // Nothing to clear.
  }
}
