// The rating queue (web: lib/ratingQueue.test.ts): one score per film, the newest wins,
// one request per film at a time, kept on the phone until the server confirms it.
import 'dart:async';
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:movie_match/data/local_store.dart';
import 'package:movie_match/data/models.dart';
import 'package:movie_match/data/rating_queue.dart';

UnsavedRating score(int id, double value) =>
    UnsavedRating(movieId: id, title: 'Film $id', score: value);

void main() {
  test('a saved score leaves the queue and is counted as saved', () async {
    final sent = <double>[];
    final store = MemoryLocalStore();
    final queue = RatingQueue(userId: 'u1', store: store, send: (b) async => sent.add(b.score));
    queue.enqueue(score(1, 8));
    expect(queue.unsaved, hasLength(1));
    await Future<void>.delayed(Duration.zero);
    expect(sent, [8]);
    expect(queue.unsaved, isEmpty);
    expect(queue.saved, {1});
    expect(jsonDecode(store.values['mm.ratingQueue.v1.u1']!), isEmpty);
  });

  test('a newer score sent while the older one is in flight goes out after it, and wins',
      () async {
    final calls = <Completer<void>>[];
    final sent = <double>[];
    final queue = RatingQueue(
      userId: 'u1',
      store: MemoryLocalStore(),
      send: (b) {
        sent.add(b.score);
        final c = Completer<void>();
        calls.add(c);
        return c.future;
      },
    );
    queue.enqueue(score(1, 5));
    queue.enqueue(score(1, 9));
    expect(sent, [5], reason: 'one request per film at a time');
    calls[0].complete();
    await Future<void>.delayed(Duration.zero);
    expect(sent, [5, 9]);
    expect(queue.unsaved.single.score, 9);
    calls[1].complete();
    await Future<void>.delayed(Duration.zero);
    expect(queue.unsaved, isEmpty);
  });

  test('a failure stays queued and is listed as failed; flush sends it again', () async {
    var fail = true;
    final queue = RatingQueue(
      userId: 'u1',
      store: MemoryLocalStore(),
      send: (b) async {
        if (fail) throw StateError('offline');
        return null;
      },
    );
    queue.enqueue(score(2, 6));
    await Future<void>.delayed(Duration.zero);
    expect(queue.failed.single.movieId, 2);
    fail = false;
    queue.flush();
    expect(queue.failed, isEmpty);
    await Future<void>.delayed(Duration.zero);
    expect(queue.unsaved, isEmpty);
  });

  test('what an earlier run left is loaded, per user, and broken storage is ignored', () {
    final store = MemoryLocalStore()
      ..values['mm.ratingQueue.v1.u1'] = jsonEncode([
        {'movie_id': 3, 'title': 'Three', 'score': 7.5, 'liked_aspects': ['humor'], 'seq': 4},
        {'nonsense': true},
      ])
      ..values['mm.ratingQueue.v1.u2'] = 'not json';
    Future<Object?> never(RatingIn _) => Completer<Object?>().future;
    final mine = RatingQueue(userId: 'u1', store: store, send: never);
    expect(mine.unsaved.single.likedAspects, ['humor']);
    expect(RatingQueue(userId: 'u2', store: store, send: never).unsaved, isEmpty);
  });
}
