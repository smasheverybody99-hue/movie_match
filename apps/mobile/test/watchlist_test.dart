// The watchlist (web: pages/Watchlist.test.tsx): its four states, the groups, Watched and
// Remove from the buttons and from a swipe, and the rollback when the server refuses.
import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/data/models.dart';
import 'package:movie_match/screens/watchlist_screen.dart';
import 'package:movie_match/state/app_state.dart';
import 'package:movie_match/theme/tokens.dart';

import 'support/fakes.dart';

Map<String, Object?> film(int id, {int? runtime = 120}) => {
      'id': id,
      'title': 'Film $id',
      'release_date': '2001-01-01',
      'runtime_minutes': runtime,
      'overview': null,
      'poster_path': null,
      'backdrop_path': null,
      'genres': <String>[],
    };

Map<String, Object?> item(int id, {int? runtime = 120, bool watched = false, String? band}) => {
      'movie': film(id, runtime: runtime),
      'added_at': '2026-11-20T10:00:00Z',
      'watched_at': watched ? '2026-11-22T10:00:00Z' : null,
      'match': 70.0,
      'band': band,
    };

class ListServer {
  ListServer([List<Map<String, Object?>>? items])
      : items = items ??
            [
              item(1, band: 'strong'),
              item(2, runtime: 85),
              item(3, watched: true),
            ];

  List<Map<String, Object?>> items;
  FutureOr<ResponseBody> Function()? listAnswer;
  int changeStatus = 200;
  Completer<void>? hold;
  late final adapter = FakeAdapter(handle);

  List<String> get changes => [
        for (final r in adapter.requests)
          if (r.method != 'GET') '${r.method} ${r.uri.path}',
      ];

  FutureOr<ResponseBody> handle(RequestOptions o) async {
    final path = o.uri.path;
    if (path == '/watchlist' && o.method == 'GET') return listAnswer?.call() ?? jsonBody(items);
    if (hold != null) await hold!.future;
    if (changeStatus != 200) return jsonBody({'detail': 'down'}, changeStatus);
    final id = int.parse(path.split('/')[2]);
    if (o.method == 'DELETE') {
      items = [for (final i in items) if ((i['movie']! as Map)['id'] != id) i];
      return ResponseBody.fromString('', 204);
    }
    if (path.endsWith('/watched')) {
      items = [
        for (final i in items)
          if ((i['movie']! as Map)['id'] == id) {...i, 'watched_at': '2026-11-24T10:00:00Z'} else i,
      ];
      return jsonBody(items.firstWhere((i) => (i['movie']! as Map)['id'] == id));
    }
    return jsonBody({'detail': 'not found'}, 404);
  }
}

Future<void> pumpList(WidgetTester tester, ListServer server, {bool settle = true}) async {
  tester.view.physicalSize = const Size(400, 1200);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  final router = GoRouter(routes: [
    GoRoute(path: '/', builder: (context, state) => const WatchlistScreen()),
    GoRoute(path: '/search', builder: (context, state) => const Scaffold(body: Text('SEARCH'))),
    GoRoute(
        path: '/movie/:id',
        builder: (context, state) => Scaffold(body: Text('FILM ${state.pathParameters['id']}'))),
  ]);
  addTearDown(router.dispose);
  await tester.pumpWidget(ProviderScope(
    retry: noRetry,
    overrides: [
      authClientProvider.overrideWithValue(FakeAuthClient(session: testSession)),
      apiClientProvider.overrideWithValue(fakeApi(server.adapter)),
    ],
    child: MaterialApp.router(theme: buildTheme(), routerConfig: router),
  ));
  if (settle) await tester.pumpAndSettle();
}

Finder row(int id) => find.byKey(ValueKey(id));

/// A fling sideways; the row's action starts on the last frame of the swipe, so one more
/// pump lets its request go out.
Future<void> swipe(WidgetTester tester, Finder target, double dx) async {
  await tester.fling(target, Offset(dx, 0), 1500);
  await tester.pumpAndSettle();
  await tester.pump();
  await tester.pumpAndSettle();
}

