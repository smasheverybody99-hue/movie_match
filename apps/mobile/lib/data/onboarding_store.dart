/// Onboarding progress that survives an app restart (FR-3: "a user who leaves mid-way
/// resumes where they were"). Mirrors apps/web/src/lib/onboardingStore.ts, under the same
/// key: ratings go to the server as they are given (through the rating queue,
/// rating_queue.dart); this keeps what the server does not know: the picks, the step, the
/// position. Kept per user, so two accounts on one phone do not share a half-done onboarding.
library;

import 'dart:convert';

import 'local_store.dart';
import 'models.dart';

class OnboardingProgress {
  const OnboardingProgress({
    this.step = OnboardingStep.pick,
    this.picks = const [],
    this.index = 0,
    this.offset = 0,
  });

  final OnboardingStep step;

  /// Films picked but not rated yet, in pick order.
  final List<Movie> picks;

  /// The film being rated: an index into [picks].
  final int index;

  /// Which page of onboarding films is showing ("none of these" moves it on).
  final int offset;

  OnboardingProgress copyWith({
    OnboardingStep? step,
    List<Movie>? picks,
    int? index,
    int? offset,
  }) =>
      OnboardingProgress(
        step: step ?? this.step,
        picks: picks ?? this.picks,
        index: index ?? this.index,
        offset: offset ?? this.offset,
      );

  Json toJson() => {
        'step': step.name,
        'picks': [for (final m in picks) m.toJson()],
        'index': index,
        'offset': offset,
      };

  /// Null for anything that is not a saved progress (a newer or broken value).
  static OnboardingProgress? fromJson(Object? value) {
    if (value is! Map<String, dynamic>) return null;
    final step = OnboardingStep.values.where((s) => s.name == value['step']).firstOrNull;
    final picks = value['picks'];
    final index = value['index'];
    final offset = value['offset'];
    if (step == null || picks is! List || index is! int || offset is! int) return null;
    try {
      return OnboardingProgress(
        step: step,
        picks: [for (final m in picks) Movie.fromJson(m as Json)],
        index: index,
        offset: offset,
      );
    } on Object {
      return null;
    }
  }
}

const _version = 1;
String _key(String userId) => 'mm.onboarding.v$_version.$userId';

OnboardingProgress loadProgress(LocalStore store, String userId) {
  final raw = store.read(_key(userId));
  if (raw == null) return const OnboardingProgress();
  try {
    return OnboardingProgress.fromJson(jsonDecode(raw)) ?? const OnboardingProgress();
  } on FormatException {
    return const OnboardingProgress();
  }
}

Future<void> saveProgress(LocalStore store, String userId, OnboardingProgress progress) =>
    store.write(_key(userId), jsonEncode(progress.toJson()));

Future<void> clearProgress(LocalStore store, String userId) => store.delete(_key(userId));
