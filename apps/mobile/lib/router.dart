import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import 'config.dart';
import 'screens/data_notice.dart';
import 'screens/onboarding_screen.dart';
import 'screens/welcome_screen.dart';
import 'state/app_state.dart';
import 'theme/tokens.dart';
import 'widgets/states.dart';

/// The app's routes. Signed out, everything leads to /welcome; signed in, /welcome leads
/// home, and every screen behind it waits for the data notice. Screens are added in the
/// web app's order (phase-06-mobile.md): auth, onboarding, feed, film, search, watchlist,
/// DNA, assistant.
final routerProvider = Provider<GoRouter>((ref) {
  final signedIn = ValueNotifier<bool>(currentSession(ref) != null);
  ref.listen(sessionProvider, (_, next) {
    if (next.hasValue) signedIn.value = next.value != null;
  });
  ref.onDispose(signedIn.dispose);

  return GoRouter(
    refreshListenable: signedIn,
    redirect: (context, state) {
      final atWelcome = state.matchedLocation == '/welcome';
      if (!signedIn.value) return atWelcome ? null : '/welcome';
      return atWelcome ? '/' : null;
    },
    routes: [
      GoRoute(path: '/welcome', builder: (context, state) => const WelcomeScreen()),
      GoRoute(
        path: '/',
        builder: (context, state) => const DataNoticeGate(child: _Home()),
      ),
      GoRoute(
        path: '/onboarding',
        builder: (context, state) => DataNoticeGate(
          child: OnboardingScreen(onFinished: () => context.go('/')),
        ),
      ),
    ],
  );
});

/// Placeholder until the feed (commit 5): who is signed in, and a way out. As the web's
/// feed does, it sends a user who has rated nothing to onboarding and offers it to one
/// who has rated fewer than 10. While /me reloads (after onboarding) it waits: the cached
/// count would send the user straight back (web: F3 item 1, 2026-10-08).
class _Home extends ConsumerWidget {
  const _Home();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final theme = Theme.of(context);
    final email = ref.watch(sessionProvider).value?.email;
    final me = ref.watch(meProvider);
    if (me.isLoading) return const Scaffold(body: LoadingState());
    final needed = me.value?.ratingsNeeded;
    if (needed != null && needed >= requiredRatings) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (context.mounted) context.go('/onboarding');
      });
      return const Scaffold(body: LoadingState());
    }
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(s.t('app.name'), style: theme.textTheme.headlineMedium),
            if (email != null) Text(email),
            if (needed != null && needed > 0) ...[
              const SizedBox(height: AppSpacing.x3),
              Text(s.t('feed.notEnough', {'n': needed})),
              TextButton(
                onPressed: () => context.go('/onboarding'),
                child: Text(s.t('feed.notEnoughCta')),
              ),
            ],
            if (!apiConfigured)
              const Padding(
                padding: EdgeInsets.only(top: AppSpacing.x3),
                child: Text('API_URL is not set (--dart-define=API_URL=...)'),
              ),
            const SizedBox(height: AppSpacing.x3),
            TextButton(
              onPressed: () => ref.read(authClientProvider)?.signOut(),
              child: Text(s.t('profile.signOut')),
            ),
          ],
        ),
      ),
    );
  }
}
