/// Scores on their way to the server. Mirrors apps/web/src/lib/ratingQueue.ts, under the
/// same storage key: kept per user on the phone until the server confirms them, so a slow
/// or failed save, an app restart or leaving onboarding loses nothing (tester 1,
/// 2026-10-12). One entry per film: a newer score replaces the older one. One request per
/// film at a time, so an older score can never land after a newer one; whatever is newest
/// when a request returns is what goes next.
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'local_store.dart';
import 'models.dart';

/// A score given but not yet confirmed by the server, with the title to name it by.
class UnsavedRating {
  const UnsavedRating({
    required this.movieId,
    required this.title,
    required this.score,
    this.likedAspects = const [],
  });

  final int movieId;
  final String title;
  final double score;
  final List<String> likedAspects;

  RatingIn get body => RatingIn(movieId: movieId, score: score, likedAspects: likedAspects);
}

class _Queued {
  const _Queued(this.rating, this.seq);

  final UnsavedRating rating;

  /// Which version of this film's score: a newer one replaces an older one.
  final int seq;

  Json toJson() => {
        'movie_id': rating.movieId,
        'title': rating.title,
        'score': rating.score,
        'liked_aspects': rating.likedAspects,
        'seq': seq,
      };

  static _Queued? fromJson(Object? value) {
    if (value is! Map<String, dynamic>) return null;
    final id = value['movie_id'];
    final score = value['score'];
    final seq = value['seq'];
    if (id is! int || score is! num || seq is! int) return null;
    final aspects = value['liked_aspects'];
    final title = value['title'];
    return _Queued(
      UnsavedRating(
        movieId: id,
        title: title is String ? title : '',
        score: score.toDouble(),
        likedAspects: aspects is List ? aspects.whereType<String>().toList() : const [],
      ),
      seq,
    );
  }
}

class RatingQueue extends ChangeNotifier {
  RatingQueue({required this.userId, required this.store, required this.send}) {
    _entries = _load();
    for (final e in _entries) {
      if (e.seq > _seq) _seq = e.seq;
    }
  }

  final String userId;
  final LocalStore store;
  final Future<Object?> Function(RatingIn body) send;

  late List<_Queued> _entries;
  final _inFlight = <int, int>{}; // film -> seq being sent
  final _failedIds = <int>{};
  final _saved = <int>{};
  int _seq = 0;
  bool _disposed = false;

  String get _key => 'mm.ratingQueue.v1.$userId';

  List<_Queued> _load() {
    try {
      final parsed = jsonDecode(store.read(_key) ?? '[]');
      if (parsed is! List) return [];
      return [for (final e in parsed) ?_Queued.fromJson(e)];
    } on FormatException {
      return [];
    }
  }

  /// Every score the server has not confirmed, one per film.
  List<UnsavedRating> get unsaved => [for (final e in _entries) e.rating];

  /// Those whose last attempt failed and that wait for Try again.
  List<UnsavedRating> get failed =>
      [for (final e in _entries) if (_failedIds.contains(e.rating.movieId)) e.rating];

  /// Films the server confirmed since the app started.
  Set<int> get saved => Set.unmodifiable(_saved);

  /// Queues this film's score (replacing an older one) and sends it when it can.
  void enqueue(UnsavedRating rating) {
    _entries = [
      for (final e in _entries)
        if (e.rating.movieId != rating.movieId) e,
      _Queued(rating, ++_seq),
    ];
    _failedIds.remove(rating.movieId);
    _saved.remove(rating.movieId);
    _changed();
    _sendLatest(rating.movieId);
  }

  /// Sends every score not on its way already (start, Try again, back in the app).
  void flush() {
    _failedIds.clear();
    _changed();
    for (final e in [..._entries]) {
      _sendLatest(e.rating.movieId);
    }
  }

  void _sendLatest(int movieId) {
    if (_inFlight.containsKey(movieId)) return; // goes out when the current request returns
    final entry = _entries.where((e) => e.rating.movieId == movieId).firstOrNull;
    if (entry == null) return;
    _inFlight[movieId] = entry.seq;
    send(entry.rating.body).then(
      (_) => _settled(entry, ok: true),
      onError: (Object _) => _settled(entry, ok: false),
    );
  }

  void _settled(_Queued sent, {required bool ok}) {
    if (_disposed) return;
    final id = sent.rating.movieId;
    _inFlight.remove(id);
    final latest = _entries.where((e) => e.rating.movieId == id).firstOrNull;
    if (latest != null && latest.seq != sent.seq) {
      // a newer score came in meanwhile: that one is what the server must end with
      _sendLatest(id);
      return;
    }
    if (ok) {
      _entries = [for (final e in _entries) if (e.rating.movieId != id) e];
      _saved.add(id);
    } else {
      _failedIds.add(id);
    }
    _changed();
  }

  void _changed() {
    if (_disposed) return;
    // Storage full or blocked: the queue still works while the app runs.
    store.write(_key, jsonEncode([for (final e in _entries) e.toJson()])).ignore();
    notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
