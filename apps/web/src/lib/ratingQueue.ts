import type { RatingIn } from "./types";

/** A score given but not yet confirmed by the server, with the title to name it by. */
export interface UnsavedRating extends RatingIn {
  title: string;
}

interface Queued extends UnsavedRating {
  /** Which version of this film's score: a newer one replaces an older one. */
  seq: number;
}

export interface QueueState {
  /** Every score the server has not confirmed, one per film. */
  unsaved: readonly UnsavedRating[];
  /** Those whose last attempt failed and that wait for Try again or the connection. */
  failed: readonly UnsavedRating[];
}

const VERSION = 1;
const key = (userId: string) => `mm.ratingQueue.v${VERSION}.${userId}`;

function isQueued(value: unknown): value is Queued {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return typeof v.movie_id === "number" && typeof v.score === "number" && typeof v.seq === "number";
}

function load(userId: string): Queued[] {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(key(userId)) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter(isQueued) : [];
  } catch {
    return [];
  }
}

/**
 * Scores on their way to the server, kept per user in localStorage until it confirms them,
 * so a slow or failed save, a reload or leaving onboarding loses nothing (tester 1,
 * 2026-10-12). One entry per film: a newer score replaces the older one. One request per
 * film at a time, so an older score can never land after a newer one; whatever is newest
 * when a request returns is what goes next.
 */
export class RatingQueue {
  private entries: Queued[];
  private readonly inFlight = new Map<number, number>(); // film -> seq being sent
  private readonly failedIds = new Set<number>();
  private readonly listeners = new Set<() => void>();
  private seq = 0;
  private state: QueueState = { unsaved: [], failed: [] };

  constructor(
    private readonly userId: string,
    private readonly sendFn: (body: RatingIn) => Promise<unknown>,
  ) {
    this.entries = load(userId);
    this.seq = Math.max(0, ...this.entries.map((e) => e.seq));
    this.refresh();
  }

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getState = (): QueueState => this.state;

  /** Queues this film's score (replacing an older one) and sends it when it can. */
  enqueue(rating: UnsavedRating): void {
    const entry: Queued = { ...rating, seq: ++this.seq };
    this.entries = [...this.entries.filter((e) => e.movie_id !== rating.movie_id), entry];
    this.failedIds.delete(rating.movie_id);
    this.changed();
    this.sendLatest(rating.movie_id);
  }

  /** Sends every score not on its way already (start, Try again, back online). */
  flush(): void {
    this.failedIds.clear();
    this.changed();
    for (const e of this.entries) this.sendLatest(e.movie_id);
  }

  private sendLatest(movieId: number): void {
    if (this.inFlight.has(movieId)) return; // goes out when the current request returns
    const entry = this.entries.find((e) => e.movie_id === movieId);
    if (!entry) return;
    this.inFlight.set(movieId, entry.seq);
    const { title: _title, seq: _seq, ...body } = entry;
    this.sendFn(body).then(
      () => this.settled(entry, true),
      () => this.settled(entry, false),
    );
  }

  private settled(sent: Queued, ok: boolean): void {
    this.inFlight.delete(sent.movie_id);
    const latest = this.entries.find((e) => e.movie_id === sent.movie_id);
    if (latest && latest.seq !== sent.seq) {
      // a newer score came in meanwhile: that one is what the server must end with
      this.sendLatest(sent.movie_id);
      return;
    }
    if (ok) this.entries = this.entries.filter((e) => e.movie_id !== sent.movie_id);
    else this.failedIds.add(sent.movie_id);
    this.changed();
  }

  private changed(): void {
    try {
      localStorage.setItem(key(this.userId), JSON.stringify(this.entries));
    } catch {
      // storage full or blocked: the queue still works for this visit
    }
    this.refresh();
    for (const listener of this.listeners) listener();
  }

  private refresh(): void {
    const strip = ({ seq: _seq, ...rest }: Queued): UnsavedRating => rest;
    this.state = {
      unsaved: this.entries.map(strip),
      failed: this.entries.filter((e) => this.failedIds.has(e.movie_id)).map(strip),
    };
  }
}

const queues = new Map<string, RatingQueue>();
// The newest mounted useRate (lib/useRatingQueue.ts): a queue outlives the screen that created
// it (onboarding hands over to the app shell), so it sends through whichever hook is current.
let sender: ((body: RatingIn) => Promise<unknown>) | null = null;

export function setSender(send: (body: RatingIn) => Promise<unknown>): void {
  sender = send;
}

/** The one queue per user for the whole app. */
export function queueFor(userId: string): RatingQueue {
  let queue = queues.get(userId);
  if (!queue) {
    queue = new RatingQueue(userId, (body) => (sender ? sender(body) : Promise.reject(new Error("no sender"))));
    queues.set(userId, queue);
  }
  return queue;
}

/** Tests only: forget the queues and the sender kept between renders. */
export function resetRatingQueues(): void {
  queues.clear();
  sender = null;
}
