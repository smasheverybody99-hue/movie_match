// The feed (web: pages/Feed.test.tsx, components/Hero.test.tsx): its four states, the
// hero and the rows, the band, saving, "Not right?" and the alpha's shown / clicked events.
import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/data/models.dart';
import 'package:movie_match/i18n/i18n.dart';
import 'package:movie_match/screens/feed_screen.dart';
import 'package:movie_match/state/app_state.dart';
import 'package:movie_match/theme/tokens.dart';
import 'package:movie_match/widgets/hero.dart';
import 'package:movie_match/widgets/match_band.dart';

import 'support/fakes.dart';

Map<String, Object?> film(int id) => {
      'id': id,
      'title': 'Film $id',
      'release_date': '2010-05-01',
      'runtime_minutes': 100,
      'overview': 'About film $id.',
      'poster_path': null,
      'backdrop_path': null,
      'genres': ['Drama'],
    };

Map<String, Object?> rec(
  int id, {
  String? band,
  List<String> named = const [],
  String? side,
  String? explanation,
}) =>
    {
      'movie': film(id),
      'match': 80.0,
      'band': band,
      'named_traits': named,
      'trait_side': side,
      'explanation': explanation,
    };

Map<String, Object?> section(String key, List<Map<String, Object?>> items, {int? seed}) =>
    {'key': key, 'seed': seed == null ? null : film(seed), 'items': items};

Map<String, Object?> ok(List<Map<String, Object?>> sections) =>
    {'status': 'ok', 'ratings_needed': 0, 'sections': sections};

Map<String, Object?> notEnough(int needed) =>
    {'status': 'not_enough_data', 'ratings_needed': needed, 'sections': <Object>[]};

/// Films 1-8 in For you, 20-22 because you loved film 99, 30-31 under 90.
Map<String, Object?> standard() => ok([
      section('for_you', [for (var i = 1; i <= 8; i++) rec(i)]),
      section('because_you_loved', [for (var i = 20; i <= 22; i++) rec(i)], seed: 99),
      section('under_90', [rec(30), rec(31)]),
    ]);

class FeedServer {
  FeedServer([Map<String, Object?>? recs]) : recs = recs ?? standard();

  Map<String, Object?> recs;
  FutureOr<ResponseBody> Function()? recsAnswer;
  List<int> saved = [];
  int watchlistStatus = 200;
  int feedbackStatus = 204;
  final feedback = <Map<String, dynamic>>[];
  final events = <Map<String, dynamic>>[];
  late final adapter = FakeAdapter(handle);

  List<String> get paths => [for (final r in adapter.requests) '${r.method} ${r.uri.path}'];

  FutureOr<ResponseBody> handle(RequestOptions o) {
    final path = o.uri.path;
    if (path == '/recommendations') return recsAnswer?.call() ?? jsonBody(recs);
    if (path == '/watchlist' && o.method == 'GET') {
      return jsonBody([
        for (final id in saved)
          {
            'movie': film(id),
            'added_at': '2026-11-20T10:00:00Z',
            'watched_at': null,
            'match': null,
            'band': null,
          },
      ]);
    }
    if (path.startsWith('/watchlist')) {
      if (watchlistStatus != 200) return jsonBody({'detail': 'down'}, watchlistStatus);
      if (o.method == 'POST') {
        final id = (jsonDecode(o.data as String) as Map<String, dynamic>)['movie_id'] as int;
        saved = [...saved, id];
        return jsonBody({
          'movie': film(id),
          'added_at': '2026-11-24T10:00:00Z',
          'watched_at': null,
          'match': null,
          'band': null,
        }, 201);
      }
      final id = int.parse(path.split('/').last);
      saved = [...saved]..remove(id);
      return ResponseBody.fromString('', 204);
    }
    if (path == '/feedback') {
      feedback.add(jsonDecode(o.data as String) as Map<String, dynamic>);
      if (feedbackStatus != 204) return jsonBody({'detail': 'down'}, feedbackStatus);
      return ResponseBody.fromString('', 204);
    }
    if (path == '/events') {
      final list = (jsonDecode(o.data as String) as Map<String, dynamic>)['events'] as List;
      events.addAll(list.cast());
      return jsonBody({'recorded': list.length});
    }
    return jsonBody({'detail': 'not found'}, 404);
  }
}

