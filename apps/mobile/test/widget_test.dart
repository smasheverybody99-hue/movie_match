// The whole app: signed out it opens on Welcome; a sign-in moves it to the feed, a sign-out
// back; a user with nothing rated lands in onboarding.
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:movie_match/main.dart';
import 'package:movie_match/state/app_state.dart';

import 'support/fakes.dart';

void main() {
  testWidgets('signed out it opens on Welcome; signing in goes home and back', (tester) async {
    final auth = FakeAuthClient();
    final api = fakeApi(FakeAdapter((o) => switch (o.uri.path) {
          '/me' => jsonBody(meJson(required: false, ratingCount: 10)),
          '/recommendations' => jsonBody({
              'status': 'ok',
              'ratings_needed': 0,
              'sections': [
                {
                  'key': 'under_90',
                  'seed': null,
                  'items': [
                    {
                      'movie': {'id': 1, 'title': 'Heat', 'genres': <String>[]},
                      'match': 80.0,
                      'band': null,
                      'named_traits': <String>[],
                      'trait_side': null,
                      'explanation': null,
                    },
                  ],
                },
              ],
            }),
          '/watchlist' => jsonBody(<Object>[]),
          _ => jsonBody({'recorded': 1}),
        }));
    await tester.pumpWidget(ProviderScope(
      retry: noRetry,
      overrides: [
        authClientProvider.overrideWithValue(auth),
        apiClientProvider.overrideWithValue(api),
      ],
      child: const MovieMatchApp(),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Continue with Google'), findsOneWidget);

    auth.emit(testSession);
    await tester.pumpAndSettle();
    expect(find.text('Continue with Google'), findsNothing);
    expect(find.text('Under 90 minutes'), findsOneWidget);

    await tester.tap(find.byTooltip('Profile'));
    await tester.pumpAndSettle();
    expect(find.text('tester@gmail.com'), findsOneWidget);
    await tester.tap(find.text('Sign out'));
    await tester.pumpAndSettle();
    expect(find.text('Continue with Google'), findsOneWidget);

    // About is public, from Welcome.
    await tester.tap(find.byKey(const Key('welcome.about')));
    await tester.pumpAndSettle();
    expect(find.textContaining('This product uses the TMDB API'), findsOneWidget);
  });

  testWidgets('signed in with nothing rated it goes to onboarding', (tester) async {
    final api = fakeApi(FakeAdapter((o) => switch (o.uri.path) {
          '/me' => jsonBody(meJson(required: false)),
          '/recommendations' => jsonBody(
              {'status': 'not_enough_data', 'ratings_needed': 10, 'sections': <Object>[]}),
          '/onboarding/films' || '/ratings' => jsonBody(<Object>[]),
          _ => jsonBody({'recorded': 1}),
        }));
    await tester.pumpWidget(ProviderScope(
      retry: noRetry,
      overrides: [
        authClientProvider.overrideWithValue(FakeAuthClient(session: testSession)),
        apiClientProvider.overrideWithValue(api),
      ],
      child: const MovieMatchApp(),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Which ones did you love?'), findsOneWidget);
  });

  testWidgets('the bottom bar moves between Home and Search; a film covers it', (tester) async {
    final film = {
      'id': 1,
      'title': 'Heat',
      'release_date': '1995-12-15',
      'runtime_minutes': 170,
      'genres': <String>[],
    };
    final api = fakeApi(FakeAdapter((o) => switch (o.uri.path) {
          '/me' => jsonBody(meJson(required: false, ratingCount: 12)),
          '/recommendations' => jsonBody({
              'status': 'ok',
              'ratings_needed': 0,
              'sections': [
                {'key': 'under_90', 'seed': null, 'items': <Object>[]},
              ],
            }),
          '/movies' => jsonBody([film]),
          '/watchlist' || '/ratings' => jsonBody(<Object>[]),
          _ => jsonBody({'detail': 'not found'}, 404),
        }));
    await tester.pumpWidget(ProviderScope(
      retry: noRetry,
      overrides: [
        authClientProvider.overrideWithValue(FakeAuthClient(session: testSession)),
        apiClientProvider.overrideWithValue(api),
      ],
      child: const MovieMatchApp(),
    ));
    await tester.pumpAndSettle();
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.text('No recommendations for you yet. Rate a few more films.'), findsOneWidget);

    await tester.tap(find.descendant(of: find.byType(NavigationBar), matching: find.text('Search')));
    await tester.pumpAndSettle();
    expect(find.text('Popular films'), findsOneWidget);

    await tester.tap(find.text('Heat').first);
    await tester.pumpAndSettle();
    expect(find.byType(NavigationBar), findsNothing, reason: 'the film page covers the bar');

    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.text('Popular films'), findsOneWidget);
    await tester.tap(find.descendant(of: find.byType(NavigationBar), matching: find.text('Home')));
    await tester.pumpAndSettle();
    expect(find.text('No recommendations for you yet. Rate a few more films.'), findsOneWidget);
  });

  testWidgets('the Assistant tab shows only while the server offers it, and goes when it stops',
      (tester) async {
    var enabled = true;
    final api = fakeApi(FakeAdapter((o) => switch (o.uri.path) {
          '/me' => jsonBody({...meJson(required: false, ratingCount: 12), 'assistant_enabled': enabled}),
          '/recommendations' => jsonBody({
              'status': 'ok',
              'ratings_needed': 0,
              'sections': [
                {'key': 'under_90', 'seed': null, 'items': <Object>[]},
              ],
            }),
          '/watchlist' || '/ratings' => jsonBody(<Object>[]),
          _ => jsonBody({'detail': 'not found'}, 404),
        }));
    await tester.pumpWidget(ProviderScope(
      retry: noRetry,
      overrides: [
        authClientProvider.overrideWithValue(FakeAuthClient(session: testSession)),
        apiClientProvider.overrideWithValue(api),
      ],
      child: const MovieMatchApp(),
    ));
    await tester.pumpAndSettle();
    Finder tab(String label) =>
        find.descendant(of: find.byType(NavigationBar), matching: find.text(label));
    expect(tab('Assistant'), findsOneWidget);
    final xs = [for (final l in ['Home', 'Search', 'Assistant', 'Movie DNA', 'Watchlist']) tester.getCenter(tab(l)).dx];
    expect(xs, orderedEquals([...xs]..sort()), reason: "the web's order");

    await tester.tap(tab('Assistant'));
    await tester.pumpAndSettle();
    expect(find.text('A dark thriller from the 90s'), findsOneWidget);

    // The server turns it off (TZ 1.38): the next /me takes the tab away, back to Home.
    enabled = false;
    ProviderScope.containerOf(tester.element(find.byType(NavigationBar))).invalidate(meProvider);
    await tester.pumpAndSettle();
    expect(tab('Assistant'), findsNothing);
    expect(find.text('No recommendations for you yet. Rate a few more films.'), findsOneWidget);
  });

  testWidgets('an API that does not say counts as off: no Assistant tab', (tester) async {
    final api = fakeApi(FakeAdapter((o) => switch (o.uri.path) {
          '/me' => jsonBody(meJson(required: false, ratingCount: 12)),
          '/recommendations' =>
            jsonBody({'status': 'ok', 'ratings_needed': 0, 'sections': <Object>[]}),
          _ => jsonBody(<Object>[]),
        }));
    await tester.pumpWidget(ProviderScope(
      retry: noRetry,
      overrides: [
        authClientProvider.overrideWithValue(FakeAuthClient(session: testSession)),
        apiClientProvider.overrideWithValue(api),
      ],
      child: const MovieMatchApp(),
    ));
    await tester.pumpAndSettle();
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.descendant(of: find.byType(NavigationBar), matching: find.text('Assistant')),
        findsNothing);
  });
}