Future<void> showGroup(WidgetTester tester, String name) async {
  await tester.tap(find.byKey(Key('watchlist.group.$name')));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('loading: rows of placeholders', (tester) async {
    final server = ListServer();
    final answer = Completer<ResponseBody>();
    server.listAnswer = () => answer.future;
    await pumpList(tester, server, settle: false);
    await tester.pump();
    expect(find.byKey(const Key('watchlist.skeleton')), findsOneWidget);
    answer.complete(jsonBody(<Object>[]));
    await tester.pumpAndSettle();
  });

  testWidgets('empty: says so, with a way to search', (tester) async {
    await pumpList(tester, ListServer([]));
    expect(find.textContaining('Your watchlist is empty.'), findsOneWidget);
    await tester.tap(find.text('Search films'));
    await tester.pumpAndSettle();
    expect(find.text('SEARCH'), findsOneWidget);
  });

  testWidgets('error: says so, and Try again asks again', (tester) async {
    final server = ListServer();
    server.listAnswer = () => jsonBody({'detail': 'down'}, 503);
    await pumpList(tester, server);
    expect(find.text("Couldn't load your watchlist. Check your connection and try again."),
        findsOneWidget);
    server.listAnswer = null;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(row(1), findsOneWidget);
  });

  testWidgets('content: unwatched films under Watch next, with the API\'s band', (tester) async {
    await pumpList(tester, ListServer());
    expect(row(1), findsOneWidget);
    expect(row(2), findsOneWidget);
    expect(row(3), findsNothing);
    expect(find.descendant(of: row(1), matching: find.text('Strong match')), findsOneWidget);
    expect(find.descendant(of: row(2), matching: find.text('Strong match')), findsNothing);
    expect(find.textContaining('70'), findsNothing, reason: 'the number is never shown');
  });

  testWidgets('the chips filter the list', (tester) async {
    await pumpList(tester, ListServer());
    await showGroup(tester, 'short');
    expect(row(2), findsOneWidget);
    expect(row(1), findsNothing);
    await showGroup(tester, 'watched');
    expect(row(3), findsOneWidget);
    expect(row(1), findsNothing);
    expect(find.byKey(const Key('watchlist.watched.3')), findsNothing,
        reason: 'a watched film cannot be marked watched again');
  });

  testWidgets('says so when a group is empty', (tester) async {
    await pumpList(tester, ListServer([item(1)]));
    await showGroup(tester, 'watched');
    expect(find.text('No films in this group.'), findsOneWidget);
  });

  testWidgets('Watched moves the row out of Watch next at once', (tester) async {
    final server = ListServer();
    final hold = Completer<void>();
    server.hold = hold;
    await pumpList(tester, server);
    await tester.tap(find.byKey(const Key('watchlist.watched.1')));
    await tester.pump();
    expect(row(1), findsNothing);
    hold.complete();
    await tester.pumpAndSettle();
    expect(server.changes, ['POST /watchlist/1/watched']);
    await showGroup(tester, 'watched');
    expect(row(1), findsOneWidget);
  });

  testWidgets('puts the row back and says so when Watched fails', (tester) async {
    final server = ListServer()..changeStatus = 503;
    await pumpList(tester, server);
    await tester.tap(find.byKey(const Key('watchlist.watched.1')));
    await tester.pumpAndSettle();
    expect(row(1), findsOneWidget);
    expect(find.text("That change wasn't saved. Try again."), findsOneWidget);
  });

  testWidgets('Remove takes the film off the list', (tester) async {
    final server = ListServer();
    await pumpList(tester, server);
    await tester.tap(find.byKey(const Key('watchlist.remove.2')));
    await tester.pumpAndSettle();
    expect(row(2), findsNothing);
    expect(server.changes, ['DELETE /watchlist/2']);
  });

  group('swipe', () {
    testWidgets('right marks the film watched', (tester) async {
      final server = ListServer();
      await pumpList(tester, server);
      await swipe(tester, row(1), 400);
      expect(row(1), findsNothing);
      expect(server.changes, ['POST /watchlist/1/watched']);
    });

    testWidgets('left removes it', (tester) async {
      final server = ListServer();
      await pumpList(tester, server);
      await swipe(tester, row(2), -400);
      expect(row(2), findsNothing);
      expect(server.changes, ['DELETE /watchlist/2']);
    });

    testWidgets('a watched film only swipes left', (tester) async {
      final server = ListServer();
      await pumpList(tester, server);
      await showGroup(tester, 'watched');
      await swipe(tester, row(3), 400);
      expect(row(3), findsOneWidget);
      expect(server.changes, isEmpty);
      await swipe(tester, row(3), -400);
      expect(server.changes, ['DELETE /watchlist/3']);
    });

    testWidgets('a refused swipe brings the row back', (tester) async {
      final server = ListServer()..changeStatus = 503;
      await pumpList(tester, server);
      await swipe(tester, row(2), -400);
      expect(row(2), findsOneWidget);
      expect(find.text("That change wasn't saved. Try again."), findsOneWidget);
    });
  });

  testWidgets('a tap on a row opens the film', (tester) async {
    await pumpList(tester, ListServer());
    await tester.tap(find.descendant(of: row(2), matching: find.text('Film 2')).last);
    await tester.pumpAndSettle();
    expect(find.text('FILM 2'), findsOneWidget);
  });

  test('groups: a short unwatched film is in Watch next and Under 90, not Watched; '
      'unknown length is not short', () {
    WatchlistItem parse(Map<String, Object?> json) => WatchlistItem.fromJson(json);
    final short = parse(item(1, runtime: 90));
    expect(inGroup(short, WatchlistGroup.next), isTrue);
    expect(inGroup(short, WatchlistGroup.short), isTrue);
    expect(inGroup(short, WatchlistGroup.watched), isFalse);
    expect(inGroup(parse(item(2, runtime: null)), WatchlistGroup.short), isFalse);
    expect(inGroup(parse(item(3, runtime: 80, watched: true)), WatchlistGroup.short), isFalse);
  });

  for (final scale in [1.0, 1.3, 2.0]) {
    testWidgets('nothing is cut off on a small phone at text size $scale', (tester) async {
      await pumpList(tester, ListServer([for (var i = 1; i <= 6; i++) item(i, band: 'strong')]));
      tester.view.physicalSize = const Size(360, 640);
      tester.platformDispatcher.textScaleFactorTestValue = scale;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.drag(find.byType(ListView).first, const Offset(0, -3000));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }
}
