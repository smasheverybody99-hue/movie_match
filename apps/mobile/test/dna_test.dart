// Movie DNA (web: pages/Dna.test.tsx, components/DnaFlower.test.tsx): its states, the
// sentence, the chart, the stats, Numbers, sharing, and the chart's geometry.
import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/data/models.dart';
import 'package:movie_match/data/traits.dart';
import 'package:movie_match/i18n/i18n.dart';
import 'package:movie_match/screens/dna_screen.dart';
import 'package:movie_match/platform.dart';
import 'package:movie_match/state/app_state.dart';
import 'package:movie_match/theme/tokens.dart';
import 'package:movie_match/widgets/dna_flower.dart';

import 'support/fakes.dart';

/// Every trait at 30, with humor 90, pacing 85, mystery 80 the strongest.
Map<String, int> taste() => {
      for (final k in traitKeys) k: 30,
      'humor': 90,
      'pacing': 85,
      'mystery': 80,
      'darkness': 60,
    };

Map<String, Object?> dnaJson({
  Map<String, int>? scores,
  int count = 14,
  int needed = 0,
  double? average = 7.5,
  String? genre = 'Crime',
  String? summary,
}) =>
    {
      'scores': scores ?? taste(),
      'summary': summary,
      'rating_count': count,
      'ratings_needed': needed,
      'average_rating': average,
      'top_genre': genre,
    };

class DnaServer {
  FutureOr<ResponseBody> Function()? answer;
  Map<String, Object?> body = dnaJson();
  late final adapter = FakeAdapter((o) {
    if (o.uri.path != '/me/dna') return jsonBody({'detail': 'not found'}, 404);
    return answer?.call() ?? jsonBody(body);
  });
}

Future<void> pumpDna(
  WidgetTester tester,
  DnaServer server, {
  Lang lang = Lang.en,
  bool settle = true,
  Sharer? sharer,
}) async {
  tester.view.physicalSize = const Size(400, 1400);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  final router = GoRouter(routes: [
    GoRoute(path: '/', builder: (context, state) => const DnaScreen()),
    GoRoute(path: '/onboarding', builder: (context, state) => const Scaffold(body: Text('ONBOARDING'))),
    GoRoute(path: '/search', builder: (context, state) => const Scaffold(body: Text('SEARCH'))),
  ]);
  addTearDown(router.dispose);
  await tester.pumpWidget(ProviderScope(
    retry: noRetry,
    overrides: [
      authClientProvider.overrideWithValue(FakeAuthClient(session: testSession)),
      apiClientProvider.overrideWithValue(fakeApi(server.adapter)),
      langProvider.overrideWithValue(lang),
      if (sharer != null) sharerProvider.overrideWithValue(sharer),
    ],
    child: MaterialApp.router(theme: buildTheme(), routerConfig: router),
  ));
  if (settle) await tester.pumpAndSettle();
}

