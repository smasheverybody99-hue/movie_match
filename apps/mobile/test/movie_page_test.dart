// The film page (web: pages/MoviePage.test.tsx): its states, "why you" and its sentence,
// the axes, the sensitive warning, and Rate / Save with their rollbacks.
import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/data/models.dart';
import 'package:movie_match/data/traits.dart';
import 'package:movie_match/screens/film_screen.dart';
import 'package:movie_match/state/app_state.dart';
import 'package:movie_match/theme/tokens.dart';
import 'package:movie_match/widgets/backdrop.dart';
import 'package:movie_match/widgets/poster.dart';
import 'package:movie_match/widgets/trait_axis.dart';

import 'support/fakes.dart';

/// Every trait at 50 except the ones given.
Map<String, int> scores([Map<String, int> some = const {}]) =>
    {for (final k in traitKeys) k: some[k] ?? 50};

Map<String, Object?> detail(
  int id, {
  double? match = 82,
  String? band = 'strong',
  List<String> named = const ['humor', 'pacing', 'mystery'],
  String? side = 'reason',
  Map<String, int>? traits,
  bool noTraits = false,
  bool sensitive = false,
  String? backdrop,
}) =>
    {
      'id': id,
      'title': 'Film $id',
      'release_date': '2010-05-01',
      'runtime_minutes': 120,
      'overview': 'About film $id.',
      'poster_path': null,
      'backdrop_path': backdrop,
      'genres': ['Drama', 'Crime'],
      'traits': noTraits ? null : {'scores': traits ?? scores({'humor': 70}), 'summary': null},
      'director': 'A Director',
      'cast': ['One Actor', 'Two Actor'],
      'match': match,
      'band': band,
      'named_traits': named,
      'trait_side': side,
      'sensitive': sensitive,
    };

class FilmServer {
  final films = <int, Map<String, Object?>>{7: detail(7), 8: detail(8)};
  FutureOr<ResponseBody> Function(int id)? filmAnswer;
  FutureOr<ResponseBody> Function(int id)? explanationAnswer;
  Map<String, int> taste = scores({'humor': 40});
  final ratings = <int, double>{};
  int rateStatus = 200;
  Completer<void>? holdRate;
  List<int> saved = [];
  late final adapter = FakeAdapter(handle);

  List<String> get paths => [for (final r in adapter.requests) '${r.method} ${r.uri.path}'];
  int explanationCalls(int id) =>
      paths.where((p) => p == 'GET /recommendations/$id/explanation').length;

  Map<String, Object?> rating(int id, double score) =>
      {'movie_id': id, 'score': score, 'liked_aspects': <String>[], 'rated_at': '2026-11-20T10:00:00Z'};

  FutureOr<ResponseBody> handle(RequestOptions o) async {
    final path = o.uri.path;
    final parts = path.split('/');
    if (parts.length == 3 && parts[1] == 'movies') {
      final id = int.parse(parts[2]);
      if (filmAnswer != null) return filmAnswer!(id);
      final film = films[id];
      return film == null ? jsonBody({'detail': 'not found'}, 404) : jsonBody(film);
    }
    if (path.endsWith('/explanation')) {
      final id = int.parse(parts[2]);
      return explanationAnswer?.call(id) ??
          jsonBody({'movie_id': id, 'lang': 'en', 'text': 'A cached line for film $id.', 'reason': null});
    }
    if (path == '/me/dna') {
      return jsonBody({
        'scores': taste,
        'summary': null,
        'rating_count': 12,
        'ratings_needed': 0,
        'average_rating': 7.5,
        'top_genre': 'Drama',
      });
    }
    if (path == '/ratings' && o.method == 'GET') {
      return jsonBody([for (final e in ratings.entries) rating(e.key, e.value)]);
    }
    if (path == '/ratings' && o.method == 'POST') {
      final body = jsonDecode(o.data as String) as Map<String, dynamic>;
      if (holdRate != null) await holdRate!.future;
      if (rateStatus != 200) return jsonBody({'detail': 'down'}, rateStatus);
      final id = body['movie_id'] as int;
      ratings[id] = (body['score'] as num).toDouble();
      return jsonBody(rating(id, ratings[id]!));
    }
    if (path == '/watchlist' && o.method == 'GET') {
      return jsonBody([
        for (final id in saved)
          {'movie': detail(id), 'added_at': '2026-11-20T10:00:00Z', 'watched_at': null, 'match': null, 'band': null},
      ]);
    }
    if (path == '/watchlist' && o.method == 'POST') {
      final id = (jsonDecode(o.data as String) as Map<String, dynamic>)['movie_id'] as int;
      saved = [...saved, id];
      return jsonBody(
          {'movie': detail(id), 'added_at': '2026-11-24T10:00:00Z', 'watched_at': null, 'match': null, 'band': null},
          201);
    }
    if (path == '/me') return jsonBody(meJson(required: false, ratingCount: 12));
    if (path == '/recommendations') {
      return jsonBody({'status': 'ok', 'ratings_needed': 0, 'sections': <Object>[]});
    }
    return jsonBody({'detail': 'not found'}, 404);
  }
}

