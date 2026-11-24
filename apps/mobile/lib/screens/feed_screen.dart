/// Home — the hero (the top 5 of "For you"), then the sections with their reasons. Mirrors
/// apps/web/src/pages/Feed.tsx: the For you row continues from the 6th film, so nothing
/// shows twice; a section without items is not drawn at all; the band on each card is the
/// API's, never recomputed here (FR-5).
///
/// Phone differences: pull to refresh (it also brings back cards hidden by "Not right?");
/// cards have no quick Rate / Save buttons (on the web they need a hovering mouse; a tap
/// opens the film, as on a touch screen there); the empty state has no "Search films"
/// button until the search screen exists (commit 7).
library;

import 'dart:async';
import 'dart:math' as math;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../format.dart';
import '../state/app_state.dart';
import '../state/watchlist_state.dart';
import '../theme/tokens.dart';
import '../widgets/hero.dart';
import '../widgets/match_band.dart';
import '../widgets/not_right.dart';
import '../widgets/poster.dart';
import '../widgets/shown.dart';
import '../widgets/states.dart';
import 'onboarding_screen.dart' show requiredRatings;

/// When the first-load words change: picking → still looking → the server is waking.
/// Render Free sleeps after 15 minutes without traffic and takes ~35 s to wake
/// (docs/deploy.md); without a word the app looks broken.
const feedLoadingSteps = [Duration(seconds: 5), Duration(seconds: 15)];

/// A neutral icon before each row's title (docs/ui.md, 2).
const sectionIcons = <SectionKey, IconData>{
  SectionKey.forYou: Icons.auto_awesome,
  SectionKey.becauseYouLoved: Icons.favorite_border,
  SectionKey.under90: Icons.timer_outlined,
  SectionKey.outsideUsual: Icons.explore_outlined,
};

class FeedScreen extends ConsumerWidget {
  const FeedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(s.t('app.name')),
        actions: [
          // Until the profile screen exists (commit 11), signing out lives here.
          IconButton(
            tooltip: s.t('profile.signOut'),
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authClientProvider)?.signOut(),
          ),
        ],
      ),
      body: const _FeedBody(),
    );
  }
}

class _FeedBody extends ConsumerWidget {
  const _FeedBody();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final recs = ref.watch(recommendationsProvider);
    final data = recs.value;
    // A cached "rate N more" can be older than the latest ratings: while the feed is fetched
    // again, wait for it instead of acting on old numbers (web: F3 item 1).
    if (recs.isLoading && (data == null || !data.enoughData)) return const _FeedLoading();
    if (data == null) {
      return ErrorState(
        message: s.t('feed.error'),
        onRetry: () => ref.invalidate(recommendationsProvider),
      );
    }
    if (!data.enoughData) {
      // A user who has rated nothing yet belongs in onboarding, not on an empty feed.
      if (data.ratingsNeeded >= requiredRatings) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (context.mounted) context.go('/onboarding');
        });
        return const _FeedLoading();
      }
      return EmptyState(
        message: s.t('feed.notEnough', {'n': data.ratingsNeeded}),
        actionLabel: s.t('feed.notEnoughCta'),
        onAction: () => context.go('/onboarding'),
      );
    }
    final hidden = ref.watch(hiddenCardsProvider);
    final sections = [
      for (final section in data.sections)
        if (section.items.where((i) => !hidden.contains(i.movie.id)).toList() case final items
            when items.isNotEmpty)
          Section(key: section.key, seed: section.seed, items: items),
    ];
    if (sections.isEmpty) return EmptyState(message: s.t('feed.empty'));

    final forYou = sections.where((x) => x.key == SectionKey.forYou).firstOrNull;
    final heroItems = forYou?.items.take(heroCount).toList() ?? const <Recommendation>[];
    // The hero's films are not repeated in the For you row: it starts at the 6th.
    final rows = [
      for (final section in sections)
        if (section.key != SectionKey.forYou)
          section
        else if (section.items.length > heroCount)
          Section(key: section.key, items: section.items.sublist(heroCount)),
    ];
    final saved = ref.watch(savedIdsProvider);

    void open(Movie movie, EventSource source) {
      ref.read(telemetryProvider).track(RecommendationEvent(
            clicked: true,
            at: DateTime.now(),
            movieId: movie.id,
            source: source,
          ));
      context.push('/movie/${movie.id}', extra: movie);
    }

    Future<void> toggleSave(Movie movie, bool isSaved) async {
      final messenger = ScaffoldMessenger.of(context);
      final ok = await ref.read(pendingSavesProvider.notifier).toggle(movie, isSaved: isSaved);
      if (!ok) {
        messenger
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(content: Text(s.t('movie.listError'))));
      }
    }

    Future<void> refresh() async {
      final messenger = ScaffoldMessenger.of(context);
      ref.read(hiddenCardsProvider.notifier).clear();
      try {
        await ref.refresh(recommendationsProvider.future).then((_) {});
      } on Object {
        messenger
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(content: Text(s.t('feed.error'))));
      }
    }

    return RefreshIndicator(
      onRefresh: refresh,
      child: ListView(
        // Pull to refresh works even when everything fits on the screen.
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.only(bottom: AppSpacing.x4),
        children: [
          if (heroItems.isNotEmpty)
            FeedHero(
              items: heroItems,
              saved: saved,
              onToggleSave: (movie, isSaved) => toggleSave(movie, isSaved),
              onOpen: (movie) => open(movie, EventSource.forYou),
            ),
          for (final section in rows)
            _SectionRow(
              key: ValueKey(section.key),
              section: section,
              onOpen: (movie) => open(movie, EventSource.fromSection(section.key)),
            ),
        ],
      ),
    );
  }
}

