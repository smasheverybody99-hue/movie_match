// The assistant (web: pages/Assistant.test.tsx, lib/assistant.test.ts): the stream as
// text, cards and follow-ups, the waiting, refused, failed and limit states, Try again,
// New conversation, and the tab that only shows while the server offers it.
import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/data/models.dart';
import 'package:movie_match/screens/assistant_screen.dart';
import 'package:movie_match/screens/feed_screen.dart' show MovieCard;
import 'package:movie_match/state/app_state.dart';
import 'package:movie_match/state/assistant_chat.dart';
import 'package:movie_match/theme/tokens.dart';

import 'support/fakes.dart';

Map<String, Object?> film(int id) => {
      'id': id,
      'title': 'Film $id',
      'release_date': '1995-12-15',
      'runtime_minutes': 120,
      'overview': null,
      'poster_path': null,
      'backdrop_path': null,
      'genres': <String>[],
    };

String sse(String event, Object data) => 'event: $event\ndata: ${jsonEncode(data)}\n\n';

/// A whole answer: words, two cards, more words, follow-ups, done.
List<String> answer() => [
      sse('text', {'text': 'Try '}),
      sse('text', {'text': 'these two.'}),
      sse('card', {'movie': film(1), 'match': 80.0, 'band': 'strong'}),
      sse('card', {'movie': film(2), 'match': 70.0, 'band': null}),
      sse('text', {'text': 'Both are tense.'}),
      sse('followups', {
        'items': ['Something shorter', 'Older ones', 'Funnier', 'A fourth']
      }),
      sse('done', <String, Object>{}),
    ];

class ChatServer {
  /// Each message's answer: SSE chunks, sent as they are added to the controller.
  final answers = <StreamController<String>>[];
  final bodies = <Map<String, dynamic>>[];
  ResponseBody Function()? refuse; // a non-stream answer (429, 500)
  bool noticeRequired = false;
  late final adapter = FakeAdapter(handle);

  StreamController<String> get current => answers.last;

  FutureOr<ResponseBody> handle(RequestOptions o) {
    final path = o.uri.path;
    if (path == '/me') {
      return jsonBody({
        ...meJson(required: noticeRequired, acceptedAt: '2026-11-20T10:00:00Z', ratingCount: 12),
        'assistant_enabled': true,
      });
    }
    if (path == '/health') return jsonBody({'status': 'ok', 'trait_dimensions': 14, 'commit': null});
    if (path == '/assistant/chat') {
      bodies.add(jsonDecode(o.data as String) as Map<String, dynamic>);
      final refused = refuse;
      if (refused != null) return refused();
      final chunks = StreamController<String>();
      answers.add(chunks);
      return ResponseBody(
        chunks.stream.map((c) => Uint8List.fromList(utf8.encode(c))),
        200,
        headers: {
          Headers.contentTypeHeader: ['text/event-stream'],
        },
      );
    }
    return jsonBody({'detail': 'not found'}, 404);
  }

  Future<void> send(WidgetTester tester, List<String> chunks, {bool close = true}) async {
    for (final c in chunks) {
      current.add(c);
    }
    if (close) await current.close();
    await tester.pumpAndSettle();
  }
}

Future<ProviderContainer> pumpChat(WidgetTester tester, ChatServer server, {Lang lang = Lang.en}) async {
  tester.view.physicalSize = const Size(400, 1400);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  final router = GoRouter(routes: [
    GoRoute(path: '/', builder: (context, state) => const AssistantScreen()),
    GoRoute(
        path: '/movie/:id',
        builder: (context, state) => Scaffold(body: Text('FILM ${state.pathParameters['id']}'))),
    GoRoute(path: '/profile', builder: (context, state) => const Scaffold(body: Text('PROFILE'))),
  ]);
  addTearDown(router.dispose);
  await tester.pumpWidget(ProviderScope(
    retry: noRetry,
    overrides: [
      authClientProvider.overrideWithValue(FakeAuthClient(session: testSession)),
      apiClientProvider.overrideWithValue(fakeApi(server.adapter)),
      langProvider.overrideWithValue(lang),
    ],
    child: MaterialApp.router(theme: buildTheme(), routerConfig: router),
  ));
  await tester.pumpAndSettle();
  return ProviderScope.containerOf(tester.element(find.byType(MaterialApp)));
}

Finder card(int id) => find.byWidgetPredicate((w) => w is MovieCard && w.item.movie.id == id);

Future<void> askTyped(WidgetTester tester, String text) async {
  await tester.enterText(find.byKey(const Key('assistant.input')), text);
  await tester.pump();
  await tester.tap(find.byKey(const Key('assistant.send')));
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 10));
}

