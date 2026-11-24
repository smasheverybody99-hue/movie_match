/// The assistant conversation (FR-8). Mirrors apps/web/src/lib/assistant.ts: the answer
/// streams in as events (data/api_client.dart assistantChat) and each one is applied to
/// the exchange it belongs to. The conversation is screen state: the API keeps the last
/// five turns as the model's context, and a screen that opens fresh starts a new
/// conversation there too.
///
/// The time limits are the server's (TZ 1.28: 25 s to the first words, 45 s in all): it
/// ends a slow answer with an `error` event whose reason is `timeout`, and the screen
/// says the assistant is busy. The client's own read timeout (30 s) sits above the first.
library;

import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../data/api_client.dart';
import '../data/models.dart';

/// What an answer shows, in the order the stream sent it: text runs and rows of cards.
sealed class AnswerPart {
  const AnswerPart();
}

class TextPart extends AnswerPart {
  const TextPart(this.text);
  final String text;
}

class CardsPart extends AnswerPart {
  const CardsPart(this.cards);
  final List<AssistantCard> cards;
}

enum ExchangeStatus { waiting, streaming, done, refused, failed, limit }

/// Why an answer failed: the stream's reasons, or no answer at all.
enum ExchangeError { failed, blocked, timeout }

@immutable
class Exchange {
  const Exchange({
    required this.id,
    required this.question,
    this.parts = const [],
    this.followups = const [],
    this.status = ExchangeStatus.waiting,
    this.refusal,
    this.error,
    this.limit,
  });

  final int id;
  final String question;
  final List<AnswerPart> parts;
  final List<String> followups;
  final ExchangeStatus status;
  final AssistantRefusalReason? refusal;
  final ExchangeError? error;

  /// The cap reached, and when it resets, on a `limit` exchange.
  final AssistantLimit? limit;

  Exchange copyWith({
    List<AnswerPart>? parts,
    List<String>? followups,
    ExchangeStatus? status,
    AssistantRefusalReason? refusal,
    ExchangeError? error,
    AssistantLimit? limit,
  }) =>
      Exchange(
        id: id,
        question: question,
        parts: parts ?? this.parts,
        followups: followups ?? this.followups,
        status: status ?? this.status,
        refusal: refusal ?? this.refusal,
        error: error ?? this.error,
        limit: limit ?? this.limit,
      );
}

/// One event applied to the answer it belongs to. Pure: the controller and the tests
/// share it (web: applyEvent).
Exchange applyEvent(Exchange e, AssistantEvent event) {
  switch (event) {
    case AssistantText(:final text):
      final last = e.parts.lastOrNull;
      final parts = last is TextPart
          ? [...e.parts.take(e.parts.length - 1), TextPart(last.text + text)]
          : [...e.parts, TextPart(text)];
      return e.copyWith(parts: parts, status: ExchangeStatus.streaming);
    case AssistantCardEvent(:final card):
      final last = e.parts.lastOrNull;
      // Cards that follow each other share a row; text in between starts a new one.
      final parts = last is CardsPart
          ? [...e.parts.take(e.parts.length - 1), CardsPart([...last.cards, card])]
          : [...e.parts, CardsPart([card])];
      return e.copyWith(parts: parts, status: ExchangeStatus.streaming);
    case AssistantFollowups(:final items):
      return e.copyWith(followups: items.take(3).toList());
    case AssistantRefusal(:final reason):
      // The interface's own fixed text replaces whatever came before the refusal.
      return e.copyWith(
          parts: const [], followups: const [], status: ExchangeStatus.refused, refusal: reason);
    case AssistantError(:final reason):
      return e.copyWith(
        status: ExchangeStatus.failed,
        error: switch (reason) {
          AssistantErrorReason.blocked => ExchangeError.blocked,
          AssistantErrorReason.timeout => ExchangeError.timeout,
          AssistantErrorReason.failed => ExchangeError.failed,
        },
      );
    case AssistantReset():
      // The server tries the call again; what came before that call is sent again.
      return e.copyWith(parts: const [], followups: const [], status: ExchangeStatus.waiting);
    case AssistantDone():
      return e.status == ExchangeStatus.refused ? e : e.copyWith(status: ExchangeStatus.done);
  }
}