/// The first load: a spinner with words that change at 5 s and 15 s. With animations
/// turned off on the phone the spinner is left out and only the words remain.
class _FeedLoading extends ConsumerStatefulWidget {
  const _FeedLoading();

  @override
  ConsumerState<_FeedLoading> createState() => _FeedLoadingState();
}

class _FeedLoadingState extends ConsumerState<_FeedLoading> {
  int _stage = 0;
  final _timers = <Timer>[];

  @override
  void initState() {
    super.initState();
    for (final (i, after) in feedLoadingSteps.indexed) {
      _timers.add(Timer(after, () {
        if (mounted) setState(() => _stage = i + 1);
      }));
    }
  }

  @override
  void dispose() {
    for (final t in _timers) {
      t.cancel();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final text = s.t(const ['feed.loading.picking', 'feed.loading.still', 'feed.loading.waking'][_stage]);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.x4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (!MediaQuery.disableAnimationsOf(context)) ...[
              const CircularProgressIndicator(color: AppColors.muted),
              const SizedBox(height: AppSpacing.x3),
            ],
            Text(text, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.muted)),
          ],
        ),
      ),
    );
  }
}

class _SectionRow extends ConsumerWidget {
  const _SectionRow({super.key, required this.section, required this.onOpen});

  final Section section;
  final void Function(Movie movie) onOpen;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final title = section.key == SectionKey.becauseYouLoved
        ? s.t('feed.section.because_you_loved', {'title': section.seed?.title ?? ''})
        : s.t('feed.section.${section.key.wire}');
    // As on the web phone layout: two and a bit cards across, so the row reads as scrollable.
    final width = (MediaQuery.sizeOf(context).width - 2 * AppSpacing.x3 - 2 * 10) / 2.4;
    // A horizontal list needs its height up front: the poster, then two title lines, the
    // meta line and "Not right?", measured at the phone's text size.
    final base = DefaultTextStyle.of(context).style;
    final scaler = MediaQuery.textScalerOf(context);
    double textHeight(TextStyle style, int lines) {
      final painter = TextPainter(
        text: TextSpan(text: List.filled(lines, 'Ag').join('\n'), style: base.merge(style)),
        textScaler: scaler,
        textDirection: TextDirection.ltr,
      )..layout();
      final height = painter.height;
      painter.dispose();
      return height;
    }

    final height = width * 1.5 +
        10 +
        textHeight(_cardTitleStyle, 2) +
        textHeight(_cardMetaStyle, 1) +
        math.max(32, textHeight(notRightTextStyle, 1)) +
        AppSpacing.x1;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(AppSpacing.x3, AppSpacing.x4, AppSpacing.x3, 12),
          child: Semantics(
            header: true,
            child: Row(
              children: [
                Icon(sectionIcons[section.key], size: 20, color: AppColors.muted),
                const SizedBox(width: AppSpacing.x2),
                Expanded(
                  child: Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, height: 1.5),
                  ),
                ),
              ],
            ),
          ),
        ),
        SizedBox(
          height: height,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x3),
            itemCount: section.items.length,
            separatorBuilder: (context, i) => const SizedBox(width: 10),
            itemBuilder: (context, i) {
              final item = section.items[i];
              return SizedBox(
                width: width,
                child: MovieCard(
                  key: ValueKey(item.movie.id),
                  item: item,
                  source: EventSource.fromSection(section.key),
                  onOpen: () => onOpen(item.movie),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

const _cardTitleStyle = TextStyle(fontSize: 13, fontWeight: FontWeight.w600, height: 1.3);
const _cardMetaStyle = TextStyle(fontSize: 12, color: AppColors.muted);

/// Poster (with the band), title in two lines at most, year · runtime; a tap opens the
/// film. "Not right?" under it. Web: components/MovieCard.tsx.
class MovieCard extends ConsumerWidget {
  const MovieCard({super.key, required this.item, required this.source, required this.onOpen});

  final Recommendation item;
  final EventSource source;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final movie = item.movie;
    final meta = movieMeta(movie, s);
    final label = [movie.title, if (showsStrong(item.band)) s.t('band.strong'), meta]
        .where((x) => x.isNotEmpty)
        .join(', ');
    return ShownTracker(
      movieId: movie.id,
      source: source,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Semantics(
            button: true,
            label: label,
            excludeSemantics: true,
            child: InkWell(
              onTap: onOpen,
              borderRadius: BorderRadius.circular(AppRadius.sm),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Poster(movie: movie, band: item.band),
                  const SizedBox(height: 10),
                  Text(
                    movie.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: _cardTitleStyle,
                  ),
                  if (meta.isNotEmpty)
                    Text(meta, maxLines: 1, overflow: TextOverflow.ellipsis, style: _cardMetaStyle),
                ],
              ),
            ),
          ),
          NotRightButton(movie: movie, source: source),
        ],
      ),
    );
  }
}
