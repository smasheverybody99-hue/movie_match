import { useEffect, useMemo, useSyncExternalStore } from "react";

import { useRate } from "./queries";
import { queueFor, setSender, type QueueState, type UnsavedRating } from "./ratingQueue";

/**
 * The user's rating queue (lib/ratingQueue.ts), one per user for the whole app, so
 * onboarding and the app shell see the same scores. Requests go through useRate (the
 * optimistic ratings list and the refetches it triggers). Leftovers from an earlier visit
 * go out on mount, failed ones again when the connection comes back.
 */
export function useRatingQueue(userId: string): QueueState & {
  enqueue: (rating: UnsavedRating) => void;
  retry: () => void;
} {
  const { mutateAsync } = useRate();
  setSender(mutateAsync);
  const queue = useMemo(() => queueFor(userId), [userId]);
  const state = useSyncExternalStore(queue.subscribe, queue.getState);

  useEffect(() => {
    queue.flush();
    const online = () => queue.flush();
    window.addEventListener("online", online);
    return () => window.removeEventListener("online", online);
  }, [queue]);

  return useMemo(
    () => ({ ...state, enqueue: (r: UnsavedRating) => queue.enqueue(r), retry: () => queue.flush() }),
    [state, queue],
  );
}