Future<GoRouter> pumpFilm(
  WidgetTester tester,
  FilmServer server, {
  String at = '/movie/7',
  Lang lang = Lang.en,
  bool settle = true,
  Movie? early,
}) async {
  tester.view.physicalSize = const Size(400, 2600);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  final router = GoRouter(initialLocation: '/', routes: [
    GoRoute(path: '/', builder: (context, state) => const Scaffold(body: Text('HOME'))),
    GoRoute(
      path: '/movie/:id',
      builder: (context, state) => FilmScreen(
        id: int.tryParse(state.pathParameters['id'] ?? ''),
        early: state.extra is Movie ? state.extra! as Movie : null,
      ),
    ),
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
  await tester.pump();
  router.push(at, extra: early);
  if (settle) {
    await tester.pumpAndSettle();
  } else {
    for (var i = 0; i < 5; i++) {
      await tester.pump(const Duration(milliseconds: 10));
    }
  }
  return router;
}

String axisLabel(WidgetTester tester, String trait) =>
    tester.getSemantics(find.byKey(Key('axis.$trait')).first).label;

Finder inWhy(Finder f) => find.descendant(of: find.byKey(const Key('film.why')), matching: f);
Finder inCompare(Finder f) =>
    find.descendant(of: find.byKey(const Key('film.compare')), matching: f);

String sentence(WidgetTester tester) =>
    tester.widget<Text>(find.byKey(const Key('film.sentence'))).data!;

void main() {
  group('states', () {
    testWidgets('loading: the page\'s shape, with the tapped card\'s backdrop', (tester) async {
      final server = FilmServer();
      final answer = Completer<ResponseBody>();
      server.filmAnswer = (_) => answer.future;
      await pumpFilm(tester, server,
          settle: false, early: const Movie(id: 7, title: 'Film 7', backdropPath: '/b.jpg'));
      expect(find.byKey(const Key('film.skeleton')), findsOneWidget);
      expect(find.descendant(of: find.byKey(const Key('film.skeleton')), matching: find.byType(Backdrop)),
          findsOneWidget);
      answer.complete(jsonBody(detail(7)));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('film.skeleton')), findsNothing);
    });

    testWidgets('asks for the taste, the ratings and the list together with the film',
        (tester) async {
      final server = FilmServer();
      final answer = Completer<ResponseBody>();
      server.filmAnswer = (_) => answer.future;
      await pumpFilm(tester, server, settle: false);
      expect(server.paths, containsAll(['GET /movies/7', 'GET /me/dna', 'GET /ratings', 'GET /watchlist']));
      answer.complete(jsonBody(detail(7)));
      await tester.pumpAndSettle();
    });

    testWidgets('empty: a film that does not exist, with a way home', (tester) async {
      await pumpFilm(tester, FilmServer(), at: '/movie/999');
      expect(find.text('We couldn\'t find this film. It may have left the catalogue.'), findsOneWidget);
      await tester.tap(find.text('Go home'));
      await tester.pumpAndSettle();
      expect(find.text('HOME'), findsOneWidget);
    });

    testWidgets('a link whose id is not a number is not found either', (tester) async {
      final server = FilmServer();
      await pumpFilm(tester, server, at: '/movie/abc');
      expect(find.text('We couldn\'t find this film. It may have left the catalogue.'), findsOneWidget);
      expect(server.paths.where((p) => p.startsWith('GET /movies')), isEmpty);
    });

    testWidgets('error: says so, and Try again fetches again', (tester) async {
      final server = FilmServer();
      server.filmAnswer = (_) => jsonBody({'detail': 'down'}, 503);
      await pumpFilm(tester, server);
      expect(find.text('Couldn\'t load this film. Check your connection and try again.'), findsOneWidget);
      server.filmAnswer = null;
      await tester.tap(find.text('Try again'));
      await tester.pumpAndSettle();
      expect(find.text('Film 7'), findsWidgets);
    });

    testWidgets('content: the band, why, the overview, the credits and the comparison',
        (tester) async {
      await pumpFilm(tester, FilmServer());
      expect(find.text('Film 7'), findsWidgets);
      for (final tag in ['2010', '120m', 'Drama', 'Crime']) {
        expect(find.text(tag), findsOneWidget, reason: tag);
      }
      expect(inWhy(find.text('STRONG MATCH')), findsOneWidget);
      expect(sentence(tester), 'A cached line for film 7.');
      expect(find.text('About film 7.'), findsOneWidget);
      expect(find.textContaining('A Director'), findsOneWidget);
      expect(find.textContaining('One Actor, Two Actor'), findsOneWidget);
      expect(inCompare(find.byType(TraitAxis)), findsNWidgets(6));
      expect(inCompare(find.text('OTHER TRAITS')), findsOneWidget);
      expect(find.textContaining('82'), findsNothing, reason: 'the number is never shown');
    });
  });

  for (final scale in [1.0, 1.3, 2.0]) {
    testWidgets('nothing is cut off on a small phone at text size $scale', (tester) async {
      final server = FilmServer()..ratings[7] = 9.5;
      server.explanationAnswer = (id) => jsonBody({
            'movie_id': id,
            'lang': 'en',
            'text': 'A long cached sentence about why this film suits you, long enough to wrap '
                'over several lines on a small phone.',
            'reason': 'daily_cap',
          });
      await pumpFilm(tester, server);
      tester.view.physicalSize = const Size(360, 640);
      tester.platformDispatcher.textScaleFactorTestValue = scale;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.scrollUntilVisible(find.byKey(const Key('film.compare')), 500,
          scrollable: find.byType(Scrollable).first);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      // Back to the top, then Rate in the middle of the screen: at the top edge it would sit
      // under the app bar.
      tester.state<ScrollableState>(find.byType(Scrollable).first).position.jumpTo(0);
      await tester.pumpAndSettle();
      await Scrollable.ensureVisible(tester.element(find.byKey(const Key('film.rate'))),
          alignment: 0.5);
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('film.rate')));
      await tester.pumpAndSettle();
      expect(find.text('Save rating'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  group('why you', () {
    testWidgets('says it is writing while the sentence is on its way, then shows it',
        (tester) async {
      final server = FilmServer();
      final answer = Completer<ResponseBody>();
      server.explanationAnswer = (_) => answer.future;
      await pumpFilm(tester, server, settle: false);
      await tester.pump();
      expect(find.text('Writing the explanation…'), findsOneWidget);
      answer.complete(jsonBody({'movie_id': 7, 'lang': 'en', 'text': 'Written now.', 'reason': null}));
      await tester.pumpAndSettle();
      expect(find.text('Writing the explanation…'), findsNothing);
      expect(sentence(tester), 'Written now.');
    });

    testWidgets('shows the three reasons on one axis each: your value and the film\'s',
        (tester) async {
      await pumpFilm(tester, FilmServer());
      expect(inWhy(find.byType(TraitAxis)), findsNWidgets(3));
      expect(axisLabel(tester, 'humor'), 'Humor: you 40, film 70');
      expect(axisLabel(tester, 'pacing'), 'Pace: you 50, film 50');
    });

    testWidgets('the you / film key shows once: in why you when it has axes, else in the comparison',
        (tester) async {
      await pumpFilm(tester, FilmServer());
      expect(find.byKey(const Key('axis.legend')), findsOneWidget);
      expect(inWhy(find.byKey(const Key('axis.legend'))), findsOneWidget);
    });

    testWidgets('without a taste profile: no dot of yours, rather than one at 0', (tester) async {
      final server = FilmServer()..taste = {};
      await pumpFilm(tester, server);
      expect(axisLabel(tester, 'humor'), 'Humor: film 70');
      expect(find.byKey(const Key('axis.you')), findsNothing);
    });

    testWidgets('falls back to the named traits when no sentence comes', (tester) async {
      final server = FilmServer();
      server.explanationAnswer =
          (id) => jsonBody({'movie_id': id, 'lang': 'en', 'text': null, 'reason': 'failed'});
      await pumpFilm(tester, server);
      expect(sentence(tester),
          'Where your taste is clearest, this film sits at your level: Humor, Pace, Mystery.');
      expect(find.byKey(const Key('film.capped')), findsNothing);
    });

    testWidgets('today\'s allowance used up: the fallback says why, and the next film does not ask',
        (tester) async {
      final server = FilmServer();
      server.explanationAnswer =
          (id) => jsonBody({'movie_id': id, 'lang': 'en', 'text': null, 'reason': 'daily_cap'});
      final router = await pumpFilm(tester, server);
      expect(find.text('Today\'s explanations are used up — new ones tomorrow'), findsOneWidget);
      expect(server.explanationCalls(7), 1);
      router.push('/movie/8');
      await tester.pumpAndSettle();
      expect(find.text('Film 8'), findsWidgets);
      expect(server.explanationCalls(8), 0);
      expect(find.text('Writing the explanation…'), findsNothing);
      expect(find.text('Today\'s explanations are used up — new ones tomorrow'), findsOneWidget);
    });

    testWidgets('one failure is bad luck: the next film still asks', (tester) async {
      final server = FilmServer();
      server.explanationAnswer =
          (id) => jsonBody({'movie_id': id, 'lang': 'en', 'text': null, 'reason': 'failed'});
      final router = await pumpFilm(tester, server);
      router.push('/movie/8');
      await tester.pumpAndSettle();
      expect(server.explanationCalls(8), 1);
    });

    testWidgets('when the rule names no trait: no sentence, no axes, no request', (tester) async {
      final server = FilmServer();
      server.films[7] = detail(7, named: [], side: null);
      await pumpFilm(tester, server);
      expect(inWhy(find.text('STRONG MATCH')), findsOneWidget);
      expect(find.byKey(const Key('film.sentence')), findsNothing);
      expect(inWhy(find.byType(TraitAxis)), findsNothing);
      expect(server.explanationCalls(7), 0);
      // The key moves to the comparison, which is then the film's strongest traits.
      expect(inCompare(find.byKey(const Key('axis.legend'))), findsOneWidget);
      expect(inCompare(find.text('ITS STRONGEST TRAITS')), findsOneWidget);
    });

    testWidgets('a closest film\'s difference: the neutral heading and how it differs',
        (tester) async {
      final server = FilmServer();
      server.films[7] = detail(7, named: ['humor'], side: 'difference');
      server.explanationAnswer =
          (id) => jsonBody({'movie_id': id, 'lang': 'en', 'text': null, 'reason': 'rejected'});
      await pumpFilm(tester, server);
      expect(inWhy(find.text('HOW IT DIFFERS')), findsOneWidget);
      expect(inWhy(find.text('STRONG MATCH')), findsNothing);
      expect(sentence(tester), 'Where it differs from your taste: Humor.');
    });

    testWidgets('without a match: the neutral heading, a word on why, and no request',
        (tester) async {
      final server = FilmServer();
      server.films[7] = detail(7, match: null, band: null);
      await pumpFilm(tester, server);
      expect(inWhy(find.text('YOU AND THIS FILM')), findsOneWidget);
      expect(find.text('Rate 10 films first to see how well this one matches you.'), findsOneWidget);
      expect(server.explanationCalls(7), 0);
    });

    testWidgets('in Russian: traits in lower case inside the sentence, a decimal comma',
        (tester) async {
      final server = FilmServer()..ratings[7] = 8.5;
      server.explanationAnswer =
          (id) => jsonBody({'movie_id': id, 'lang': 'ru', 'text': null, 'reason': 'failed'});
      await pumpFilm(tester, server, lang: Lang.ru);
      final s = sentence(tester);
      expect(s, contains('юмор'));
      expect(s, isNot(contains('Юмор')));
      expect(find.textContaining('8,5'), findsWidgets);
    });
  });

  group('sensitive film', () {
    testWidgets('warns first, without its images, and opens the page when asked', (tester) async {
      final server = FilmServer();
      server.films[7] = detail(7, sensitive: true, backdrop: '/b.jpg');
      await pumpFilm(tester, server);
      expect(find.text('Explicit or extreme film'), findsOneWidget);
      expect(find.byType(Backdrop), findsNothing);
      expect(find.byType(Poster), findsNothing);
      await tester.tap(find.text('Show the page'));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('film.why')), findsOneWidget);
    });

    testWidgets('Go back leaves without opening it', (tester) async {
      final server = FilmServer();
      server.films[7] = detail(7, sensitive: true);
      await pumpFilm(tester, server);
      await tester.tap(find.text('Go back'));
      await tester.pumpAndSettle();
      expect(find.text('HOME'), findsOneWidget);
    });

    testWidgets('an ordinary film has no warning', (tester) async {
      await pumpFilm(tester, FilmServer());
      expect(find.text('Explicit or extreme film'), findsNothing);
    });
  });

  group('rate and save', () {
    Future<void> rateTo(WidgetTester tester, {required int steps}) async {
      await tester.tap(find.byKey(const Key('film.rate')));
      await tester.pumpAndSettle();
      expect(find.text('Rate Film 7'), findsOneWidget);
      final slider = tester.widget<Slider>(find.byType(Slider));
      slider.onChanged!(slider.value + steps * 0.5);
      await tester.pump();
      await tester.tap(find.text('Save rating'));
      await tester.pump();
    }

    testWidgets('the rating shows at once and rolls back to the previous one on failure',
        (tester) async {
      final server = FilmServer()
        ..ratings[7] = 8.0
        ..rateStatus = 503;
      final hold = Completer<void>();
      server.holdRate = hold;
      await pumpFilm(tester, server);
      expect(find.byKey(const Key('film.myRating')), findsOneWidget);
      expect(find.text('Your rating: 8.0'), findsWidgets);
      await rateTo(tester, steps: 2);
      await tester.pump(const Duration(milliseconds: 500));
      expect(find.text('Your rating: 9.0'), findsOneWidget);
      hold.complete();
      await tester.pumpAndSettle();
      expect(find.text('Your rating: 8.0'), findsWidgets);
      expect(find.text('Your rating: 9.0'), findsNothing);
      expect(find.text('The rating wasn\'t saved. Try again.'), findsOneWidget);
    });

    testWidgets('keeps a successful rating and sends it with no aspects below 8.0',
        (tester) async {
      final server = FilmServer();
      await pumpFilm(tester, server);
      expect(find.byKey(const Key('film.myRating')), findsNothing);
      await rateTo(tester, steps: 1);
      await tester.pumpAndSettle();
      expect(find.text('Your rating: 7.5'), findsWidgets);
      expect(server.ratings[7], 7.5);
      final body = server.adapter.requests
          .lastWhere((r) => r.method == 'POST' && r.uri.path == '/ratings')
          .data as String;
      expect(jsonDecode(body), {'movie_id': 7, 'score': 7.5, 'liked_aspects': <String>[]});
      expect(find.text('The rating wasn\'t saved. Try again.'), findsNothing);
    });

    testWidgets('while a rating saves, Rate says so inside, stays enabled and ignores a press',
        (tester) async {
      final server = FilmServer();
      final hold = Completer<void>();
      server.holdRate = hold;
      await pumpFilm(tester, server);
      await rateTo(tester, steps: 1);
      await tester.pump(const Duration(milliseconds: 500));
      expect(find.text('Saving…'), findsOneWidget);
      final button = find.byKey(const Key('film.rate'));
      expect(tester.widget<ButtonStyleButton>(button).onPressed, isNotNull);
      await tester.tap(button);
      await tester.pump(const Duration(milliseconds: 500));
      expect(find.text('Rate Film 7'), findsNothing);
      hold.complete();
      await tester.pumpAndSettle();
      expect(find.text('Saving…'), findsNothing);
    });

    testWidgets('saves to the watchlist at once', (tester) async {
      final server = FilmServer();
      await pumpFilm(tester, server);
      await tester.tap(find.byKey(const Key('film.save')));
      await tester.pump();
      expect(find.text('Saved'), findsOneWidget);
      await tester.pumpAndSettle();
      expect(server.saved, [7]);
      expect(find.text('Saved'), findsOneWidget);
    });
  });

  group('helpers', () {
    test('comparedTraits leaves out the reasons why you shows, then the film\'s strongest', () {
      final d = MovieDetail.fromJson(detail(7,
          named: ['humor', 'pacing'],
          traits: scores({'humor': 99, 'pacing': 98, 'action': 90, 'romance': 80, 'mystery': 10})));
      final picked = comparedTraits(d);
      expect(picked, hasLength(6));
      expect(picked.take(2), ['action', 'romance']);
      expect(picked, isNot(contains('humor')));
      expect(picked, isNot(contains('pacing')));
      expect(picked, isNot(contains('mystery')));
      // Ties keep the traits.json order.
      expect(picked.skip(2), ['psychological_complexity', 'plot_twist', 'character_depth', 'emotional_intensity']);
    });

    test('axisPositions puts each dot at its value, pushed apart only when closer than the gap',
        () {
      expect(axisPositions(20, 80, 200), (you: 40.0, film: 160.0));
      final close = axisPositions(50, 52, 200);
      expect(close.film - close.you, dotGap);
      expect((close.you + close.film) / 2, closeTo(102, 0.001));
      final reversed = axisPositions(80, 20, 200);
      expect(reversed.you, 160.0);
      final edge = axisPositions(0, 1, 200);
      expect(edge.you, 0);
      expect(edge.film, dotGap);
    });
  });
}
