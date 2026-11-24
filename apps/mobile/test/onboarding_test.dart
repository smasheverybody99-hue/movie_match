// Onboarding (FR-3; web: pages/Onboarding.test.tsx): the four states of the pick step;
// continue disabled below 10 and enabled at 10; progress restored after an app restart;
// scores sent through the queue, failures named with Try again; done waits for saves.
import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/data/local_store.dart';
import 'package:movie_match/screens/onboarding_screen.dart';

import 'support/fakes.dart';

Map<String, Object?> film(int id) => {
      'id': id,
      'title': 'Film $id',
      'release_date': '2001-05-0${id % 9 + 1}',
      'runtime_minutes': 100 + id,
      'overview': null,
      'poster_path': null,
      'backdrop_path': null,
      'genres': ['Drama'],
    };

List<Map<String, Object?>> films(int from, int count) => [for (var i = 0; i < count; i++) film(from + i)];

Map<String, Object?> ratingJson(int id, [double score = 7]) =>
    {'movie_id': id, 'score': score, 'liked_aspects': <String>[], 'rated_at': '2026-11-24T10:00:00Z'};

/// The API as onboarding uses it. Every call is recorded; `rate` decides each POST /ratings.
class FakeServer {
  FakeServer({this.page = const [], this.rated = const []});

  List<Map<String, Object?>> page;
  List<int> rated;
  FutureOr<ResponseBody> Function(Map<String, dynamic> body)? rate;
  FutureOr<ResponseBody> Function()? filmsAnswer;
  final ratingBodies = <Map<String, dynamic>>[];
  final events = <Map<String, dynamic>>[];
  var done = 0;
  late final adapter = FakeAdapter(handle);

  FutureOr<ResponseBody> handle(RequestOptions o) {
    final path = o.uri.path;
    if (path == '/onboarding/films') {
      final offset = int.parse(o.uri.queryParameters['offset']!);
      return filmsAnswer?.call() ?? jsonBody(offset == 0 ? page : films(1000 + offset, 3));
    }
    if (path == '/movies') {
      final q = o.uri.queryParameters['q']!;
      return jsonBody(q == 'zzz' ? [] : [film(500)]);
    }
    if (path == '/ratings' && o.method == 'GET') {
      return jsonBody([for (final id in rated) ratingJson(id)]);
    }
    if (path == '/ratings' && o.method == 'POST') {
      final body = jsonDecode(o.data as String) as Map<String, dynamic>;
      ratingBodies.add(body);
      return rate?.call(body) ??
          jsonBody(ratingJson(body['movie_id'] as int, (body['score'] as num).toDouble()));
    }
    if (path == '/events') {
      final list = (jsonDecode(o.data as String) as Map<String, dynamic>)['events'] as List;
      events.addAll(list.cast());
      return jsonBody({'recorded': list.length});
    }
    if (path == '/onboarding/done') {
      done++;
      return ResponseBody.fromString('', 204);
    }
    return jsonBody({'detail': 'not found'}, 404);
  }
}

Finder button(String text) => find.ancestor(
    of: find.text(text), matching: find.byWidgetPredicate((w) => w is ButtonStyleButton));

bool enabled(WidgetTester tester, String text) =>
    tester.widget<ButtonStyleButton>(button(text)).onPressed != null;

Future<void> pumpOnboarding(
  WidgetTester tester,
  FakeServer server, {
  LocalStore? store,
  VoidCallback? onFinished,
}) async {
  await pumpWithFakes(
    tester,
    OnboardingScreen(onFinished: onFinished ?? () {}),
    auth: FakeAuthClient(session: testSession),
    api: fakeApi(server.adapter),
    store: store ?? MemoryLocalStore(),
  );
  await tester.pumpAndSettle();
}

Future<void> pick(WidgetTester tester, Iterable<int> ids) async {
  for (final id in ids) {
    await tester.ensureVisible(find.byKey(ValueKey('pick.$id')));
    await tester.tap(find.byKey(ValueKey('pick.$id')));
    await tester.pump();
  }
  await tester.pumpAndSettle();
}

/// Past the search field's pause, then the answer.
Future<void> settleSearch(WidgetTester tester) async {
  await tester.pump(const Duration(milliseconds: 300));
  await tester.pump();
  await tester.pumpAndSettle();
}

