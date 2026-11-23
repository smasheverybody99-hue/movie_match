/// The slice of Supabase Auth the app uses, behind a small interface so screens and tests
/// never touch the SDK. Mirrors apps/web/src/lib/supabase.ts: Supabase issues and refreshes
/// the access token (FR-1); the API only verifies it.
library;

import 'dart:async';

import 'package:supabase_flutter/supabase_flutter.dart' as sb;

import '../config.dart';

class Session {
  const Session({required this.accessToken, required this.userId, this.email});

  final String accessToken;
  final String userId;
  final String? email;
}

enum AuthProvider { google, apple }

enum AuthFailureKind { providerDisabled, failed }

/// Why a sign-in attempt failed, in terms a screen can word for a person.
class AuthFailure implements Exception {
  const AuthFailure(this.kind, this.message);

  final AuthFailureKind kind;
  final String message;

  /// Supabase answers "Unsupported provider: provider is not enabled" (400) for a provider
  /// that is not switched on in the dashboard.
  factory AuthFailure.from(Object error) {
    final message = error is sb.AuthException ? error.message : '$error';
    final disabled = RegExp('not enabled|unsupported provider', caseSensitive: false);
    return AuthFailure(
      disabled.hasMatch(message) ? AuthFailureKind.providerDisabled : AuthFailureKind.failed,
      message,
    );
  }

  @override
  String toString() => 'AuthFailure(${kind.name}): $message';
}

abstract interface class AuthClient {
  /// The session restored at start-up, or null signed out.
  Session? get currentSession;

  /// Every sign-in, sign-out and token refresh.
  Stream<Session?> get changes;

  /// Opens the provider in the browser; the session arrives on [changes] once the browser
  /// comes back through [authRedirectUrl].
  Future<void> signInWithOAuth(AuthProvider provider);

  /// Sends a sign-in link; opening it on the phone signs in.
  Future<void> signInWithEmail(String email);

  Future<void> signOut();
}

Session? _session(sb.Session? s) => s == null
    ? null
    : Session(accessToken: s.accessToken, userId: s.user.id, email: s.user.email);

class SupabaseAuthClient implements AuthClient {
  SupabaseAuthClient(this._auth);

  /// Initialises Supabase (it restores a saved session and listens for the redirect).
  /// Null when sign-in is not configured.
  static Future<SupabaseAuthClient?> start() async {
    if (!authConfigured) return null;
    // The anon key goes in as the publishable key: both are sent as `apikey`, and
    // supabase_flutter deprecates the `anonKey` parameter.
    final app = await sb.Supabase.initialize(url: supabaseUrl, publishableKey: supabaseAnonKey);
    return SupabaseAuthClient(app.client.auth);
  }

  final sb.GoTrueClient _auth;

  @override
  Session? get currentSession => _session(_auth.currentSession);

  @override
  Stream<Session?> get changes => _auth.onAuthStateChange.map((state) => _session(state.session));

  @override
  Future<void> signInWithOAuth(AuthProvider provider) async {
    try {
      await _auth.signInWithOAuth(
        provider == AuthProvider.google ? sb.OAuthProvider.google : sb.OAuthProvider.apple,
        redirectTo: authRedirectUrl,
        authScreenLaunchMode: sb.LaunchMode.externalApplication,
      );
    } on Object catch (e) {
      throw AuthFailure.from(e);
    }
  }

  @override
  Future<void> signInWithEmail(String email) async {
    try {
      await _auth.signInWithOtp(email: email, emailRedirectTo: authRedirectUrl);
    } on Object catch (e) {
      throw AuthFailure.from(e);
    }
  }

  @override
  Future<void> signOut() async {
    try {
      await _auth.signOut();
    } on Object catch (e) {
      throw AuthFailure.from(e);
    }
  }
}
