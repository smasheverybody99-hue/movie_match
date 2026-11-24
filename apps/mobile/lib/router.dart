import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import 'data/models.dart';
import 'screens/assistant_screen.dart';
import 'screens/data_notice.dart';
import 'screens/dna_screen.dart';
import 'screens/feed_screen.dart';
import 'screens/film_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/search_screen.dart';
import 'screens/watchlist_screen.dart';
import 'screens/welcome_screen.dart';
import 'state/app_state.dart';
import 'widgets/app_shell.dart';

/// The app's routes. Signed out, everything leads to /welcome; signed in, /welcome leads
/// home, and every screen behind it waits for the data notice. The main sections sit under
/// the bottom bar; the film page and onboarding cover it. Screens are added in the
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
      // About is public: Welcome links to it (TMDB attribution).
      if (state.matchedLocation == '/about') return null;
      if (!signedIn.value) return atWelcome ? null : '/welcome';
      return atWelcome ? '/' : null;
    },
    routes: [
      GoRoute(path: '/welcome', builder: (context, state) => const WelcomeScreen()),
      GoRoute(path: '/about', builder: (context, state) => const AboutScreen()),
      GoRoute(
        path: '/profile',
        builder: (context, state) => const DataNoticeGate(child: ProfileScreen()),
      ),
      // The main sections under the bottom bar (widgets/app_shell.dart), in its order.
      StatefulShellRoute.indexedStack(
        builder: (context, state, shell) => DataNoticeGate(child: AppShell(shell: shell)),
        branches: [
          StatefulShellBranch(routes: [
            GoRoute(path: '/', builder: (context, state) => const FeedScreen()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: '/search', builder: (context, state) => const SearchScreen()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: '/assistant', builder: (context, state) => const AssistantScreen()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: '/dna', builder: (context, state) => const DnaScreen()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: '/watchlist', builder: (context, state) => const WatchlistScreen()),
          ]),
        ],
      ),
      GoRoute(
        path: '/movie/:id',
        builder: (context, state) => DataNoticeGate(
          child: FilmScreen(
            id: int.tryParse(state.pathParameters['id'] ?? ''),
            early: state.extra is Movie ? state.extra! as Movie : null,
          ),
        ),
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