/// Taps Next once the guard against a double tap has passed.
Future<void> next(WidgetTester tester) async {
  await tester.pump(nextGuard);
  await tester.tap(find.text('Next'));
  await tester.pumpAndSettle();
}

Future<void> toRate(WidgetTester tester, FakeServer server) async {
  await pick(tester, [for (final f in server.page.take(10)) f['id'] as int]);
  await tester.tap(find.text('Continue'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('loading: a skeleton while the films load', (tester) async {
    final pending = Completer<ResponseBody>();
    final server = FakeServer()..filmsAnswer = () => pending.future;
    await pumpWithFakes(tester, OnboardingScreen(onFinished: () {}),
        auth: FakeAuthClient(session: testSession),
        api: fakeApi(server.adapter),
        store: MemoryLocalStore());
    await tester.pump();
    expect(find.byKey(const Key('onboarding.loading')), findsOneWidget);
    pending.complete(jsonBody(films(1, 3)));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('onboarding.loading')), findsNothing);
  });

  testWidgets('empty: says so and offers the search', (tester) async {
    await pumpOnboarding(tester, FakeServer());
    expect(find.text('No films here yet. Try searching by title.'), findsOneWidget);
    expect(find.text('Search films'), findsOneWidget);
  });

  testWidgets('error: says so, and Try again asks again', (tester) async {
    var fail = true;
    final server = FakeServer(page: films(1, 12));
    server.filmsAnswer = () => fail ? jsonBody({'detail': 'down'}, 503) : jsonBody(server.page);
    await pumpOnboarding(tester, server);
    expect(find.text("Couldn't load films. Check your connection and try again."), findsOneWidget);
    fail = false;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('pick.1')), findsOneWidget);
  });

  testWidgets('content: the films from the API, each with its title', (tester) async {
    await pumpOnboarding(tester, FakeServer(page: films(1, 12)));
    expect(find.byKey(const ValueKey('pick.1')), findsOneWidget);
    expect(find.text('Which ones did you love?'), findsOneWidget);
    expect(find.text('0 / 10 picked'), findsOneWidget);
  });

  testWidgets('continue is disabled below 10 picks and enabled at 10', (tester) async {
    await pumpOnboarding(tester, FakeServer(page: films(1, 12)));
    expect(enabled(tester, 'Pick 10 more'), isFalse);
    await pick(tester, [for (var i = 1; i <= 9; i++) i]);
    expect(find.text('9 / 10 picked'), findsOneWidget);
    expect(enabled(tester, 'Pick 1 more'), isFalse);
    await pick(tester, [10]);
    expect(find.text('10 / 10 picked'), findsOneWidget);
    expect(enabled(tester, 'Continue'), isTrue);
  });

  testWidgets('a second tap unpicks a film', (tester) async {
    await pumpOnboarding(tester, FakeServer(page: films(1, 12)));
    await pick(tester, [1, 1]);
    expect(find.text('0 / 10 picked'), findsOneWidget);
  });

  testWidgets('films already rated count towards the 10', (tester) async {
    await pumpOnboarding(tester, FakeServer(page: films(1, 12), rated: [900, 901, 902, 903]));
    expect(find.text('4 / 10 picked'), findsOneWidget);
    await pick(tester, [1, 2, 3, 4, 5, 6]);
    expect(enabled(tester, 'Continue'), isTrue);
  });

  testWidgets('"none of these" loads the next films', (tester) async {
    await pumpOnboarding(tester, FakeServer(page: films(1, 12)));
    await tester.tap(find.text("I haven't seen any of these"));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('pick.1060')), findsOneWidget);
    expect(find.byKey(const ValueKey('pick.1')), findsNothing);
  });

  testWidgets('search shows matches, says when there are none, and hides "none of these"',
      (tester) async {
    await pumpOnboarding(tester, FakeServer(page: films(1, 12)));
    await tester.enterText(find.byKey(const Key('onboarding.search')), 'mat');
    await settleSearch(tester);
    expect(find.byKey(const ValueKey('pick.500')), findsOneWidget);
    expect(find.text("I haven't seen any of these"), findsNothing);

    await tester.enterText(find.byKey(const Key('onboarding.search')), 'zzz');
    await settleSearch(tester);
    expect(find.text('No films found for “zzz”. Try another spelling.'), findsOneWidget);
  });

  testWidgets('progress is restored after an app restart', (tester) async {
    final store = MemoryLocalStore();
    final server = FakeServer(page: films(1, 12));
    await pumpOnboarding(tester, server, store: store);
    await pick(tester, [1, 2, 3]);
    expect(find.text('3 / 10 picked'), findsOneWidget);

    // The app closes and opens again with the same phone storage.
    await tester.pumpWidget(const SizedBox());
    await pumpOnboarding(tester, server, store: store);
    expect(find.text('3 / 10 picked'), findsOneWidget);
    await pick(tester, [4, 5, 6, 7, 8, 9, 10]);
    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();
    await next(tester);
    await next(tester);
    expect(find.text('3 / 10'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    await pumpOnboarding(tester, server, store: store);
    expect(find.text('How much did you like it?'), findsOneWidget);
    expect(find.text('3 / 10'), findsOneWidget);
    expect(find.text('Film 3'), findsWidgets);
  });

  testWidgets('liked aspects appear above 8.0, not at it; Next sends score and aspects',
      (tester) async {
    final server = FakeServer(page: films(1, 12));
    await pumpOnboarding(tester, server);
    await toRate(tester, server);
    expect(find.byKey(const Key('onboarding.score')), findsOneWidget);
    expect(find.text('7.0'), findsOneWidget);
    expect(find.byKey(const Key('onboarding.likedAspects')), findsNothing);

    final slider = tester.widget<Slider>(find.byType(Slider));
    slider.onChanged!(8.0);
    await tester.pump();
    expect(find.byKey(const Key('onboarding.likedAspects')), findsNothing);
    slider.onChanged!(9.0);
    await tester.pump();
    expect(find.byKey(const Key('onboarding.likedAspects')), findsOneWidget);
    await tester.ensureVisible(find.text('Plot twists'));
    await tester.tap(find.text('Plot twists'));
    await tester.pump();

    await next(tester);
    expect(server.ratingBodies.single,
        {'movie_id': 1, 'score': 9.0, 'liked_aspects': ['plot_twist']});
    expect(find.text('2 / 10'), findsOneWidget);
    expect(find.text('7.0'), findsOneWidget, reason: 'the next film starts from the default');
  });

  testWidgets('a quick second tap on Next rates one film, not the next one too', (tester) async {
    final server = FakeServer(page: films(1, 12));
    await pumpOnboarding(tester, server);
    await toRate(tester, server);
    await tester.pump(nextGuard);
    await tester.tap(find.text('Next'));
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('Next')); // the second tap lands on film 2
    await tester.pumpAndSettle();
    expect(server.ratingBodies, hasLength(1));
    expect(find.text('2 / 10'), findsOneWidget);
  });

  testWidgets("\"Haven't seen it\" drops the film without a score", (tester) async {
    final server = FakeServer(page: films(1, 12));
    await pumpOnboarding(tester, server);
    await toRate(tester, server);
    await tester.tap(find.text("Haven't seen it"));
    await tester.pumpAndSettle();
    expect(server.ratingBodies, isEmpty);
    expect(find.text('1 / 9'), findsOneWidget);
  });

  testWidgets('below 10 after "haven\'t seen", it asks for more films', (tester) async {
    final server = FakeServer(page: films(1, 12));
    await pumpOnboarding(tester, server);
    await toRate(tester, server);
    for (var i = 0; i < 10; i++) {
      await tester.tap(find.text("Haven't seen it"));
      await tester.pumpAndSettle();
    }
    expect(find.text('Recommendations need 10 more ratings. Pick a few more films.'),
        findsOneWidget);
    await tester.tap(find.text('Pick more films'));
    await tester.pumpAndSettle();
    expect(find.text('0 / 10 picked'), findsOneWidget);
  });

  testWidgets('a score that fails to save is named; Try again sends that same score',
      (tester) async {
    final server = FakeServer(page: films(1, 12));
    var fail = true;
    server.rate = (body) => fail ? jsonBody({'detail': 'down'}, 503) : jsonBody(ratingJson(1));
    await pumpOnboarding(tester, server);
    await toRate(tester, server);
    await next(tester);
    expect(find.text("Couldn't save your score for Film 1. Check your connection."),
        findsOneWidget);

    fail = false;
    await tester.tap(find.descendant(
        of: find.byKey(const Key('onboarding.saveAlert')), matching: find.text('Try again')));
    await tester.pumpAndSettle();
    expect(server.ratingBodies, hasLength(2));
    expect(server.ratingBodies.last, server.ratingBodies.first);
    expect(find.byKey(const Key('onboarding.saveAlert')), findsNothing);
  });

  testWidgets('a score the last run left queued is sent on start', (tester) async {
    final store = MemoryLocalStore();
    store.values['mm.ratingQueue.v1.u1'] = jsonEncode([
      {'movie_id': 77, 'title': 'Left over', 'score': 6.5, 'liked_aspects': [], 'seq': 3},
    ]);
    final server = FakeServer(page: films(1, 12));
    await pumpOnboarding(tester, server, store: store);
    expect(server.ratingBodies.single, {'movie_id': 77, 'score': 6.5, 'liked_aspects': []});
    expect(jsonDecode(store.values['mm.ratingQueue.v1.u1']!), isEmpty);
  });

  testWidgets('after the tenth score: done, then the feed; onboarding marked finished',
      (tester) async {
    final server = FakeServer(page: films(1, 12));
    final store = MemoryLocalStore();
    var finished = 0;
    await pumpOnboarding(tester, server, store: store, onFinished: () => finished++);
    await toRate(tester, server);
    for (var i = 0; i < 10; i++) {
      await next(tester);
    }
    expect(find.text('All set!'), findsOneWidget);
    expect(find.text('You rated 10 films. Your recommendations are ready.'), findsOneWidget);
    await tester.tap(find.text('See my recommendations'));
    await tester.pumpAndSettle();
    expect(finished, 1);
    expect(server.done, 1);
    expect(store.values.containsKey('mm.onboarding.v1.u1'), isFalse);
    // The funnel: each step once.
    await tester.pump(const Duration(seconds: 10));
    expect([for (final e in server.events) e['step']], ['pick', 'rate', 'done']);
  });

  testWidgets('below 10 saved, done waits and says what it waits for', (tester) async {
    final server = FakeServer(page: films(1, 12));
    server.rate = (body) => body['movie_id'] == 10
        ? jsonBody({'detail': 'down'}, 503)
        : jsonBody(ratingJson(body['movie_id'] as int));
    var finished = 0;
    await pumpOnboarding(tester, server, onFinished: () => finished++);
    await toRate(tester, server);
    for (var i = 0; i < 10; i++) {
      await next(tester);
    }
    expect(find.byKey(const Key('onboarding.waiting')), findsOneWidget);
    expect(
        find.text('Recommendations need 10 saved scores: 1 more is waiting to be sent. '
            "We'll send it again when the connection is back."),
        findsOneWidget);
    expect(enabled(tester, 'See my recommendations'), isFalse);
    expect(finished, 0);
  });

  testWidgets('while the last score saves, done says "Saving…"; then it goes on',
      (tester) async {
    final server = FakeServer(page: films(1, 12));
    final hold = Completer<ResponseBody>();
    server.rate = (body) =>
        body['movie_id'] == 10 ? hold.future : jsonBody(ratingJson(body['movie_id'] as int));
    await pumpOnboarding(tester, server);
    await toRate(tester, server);
    for (var i = 0; i < 10; i++) {
      await next(tester);
    }
    expect(find.text('Saving…'), findsOneWidget);
    hold.complete(jsonBody(ratingJson(10)));
    await tester.pumpAndSettle();
    expect(enabled(tester, 'See my recommendations'), isTrue);
  });

  testWidgets('with 10 scores on the server, one that never saves does not keep the user in',
      (tester) async {
    final server = FakeServer(page: films(1, 12), rated: [for (var i = 900; i < 910; i++) i]);
    server.rate = (_) => jsonBody({'detail': 'down'}, 503);
    var finished = 0;
    await pumpOnboarding(tester, server, onFinished: () => finished++);
    await pick(tester, [1]);
    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();
    await next(tester);
    expect(find.text('All set!'), findsOneWidget);
    expect(find.text("Couldn't save your score for Film 1. Check your connection."),
        findsOneWidget);
    await tester.tap(find.text('See my recommendations'));
    await tester.pumpAndSettle();
    expect(finished, 1);
  });
}
