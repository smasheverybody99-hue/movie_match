import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import 'config.dart';
import 'theme/tokens.dart';

/// The app's routes. Screens are added in the web app's order (phase-06-mobile.md):
/// auth, onboarding, feed, film, search, watchlist, DNA, assistant.
final routerProvider = Provider<GoRouter>(
  (ref) => GoRouter(
    routes: [
      GoRoute(path: '/', builder: (context, state) => const _Home()),
    ],
  ),
);

class _Home extends StatelessWidget {
  const _Home();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Movie Match', style: theme.textTheme.headlineMedium),
            if (!apiConfigured)
              const Padding(
                padding: EdgeInsets.only(top: AppSpacing.x3),
                child: Text('API_URL is not set (--dart-define=API_URL=...)'),
              ),
          ],
        ),
      ),
    );
  }
}