void main() {
  testWidgets('loading: the page\'s shape', (tester) async {
    final server = DnaServer();
    final answer = Completer<ResponseBody>();
    server.answer = () => answer.future;
    await pumpDna(tester, server, settle: false);
    await tester.pump();
    expect(find.byKey(const Key('dna.skeleton')), findsOneWidget);
    answer.complete(jsonBody(dnaJson()));
    await tester.pumpAndSettle();
  });

  testWidgets('below 10 ratings: "rate more", not empty bars', (tester) async {
    final server = DnaServer()..body = dnaJson(count: 7, needed: 3, scores: {});
    await pumpDna(tester, server);
    expect(find.text('Rate 3 more films to unlock your Movie DNA.'), findsOneWidget);
    expect(find.byKey(const Key('dna.flower')), findsNothing);
    await tester.tap(find.text('Rate films'));
    await tester.pumpAndSettle();
    expect(find.text('ONBOARDING'), findsOneWidget);
  });

  testWidgets('with 10 ratings but no liked film: what is missing, not empty bars',
      (tester) async {
    final server = DnaServer()..body = dnaJson(scores: {});
    await pumpDna(tester, server);
    expect(find.textContaining('No liked films yet'), findsOneWidget);
    await tester.tap(find.text('Rate films'));
    await tester.pumpAndSettle();
    expect(find.text('SEARCH'), findsOneWidget);
  });

  testWidgets('error: says so, and Try again asks again', (tester) async {
    final server = DnaServer();
    server.answer = () => jsonBody({'detail': 'down'}, 503);
    await pumpDna(tester, server);
    expect(find.text("Couldn't load your Movie DNA. Check your connection and try again."),
        findsOneWidget);
    server.answer = null;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('dna.flower')), findsOneWidget);
  });

  testWidgets('content: the sentence, the chart, the stats', (tester) async {
    await pumpDna(tester, DnaServer());
    expect(find.text('“You prefer films strong in Humor, Pace and Mystery.”'), findsOneWidget);
    expect(tester.getSemantics(find.byKey(const Key('dna.flower'))).label,
        'Movie DNA chart. Strongest: Humor 90, Pace 85, Mystery 80.');
    expect(find.text('14'), findsOneWidget);
    expect(find.text('7.5'), findsOneWidget);
    expect(find.text('Crime'), findsOneWidget);
  });

  testWidgets('the exact values are under Numbers, closed until opened, strongest first',
      (tester) async {
    await pumpDna(tester, DnaServer());
    expect(find.byKey(const Key('dna.bar.humor')), findsNothing);
    await tester.tap(find.text('Numbers'));
    await tester.pumpAndSettle();
    for (final k in traitKeys) {
      expect(find.byKey(Key('dna.bar.$k')), findsOneWidget, reason: k);
    }
    final ys = [
      for (final k in ['humor', 'pacing', 'mystery', 'darkness', 'psychological_complexity'])
        tester.getTopLeft(find.byKey(Key('dna.bar.$k'))).dy,
    ];
    expect(ys, orderedEquals([...ys]..sort()));
    expect(tester.getSemantics(find.byKey(const Key('dna.bar.humor'))).label, 'Humor: 90');
  });

  testWidgets('in Russian: traits in lower case in the sentence, a decimal comma, the genre',
      (tester) async {
    await pumpDna(tester, DnaServer(), lang: Lang.ru);
    final summary = tester.widget<Text>(find.byKey(const Key('dna.summary'))).data!;
    final s = Strings(Lang.ru);
    expect(summary, contains(s.t('trait.humor').toLowerCase()));
    expect(find.text('7,5'), findsOneWidget);
    expect(find.text(s.t('genre.crime')), findsOneWidget);
  });

  testWidgets('prefers the API\'s summary when there is one', (tester) async {
    final server = DnaServer()..body = dnaJson(summary: 'A sentence from the server.');
    await pumpDna(tester, server);
    expect(find.text('“A sentence from the server.”'), findsOneWidget);
  });

  testWidgets('Share sends the sentence and the five strongest', (tester) async {
    final shared = <String>[];
    await pumpDna(tester, DnaServer(), sharer: (text) async {
      shared.add(text);
      return ShareOutcome.shared;
    });
    await tester.tap(find.byTooltip('Share'));
    await tester.pumpAndSettle();
    expect(shared, [
      'You prefer films strong in Humor, Pace and Mystery. '
          'My Movie DNA: Humor 90, Pace 85, Mystery 80, ${Strings(Lang.en).t('trait.darkness')} 60, '
          '${Strings(Lang.en).t('trait.psychological_complexity')} 30.',
    ]);
    expect(find.byType(SnackBar), findsNothing);
  });

  testWidgets('without a share sheet it copies, and says so; a failure says so too',
      (tester) async {
    var outcome = ShareOutcome.copied;
    await pumpDna(tester, DnaServer(), sharer: (_) async => outcome);
    await tester.tap(find.byTooltip('Share'));
    await tester.pumpAndSettle();
    expect(find.text('Copied'), findsOneWidget);
    outcome = ShareOutcome.failed;
    await tester.tap(find.byTooltip('Share'));
    await tester.pumpAndSettle();
    expect(find.text("Couldn't share. Copy the text by hand."), findsOneWidget);
  });

  testWidgets('the real sharer copies where there is no share sheet (tests)', (tester) async {
    String? copied;
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform,
        (call) async {
      if (call.method == 'Clipboard.setData') copied = (call.arguments as Map)['text'] as String;
      return null;
    });
    addTearDown(() =>
        tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, null));
    // A real platform call: outside the test's fake clock.
    expect(await tester.runAsync(() => shareText('hello')), ShareOutcome.copied);
    expect(copied, 'hello');
  });

  group('chart geometry', () {
    test('length is linear in the value, from the inner circle to the 100 ring', () {
      expect(rayLength(0), 40);
      expect(rayLength(100), 170);
      expect(rayLength(50), 105);
      expect(rayLength(150), 170);
    });

    test('each trait keeps its angle: the first at 12 o\'clock, then clockwise', () {
      expect(rayAngle(0), closeTo(-1.5708, 0.0001));
      expect(rayAngle(7), closeTo(1.5708, 0.0001));
    });

    test('the three strongest fully lit, the rest by value but never below 0.4', () {
      expect(rayOpacity(10, strongest: true), 1);
      expect(rayOpacity(0, strongest: false), 0.4);
      expect(rayOpacity(100, strongest: false), closeTo(0.85, 0.0001));
      expect(strongestTraits(taste()), {'humor', 'pacing', 'mystery'});
    });

    test('a label of 12 characters or more goes on two lines at the space nearest the middle',
        () {
      expect(labelLines('Humor'), ['Humor']);
      expect(labelLines('Накал эмоций'), ['Накал', 'эмоций']);
      expect(labelLines('Psychological complexity'), ['Psychological', 'complexity']);
    });

    test('sortedTraits: strongest first, ties in vector order, unknown keys left out', () {
      final sorted = sortedTraits({'humor': 50, 'plot_twist': 50, 'nonsense': 99, 'action': 70});
      expect(sorted, [('action', 70), ('plot_twist', 50), ('humor', 50)]);
    });
  });

  for (final scale in [1.0, 1.3, 2.0]) {
    testWidgets('nothing is cut off on a small phone at text size $scale', (tester) async {
      await pumpDna(tester, DnaServer(), lang: Lang.ru);
      tester.view.physicalSize = const Size(360, 640);
      tester.platformDispatcher.textScaleFactorTestValue = scale;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      // Russian: the longest labels.
      await tester.scrollUntilVisible(find.byKey(const Key('dna.numbers')), 200,
          scrollable: find.byType(Scrollable).first);
      await tester.tap(find.byKey(const Key('dna.numbers')));
      await tester.pumpAndSettle();
      await tester.drag(find.byType(Scrollable).first, const Offset(0, -3000));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }
}
