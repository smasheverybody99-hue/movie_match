// Profile and About (web: pages/Profile.test.tsx): the language, sign out, delete account
// with its confirmation, and the TMDB attribution.
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/data/local_store.dart';
import 'package:movie_match/data/models.dart';
import 'package:movie_match/platform.dart';
import 'package:movie_match/screens/profile_screen.dart';
import 'package:movie_match/state/app_state.dart';
import 'package:movie_match/theme/tokens.dart';

import 'support/fakes.dart';

class ProfileServer {
  int deleteStatus = 204;
  late final adapter = FakeAdapter((o) {
    if (o.method == 'DELETE' && o.uri.path == '/me') {
      return deleteStatus == 204
          ? ResponseBody.fromString('', 204)
          : jsonBody({'detail': 'down'}, deleteStatus);
    }
    return jsonBody({'detail': 'not found'}, 404);
  });

  List<String> get calls => [for (final r in adapter.requests) '${r.method} ${r.uri.path}'];
}

Future<FakeAuthClient> pumpProfile(
  WidgetTester tester, {
  ProfileServer? server,
  MemoryLocalStore? store,
  List<String>? opened,
}) async {
  final auth = FakeAuthClient(session: testSession);
  final router = GoRouter(routes: [
    GoRoute(path: '/', builder: (context, state) => const ProfileScreen()),
  ]);
  addTearDown(router.dispose);
  await tester.pumpWidget(ProviderScope(
    retry: noRetry,
    overrides: [
      authClientProvider.overrideWithValue(auth),
      apiClientProvider.overrideWithValue(fakeApi((server ?? ProfileServer()).adapter)),
      localStoreProvider.overrideWithValue(store ?? MemoryLocalStore()),
      if (opened != null)
        linkOpenerProvider.overrideWithValue((url) async {
          opened.add(url);
          return true;
        }),
    ],
    child: MaterialApp.router(theme: buildTheme(), routerConfig: router),
  ));
  await tester.pumpAndSettle();
  return auth;
}

ChoiceChip chip(WidgetTester tester, Lang lang) =>
    tester.widget<ChoiceChip>(find.byKey(Key('profile.lang.${lang.name}')));

void main() {
  testWidgets('offers English, O\'zbek and Русский in that order, the current one chosen',
      (tester) async {
    await pumpProfile(tester);
    final xs = [
      for (final l in Lang.values) tester.getTopLeft(find.byKey(Key('profile.lang.${l.name}'))).dx,
    ];
    expect(xs, orderedEquals([...xs]..sort()));
    expect(find.text('English'), findsOneWidget);
    expect(find.text("O'zbek"), findsOneWidget);
    expect(find.text('Русский'), findsOneWidget);
    expect(chip(tester, Lang.en).selected, isTrue);
    expect(find.text('tester@gmail.com'), findsOneWidget);
  });

  testWidgets('switches the interface and remembers the choice on the phone', (tester) async {
    final store = MemoryLocalStore();
    await pumpProfile(tester, store: store);
    await tester.tap(find.text("O'zbek"));
    await tester.pumpAndSettle();
    expect(find.text('Profil'), findsWidgets);
    expect(chip(tester, Lang.uz).selected, isTrue);
    expect(store.values['mm.lang'], 'uz');
    // The language names stay the same in Uzbek.
    expect(find.text('English'), findsOneWidget);
    expect(find.text('Русский'), findsOneWidget);
  });

  testWidgets('a choice made earlier is used from the start', (tester) async {
    final store = MemoryLocalStore();
    await store.write('mm.lang', 'ru');
    await pumpProfile(tester, store: store);
    expect(chip(tester, Lang.ru).selected, isTrue);
    expect(find.text('Профиль'), findsWidgets);
  });

  testWidgets('Sign out signs out', (tester) async {
    final auth = await pumpProfile(tester);
    await tester.tap(find.text('Sign out'));
    await tester.pumpAndSettle();
    expect(auth.calls, ['signOut']);
  });

  testWidgets('Delete account asks first; Cancel deletes nothing', (tester) async {
    final server = ProfileServer();
    final auth = await pumpProfile(tester, server: server);
    await tester.tap(find.text('Delete account'));
    await tester.pumpAndSettle();
    expect(find.textContaining('This can\'t be undone.'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(server.calls, isEmpty);
    expect(auth.calls, isEmpty);
  });

  testWidgets('Yes, delete deletes the account, then signs out', (tester) async {
    final server = ProfileServer();
    final auth = await pumpProfile(tester, server: server);
    await tester.tap(find.text('Delete account'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('profile.deleteYes')));
    await tester.pumpAndSettle();
    expect(server.calls, ['DELETE /me']);
    expect(auth.calls, ['signOut']);
  });

  testWidgets('a failed delete says so and keeps the user signed in', (tester) async {
    final server = ProfileServer()..deleteStatus = 503;
    final auth = await pumpProfile(tester, server: server);
    await tester.tap(find.text('Delete account'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('profile.deleteYes')));
    await tester.pumpAndSettle();
    expect(find.text("Couldn't delete the account. Try again."), findsOneWidget);
    expect(auth.calls, isEmpty);
  });

  testWidgets('About: the TMDB attribution, and its link opens TMDB', (tester) async {
    final opened = <String>[];
    await pumpProfile(tester, opened: opened);
    expect(
        find.text('This product uses the TMDB API but is not endorsed or certified by TMDB.'),
        findsOneWidget);
    await tester.ensureVisible(find.byKey(const Key('about.tmdb')));
    await tester.tap(find.byKey(const Key('about.tmdb')));
    await tester.pump();
    expect(opened, ['https://www.themoviedb.org/']);
  });

  for (final scale in [1.0, 1.3, 2.0]) {
    testWidgets('nothing is cut off on a small phone at text size $scale', (tester) async {
      tester.view.physicalSize = const Size(360, 640);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      tester.platformDispatcher.textScaleFactorTestValue = scale;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await pumpProfile(tester);
      expect(tester.takeException(), isNull);
      await tester.tap(find.text('Delete account'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }
}