/// How often the screen may open the connection to the API ahead of a message (web:
/// WARM_EVERY_MS): a new connection cost ~1 s more than a reused one.
const warmEvery = Duration(seconds: 30);

class AssistantChat extends ChangeNotifier {
  AssistantChat({required this.api, required this.lang, DateTime Function()? now})
      : _now = now ?? DateTime.now;

  final ApiClient api;
  final Lang lang;
  final DateTime Function() _now;

  final _exchanges = <Exchange>[];
  int _nextId = 1;
  bool _fresh = true; // the first message from this screen starts a new conversation
  bool _busy = false;
  CancelToken? _cancel;
  StreamSubscription<AssistantEvent>? _stream;
  DateTime? _warmedAt;
  bool _disposed = false;

  List<Exchange> get exchanges => List.unmodifiable(_exchanges);
  bool get busy => _busy;

  /// Set once today's cap is hit and until it resets: the screen stops offering to send.
  AssistantLimit? get limit {
    for (final e in _exchanges.reversed) {
      final l = e.limit;
      if (e.status == ExchangeStatus.limit && l != null) {
        return l.resetsAt.isAfter(_now()) ? l : null;
      }
    }
    return null;
  }

  /// The last question, when its answer failed: Try again sends it again.
  String? get retryable {
    final last = _exchanges.lastOrNull;
    return last != null && last.status == ExchangeStatus.failed ? last.question : null;
  }

  void _update(int id, Exchange Function(Exchange) change) {
    if (_disposed) return;
    final i = _exchanges.indexWhere((e) => e.id == id);
    if (i == -1) return;
    _exchanges[i] = change(_exchanges[i]);
    notifyListeners();
  }

  void ask(String text) {
    final message = text.trim();
    if (message.isEmpty || _busy) return;
    final id = _nextId++;
    _exchanges.add(Exchange(id: id, question: message));
    _busy = true;
    notifyListeners();
    final cancel = _cancel = CancelToken();
    final body = AssistantChatIn(message: message, lang: lang, newConversation: _fresh);
    _fresh = false;
    _stream = api.assistantChat(body, cancel: cancel).listen(
          (event) => _update(id, (e) => applyEvent(e, event)),
          onError: (Object error) {
            if (cancel.isCancelled) return;
            _update(
              id,
              (e) => error is AssistantLimitException
                  ? e.copyWith(status: ExchangeStatus.limit, limit: error.limit)
                  : e.copyWith(status: ExchangeStatus.failed, error: ExchangeError.failed),
            );
            _finish();
          },
          onDone: () {
            // A stream that ended without `done` or `error` broke off: say so.
            _update(
              id,
              (e) => e.status == ExchangeStatus.waiting || e.status == ExchangeStatus.streaming
                  ? e.copyWith(status: ExchangeStatus.failed, error: ExchangeError.failed)
                  : e,
            );
            _finish();
          },
          cancelOnError: true,
        );
  }

  void _finish() {
    _busy = false;
    _stream = null;
    if (!_disposed) notifyListeners();
  }

  /// A new conversation: the answer on its way is dropped.
  void restart() {
    _cancel?.cancel();
    _stream?.cancel();
    _stream = null;
    _busy = false;
    _exchanges.clear();
    _fresh = true;
    notifyListeners();
  }

  /// While the viewer types: a cheap request, so the message finds the connection open.
  void warm() {
    final now = _now();
    final at = _warmedAt;
    if (at != null && now.difference(at) < warmEvery) return;
    _warmedAt = now;
    api.health().then<void>((_) {}, onError: (Object _) {}); // only the connection matters
  }

  @override
  void dispose() {
    _disposed = true;
    _cancel?.cancel();
    _stream?.cancel();
    super.dispose();
  }
}
