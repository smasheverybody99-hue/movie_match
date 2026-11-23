/// Welcome — one sentence and the sign-in buttons: Google and Apple, then a passwordless
/// email link. No guest mode (FR-1). Mirrors apps/web/src/pages/Welcome.tsx.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../auth/auth_client.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';

final _email = RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$');

class WelcomeScreen extends ConsumerStatefulWidget {
  const WelcomeScreen({super.key});

  @override
  ConsumerState<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends ConsumerState<WelcomeScreen> {
  final _controller = TextEditingController();
  bool _emailOpen = false;
  bool _invalid = false;
  bool _busy = false;
  String? _sentTo;
  String? _errorKey;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  String _failureKey(Object error) =>
      error is AuthFailure && error.kind == AuthFailureKind.providerDisabled
          ? 'welcome.providerOff'
          : 'welcome.error';

  Future<void> _oauth(AuthClient auth, AuthProvider provider) async {
    setState(() {
      _errorKey = null;
      _busy = true;
    });
    try {
      await auth.signInWithOAuth(provider); // the browser opens; the session comes back
    } on Object catch (e) {
      if (mounted) setState(() => _errorKey = _failureKey(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _sendLink(AuthClient auth) async {
    final value = _controller.text.trim();
    if (!_email.hasMatch(value)) {
      setState(() => _invalid = true);
      return;
    }
    setState(() {
      _invalid = false;
      _errorKey = null;
      _busy = true;
    });
    try {
      await auth.signInWithEmail(value);
      if (mounted) setState(() => _sentTo = value);
    } on Object catch (e) {
      if (mounted) setState(() => _errorKey = _failureKey(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final auth = ref.watch(authClientProvider);
    final theme = Theme.of(context);
    final disabled = auth == null || _busy;

    Widget providerButton(AuthProvider provider, String key) => SizedBox(
          width: double.infinity,
          child: OutlinedButton(
            onPressed: disabled ? null : () => _oauth(auth, provider),
            child: Text(s.t(key)),
          ),
        );

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.x4),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(s.t('app.name'),
                      style: theme.textTheme.displayLarge?.copyWith(fontSize: 40),
                      textAlign: TextAlign.center),
                  const SizedBox(height: AppSpacing.x2),
                  Text(s.t('welcome.tagline'), textAlign: TextAlign.center),
                  const SizedBox(height: AppSpacing.x5),
                  if (auth == null) ...[
                    Text(s.t('welcome.notConfigured'),
                        key: const Key('welcome.notConfigured'), textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.x3),
                  ],
                  providerButton(AuthProvider.google, 'welcome.google'),
                  const SizedBox(height: AppSpacing.x2),
                  providerButton(AuthProvider.apple, 'welcome.apple'),
                  const SizedBox(height: AppSpacing.x2),
                  if (!_emailOpen)
                    TextButton(
                      onPressed: auth == null ? null : () => setState(() => _emailOpen = true),
                      child: Text(s.t('welcome.email')),
                    )
                  else if (_sentTo != null)
                    Text(s.t('welcome.emailSent', {'email': _sentTo!}),
                        key: const Key('welcome.emailSent'))
                  else ...[
                    TextField(
                      key: const Key('welcome.emailField'),
                      controller: _controller,
                      autofocus: true,
                      keyboardType: TextInputType.emailAddress,
                      autofillHints: const [AutofillHints.email],
                      decoration: InputDecoration(
                        labelText: s.t('welcome.emailLabel'),
                        hintText: s.t('welcome.emailPlaceholder'),
                        errorText: _invalid ? s.t('welcome.emailInvalid') : null,
                      ),
                      onSubmitted: (_) => _sendLink(auth!),
                    ),
                    const SizedBox(height: AppSpacing.x2),
                    FilledButton(
                      onPressed: _busy ? null : () => _sendLink(auth!),
                      child: Text(s.t('welcome.emailSend')),
                    ),
                  ],
                  if (_errorKey != null) ...[
                    const SizedBox(height: AppSpacing.x3),
                    Text(s.t(_errorKey!),
                        key: const Key('welcome.error'),
                        style: const TextStyle(color: AppColors.gold),
                        textAlign: TextAlign.center),
                  ],
                  const SizedBox(height: AppSpacing.x4),
                  Text(s.t('welcome.terms'),
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodySmall?.copyWith(color: AppColors.muted)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
