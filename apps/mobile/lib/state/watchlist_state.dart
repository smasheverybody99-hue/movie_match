/// The watchlist as the cards and the hero see it: which films are saved, and Save / Saved
/// changing at once (web: useWatchlist and the optimistic useWatchlistChange in
/// lib/queries.ts). A change the server refuses rolls back and the caller says so.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/api_client.dart';
import '../data/models.dart';
import 'app_state.dart';

/// GET /watchlist for the signed-in user.
final watchlistProvider = FutureProvider<List<WatchlistItem>>((ref) async {
  if (ref.watch(userIdProvider) == null) throw const ApiException(401, 'signed out');
  return ref.watch(apiClientProvider).watchlist();
});

/// Changes on their way to the server: film -> saved after the change.
class PendingSaves extends Notifier<Map<int, bool>> {
  @override
  Map<int, bool> build() {
    ref.watch(userIdProvider);
    return const {};
  }

  /// Saves or unsaves `movie` at once; false when the server refused (it is rolled back).
  Future<bool> toggle(Movie movie, {required bool isSaved}) async {
    final id = movie.id;
    state = {...state, id: !isSaved};
    final api = ref.read(apiClientProvider);
    var ok = true;
    try {
      if (isSaved) {
        await api.removeFromWatchlist(id);
      } else {
        await api.addToWatchlist(id);
      }
      ref.invalidate(watchlistProvider);
      // Hold the new state until the list has it, so the button does not flicker back.
      await ref.read(watchlistProvider.future).then<void>((_) {}, onError: (Object _) {});
    } on Object {
      ok = false;
    }
    if (ref.mounted) state = {...state}..remove(id);
    return ok;
  }
}

final pendingSavesProvider = NotifierProvider<PendingSaves, Map<int, bool>>(PendingSaves.new);

/// The films that are saved, pending changes included.
final savedIdsProvider = Provider<Set<int>>((ref) {
  final listed = <int>{
    for (final item in ref.watch(watchlistProvider).value ?? const <WatchlistItem>[]) item.movie.id,
  };
  for (final MapEntry(:key, :value) in ref.watch(pendingSavesProvider).entries) {
    value ? listed.add(key) : listed.remove(key);
  }
  return listed;
});
