/// /watchlist — group chips on top, rows below; marking a film watched moves its row out of
/// "Watch next". Mirrors apps/web/src/pages/Watchlist.tsx; changes show at once and come
/// back with a message if the server refuses them (state/watchlist_state.dart).
///
/// Phone differences: a row swipes right for Watched and left for Remove (the parity
/// table's swipe on watchlist rows); the buttons stay, for TalkBack and for anyone who does
/// not swipe. A tap on a row opens the film.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../format.dart';
import '../state/app_state.dart';
import '../state/watchlist_state.dart';
import '../theme/tokens.dart';
import '../widgets/match_band.dart';
import '../widgets/poster.dart';
import '../widgets/states.dart';
import 'profile_screen.dart' show ProfileButton;

/// Groups computed from what every item already carries. The trait-based smart groups
/// (Challenging, Light, Hidden gems) are Phase 8; these three need no traits.
enum WatchlistGroup {
  next('watchlist.group.next', Icons.playlist_play),
  short('watchlist.group.short', Icons.timer_outlined),
  watched('watchlist.group.watched', Icons.check_circle_outline);

  const WatchlistGroup(this.label, this.icon);
  final String label;
  final IconData icon;
}

bool inGroup(WatchlistItem item, WatchlistGroup group) => switch (group) {
      WatchlistGroup.next => item.watchedAt == null,
      WatchlistGroup.short => item.watchedAt == null &&
          item.movie.runtimeMinutes != null &&
          item.movie.runtimeMinutes! <= 90,
      WatchlistGroup.watched => item.watchedAt != null,
    };

class WatchlistScreen extends ConsumerStatefulWidget {
  const WatchlistScreen({super.key});

  @override
  ConsumerState<WatchlistScreen> createState() => _WatchlistScreenState();
}

class _WatchlistScreenState extends ConsumerState<WatchlistScreen> {
  WatchlistGroup _group = WatchlistGroup.next;
  bool _failed = false;

  Future<void> _change(Future<bool> Function(WatchlistEdits edits) action) async {
    setState(() => _failed = false);
    final ok = await action(ref.read(watchlistEditsProvider.notifier));
    if (mounted) setState(() => _failed = !ok);
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final list = ref.watch(watchlistViewProvider);
    final items = list.value;
    final Widget body;
    if (items == null) {
      body = list.hasError && !list.isLoading
          ? ErrorState(
              message: s.t('watchlist.error'),
              onRetry: () => ref.invalidate(watchlistProvider),
            )
          : const _ListSkeleton();
    } else if (items.isEmpty) {
      body = EmptyState(
        message: s.t('watchlist.empty'),
        actionLabel: s.t('watchlist.emptyCta'),
        onAction: () => context.go('/search'),
      );
    } else {
      final shown = [for (final item in items) if (inGroup(item, _group)) item];
      body = ListView(
        padding: const EdgeInsets.only(bottom: AppSpacing.x4),
        children: [
          // Wrapped, not scrolled sideways: on a phone the third chip would start off
          // screen, and nothing would say it is there.
          Padding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.x3, AppSpacing.x2, AppSpacing.x3, 12),
            child: Semantics(
              container: true,
              label: s.t('watchlist.groups'),
              child: Wrap(
                spacing: AppSpacing.x2,
                runSpacing: AppSpacing.x2,
                children: [
                  for (final g in WatchlistGroup.values)
                    ChoiceChip(
                      key: Key('watchlist.group.${g.name}'),
                      avatar: Icon(g.icon, size: 16),
                      label: Text(s.t(g.label)),
                      selected: _group == g,
                      showCheckmark: false,
                      onSelected: (_) => setState(() => _group = g),
                    ),
                ],
              ),
            ),
          ),
          if (_failed)
            Padding(
              padding: const EdgeInsets.fromLTRB(AppSpacing.x3, 0, AppSpacing.x3, AppSpacing.x2),
              child: Semantics(
                liveRegion: true,
                child: Text(s.t('watchlist.actionError'),
                    style: const TextStyle(fontSize: 13, color: AppColors.red)),
              ),
            ),
          if (shown.isEmpty)
            Padding(
              padding: const EdgeInsets.all(AppSpacing.x3),
              child: Text(s.t('watchlist.emptyGroup'),
                  style: const TextStyle(color: AppColors.muted)),
            )
          else
            for (final item in shown)
              _Row(
                key: ValueKey(item.movie.id),
                item: item,
                onWatched: () => _change((e) => e.markWatched(item.movie.id)),
                onRemove: () => _change((e) => e.remove(item.movie.id)),
              ),
        ],
      );
    }
    return Scaffold(
      appBar: AppBar(title: Text(s.t('watchlist.title')), actions: const [ProfileButton()]),
      body: body,
    );
  }
}

