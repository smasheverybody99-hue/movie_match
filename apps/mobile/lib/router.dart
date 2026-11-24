import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import 'data/models.dart';
import 'screens/data_notice.dart';
import 'screens/feed_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/welcome_screen.dart';
import 'state/app_state.dart';
import 'theme/tokens.dart';
import 'widgets/poster.dart';

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
        builder: (context, state) => const DataNoticeGate(child: FeedScreen()),
      ),
      GoRoute(
        path: '/movie/:id',
        builder: (context, state) => DataNoticeGate(
          child: _FilmPlaceholder(movie: state.extra is Movie ? state.extra! as Movie : null),
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

/// Until the film page (commit 6): the film's title, its poster and its overview, so a tap
/// on a card leads somewhere true. The film comes from the card (`extra`); opened without
/// one, there is nothing to show yet.
class _FilmPlaceholder extends StatelessWidget {
  const _FilmPlaceholder({required this.movie});

  final Movie? movie;

  @override
  Widget build(BuildContext context) {
    final film = movie;
    return Scaffold(
      appBar: AppBar(title: Text(film?.title ?? '')),
      body: film == null
          ? const SizedBox.shrink()
          : ListView(
              padding: const EdgeInsets.all(AppSpacing.x3),
              children: [
                Center(child: SizedBox(width: 200, child: Poster(movie: film))),
                if (film.overview != null) ...[
                  const SizedBox(height: AppSpacing.x3),
                  Text(film.overview!),
                ],
              ],
            ),
    );
  }
}
