/// App-wide Riverpod providers: auth, the API client, the language and the signed-in user.
/// main.dart overrides [authClientProvider] and [noticeMemoryProvider] with the real
/// implementations; widget tests override them with fakes.
library;

import 'dart:ui' show PlatformDispatcher;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../auth/auth_client.dart';
import '../config.dart';
import '../data/api_client.dart';
import '../data/models.dart';
import '../i18n/i18n.dart';

/// For ProviderScope: no automatic retries. A failed request shows its error with a "Try
/// again" button (ApiException.retryable), as on the web; Riverpod's default would retry in
/// the background and hide the failure for seconds.
Duration? noRetry(int retryCount, Object error) => null;

/// Null when sign-in is not configured (no Supabase URL or key in the build).
final authClientProvider = Provider<AuthClient?>((ref) => null);

/// The current session: the restored one first, then every change.
final sessionProvider = StreamProvider<Session?>((ref) async* {
  final auth = ref.watch(authClientProvider);
  if (auth == null) {
    yield null;
    return;
  }
  yield auth.currentSession;
  yield* auth.changes;
});

/// The session right now, without waiting for the stream's first event.
Session? currentSession(Ref ref) =>
    ref.read(sessionProvider).value ?? ref.read(authClientProvider)?.currentSession;

final apiClientProvider = Provider<ApiClient>((ref) {
  final client = ApiClient(baseUrl: apiBaseUrl);
  client.accessToken = currentSession(ref)?.accessToken;
  ref.listen(sessionProvider, (_, next) => client.accessToken = next.value?.accessToken);
  return client;
});

/// The interface language. The device locale for now; the profile screen will let the
/// user choose (web: the language menu).
final langProvider = Provider<Lang>((ref) => langForLocale(PlatformDispatcher.instance.locale));

final stringsProvider = Provider<Strings>((ref) => Strings(ref.watch(langProvider)));

/// The signed-in user's id, from the restored session until the stream's first event, so
/// it does not flip null -> id at start-up (which would fetch /me twice).
final userIdProvider = Provider<String?>(
  (ref) => switch (ref.watch(sessionProvider)) {
    AsyncData(:final value) => value?.userId,
    _ => ref.read(authClientProvider)?.currentSession?.userId,
  },
);

/// GET /me for the signed-in user; fetched again when the user changes. Signed out there
/// is no request: the call would only come back 401.
final meProvider = FutureProvider<Me>((ref) async {
  if (ref.watch(userIdProvider) == null) throw const ApiException(401, 'signed out');
  return ref.watch(apiClientProvider).me();
});

/// Remembers that this phone has seen a user accept the data notice, so it is not asked
/// for again while /me loads (web: localStorage `mm.dataNotice.v1.<userId>`).
abstract interface class NoticeMemory {
  bool accepted(String userId);
  Future<void> remember(String userId);
}

class PrefsNoticeMemory implements NoticeMemory {
  PrefsNoticeMemory(this._prefs);

  static Future<PrefsNoticeMemory> load() async => PrefsNoticeMemory(
        await SharedPreferencesWithCache.create(
          cacheOptions: const SharedPreferencesWithCacheOptions(),
        ),
      );

  static const _prefix = 'mm.dataNotice.v1.';
  final SharedPreferencesWithCache _prefs;

  @override
  bool accepted(String userId) => _prefs.getString(_prefix + userId) == 'accepted';

  @override
  Future<void> remember(String userId) => _prefs.setString(_prefix + userId, 'accepted');
}

class MemoryNoticeMemory implements NoticeMemory {
  final _accepted = <String>{};

  @override
  bool accepted(String userId) => _accepted.contains(userId);

  @override
  Future<void> remember(String userId) async => _accepted.add(userId);
}

final noticeMemoryProvider = Provider<NoticeMemory>((ref) => MemoryNoticeMemory());
