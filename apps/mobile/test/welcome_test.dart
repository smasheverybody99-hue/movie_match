// Welcome (FR-1): sign-in buttons, the email link, and the states the web's Welcome has —
// not configured, busy, failed, sent.
import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/auth/auth_client.dart';
import 'package:movie_match/screens/welcome_screen.dart';

import 'support/fakes.dart';

Finder button(String text) => find.ancestor(of: find.text(text), matching: find.byWidgetPredicate(
    (w) => w is ButtonStyleButton));

bool enabled(WidgetTester tester, String text) =>
    tester.widget<ButtonStyleButton>(button(text)).onPressed != null;

void main() {
  testWidgets('not configured: says so and every button is off', (tester) async {
    await pumpWithFakes(tester, const WelcomeScreen());
    expect(find.byKey(const Key('welcome.notConfigured')), findsOneWidget);
    expect(enabled(tester, 'Continue with Google'), isFalse);
    expect(enabled(tester, 'Continue with Apple'), isFalse);
    expect(enabled(tester, 'Continue with email'), isFalse);
  });

  testWidgets('Google: calls the provider and is busy until it returns', (tester) async {
    final auth = FakeAuthClient()..hold = Completer<void>();
    await pumpWithFakes(tester, const WelcomeScreen(), auth: auth);
    expect(find.byKey(const Key('welcome.notConfigured')), findsNothing);

    await tester.tap(button('Continue with Google'));
    await tester.pump();
    expect(auth.calls, ['oauth:google']);
    expect(enabled(tester, 'Continue with Google'), isFalse);
    expect(enabled(tester, 'Continue with Apple'), isFalse);

    auth.hold!.complete();
    await tester.pump();
    expect(enabled(tester, 'Continue with Google'), isTrue);
    expect(find.byKey(const Key('welcome.error')), findsNothing);
  });

  testWidgets('a provider that is off says so', (tester) async {
    final auth = FakeAuthClient()
      ..failWith = const AuthFailure(AuthFailureKind.providerDisabled, 'not enabled');
    await pumpWithFakes(tester, const WelcomeScreen(), auth: auth);
    await tester.tap(button('Continue with Apple'));
    await tester.pump();
    expect(find.text("This sign-in method isn't switched on yet. Use another one."), findsOneWidget);
  });

  testWidgets('any other failure asks to check the connection', (tester) async {
    final auth = FakeAuthClient()..failWith = const AuthFailure(AuthFailureKind.failed, 'x');
    await pumpWithFakes(tester, const WelcomeScreen(), auth: auth);
    await tester.tap(button('Continue with Google'));
    await tester.pump();
    expect(find.text("Couldn't sign you in. Check your connection and try again."), findsOneWidget);
  });

  testWidgets('email: refuses a partial address, then sends the link', (tester) async {
    final auth = FakeAuthClient();
    await pumpWithFakes(tester, const WelcomeScreen(), auth: auth);
    await tester.tap(button('Continue with email'));
    await tester.pump();

    await tester.enterText(find.byKey(const Key('welcome.emailField')), 'tester@gmail');
    await tester.tap(button('Send me a sign-in link'));
    await tester.pump();
    expect(find.text('Enter a full email address, like you@example.com'), findsOneWidget);
    expect(auth.calls, isEmpty);

    await tester.enterText(find.byKey(const Key('welcome.emailField')), '  tester@gmail.com ');
    await tester.tap(button('Send me a sign-in link'));
    await tester.pump();
    expect(auth.calls, ['email:tester@gmail.com']);
    expect(find.text('We sent a link to tester@gmail.com. Open your inbox and tap it.'),
        findsOneWidget);
  });
}
