// The alpha's event queue (web: lib/telemetry.test.tsx): steps once per run, a batch at 20
// or after 10 s, a failed batch kept, a refused (422) one dropped. testWidgets for its fake
// clock: tester.pump moves time on.
import 'package:flutter_test/flutter_test.dart';
import 'package:movie_match/data/api_client.dart';
import 'package:movie_match/data/models.dart';
import 'package:movie_match/data/telemetry.dart';

final at = DateTime.utc(2026, 11, 24);
ClientEvent step(OnboardingStep s) => OnboardingStepEvent(at: at, step: s);
ClientEvent shown(int id) =>
    RecommendationEvent(clicked: false, at: at, movieId: id, source: EventSource.forYou);
ClientEvent clicked(int id) =>
    RecommendationEvent(clicked: true, at: at, movieId: id, source: EventSource.forYou);

void main() {
  testWidgets('a step and a shown card count once; clicks every time; sent after 10 s',
      (tester) async {
    final batches = <List<ClientEvent>>[];
    final t = Telemetry((events) async => (batches..add(events)).length);
    t
      ..track(step(OnboardingStep.pick))
      ..track(step(OnboardingStep.pick))
      ..track(shown(1))
      ..track(shown(1))
      ..track(clicked(1))
      ..track(clicked(1));
    expect(t.queued, hasLength(4));
    await tester.pump(const Duration(seconds: 9));
    expect(batches, isEmpty);
    await tester.pump(const Duration(seconds: 1));
    expect(batches.single, hasLength(4));
    expect(t.queued, isEmpty);
  });

  testWidgets('20 waiting go out at once', (tester) async {
    final batches = <List<ClientEvent>>[];
    final t = Telemetry((events) async => (batches..add(events)).length);
    for (var i = 0; i < flushAt; i++) {
      t.track(shown(i));
    }
    await tester.pump();
    expect(batches.single, hasLength(flushAt));
  });

  testWidgets('a batch that fails is kept for the next try; one refused as malformed is dropped',
      (tester) async {
    Object error = const ApiException(0, 'offline', retryable: true);
    final t = Telemetry((events) async => throw error);
    t.track(clicked(1));
    await tester.pump(flushEvery);
    expect(t.queued, hasLength(1));
    error = const ApiException(422, 'bad');
    await tester.pump(flushEvery);
    expect(t.queued, isEmpty);
  });

  test('closed (signed out) it records nothing', () {
    final t = Telemetry((events) async => events.length)..close();
    t.track(clicked(1));
    expect(t.queued, isEmpty);
  });
}
