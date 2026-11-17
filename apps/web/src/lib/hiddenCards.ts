import { useSyncExternalStore } from "react";

/**
 * Cards taken out of view after "Not right?" (Phase 5). Only for this page load: the
 * press is data for the alpha, not a ranking input, so the next load of the feed shows
 * what the engine picks, the film included (user decision, 2026-11-17; TZ 1.31).
 *
 * Also the one notice the pages show about it: thanks, or that the press did not arrive
 * (the card is back then).
 */
export type WrongNotice = { kind: "thanks" | "error"; title: string } | null;

interface State {
  hidden: ReadonlySet<number>;
  notice: WrongNotice;
}

let state: State = { hidden: new Set(), notice: null };
const listeners = new Set<() => void>();

function set(next: State): void {
  state = next;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function hideCard(movieId: number, title: string): void {
  set({ hidden: new Set([...state.hidden, movieId]), notice: { kind: "thanks", title } });
}

/** The press did not arrive: the card comes back, and the page says so. */
export function restoreCard(movieId: number, title: string): void {
  const hidden = new Set(state.hidden);
  hidden.delete(movieId);
  set({ hidden, notice: { kind: "error", title } });
}

export function clearWrongNotice(): void {
  if (state.notice !== null) set({ ...state, notice: null });
}

export function useHiddenCards(): State {
  return useSyncExternalStore(subscribe, () => state);
}

/** Tests: start clean. */
export function resetHiddenCards(): void {
  set({ hidden: new Set(), notice: null });
}
