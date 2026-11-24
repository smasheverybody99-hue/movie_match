/// What the viewer saw, for the closed alpha's metrics (Phase 5). Mirrors
/// apps/web/src/lib/telemetry.ts: a recommendation shown or clicked, an onboarding step;
/// the server records everything it handles itself (ratings, the watchlist, assistant
/// messages, onboarding finished).
///
/// Events wait in a queue and go out together: every 10 s, at 20 waiting, and when the app
/// goes to the background. A batch that fails to arrive goes back to the front of the queue
/// for the next try; one the API refuses as malformed (422) is a bug here and is dropped
/// rather than sent forever. One instance per signed-in user (state/app_state.dart), so a
/// different account starts afresh. No event carries text the viewer typed.
library;

import 'dart:async';

import 'package:flutter/foundation.dart';

import 'api_client.dart';
import 'models.dart';

const flushEvery = Duration(seconds: 10);
const flushAt = 20;
const _maxBatch = 50; // the API's limit
const _maxQueue = 200; // offline for long: keep the newest

class Telemetry {
  Telemetry(this._send);

  final Future<int> Function(List<ClientEvent> events) _send;
  var _queue = <ClientEvent>[];
  Timer? _timer;
  bool _sending = false;
  bool _closed = false;

  /// Shown and onboarding steps count once per app run; clicks every time.
  final _once = <String>{};

  @visibleForTesting
  List<ClientEvent> get queued => List.unmodifiable(_queue);

  void track(ClientEvent event) {
    if (_closed) return;
    final key = switch (event) {
      OnboardingStepEvent(:final step) => 'step:${step.name}',
      RecommendationEvent(clicked: false, :final source, :final movieId) =>
        'shown:${source.wire}:$movieId',
      RecommendationEvent() => null,
    };
    if (key != null && !_once.add(key)) return;
    _queue.add(event);
    if (_queue.length > _maxQueue) _queue = _queue.sublist(_queue.length - _maxQueue);
    if (_queue.length >= flushAt) {
      flush();
    } else {
      _schedule();
    }
  }

  void _schedule() => _timer ??= Timer(flushEvery, flush);

  /// Send what is waiting, one batch at a time.
  Future<void> flush() async {
    _timer?.cancel();
    _timer = null;
    if (_closed || _sending || _queue.isEmpty) return;
    final batch = _queue.take(_maxBatch).toList();
    _queue = _queue.sublist(batch.length);
    _sending = true;
    try {
      await _send(batch);
    } on ApiException catch (e) {
      if (e.status != 422) _requeue(batch);
    } on Object {
      _requeue(batch);
    } finally {
      _sending = false;
    }
    if (_queue.isNotEmpty) _schedule();
  }

  void _requeue(List<ClientEvent> batch) {
    final all = [...batch, ..._queue];
    _queue = all.length > _maxQueue ? all.sublist(all.length - _maxQueue) : all;
  }

  void close() {
    _closed = true;
    _timer?.cancel();
    _timer = null;
  }
}
