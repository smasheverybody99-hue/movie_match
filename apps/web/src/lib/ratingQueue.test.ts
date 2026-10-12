import { beforeEach, describe, expect, it } from "vitest";

import { RatingQueue, type UnsavedRating } from "./ratingQueue";
import type { RatingIn } from "./types";

/** A sender the test answers by hand, request by request. */
function sender() {
  const calls: { body: RatingIn; ok: () => void; fail: () => void }[] = [];
  const send = (body: RatingIn) =>
    new Promise<unknown>((resolve, reject) => {
      calls.push({ body, ok: () => resolve(undefined), fail: () => reject(new Error("offline")) });
    });
  return { calls, send };
}

const flush = () => new Promise((r) => setTimeout(r, 0));
const arrival = (score: number, aspects: string[] = []): UnsavedRating => ({
  movie_id: 329865,
  title: "Arrival",
  score,
  liked_aspects: aspects,
});

describe("RatingQueue", () => {
  beforeEach(() => localStorage.clear());

  it("keeps one entry per film: a new score replaces the older one", () => {
    const { send } = sender();
    const queue = new RatingQueue("u", send);
    queue.enqueue(arrival(9, ["mystery", "plot_twist"]));
    queue.enqueue(arrival(7));
    expect(queue.getState().unsaved).toEqual([arrival(7)]);
  });

  it("never lets an older score land after a newer one", async () => {
    const { calls, send } = sender();
    const queue = new RatingQueue("u", send);
    queue.enqueue(arrival(9, ["mystery"]));
    queue.enqueue(arrival(7)); // changed while the first is on its way
    expect(calls).toHaveLength(1); // one request per film at a time

    calls[0]!.ok();
    await flush();
    // the old one's success does not drop the newer score: that one goes next
    expect(queue.getState().unsaved).toEqual([arrival(7)]);
    expect(calls.map((c) => c.body.score)).toEqual([9, 7]);

    calls[1]!.ok();
    await flush();
    expect(queue.getState().unsaved).toEqual([]);
  });

  it("an older score that fails does not mark the newer one failed; the newer one is sent", async () => {
    const { calls, send } = sender();
    const queue = new RatingQueue("u", send);
    queue.enqueue(arrival(9));
    queue.enqueue(arrival(7));
    calls[0]!.fail();
    await flush();
    expect(queue.getState().failed).toEqual([]);
    expect(calls[1]!.body.score).toBe(7);
  });

  it("names what failed and sends it again on flush", async () => {
    const { calls, send } = sender();
    const queue = new RatingQueue("u", send);
    queue.enqueue(arrival(9, ["mystery"]));
    calls[0]!.fail();
    await flush();
    expect(queue.getState().failed).toEqual([arrival(9, ["mystery"])]);

    queue.flush();
    expect(queue.getState().failed).toEqual([]);
    expect(calls[1]!.body).toEqual({ movie_id: 329865, score: 9, liked_aspects: ["mystery"] });
  });

  it("survives a reload, per user", () => {
    new RatingQueue("u", sender().send).enqueue(arrival(9));
    expect(new RatingQueue("u", sender().send).getState().unsaved).toEqual([arrival(9)]);
    expect(new RatingQueue("someone else", sender().send).getState().unsaved).toEqual([]);
  });
});
