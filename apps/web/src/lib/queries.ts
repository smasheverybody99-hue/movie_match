/**
 * Server state, all through TanStack Query (CLAUDE.md: no fetch calls in components).
 *
 * Rating and watchlist changes are optimistic (FR-4): the cache changes first, the
 * request follows, and a failure puts the previous cache back.
 */
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";

import { useI18n } from "../i18n";
import { api, type SearchParams } from "./api";
import type { Lang, Movie, Rating, RatingIn, WatchlistItem } from "./types";

export const keys = {
  me: ["me"] as const,
  dna: ["dna"] as const,
  ratings: ["ratings"] as const,
  watchlist: ["watchlist"] as const,
  recommendations: (lang: Lang) => ["recommendations", lang] as const,
  movie: (id: number) => ["movie", id] as const,
  explanation: (id: number, lang: Lang) => ["explanation", id, lang] as const,
  search: (params: SearchParams) => ["search", params] as const,
  onboarding: (offset: number) => ["onboarding", offset] as const,
};

export const ONBOARDING_PAGE = 60;

export function useMe() {
  return useQuery({ queryKey: keys.me, queryFn: api.me });
}

export function useDna() {
  return useQuery({ queryKey: keys.dna, queryFn: api.dna });
}

export function useRatings() {
  return useQuery({ queryKey: keys.ratings, queryFn: api.ratings });
}

export function useWatchlist() {
  return useQuery({ queryKey: keys.watchlist, queryFn: api.watchlist });
}

export function useRecommendations() {
  const { lang } = useI18n();
  return useQuery({ queryKey: keys.recommendations(lang), queryFn: () => api.recommendations(lang) });
}

export function useMovie(id: number) {
  return useQuery({ queryKey: keys.movie(id), queryFn: () => api.getMovie(id), enabled: id > 0 });
}

/**
 * "Why you'll like this". The API serves the cached sentence or makes one (capped per
 * user per day, cached for good), so it is asked for once per film and language and
 * never refetched in the background.
 */
export function useExplanation(id: number, enabled: boolean) {
  const { lang } = useI18n();
  return useQuery({
    queryKey: keys.explanation(id, lang),
    queryFn: () => api.explanation(id, lang),
    enabled,
    staleTime: Infinity,
    retry: false,
  });
}

export function useSearch(params: SearchParams) {
  return useQuery({
    queryKey: keys.search(params),
    queryFn: () => api.searchMovies(params),
    placeholderData: keepPreviousData,
  });
}

export function useOnboardingFilms(offset: number) {
  return useQuery({
    queryKey: keys.onboarding(offset),
    queryFn: () => api.onboardingFilms(ONBOARDING_PAGE, offset),
    staleTime: Infinity,
  });
}

/** Put back what `onMutate` replaced; with nothing cached before, drop the guess. */
function rollback<T>(client: QueryClient, key: readonly unknown[], previous: T | undefined) {
  if (previous === undefined) void client.resetQueries({ queryKey: key, exact: true });
  else client.setQueryData(key, previous);
}

/** Everything a rating can change: taste, DNA, matches, the feed. */
function invalidateTaste(client: QueryClient, movieId: number) {
  for (const key of [keys.me, keys.dna, keys.watchlist, ["recommendations"], keys.movie(movieId)]) {
    void client.invalidateQueries({ queryKey: key });
  }
}

export function useRate() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: RatingIn) => api.rate(body),
    onMutate: async (body) => {
      await client.cancelQueries({ queryKey: keys.ratings });
      const previous = client.getQueryData<Rating[]>(keys.ratings);
      const optimistic: Rating = {
        movie_id: body.movie_id,
        score: body.score,
        liked_aspects: body.liked_aspects ?? [],
        rated_at: new Date().toISOString(),
      };
      client.setQueryData<Rating[]>(keys.ratings, (list = []) => [
        optimistic,
        ...list.filter((r) => r.movie_id !== body.movie_id),
      ]);
      return { previous };
    },
    onError: (_error, _body, context) => rollback(client, keys.ratings, context?.previous),
    onSettled: (_data, _error, body) => {
      void client.invalidateQueries({ queryKey: keys.ratings });
      invalidateTaste(client, body.movie_id);
    },
  });
}

type WatchlistChange =
  | { kind: "add"; movie: Movie }
  | { kind: "remove"; movieId: number }
  | { kind: "watched"; movieId: number };

function applyChange(list: WatchlistItem[], change: WatchlistChange): WatchlistItem[] {
  switch (change.kind) {
    case "add":
      if (list.some((i) => i.movie.id === change.movie.id)) return list;
      return [
        { movie: change.movie, added_at: new Date().toISOString(), watched_at: null, match: null, band: null },
        ...list,
      ];
    case "remove":
      return list.filter((i) => i.movie.id !== change.movieId);
    case "watched":
      return list.map((i) =>
        i.movie.id === change.movieId && !i.watched_at
          ? { ...i, watched_at: new Date().toISOString() }
          : i,
      );
  }
}

function send(change: WatchlistChange): Promise<unknown> {
  switch (change.kind) {
    case "add":
      return api.addToWatchlist(change.movie.id);
    case "remove":
      return api.removeFromWatchlist(change.movieId);
    case "watched":
      return api.markWatched(change.movieId);
  }
}

export function useWatchlistChange() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: send,
    onMutate: async (change: WatchlistChange) => {
      await client.cancelQueries({ queryKey: keys.watchlist });
      const previous = client.getQueryData<WatchlistItem[]>(keys.watchlist);
      client.setQueryData<WatchlistItem[]>(keys.watchlist, (list = []) => applyChange(list, change));
      return { previous };
    },
    onError: (_error, _change, context) => rollback(client, keys.watchlist, context?.previous),
    onSettled: () => {
      void client.invalidateQueries({ queryKey: keys.watchlist });
    },
  });
}

export function useDeleteAccount() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.deleteAccount,
    onSuccess: () => client.clear(),
  });
}