void main() {
  testWidgets('empty: the lead and three starters; nothing to send yet', (tester) async {
    await pumpChat(tester, ChatServer());
    expect(find.textContaining('Ask for a film the way'), findsOneWidget);
    expect(find.text('I have 90 minutes — blow my mind'), findsOneWidget);
    expect(find.text('Something light for a tired evening'), findsOneWidget);
    expect(find.text('A dark thriller from the 90s'), findsOneWidget);
    final send = tester.widget<IconButton>(find.byKey(const Key('assistant.send')));
    expect(send.onPressed, isNull);
  });

  testWidgets('reminds of the free tier while the data notice applies', (tester) async {
    await pumpChat(tester, ChatServer()..noticeRequired = true);
    expect(find.byKey(const Key('assistant.reminder')), findsOneWidget);
  });

  testWidgets('loading, then content: text, a row of cards, more text, three follow-ups',
      (tester) async {
    final server = ChatServer();
    await pumpChat(tester, server);
    await tester.tap(find.text('A dark thriller from the 90s'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 10));
    expect(find.text('Looking through your films…'), findsOneWidget);
    expect(server.bodies.single,
        {'message': 'A dark thriller from the 90s', 'lang': 'en', 'new_conversation': true});

    await server.send(tester, answer());
    expect(find.text('Looking through your films…'), findsNothing);
    expect(find.text('Try these two.'), findsOneWidget);
    expect(find.text('Both are tense.'), findsOneWidget);
    expect(card(1), findsOneWidget);
    expect(card(2), findsOneWidget);
    expect(find.descendant(of: card(1), matching: find.text('Strong match')), findsOneWidget);
    expect(find.byType(ActionChip), findsNWidgets(3));
    expect(find.text('A fourth'), findsNothing);
  });

  testWidgets('the next message continues the conversation; a follow-up is a message',
      (tester) async {
    final server = ChatServer();
    await pumpChat(tester, server);
    await askTyped(tester, '  like Heat  ');
    await server.send(tester, answer());
    await tester.tap(find.text('Older ones'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 10));
    expect(server.bodies.map((b) => [b['message'], b['new_conversation']]), [
      ['like Heat', true],
      ['Older ones', false],
    ]);
    await server.send(tester, [sse('done', <String, Object>{})]);
  });

  testWidgets('a reset drops what the answer showed before the retried call', (tester) async {
    final server = ChatServer();
    await pumpChat(tester, server);
    await askTyped(tester, 'hi');
    await server.send(tester, [sse('text', {'text': 'Half an ans'})], close: false);
    expect(find.text('Half an ans'), findsOneWidget);
    await server.send(tester, [
      sse('reset', <String, Object>{}),
      sse('text', {'text': 'A whole answer.'}),
      sse('done', <String, Object>{}),
    ]);
    expect(find.text('Half an ans'), findsNothing);
    expect(find.text('A whole answer.'), findsOneWidget);
  });

  testWidgets('a refusal shows the interface\'s own words', (tester) async {
    final server = ChatServer();
    await pumpChat(tester, server);
    await askTyped(tester, 'write my essay');
    await server.send(tester, [
      sse('text', {'text': 'Sure, '}),
      sse('refusal', {'reason': 'off_topic'}),
      sse('done', <String, Object>{}),
    ]);
    expect(find.text('Sure,'), findsNothing);
    expect(find.text("I can only help with films. Tell me what you're in the mood to watch."),
        findsOneWidget);
  });

  testWidgets('a slow answer says the assistant is busy, and Try again sends it again',
      (tester) async {
    final server = ChatServer();
    await pumpChat(tester, server);
    await askTyped(tester, 'like Heat');
    await server.send(tester, [sse('error', {'reason': 'timeout'})]);
    expect(find.text('The assistant is busy right now. Try again in a minute.'), findsOneWidget);
    await tester.tap(find.text('Try again'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 10));
    expect(server.bodies.map((b) => b['message']), ['like Heat', 'like Heat']);
    await server.send(tester, answer());
    expect(card(1), findsOneWidget);
  });

  testWidgets('a blocked answer offers no Try again', (tester) async {
    final server = ChatServer();
    await pumpChat(tester, server);
    await askTyped(tester, 'something');
    await server.send(tester, [sse('error', {'reason': 'blocked'})]);
    expect(find.text("I can't answer that one. Try asking another way."), findsOneWidget);
    expect(find.text('Try again'), findsNothing);
  });

  testWidgets('a stream that breaks off without done says it failed', (tester) async {
    final server = ChatServer();
    await pumpChat(tester, server);
    await askTyped(tester, 'like Heat');
    await server.send(tester, [sse('text', {'text': 'Try '})]);
    expect(find.text("The assistant couldn't answer. Try again."), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('a server error says it failed, with Try again', (tester) async {
    final server = ChatServer()..refuse = () => jsonBody({'detail': 'down'}, 500);
    await pumpChat(tester, server);
    await askTyped(tester, 'like Heat');
    await tester.pumpAndSettle();
    expect(find.text("The assistant couldn't answer. Try again."), findsOneWidget);
  });

  testWidgets('today\'s cap: says when it resets, and the field stops taking messages',
      (tester) async {
    final resets = DateTime.now().toUtc().add(const Duration(hours: 5));
    final server = ChatServer()
      ..refuse = () => jsonBody({
            'detail': 'limit',
            'limit': 30,
            'resets_at': resets.toIso8601String(),
          }, 429);
    await pumpChat(tester, server);
    await askTyped(tester, 'one more');
    await tester.pumpAndSettle();
    final text = tester.widget<Text>(find.byKey(const Key('assistant.limit'))).data!;
    expect(text, "You've asked all 30 of today's questions. You can ask again at "
        '${resetTime(resets, Lang.en)}.');
    expect(tester.widget<TextField>(find.byKey(const Key('assistant.input'))).enabled, isFalse);
    expect(tester.widget<IconButton>(find.byKey(const Key('assistant.send'))).onPressed, isNull);
  });

  testWidgets('a card opens the film and counts as a click from the assistant', (tester) async {
    final server = ChatServer();
    final c = await pumpChat(tester, server);
    await askTyped(tester, 'like Heat');
    await server.send(tester, answer());
    await tester.tap(find.descendant(of: card(2), matching: find.byType(InkWell)).first);
    await tester.pumpAndSettle();
    expect(find.text('FILM 2'), findsOneWidget);
    expect(
      [
        for (final e in c.read(telemetryProvider).queued)
          if (e case RecommendationEvent(clicked: true, :final movieId, :final source))
            '${source.wire}:$movieId',
      ],
      ['assistant:2'],
    );
  });

  testWidgets('New conversation clears the screen and starts afresh on the server too',
      (tester) async {
    final server = ChatServer();
    await pumpChat(tester, server);
    await askTyped(tester, 'like Heat');
    await server.send(tester, answer());
    await tester.tap(find.byTooltip('New conversation'));
    await tester.pumpAndSettle();
    expect(find.text('Try these two.'), findsNothing);
    expect(find.text('A dark thriller from the 90s'), findsOneWidget);
    await askTyped(tester, 'again');
    expect(server.bodies.last['new_conversation'], isTrue);
    await server.send(tester, [sse('done', <String, Object>{})]);
  });

  group('applyEvent', () {
    const card1 = AssistantCard(movie: Movie(id: 1, title: 'A'), match: 80);
    const card2 = AssistantCard(movie: Movie(id: 2, title: 'B'), match: 70);

    test('text runs join; cards in a row share it; text between starts a new row', () {
      var e = const Exchange(id: 1, question: 'q');
      for (final event in const <AssistantEvent>[
        AssistantText('a'),
        AssistantText('b'),
        AssistantCardEvent(card1),
        AssistantCardEvent(card2),
        AssistantText('c'),
        AssistantCardEvent(card1),
      ]) {
        e = applyEvent(e, event);
      }
      expect(e.status, ExchangeStatus.streaming);
      expect(e.parts.map((p) => switch (p) {
            TextPart(:final text) => text,
            CardsPart(:final cards) => cards.map((c) => c.movie.id).join(','),
          }), ['ab', '1,2', 'c', '1']);
    });

    test('done after a refusal keeps the refusal', () {
      var e = applyEvent(const Exchange(id: 1, question: 'q'),
          const AssistantRefusal(AssistantRefusalReason.leak));
      e = applyEvent(e, const AssistantDone());
      expect(e.status, ExchangeStatus.refused);
      expect(e.refusal, AssistantRefusalReason.leak);
    });
  });

  test('the reset time in the viewer\'s clock', () {
    final at = DateTime(2026, 11, 25, 5, 0);
    expect(resetTime(at, Lang.uz), '05:00');
    expect(resetTime(at, Lang.en), '05:00 AM');
    expect(resetTime(DateTime(2026, 11, 25, 17, 30), Lang.en), '05:30 PM');
    expect(resetTime(DateTime(2026, 11, 25, 0, 5), Lang.en), '12:05 AM');
  });

  for (final scale in [1.0, 1.3, 2.0]) {
    testWidgets('nothing is cut off on a small phone at text size $scale', (tester) async {
      final server = ChatServer()..noticeRequired = true;
      await pumpChat(tester, server, lang: Lang.ru);
      tester.view.physicalSize = const Size(360, 640);
      tester.platformDispatcher.textScaleFactorTestValue = scale;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await askTyped(tester, 'like Heat');
      await server.send(tester, answer());
      expect(tester.takeException(), isNull);
      await tester.drag(find.byType(ListView).first, const Offset(0, 3000));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }
}
