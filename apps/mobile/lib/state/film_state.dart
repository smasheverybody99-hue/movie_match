/// What the film page reads and changes: the film, the user's taste, the "why you"
/// sentence and the user's own score. Mirrors useMovie, useDna, useExplanation and the
/// optimistic useRate in apps/web/src/lib/queries.ts, and lib/explanations.ts.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/api_client.dart';
import '../data/models.dart';
import 'app_state.dart';
import 'watchlist_state.dart';

/// GET /movies/{id}, for the signed-in user (the match and its reasons are the caller's).
final movieProvider = FutureProvider.autoDispose.family<MovieDetail, int>((ref, id) async {
  if (ref.watch(userIdProvider) == null) throw const ApiException(401, 'signed out');
  return ref.watch(apiClientProvider).getMovie(id);
});

/// GET /me/dna: the taste the film page draws as "you" on each axis.
final dnaProvider = FutureProvider<MovieDna>((ref) async {
  if (ref.watch(userIdProvider) == null) throw const ApiException(401, 'signed out');
  return ref.watch(apiClientProvider).dna();
});

/// Whether asking for another "why you" sentence is still worth it in this run of the app.
/// Three reasons will not change meanwhile (nothing can generate, today's allowance is used
/// up, no taste profile yet): after one of them the page stops asking and stops showing
/// "Writing the explanation…", which otherwise promises a sentence that never comes (tester,
/// 2026-10-13). One `failed` is bad luck; two in a row is the provider down.
class ExplanationGate extends Notifier<ExplanationReason?> {
  static const _settled = {
    ExplanationReason.noGenerator,
    ExplanationReason.dailyCap,
    ExplanationReason.noTaste,
  };
  static const _failuresAllowed = 2;
  int _failures = 0;

  @override
  ExplanationReason? build() {
    ref.watch(userIdProvider);
    _failures = 0;
    return null;
  }

  /// Called with every answer: null for a sentence, else why there is none.
  void note(ExplanationReason? reason) {
    if (reason == null) {
      _failures = 0; // a sentence arrived, so the provider is answering
    } else if (_settled.contains(reason)) {
      state = reason;
    } else if (reason == ExplanationReason.failed && ++_failures >= _failuresAllowed) {
      state = reason;
    }
    // no_traits, nothing_named and rejected are about one film, not the session.
  }
}

final explanationGateProvider =
    NotifierProvider<ExplanationGate, ExplanationReason?>(ExplanationGate.new);

/// GET /recommendations/{id}/explanation in the interface language. Kept for the app run
/// (web: staleTime Infinity), so a sentence is never paid for twice.
final explanationProvider = FutureProvider.family<Explanation, int>((ref, id) async {
  if (ref.watch(userIdProvider) == null) throw const ApiException(401, 'signed out');
  final answer = await ref.watch(apiClientProvider).explanation(id, ref.watch(langProvider));
  ref.read(explanationGateProvider.notifier).note(answer.reason);
  return answer;
});

/// Scores on their way: film -> the score shown meanwhile. The page shows it at once and
/// goes back to the previous score (not to none) if the server refuses it.
class PendingRatings extends Notifier<Map<int, double>> {
  @override
  Map<int, double> build() {
    ref.watch(userIdProvider);
    return const {};
  }

  /// Sends `body`; false when the server refused it (it is rolled back).
  Future<bool> rate(RatingIn body) async {
    final id = body.movieId;
    if (state.containsKey(id)) return true; // one at a time; the page ignores a second press
    state = {...state, id: body.score};
    var ok = true;
    try {
      await ref.read(apiClientProvider).rate(body);
      // A new score moves the taste: everything drawn from it is fetched again.
      ref.invalidate(meProvider);
      ref.invalidate(dnaProvider);
      ref.invalidate(watchlistProvider);
      ref.invalidate(recommendationsProvider);
      ref.invalidate(movieProvider(id));
      ref.invalidate(ratingsProvider);
      // Hold the new score until the list has it, so it does not flicker back.
      await ref.read(ratingsProvider.future).then<void>((_) {}, onError: (Object _) {});
    } on Object {
      ok = false;
    }
    if (ref.mounted) state = {...state}..remove(id);
    return ok;
  }
}

final pendingRatingsProvider =
    NotifierProvider<PendingRatings, Map<int, double>>(PendingRatings.new);

/// The user's score for a film, a pending one first; null when not rated.
final myScoreProvider = Provider.family<double?, int>((ref, id) {
  final pending = ref.watch(pendingRatingsProvider)[id];
  if (pending != null) return pending;
  for (final r in ref.watch(ratingsProvider).value ?? const <Rating>[]) {
    if (r.movieId == id) return r.score;
  }
  return null;
});
