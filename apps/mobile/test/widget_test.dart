// The whole app: signed out it opens on Welcome; a sign-in moves it to the feed, a sign-out
// back; a user with nothing rated lands in onboarding.
import 'package:flutter_riverpod/flutter_riverpod.dart';
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

    await tester.tap(find.byTooltip('Sign out'));
    await tester.pumpAndSettle();
    expect(find.text('Continue with Google'), findsOneWidget);
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
}
