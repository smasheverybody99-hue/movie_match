// The data notice gate: loading, error, the notice itself, and content once accepted or
// not required (web: components/DataNotice.tsx).
import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/screens/data_notice.dart';
import 'package:movie_match/state/app_state.dart';

import 'support/fakes.dart';

const content = Text('the app', key: Key('content'));

void main() {
  testWidgets('loading: a spinner while /me loads', (tester) async {
    final pending = Completer<ResponseBody>();
    final api = fakeApi(FakeAdapter((_) => pending.future));
    await pumpWithFakes(tester, const DataNoticeGate(child: content),
        auth: FakeAuthClient(session: testSession), api: api);
    await tester.pump();
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.byKey(const Key('content')), findsNothing);
    pending.complete(jsonBody(meJson(required: false)));
    await tester.pumpAndSettle();
  });

  testWidgets('a phone that saw this user accept goes straight through while /me loads',
      (tester) async {
    final pending = Completer<ResponseBody>();
    final memory = MemoryNoticeMemory();
    await memory.remember('u1');
    await pumpWithFakes(tester, const DataNoticeGate(child: content),
        auth: FakeAuthClient(session: testSession),
        api: fakeApi(FakeAdapter((_) => pending.future)),
        memory: memory);
    await tester.pump();
    expect(find.byKey(const Key('content')), findsOneWidget);
    pending.complete(jsonBody(meJson(acceptedAt: '2026-11-21T09:00:00Z')));
    await tester.pumpAndSettle();
  });

  testWidgets('error: says so, and Try again asks /me again', (tester) async {
    var answer = jsonBody({'detail': 'down'}, 503);
    final adapter = FakeAdapter((_) => answer);
    await pumpWithFakes(tester, const DataNoticeGate(child: content),
        auth: FakeAuthClient(session: testSession), api: fakeApi(adapter));
    await tester.pumpAndSettle();
    expect(find.text("Couldn't load your account. Check your connection and try again."),
        findsOneWidget);

    answer = jsonBody(meJson(required: false));
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('content')), findsOneWidget);
    expect(adapter.requests.where((r) => r.path == '/me'), hasLength(2));
  });

  testWidgets('not required: content, no notice', (tester) async {
    await pumpWithFakes(tester, const DataNoticeGate(child: content),
        auth: FakeAuthClient(session: testSession),
        api: fakeApi(FakeAdapter((_) => jsonBody(meJson(required: false)))));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('content')), findsOneWidget);
    expect(find.text('Before you start'), findsNothing);
  });

  testWidgets('required: the notice; accepting saves it on the server and opens the app',
      (tester) async {
    var accepted = false;
    final memory = MemoryNoticeMemory();
    final adapter = FakeAdapter((o) {
      if (o.method == 'POST' && o.path == '/me/data-notice') {
        accepted = true;
        return ResponseBody.fromString('', 204);
      }
      return jsonBody(meJson(acceptedAt: accepted ? '2026-11-23T10:00:00Z' : null));
    });
    await pumpWithFakes(tester, const DataNoticeGate(child: content),
        auth: FakeAuthClient(session: testSession), api: fakeApi(adapter), memory: memory);
    await tester.pumpAndSettle();
    expect(find.text('Before you start'), findsOneWidget);
    expect(find.byKey(const Key('content')), findsNothing);

    await tester.tap(find.text('I agree, continue'));
    await tester.pumpAndSettle();
    expect(accepted, isTrue);
    expect(memory.accepted('u1'), isTrue);
    expect(find.byKey(const Key('content')), findsOneWidget);
  });

  testWidgets('a failed save says so and keeps the notice', (tester) async {
    final adapter = FakeAdapter((o) => o.method == 'POST'
        ? jsonBody({'detail': 'down'}, 500)
        : jsonBody(meJson()));
    await pumpWithFakes(tester, const DataNoticeGate(child: content),
        auth: FakeAuthClient(session: testSession), api: fakeApi(adapter));
    await tester.pumpAndSettle();
    await tester.tap(find.text('I agree, continue'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('notice.saveError')), findsOneWidget);
    expect(find.text('Before you start'), findsOneWidget);
  });

  testWidgets('declining signs out', (tester) async {
    final auth = FakeAuthClient(session: testSession);
    final adapter = FakeAdapter((_) => jsonBody(meJson()));
    await pumpWithFakes(tester, const DataNoticeGate(child: content),
        auth: auth, api: fakeApi(adapter));
    await tester.pumpAndSettle();
    final asked = adapter.requests.length;
    await tester.tap(find.text("I don't agree — sign out"));
    await tester.pumpAndSettle();
    expect(auth.calls, ['signOut']);
    expect(adapter.requests, hasLength(asked), reason: 'no /me once signed out');
  });
}
