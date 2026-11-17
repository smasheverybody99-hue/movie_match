import { useEffect, useRef } from "react";

import { ApiError, api, hasAccessToken } from "./api";
import type { ClientEvent, EventSource, OnboardingStep } from "./types";

/**
 * What the viewer saw, for the closed alpha's metrics (Phase 5): a recommendation shown
 * or clicked, an onboarding step. The server records everything it handles itself
 * (ratings, the watchlist, assistant messages, onboarding finished), so only these three
 * come from here.
 *
 * Events wait in a queue and go out together: every 10 s, at 20 waiting, and when the
 * page is hidden or closed (`keepalive`, so the request outlives the page). A batch that
 * fails to arrive goes back to the front of the queue for the next try; one the API
 * refuses as malformed (422) is a bug here and is dropped, with a warning, rather than
 * sent forever. Nothing goes out signed out, and a different account starts afresh.
 *
 * No event carries text the viewer typed (app/services/events.py).
 */
export const FLUSH_EVERY_MS = 10_000;
export const FLUSH_AT = 20;
const MAX_BATCH = 50; // the API's limit
const MAX_QUEUE = 200; // offline for long: keep the newest
/** "Shown" means at least half the card in view for a second (user decision, 2026-11-17). */
export const SHOWN_RATIO = 0.5;
export const SHOWN_AFTER_MS = 1000;

type Tracked =
  | { type: "recommendation_shown" | "recommendation_clicked"; movie_id: number; source: EventSource }
  | { type: "onboarding_step"; step: OnboardingStep };

let queue: ClientEvent[] = [];
let timer: ReturnType<typeof setTimeout> | undefined;
let sending = false;
/** Shown and onboarding steps count once per page load; clicks every time. */
const once = new Set<string>();

function onceKey(event: Tracked): string | null {
  if (event.type === "recommendation_shown") return `shown:${event.source}:${event.movie_id}`;
  if (event.type === "onboarding_step") return `step:${event.step}`;
  return null;
}

function schedule(): void {
  if (timer === undefined) timer = setTimeout(() => void flush(), FLUSH_EVERY_MS);
}

export function track(event: Tracked): void {
  const key = onceKey(event);
  if (key !== null) {
    if (once.has(key)) return;
    once.add(key);
  }
  queue.push({ ...event, at: new Date().toISOString() } as ClientEvent);
  if (queue.length > MAX_QUEUE) queue = queue.slice(-MAX_QUEUE);
  if (queue.length >= FLUSH_AT) void flush();
  else schedule();
}

/** Send what is waiting, one batch at a time. */
export async function flush({ keepalive = false }: { keepalive?: boolean } = {}): Promise<void> {
  clearTimeout(timer);
  timer = undefined;
  if (sending || queue.length === 0) return;
  if (!hasAccessToken()) {
    schedule();
    return;
  }
  const batch = queue.splice(0, MAX_BATCH);
  sending = true;
  try {
    await Promise.resolve(api.sendEvents(batch, keepalive));
  } catch (error) {
    if (error instanceof ApiError && error.status === 422) {
      console.warn("telemetry: the API refused a batch", error.message);
    } else {
      queue = [...batch, ...queue].slice(-MAX_QUEUE);
    }
  } finally {
    sending = false;
  }
  if (queue.length > 0) schedule();
}

/** Hidden or closed: send now, with keepalive. Returns the clean-up. */
export function startTelemetry(): () => void {
  const onHide = () => {
    if (document.visibilityState === "hidden") void flush({ keepalive: true });
  };
  const onPageHide = () => void flush({ keepalive: true });
  document.addEventListener("visibilitychange", onHide);
  window.addEventListener("pagehide", onPageHide);
  return () => {
    document.removeEventListener("visibilitychange", onHide);
    window.removeEventListener("pagehide", onPageHide);
  };
}

/** A new account, and tests: what was queued belonged to someone else. */
export function resetTelemetry(): void {
  queue = [];
  once.clear();
  clearTimeout(timer);
  timer = undefined;
  sending = false;
}

/** For tests: what is waiting. */
export function queued(): readonly ClientEvent[] {
  return queue;
}

/**
 * A ref for a recommendation card: `recommendation_shown` once at least half of it has
 * been in view for a second. Without IntersectionObserver (old browsers, tests) nothing
 * is recorded rather than everything.
 */
export function useShownRef<T extends Element>(movieId: number, source: EventSource) {
  const ref = useRef<T | null>(null);
  useEffect(() => {
    const element = ref.current;
    if (!element || typeof IntersectionObserver !== "function") return;
    let wait: ReturnType<typeof setTimeout> | undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[entries.length - 1];
        if (entry && entry.isIntersecting && entry.intersectionRatio >= SHOWN_RATIO) {
          wait ??= setTimeout(() => {
            track({ type: "recommendation_shown", movie_id: movieId, source });
            observer.disconnect();
          }, SHOWN_AFTER_MS);
        } else {
          clearTimeout(wait);
          wait = undefined;
        }
      },
      { threshold: [0, SHOWN_RATIO] },
    );
    observer.observe(element);
    return () => {
      observer.disconnect();
      clearTimeout(wait);
    };
  }, [movieId, source]);
  return ref;
}
