import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'auth/auth_client.dart';
import 'data/local_store.dart';
import 'router.dart';
import 'state/app_state.dart';
import 'theme/tokens.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Supabase restores a saved session before the first frame, so a signed-in user does
  // not see /welcome flash.
  final auth = await SupabaseAuthClient.start();
  final prefs = await SharedPreferencesWithCache.create(
    cacheOptions: const SharedPreferencesWithCacheOptions(),
  );
  runApp(ProviderScope(
    retry: noRetry,
    overrides: [
      authClientProvider.overrideWithValue(auth),
      noticeMemoryProvider.overrideWithValue(PrefsNoticeMemory(prefs)),
      localStoreProvider.overrideWithValue(PrefsLocalStore(prefs)),
    ],
    child: const MovieMatchApp(),
  ));
}

class MovieMatchApp extends ConsumerWidget {
  const MovieMatchApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp.router(
        title: 'Movie Match',
        theme: buildTheme(),
        routerConfig: ref.watch(routerProvider),
      );
}