class _Row extends ConsumerWidget {
  const _Row({super.key, required this.item, required this.onWatched, required this.onRemove});

  final WatchlistItem item;
  final VoidCallback onWatched;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final movie = item.movie;
    final meta = movieMeta(movie, s);
    final unwatched = item.watchedAt == null;
    Widget swipeLabel(IconData icon, String text, Color color, Alignment align) => ColoredBox(
          color: color,
          child: Align(
            alignment: align,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x4),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                Icon(icon, color: AppColors.text),
                const SizedBox(width: AppSpacing.x2),
                Text(text, style: const TextStyle(fontWeight: FontWeight.w700)),
              ]),
            ),
          ),
        );
    return Dismissible(
      key: ValueKey('swipe.${movie.id}'),
      // Right for Watched (only while unwatched), left for Remove.
      direction: unwatched ? DismissDirection.horizontal : DismissDirection.endToStart,
      background: swipeLabel(Icons.check, s.t('watchlist.markWatched'), AppColors.surface2,
          Alignment.centerLeft),
      secondaryBackground: swipeLabel(Icons.delete_outline, s.t('watchlist.remove'),
          AppColors.redDark, Alignment.centerRight),
      onDismissed: (direction) =>
          direction == DismissDirection.startToEnd ? onWatched() : onRemove(),
      child: InkWell(
        onTap: () => context.push('/movie/${movie.id}', extra: movie),
        child: Container(
          decoration: const BoxDecoration(
            border: Border(bottom: BorderSide(color: AppColors.line)),
          ),
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x3, vertical: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(width: 52, child: Poster(movie: movie, size: 'w185')),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(movie.title,
                        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                    if (meta.isNotEmpty)
                      Text(meta, style: const TextStyle(fontSize: 12, color: AppColors.muted)),
                    if (showsStrong(item.band)) ...[
                      const SizedBox(height: AppSpacing.x1),
                      BandPill(band: item.band),
                    ],
                    // Under the title, as on the web's narrow screens.
                    Wrap(
                      spacing: AppSpacing.x1,
                      children: [
                        if (unwatched)
                          Semantics(
                            button: true,
                            label: s.t('watchlist.markWatchedLabel', {'title': movie.title}),
                            excludeSemantics: true,
                            child: OutlinedButton(
                              key: Key('watchlist.watched.${movie.id}'),
                              onPressed: onWatched,
                              child: Text(s.t('watchlist.markWatched')),
                            ),
                          ),
                        Semantics(
                          button: true,
                          label: s.t('watchlist.removeLabel', {'title': movie.title}),
                          excludeSemantics: true,
                          child: TextButton(
                            key: Key('watchlist.remove.${movie.id}'),
                            onPressed: onRemove,
                            child: Text(s.t('watchlist.remove')),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ListSkeleton extends ConsumerWidget {
  const _ListSkeleton();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    Widget bar(double width, double height) => Container(
          width: width,
          height: height,
          decoration: BoxDecoration(
            color: AppColors.surface2,
            borderRadius: BorderRadius.circular(AppRadius.sm),
          ),
        );
    return Semantics(
      label: ref.watch(stringsProvider).t('common.loading'),
      child: ExcludeSemantics(
        child: ListView(
          key: const Key('watchlist.skeleton'),
          physics: const NeverScrollableScrollPhysics(),
          padding: const EdgeInsets.all(AppSpacing.x3),
          children: [
            for (var i = 0; i < 5; i++)
              Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.x3),
                child: Row(children: [
                  bar(52, 78),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      bar(180, 16),
                      const SizedBox(height: AppSpacing.x2),
                      bar(100, 12),
                    ]),
                  ),
                ]),
              ),
          ],
        ),
      ),
    );
  }
}
