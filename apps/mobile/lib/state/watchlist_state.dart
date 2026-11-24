/// The watchlist as every screen sees it: the server's list with the changes on their way
/// applied, so Save, Watched and Remove show at once (web: useWatchlist and the optimistic
/// useWatchlistChange in lib/queries.ts). A change the server refuses rolls back and the
/// caller says so.
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

/// A change on its way to the server.
sealed class WatchlistEdit {
  const WatchlistEdit();
}

class AddEdit extends WatchlistEdit {
  const AddEdit(this.movie, this.at);
  final Movie movie;
  final DateTime at;
}

class RemoveEdit extends WatchlistEdit {
  const RemoveEdit();
}

class WatchedEdit extends WatchlistEdit {
  const WatchedEdit(this.at);
  final DateTime at;
}

/// `list` with `edits` applied (web: applyChange).
List<WatchlistItem> applyEdits(List<WatchlistItem> list, Map<int, WatchlistEdit> edits) {
  final out = <WatchlistItem>[
    for (final MapEntry(key: id, value: edit) in edits.entries)
      if (edit is AddEdit && !list.any((i) => i.movie.id == id))
        WatchlistItem(movie: edit.movie, addedAt: edit.at),
  ];
  for (final item in list) {
    switch (edits[item.movie.id]) {
      case RemoveEdit():
        continue;
      case WatchedEdit(:final at) when item.watchedAt == null:
        out.add(WatchlistItem(
          movie: item.movie,
          addedAt: item.addedAt,
          watchedAt: at,
          match: item.match,
          band: item.band,
        ));
      default:
        out.add(item);
    }
  }
  return out;
}

/// Changes on their way to the server, one per film.
class WatchlistEdits extends Notifier<Map<int, WatchlistEdit>> {
  @override
  Map<int, WatchlistEdit> build() {
    ref.watch(userIdProvider);
    return const {};
  }

  /// Saves or unsaves `movie`; false when the server refused (it is rolled back).
  Future<bool> toggle(Movie movie, {required bool isSaved}) {
    final api = ref.read(apiClientProvider);
    return isSaved
        ? _run(movie.id, const RemoveEdit(), () => api.removeFromWatchlist(movie.id))
        : _run(movie.id, AddEdit(movie, DateTime.now()), () => api.addToWatchlist(movie.id));
  }

  Future<bool> markWatched(int movieId) {
    final api = ref.read(apiClientProvider);
    return _run(movieId, WatchedEdit(DateTime.now()), () => api.markWatched(movieId));
  }

  Future<bool> remove(int movieId) {
    final api = ref.read(apiClientProvider);
    return _run(movieId, const RemoveEdit(), () => api.removeFromWatchlist(movieId));
  }

  Future<bool> _run(int id, WatchlistEdit edit, Future<Object?> Function() send) async {
    state = {...state, id: edit};
    var ok = true;
    try {
      await send();
      ref.invalidate(watchlistProvider);
      // Hold the change until the list has it, so the screen does not flicker back.
      await ref.read(watchlistProvider.future).then<void>((_) {}, onError: (Object _) {});
    } on Object {
      ok = false;
    }
    if (ref.mounted && identical(state[id], edit)) state = {...state}..remove(id);
    return ok;
  }
}

final watchlistEditsProvider =
    NotifierProvider<WatchlistEdits, Map<int, WatchlistEdit>>(WatchlistEdits.new);

/// The watchlist with the pending changes applied; loading and errors as the server's.
final watchlistViewProvider = Provider<AsyncValue<List<WatchlistItem>>>((ref) {
  final edits = ref.watch(watchlistEditsProvider);
  return ref.watch(watchlistProvider).whenData((list) => applyEdits(list, edits));
});

/// The films that are saved, pending changes included.
final savedIdsProvider = Provider<Set<int>>((ref) {
  final edits = ref.watch(watchlistEditsProvider);
  final listed = <int>{
    for (final item in ref.watch(watchlistProvider).value ?? const <WatchlistItem>[])
      item.movie.id,
  };
  for (final MapEntry(key: id, value: edit) in edits.entries) {
    edit is RemoveEdit ? listed.remove(id) : listed.add(id);
  }
  return listed;
});
