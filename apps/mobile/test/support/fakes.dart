// Fakes for widget tests: an AuthClient the test drives, and an ApiClient whose Dio answers
// from a handler. No network, no Supabase.
import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/auth/auth_client.dart';
import 'package:movie_match/data/api_client.dart';
import 'package:movie_match/data/local_store.dart';
import 'package:movie_match/state/app_state.dart';
import 'package:movie_match/theme/tokens.dart';

const testSession = Session(accessToken: 'tok', userId: 'u1', email: 'tester@gmail.com');

class FakeAuthClient implements AuthClient {
  FakeAuthClient({Session? session}) : _current = session;

  Session? _current;
  final _changes = StreamController<Session?>.broadcast();
  final calls = <String>[];

  /// Set to make the next sign-in call fail with it.
  Object? failWith;

  /// Set to hold the next sign-in call open until completed.
  Completer<void>? hold;

  void emit(Session? session) {
    _current = session;
    _changes.add(session);
  }

  @override
  Session? get currentSession => _current;

  @override
  Stream<Session?> get changes => _changes.stream;

  Future<void> _call(String name) async {
    calls.add(name);
    if (hold != null) await hold!.future;
    final error = failWith;
    failWith = null;
    if (error != null) throw error;
  }

  @override
  Future<void> signInWithOAuth(AuthProvider provider) => _call('oauth:${provider.name}');

  @override
  Future<void> signInWithEmail(String email) => _call('email:$email');

  @override
  Future<void> signOut() async {
    calls.add('signOut');
    emit(null);
  }
}

typedef Handler = FutureOr<ResponseBody> Function(RequestOptions options);

class FakeAdapter implements HttpClientAdapter {
  FakeAdapter(this.handler);

  Handler handler;
  final requests = <RequestOptions>[];

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream,
      Future<void>? cancelFuture) async {
    requests.add(options);
    return handler(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody jsonBody(Object? body, [int status = 200]) => ResponseBody.fromString(
      jsonEncode(body),
      status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );

/// Timeouts off: a pending fake answer must not leave Dio's timer running after a test.
ApiClient fakeApi(FakeAdapter adapter) => ApiClient(
      baseUrl: 'https://api.test',
      dio: Dio()..httpClientAdapter = adapter,
      connectTimeout: Duration.zero,
      receiveTimeout: Duration.zero,
    );

Map<String, Object?> meJson({bool required = true, String? acceptedAt, int ratingCount = 0}) => {
      'id': 'u1',
      'created_at': '2026-11-20T10:00:00Z',
      'rating_count': ratingCount,
      'ratings_needed': ratingCount >= 10 ? 0 : 10 - ratingCount,
      'has_taste_profile': false,
      'taste_updated_at': null,
      'data_notice_required': required,
      'data_notice_accepted_at': acceptedAt,
    };

/// Pumps `child` inside the app theme with the given fakes.
Future<void> pumpWithFakes(
  WidgetTester tester,
  Widget child, {
  AuthClient? auth,
  ApiClient? api,
  NoticeMemory? memory,
  LocalStore? store,
}) =>
    tester.pumpWidget(ProviderScope(
      retry: noRetry,
      overrides: [
        authClientProvider.overrideWithValue(auth),
        if (api != null) apiClientProvider.overrideWithValue(api),
        if (memory != null) noticeMemoryProvider.overrideWithValue(memory),
        if (store != null) localStoreProvider.overrideWithValue(store),
      ],
      child: MaterialApp(theme: buildTheme(), home: child),
    ));
