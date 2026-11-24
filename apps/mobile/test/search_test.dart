// The search screen (web: pages/Search.test.tsx): popular films first, one request per
// pause in typing, the filters, its four states, and a tile opening the film.
import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/screens/search_screen.dart';
import 'package:movie_match/state/app_state.dart';
import 'package:movie_match/theme/tokens.dart';
import 'package:movie_match/widgets/film_tile.dart';

import 'support/fakes.dart';

Map<String, Object?> film(int id, [String? title]) => {
      'id': id,
      'title': title ?? 'Film $id',
      'release_date': '1995-12-15',
      'runtime_minutes': 170,
      'overview': null,
      'poster_path': null,
      'backdrop_path': null,
      'genres': ['Crime'],
    };

class SearchServer {
  FutureOr<ResponseBody> Function(Uri uri)? answer;
  late final adapter = FakeAdapter((o) {
    if (o.uri.path != '/movies') return jsonBody({'detail': 'not found'}, 404);
    if (answer != null) return answer!(o.uri);
    final q = o.uri.queryParameters['q'];
    if (q == 'zzz') return jsonBody(<Object>[]);
    if (q != null) return jsonBody([film(949, 'Heat')]);
    return jsonBody([for (var i = 1; i <= 6; i++) film(i)]);
  });

  List<Uri> get searches => [for (final r in adapter.requests) r.uri];
}

Future<void> pumpSearch(WidgetTester tester, SearchServer server, {bool settle = true}) async {
  tester.view.physicalSize = const Size(400, 1600);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  final router = GoRouter(routes: [
    GoRoute(path: '/', builder: (context, state) => const SearchScreen()),
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

Finder tile(int id) => find.byWidgetPredicate((w) => w is FilmTile && w.movie.id == id);

Future<void> openFilters(WidgetTester tester) async {
  await tester.tap(find.text('Filters'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('loading: a grid of placeholders', (tester) async {
    final server = SearchServer();
    final answer = Completer<ResponseBody>();
    server.answer = (_) => answer.future;
    await pumpSearch(tester, server, settle: false);
    await tester.pump();
    expect(find.byKey(const Key('search.skeleton')), findsOneWidget);
    answer.complete(jsonBody(<Object>[]));
    await tester.pumpAndSettle();
  });

  testWidgets('shows popular films before anything is typed', (tester) async {
    final server = SearchServer();
    await pumpSearch(tester, server);
    expect(find.text('Popular films'), findsOneWidget);
    expect(tile(1), findsOneWidget);
    expect(server.searches.single.queryParameters, {'limit': '40'});
  });

  testWidgets('searches by title once typing pauses, keeping the last results meanwhile',
      (tester) async {
    final server = SearchServer();
    await pumpSearch(tester, server);
    final answer = Completer<ResponseBody>();
    server.answer = (_) => answer.future;
    await tester.enterText(find.byKey(const Key('search.q')), 'He');
    await tester.pump(const Duration(milliseconds: 100));
    await tester.enterText(find.byKey(const Key('search.q')), 'Heat');
    await tester.pump(const Duration(milliseconds: 249));
    expect(server.searches, hasLength(1), reason: 'no request before the pause');
    await tester.pump(const Duration(milliseconds: 1));
    await tester.pump(const Duration(milliseconds: 10));
    await tester.pump(const Duration(milliseconds: 10));
    expect(server.searches, hasLength(2));
    expect(server.searches.last.queryParameters['q'], 'Heat');
    // The popular films stay, with a sign that new ones are coming.
    expect(tile(1), findsOneWidget);
    expect(find.byKey(const Key('search.busy')), findsOneWidget);
    answer.complete(jsonBody([film(949, 'Heat')]));
    await tester.pumpAndSettle();
    expect(find.text('Results'), findsOneWidget);
    expect(tile(949), findsOneWidget);
    expect(tile(1), findsNothing);
  });

  testWidgets('sends year, runtime and trait filters', (tester) async {
    final server = SearchServer();
    await pumpSearch(tester, server);
    await openFilters(tester);
    await tester.enterText(find.byKey(const Key('search.yearFrom')), '19x90');
    await tester.enterText(find.byKey(const Key('search.yearTo')), '19999');
    await tester.pumpAndSettle();
    expect(find.text('1990'), findsOneWidget, reason: 'digits only');
    expect(find.text('1999'), findsOneWidget, reason: 'four at most');
    await tester.tap(find.byKey(const Key('search.runtime')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Up to 120 minutes').last);
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilterChip, 'Humor'));
    await tester.pumpAndSettle();
    final last = server.searches.last;
    expect(last.queryParameters['year_from'], '1990');
    expect(last.queryParameters['year_to'], '1999');
    expect(last.queryParameters['max_runtime'], '120');
    expect(last.queryParametersAll['trait'], ['humor:70']);
    expect(find.text('Results'), findsOneWidget);
  });

  testWidgets('a year is sent only once it has four digits', (tester) async {
    final server = SearchServer();
    await pumpSearch(tester, server);
    await openFilters(tester);
    await tester.enterText(find.byKey(const Key('search.yearFrom')), '19');
    await tester.pumpAndSettle();
    expect(server.searches.last.queryParameters.containsKey('year_from'), isFalse);
  });

  testWidgets('empty: says so, and clears the filters and the text', (tester) async {
    final server = SearchServer();
    await pumpSearch(tester, server);
    await openFilters(tester);
    await tester.tap(find.widgetWithText(FilterChip, 'Romance'));
    await tester.enterText(find.byKey(const Key('search.q')), 'zzz');
    await tester.pump(searchDelay);
    await tester.pumpAndSettle();
    expect(find.text('No films match these filters. Try loosening them.'), findsOneWidget);
    await tester.tap(find.widgetWithText(OutlinedButton, 'Clear filters'));
    await tester.pumpAndSettle();
    expect(find.text('Popular films'), findsOneWidget);
    expect(tile(1), findsOneWidget);
    expect(tester.widget<TextField>(find.byKey(const Key('search.q'))).controller!.text, '');
    expect(tester.widget<FilterChip>(find.widgetWithText(FilterChip, 'Romance')).selected,
        isFalse);
  });

  testWidgets('error: says so, and Try again asks again', (tester) async {
    final server = SearchServer();
    server.answer = (_) => jsonBody({'detail': 'down'}, 503);
    await pumpSearch(tester, server);
    expect(find.text("Search didn't work. Check your connection and try again."), findsOneWidget);
    server.answer = null;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(tile(1), findsOneWidget);
  });

  testWidgets('a tile opens the film', (tester) async {
    await pumpSearch(tester, SearchServer());
    await tester.tap(tile(3));
    await tester.pumpAndSettle();
    expect(find.text('FILM 3'), findsOneWidget);
  });

  test('the same request is the same search', () {
    expect(toParams(' Heat ', const SearchFilters()), toParams('Heat', const SearchFilters()));
    expect(toParams('', const SearchFilters(traits: ['humor'])).toQuery(),
        'trait=humor%3A70&limit=40');
    expect(gridColumns(328), 3);
    expect(gridColumns(150), 2);
  });

  for (final scale in [1.0, 1.3, 2.0]) {
    testWidgets('nothing is cut off on a small phone at text size $scale', (tester) async {
      await pumpSearch(tester, SearchServer());
      tester.view.physicalSize = const Size(360, 640);
      tester.platformDispatcher.textScaleFactorTestValue = scale;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await openFilters(tester);
      await tester.tap(find.widgetWithText(FilterChip, 'Humor'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.scrollUntilVisible(tile(6), 300, scrollable: find.byType(Scrollable).first);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }
}