Future<ProviderContainer> pumpFeed(
  WidgetTester tester,
  FeedServer server, {
  bool reduce = false,
  Lang lang = Lang.en,
  bool settle = true,
}) async {
  // Tall enough for every row to be built.
  tester.view.physicalSize = const Size(400, 2400);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  final router = GoRouter(routes: [
    GoRoute(path: '/', builder: (context, state) => const FeedScreen()),
    GoRoute(
        path: '/onboarding',
        builder: (context, state) => const Scaffold(body: Text('ONBOARDING'))),
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
      langProvider.overrideWithValue(lang),
    ],
    child: MaterialApp.router(
      theme: buildTheme(),
      routerConfig: router,
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(disableAnimations: reduce),
        child: child!,
      ),
    ),
  ));
  if (settle) await tester.pumpAndSettle();
  return ProviderScope.containerOf(tester.element(find.byType(MaterialApp)));
}

Finder card(int id) => find.byWidgetPredicate((w) => w is MovieCard && w.item.movie.id == id);
Finder inHero(Finder f) => find.descendant(of: find.byType(FeedHero), matching: f);
Finder inCard(int id, Finder f) => find.descendant(of: card(id), matching: f);

List<String> recorded(ProviderContainer c) => [
      for (final e in c.read(telemetryProvider).queued)
        if (e case RecommendationEvent(:final clicked, :final movieId, :final source))
          '${clicked ? 'clicked' : 'shown'}:${source.wire}:$movieId',
    ];

