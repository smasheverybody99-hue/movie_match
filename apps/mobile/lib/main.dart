import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import 'router.dart';
import 'theme/tokens.dart';

void main() => runApp(const ProviderScope(child: MovieMatchApp()));

class MovieMatchApp extends ConsumerWidget {
  const MovieMatchApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp.router(
        title: 'Movie Match',
        theme: buildTheme(),
        routerConfig: ref.watch(routerProvider),
      );
}