void main() {
  group('first load', () {
    testWidgets('spins and changes its words at 5 s and 15 s, the last about the server waking',
        (tester) async {
      final server = FeedServer();
      final answer = Completer<ResponseBody>();
      server.recsAnswer = () => answer.future;
      await pumpFeed(tester, server, settle: false);
      await tester.pump();
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Picking your films…'), findsOneWidget);
      await tester.pump(const Duration(seconds: 5));
      expect(find.text('Still looking…'), findsOneWidget);
      await tester.pump(const Duration(seconds: 10));
      expect(find.text('The server is waking up, just a moment…'), findsOneWidget);
      answer.complete(jsonBody(standard()));
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film 1')), findsOneWidget);
    });

    testWidgets('with animations off there is no spinner, only the words', (tester) async {
      final server = FeedServer();
      final answer = Completer<ResponseBody>();
      server.recsAnswer = () => answer.future;
      await pumpFeed(tester, server, settle: false, reduce: true);
      await tester.pump();
      expect(find.byType(CircularProgressIndicator), findsNothing);
      expect(find.text('Picking your films…'), findsOneWidget);
      answer.complete(jsonBody(standard()));
      await tester.pumpAndSettle();
    });

    testWidgets('speaks Uzbek too', (tester) async {
      final server = FeedServer();
      final answer = Completer<ResponseBody>();
      server.recsAnswer = () => answer.future;
      await pumpFeed(tester, server, settle: false, lang: Lang.uz);
      await tester.pump();
      expect(find.text('Filmlaringiz tanlanmoqda…'), findsOneWidget);
      answer.complete(jsonBody(standard()));
      await tester.pumpAndSettle();
    });
  });

  testWidgets('renders sections; For you continues after the hero\'s five, so nothing shows twice',
      (tester) async {
    await pumpFeed(tester, FeedServer());
    expect(inHero(find.text('Film 1')), findsOneWidget);
    for (final id in [1, 2, 3, 4, 5]) {
      expect(card(id), findsNothing, reason: 'film $id is in the hero');
    }
    for (final id in [6, 7, 8, 20, 21, 22, 30, 31]) {
      expect(card(id), findsOneWidget, reason: 'film $id');
    }
    expect(find.text('For you'), findsOneWidget);
    expect(find.text('Because you loved Film 99'), findsOneWidget);
    expect(find.text('Under 90 minutes'), findsOneWidget);
    expect(inCard(6, find.text('2010 · 100m')), findsOneWidget);
  });

  testWidgets('does not render a section that has no items', (tester) async {
    await pumpFeed(
        tester,
        FeedServer(ok([
          section('for_you', [for (var i = 1; i <= 7; i++) rec(i)]),
          section('under_90', []),
        ])));
    expect(find.text('For you'), findsOneWidget);
    expect(find.text('Under 90 minutes'), findsNothing);
  });

  testWidgets('shows the band, never the number: red only for strong, nothing for good',
      (tester) async {
    await pumpFeed(
        tester,
        FeedServer(ok([
          section('for_you', [
            for (var i = 1; i <= 5; i++) rec(i),
            rec(6, band: 'strong'),
            rec(7, band: 'good'),
          ]),
        ])));
    expect(inCard(6, find.text('Strong match')), findsOneWidget);
    expect(inCard(7, find.text('Strong match')), findsNothing);
    expect(find.textContaining('80'), findsNothing);
    final label = tester.getSemantics(inCard(6, find.byType(InkWell)).first);
    expect(label.label, 'Film 6, Strong match, 2010 · 100m');
  });

  testWidgets('puts the top five of For you in the hero and never asks for an explanation',
      (tester) async {
    final server = FeedServer();
    await pumpFeed(tester, server);
    for (var i = 2; i <= 5; i++) {
      await tester.tap(find.byKey(Key('hero.dot.${i - 1}')));
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film $i')), findsOneWidget);
    }
    expect(find.byKey(const Key('hero.dot.5')), findsNothing);
    expect(server.paths.where((p) => p.contains('explanation')), isEmpty);
  });

  testWidgets('with five or fewer in For you: all in the hero and no For you row',
      (tester) async {
    await pumpFeed(
        tester,
        FeedServer(ok([
          section('for_you', [rec(1), rec(2), rec(3)]),
          section('under_90', [rec(30)]),
        ])));
    expect(find.byType(FeedHero), findsOneWidget);
    expect(find.text('For you'), findsNothing);
    expect(card(30), findsOneWidget);
  });

  testWidgets('has no hero when For you is empty', (tester) async {
    await pumpFeed(
        tester,
        FeedServer(ok([
          section('for_you', []),
          section('under_90', [rec(30)]),
        ])));
    expect(find.byType(FeedHero), findsNothing);
    expect(card(30), findsOneWidget);
  });

  testWidgets('renders its empty state when nothing matches, with a way to search', (tester) async {
    await pumpFeed(tester, FeedServer(ok([section('for_you', [])])));
    expect(find.text('No recommendations for you yet. Rate a few more films.'), findsOneWidget);
    await tester.tap(find.text('Search films'));
    await tester.pumpAndSettle();
    expect(find.text('SEARCH'), findsOneWidget);
  });

  testWidgets('asks for more ratings below 10, with a way back to onboarding', (tester) async {
    await pumpFeed(tester, FeedServer(notEnough(4)));
    expect(find.text('Rate 4 more films to get recommendations.'), findsOneWidget);
    await tester.tap(find.text('Keep rating'));
    await tester.pumpAndSettle();
    expect(find.text('ONBOARDING'), findsOneWidget);
  });

  testWidgets('sends a user with no ratings to onboarding', (tester) async {
    await pumpFeed(tester, FeedServer(notEnough(10)));
    expect(find.text('ONBOARDING'), findsOneWidget);
  });

  testWidgets('waits for the fresh feed instead of acting on a cached "rate 10 more"',
      (tester) async {
    final server = FeedServer(notEnough(10));
    final c = await pumpFeed(tester, server);
    expect(find.text('ONBOARDING'), findsOneWidget);
    // Back from onboarding: the cached answer says 10 more, the fresh one has the feed.
    server.recs = standard();
    final answer = Completer<ResponseBody>();
    server.recsAnswer = () => answer.future;
    c.invalidate(recommendationsProvider);
    GoRouter.of(tester.element(find.text('ONBOARDING'))).go('/');
    await tester.pump();
    await tester.pump();
    expect(find.text('Picking your films…'), findsOneWidget);
    answer.complete(jsonBody(standard()));
    await tester.pumpAndSettle();
    expect(find.text('ONBOARDING'), findsNothing);
    expect(inHero(find.text('Film 1')), findsOneWidget);
  });

  testWidgets('renders its error state with a retry that fetches again', (tester) async {
    final server = FeedServer();
    server.recsAnswer = () => jsonBody({'detail': 'down'}, 503);
    await pumpFeed(tester, server);
    expect(
        find.text('Couldn\'t load recommendations. Check your connection and try again.'),
        findsOneWidget);
    server.recsAnswer = null;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(inHero(find.text('Film 1')), findsOneWidget);
  });

  testWidgets('uses the interface language for the titles and for the request', (tester) async {
    final server = FeedServer();
    await pumpFeed(tester, server, lang: Lang.uz);
    expect(find.text('Siz uchun'), findsOneWidget);
    expect(find.text('Film 99 yoqqani uchun'), findsOneWidget);
    final request = server.adapter.requests.firstWhere((r) => r.uri.path == '/recommendations');
    expect(request.uri.queryParameters['lang'], 'uz');
  });

  testWidgets('puts a neutral icon before each row\'s title', (tester) async {
    await pumpFeed(tester, FeedServer());
    expect(find.byIcon(Icons.auto_awesome), findsWidgets);
    expect(find.byIcon(Icons.favorite_border), findsOneWidget);
    expect(find.byIcon(Icons.timer_outlined), findsOneWidget);
  });

  for (final scale in [1.0, 1.3, 2.0]) {
    testWidgets('nothing is cut off on a small phone at text size $scale', (tester) async {
      await pumpFeed(
          tester,
          FeedServer(ok([
            section('for_you', [
              for (var i = 1; i <= 8; i++)
                rec(i,
                    band: 'strong',
                    named: ['humor', 'pacing', 'mystery'],
                    side: 'reason',
                    explanation: 'A long cached sentence about why this film suits you, long '
                        'enough to wrap more than twice on a phone.'),
            ]),
            section('under_90', [rec(30), rec(31)]),
          ])));
      tester.view.physicalSize = const Size(360, 640);
      tester.platformDispatcher.textScaleFactorTestValue = scale;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.drag(find.byType(ListView).first, const Offset(0, -2000));
      await tester.pumpAndSettle();
      expect(card(30), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  group('hero', () {
    testWidgets('rotates every 7 s', (tester) async {
      await pumpFeed(tester, FeedServer());
      await tester.pump(const Duration(seconds: 6));
      expect(inHero(find.text('Film 1')), findsOneWidget);
      await tester.pump(const Duration(seconds: 1));
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film 2')), findsOneWidget);
    });

    testWidgets('a finger on it holds it, so the slide cannot change under a tap',
        (tester) async {
      await pumpFeed(tester, FeedServer());
      final finger = await tester.startGesture(tester.getCenter(find.byType(FeedHero)));
      await tester.pump(const Duration(seconds: 10));
      expect(inHero(find.text('Film 1')), findsOneWidget);
      await finger.up();
      await tester.pump(const Duration(seconds: 6));
      expect(inHero(find.text('Film 1')), findsOneWidget);
      await tester.pump(const Duration(seconds: 1));
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film 2')), findsOneWidget);
    });

    testWidgets('a swipe moves it and stops the rotation', (tester) async {
      await pumpFeed(tester, FeedServer());
      await tester.fling(find.byType(PageView), const Offset(-300, 0), 1000);
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film 2')), findsOneWidget);
      await tester.pump(const Duration(seconds: 15));
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film 2')), findsOneWidget);
    });

    testWidgets('prev / next and the dots move it, wrapping at both ends', (tester) async {
      await pumpFeed(tester, FeedServer());
      await tester.tap(find.byTooltip('Previous film'));
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film 5')), findsOneWidget);
      await tester.tap(find.byTooltip('Next film'));
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film 1')), findsOneWidget);
      await tester.tap(find.byKey(const Key('hero.dot.2')));
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film 3')), findsOneWidget);
      // Steering by hand stopped it.
      await tester.pump(const Duration(seconds: 15));
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film 3')), findsOneWidget);
    });

    testWidgets('holds after Pause, and Play starts it again', (tester) async {
      await pumpFeed(tester, FeedServer());
      await tester.tap(find.byTooltip('Pause rotation'));
      await tester.pump(const Duration(seconds: 10));
      expect(inHero(find.text('Film 1')), findsOneWidget);
      await tester.tap(find.byTooltip('Resume rotation'));
      await tester.pump(const Duration(seconds: 7));
      await tester.pumpAndSettle();
      expect(inHero(find.text('Film 2')), findsOneWidget);
    });

    testWidgets('with animations off: never moves on its own, and has no Pause', (tester) async {
      await pumpFeed(tester, FeedServer(), reduce: true);
      await tester.pump(const Duration(seconds: 15));
      expect(inHero(find.text('Film 1')), findsOneWidget);
      expect(find.byTooltip('Pause rotation'), findsNothing);
      await tester.tap(find.byTooltip('Next film'));
      await tester.pump();
      expect(inHero(find.text('Film 2')), findsOneWidget);
    });

    testWidgets('with one film: no controls', (tester) async {
      await pumpFeed(tester, FeedServer(ok([section('for_you', [rec(1)])])));
      expect(inHero(find.text('Film 1')), findsOneWidget);
      expect(find.byTooltip('Next film'), findsNothing);
      expect(find.byKey(const Key('hero.dot.0')), findsNothing);
    });

    testWidgets('shows the cached sentence under a strong film\'s red kicker', (tester) async {
      await pumpFeed(
          tester,
          FeedServer(ok([
            section('for_you', [
              rec(1,
                  band: 'strong',
                  named: ['humor'],
                  side: 'reason',
                  explanation: 'A cached line about it.'),
            ]),
          ])));
      expect(inHero(find.text('A cached line about it.')), findsOneWidget);
      expect(inHero(find.text('STRONG MATCH')), findsOneWidget);
    });

    testWidgets('See why opens the film and is recorded as a click', (tester) async {
      final c = await pumpFeed(tester, FeedServer());
      await tester.tap(find.text('See why'));
      await tester.pumpAndSettle();
      expect(find.text('FILM 1'), findsOneWidget);
      expect(recorded(c), contains('clicked:for_you:1'));
    });
  });

  group('the sentence and its heading', () {
    final s = Strings(Lang.en);
    Recommendation item(Map<String, Object?> json) => Recommendation.fromJson(json);

    test('without a cached sentence: the free fallback from the named traits', () {
      expect(
        heroSentence(item(rec(1, named: ['humor', 'pacing'], side: 'reason')), s),
        'Where your taste is clearest, this film sits at your level: '
        '${s.t('trait.humor')}, ${s.t('trait.pacing')}.',
      );
    });

    test('states how a film differs when its traits fall on that side', () {
      expect(
        heroSentence(item(rec(1, named: ['humor'], side: 'difference')), s),
        'Where it differs from your taste: ${s.t('trait.humor')}.',
      );
    });

    test('with nothing named: no sentence at all; unknown names do not count', () {
      expect(heroSentence(item(rec(1, side: 'reason')), s), isNull);
      expect(heroSentence(item(rec(1, named: ['not_a_trait'], side: 'reason')), s), isNull);
    });

    testWidgets('a strong film\'s difference gets the neutral heading, never the red one',
        (tester) async {
      Future<String> heading(MatchBand? band, TraitSide? side) async {
        await pumpWithFakes(tester, Kicker(band: band, side: side));
        return tester.widget<Text>(find.byType(Text)).data!;
      }

      expect(await heading(MatchBand.strong, TraitSide.difference), 'HOW IT DIFFERS');
      expect(await heading(MatchBand.strong, TraitSide.reason), 'STRONG MATCH');
      expect(await heading(MatchBand.strong, null), 'STRONG MATCH');
      expect(await heading(MatchBand.good, TraitSide.reason), 'WHY IT SUITS YOU');
      expect(await heading(null, null), 'YOU AND THIS FILM');
    });
  });

  group('save', () {
    testWidgets('saves the shown film at once', (tester) async {
      final server = FeedServer();
      await pumpFeed(tester, server);
      await tester.tap(inHero(find.text('Save')));
      await tester.pump();
      expect(inHero(find.text('Saved')), findsOneWidget);
      await tester.pumpAndSettle();
      expect(server.paths, contains('POST /watchlist'));
      expect(server.saved, [1]);
      expect(inHero(find.text('Saved')), findsOneWidget);
    });

    testWidgets('takes off a film already on the list', (tester) async {
      final server = FeedServer()..saved = [1];
      await pumpFeed(tester, server);
      expect(inHero(find.text('Saved')), findsOneWidget);
      await tester.tap(inHero(find.text('Saved')));
      await tester.pumpAndSettle();
      expect(server.paths, contains('DELETE /watchlist/1'));
      expect(inHero(find.text('Save')), findsOneWidget);
    });

    testWidgets('says so when saving fails, and rolls the button back', (tester) async {
      final server = FeedServer()..watchlistStatus = 503;
      await pumpFeed(tester, server);
      await tester.tap(inHero(find.text('Save')));
      await tester.pumpAndSettle();
      expect(find.text('Your watchlist didn\'t change. Try again.'), findsOneWidget);
      expect(inHero(find.text('Save')), findsOneWidget);
    });
  });

  group('Not right?', () {
    testWidgets('takes the card out at once and sends the reason', (tester) async {
      final server = FeedServer();
      await pumpFeed(tester, server);
      await tester.tap(inCard(6, find.text('Not right?')));
      await tester.pumpAndSettle();
      expect(find.text('What\'s wrong with it?'), findsOneWidget);
      expect(find.text('I\'ve seen it'), findsOneWidget);
      expect(find.text('Too old'), findsOneWidget);
      await tester.tap(find.text('Not my genre'));
      await tester.pumpAndSettle();
      expect(card(6), findsNothing);
      expect(server.feedback, [
        {'movie_id': 6, 'source': 'for_you', 'reason': 'not_my_genre'},
      ]);
      expect(find.text('Thanks, noted. Film 6 is hidden for now.'), findsOneWidget);
    });

    testWidgets('"Just hide it" sends no reason; Cancel sends nothing', (tester) async {
      final server = FeedServer();
      await pumpFeed(tester, server);
      await tester.tap(inCard(20, find.text('Not right?')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      expect(card(20), findsOneWidget);
      expect(server.feedback, isEmpty);
      await tester.tap(inCard(20, find.text('Not right?')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Just hide it'));
      await tester.pumpAndSettle();
      expect(card(20), findsNothing);
      expect(server.feedback, [
        {'movie_id': 20, 'source': 'because_you_loved', 'reason': null},
      ]);
    });

    testWidgets('brings the card back and says so when the press does not arrive',
        (tester) async {
      final server = FeedServer()..feedbackStatus = 503;
      await pumpFeed(tester, server);
      await tester.tap(inCard(6, find.text('Not right?')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Other'));
      await tester.pumpAndSettle();
      expect(card(6), findsOneWidget);
      expect(find.text('Couldn\'t send that about Film 6. It\'s back — try again.'),
          findsOneWidget);
    });

    testWidgets('pull to refresh shows the engine\'s picks again, the hidden film included',
        (tester) async {
      final server = FeedServer();
      await pumpFeed(tester, server);
      await tester.tap(inCard(6, find.text('Not right?')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Just hide it'));
      await tester.pumpAndSettle();
      expect(card(6), findsNothing);
      // A quarter of the screen's height starts a refresh: 600 px on this tall test screen.
      await tester.fling(find.text('Under 90 minutes'), const Offset(0, 900), 1000);
      await tester.pumpAndSettle();
      expect(card(6), findsOneWidget);
      expect(server.paths.where((p) => p == 'GET /recommendations'), hasLength(2));
    });
  });

  group('alpha telemetry', () {
    testWidgets('a card in view for a second is shown once; one out of view is not',
        (tester) async {
      final server = FeedServer(ok([
        section('for_you', [for (var i = 1; i <= 16; i++) rec(i)]),
      ]));
      final c = await pumpFeed(tester, server);
      expect(recorded(c), isEmpty);
      await tester.pump(const Duration(milliseconds: 1100));
      final shown = recorded(c);
      expect(shown, containsAll(['shown:for_you:1', 'shown:for_you:6', 'shown:for_you:7']));
      // Film 16 is the 11th card of a row that shows two and a bit.
      expect(shown, isNot(contains('shown:for_you:16')));
      await tester.drag(find.byType(ListView).last, const Offset(-2000, 0));
      await tester.pumpAndSettle();
      await tester.pump(const Duration(milliseconds: 1100));
      expect(recorded(c), contains('shown:for_you:16'));
      expect(recorded(c).where((e) => e == 'shown:for_you:6'), hasLength(1));
    });

    testWidgets('a hero slide counts when it is the one on screen', (tester) async {
      final c = await pumpFeed(tester, FeedServer());
      await tester.pump(const Duration(milliseconds: 1100));
      expect(recorded(c), contains('shown:for_you:1'));
      expect(recorded(c), isNot(contains('shown:for_you:2')));
    });

    testWidgets('a tap on a card opens the film and is recorded as a click', (tester) async {
      final c = await pumpFeed(tester, FeedServer());
      await tester.tap(inCard(21, find.byType(InkWell)).first);
      await tester.pumpAndSettle();
      expect(find.text('FILM 21'), findsOneWidget);
      expect(recorded(c), contains('clicked:because_you_loved:21'));
    });
  });
}
