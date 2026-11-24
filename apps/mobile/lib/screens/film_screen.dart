/// /movie/:id — the backdrop, the poster and title with Rate and Save, then "why you",
/// the overview and credits, and the film's other traits against the user's. Mirrors
/// apps/web/src/pages/MoviePage.tsx (docs/ui.md, 5).
///
/// "Why you" follows the side the API found (TZ 1.27): a reason gets the why-you sentence,
/// a film far from the viewer a plain statement of how it differs, and with nothing named
/// the panel says nothing beyond its heading. The sentence is the cached explanation, or
/// the free fallback; "Writing the explanation…" shows only while one can still arrive.
///
/// Phone differences: the rating opens in a bottom sheet; while the film loads, the
/// backdrop of the card that was tapped is already there (web: the early answer).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../data/api_client.dart';
import '../data/models.dart';
import '../data/traits.dart';
import '../format.dart';
import '../i18n/i18n.dart';
import '../state/app_state.dart';
import '../state/film_state.dart';
import '../state/watchlist_state.dart';
import '../theme/tokens.dart';
import '../widgets/backdrop.dart';
import '../widgets/match_band.dart';
import '../widgets/poster.dart';
import '../widgets/rating_input.dart';
import '../widgets/states.dart';
import '../widgets/trait_axis.dart';

/// The comparison shows this many traits.
const compared = 6;

/// "Why you" names at most this many traits (matching.trait_notes, n = 3).
const whyTraits = 3;

List<String> _named(MovieDetail d) => d.namedTraits.where(traitKeys.contains).take(whyTraits).toList();

/// The film's strongest traits that "Why you" does not already show, up to [compared];
/// ties keep the traits.json order.
List<String> comparedTraits(MovieDetail detail) {
  final scores = detail.traits?.scores ?? const {};
  final shown = _named(detail);
  final rest = [for (final k in traitKeys) if (!shown.contains(k)) k];
  final order = {for (final (i, k) in traitKeys.indexed) k: i};
  rest.sort((a, b) {
    final byScore = (scores[b] ?? 0).compareTo(scores[a] ?? 0);
    return byScore != 0 ? byScore : order[a]!.compareTo(order[b]!);
  });
  return rest.take(compared).toList();
}

/// The user's taste, or null while it loads or without a taste profile: the API sends
/// `scores: {}` then, and a missing score must not be drawn as a "you" dot at 0.
Map<String, int>? _taste(WidgetRef ref) {
  final scores = ref.watch(dnaProvider).value?.scores;
  return scores == null || scores.isEmpty ? null : scores;
}

bool _whyHasAxes(MovieDetail d) => d.match != null && _named(d).isNotEmpty;

class FilmScreen extends ConsumerStatefulWidget {
  const FilmScreen({super.key, required this.id, this.early});

  /// Null when the link's id is not a number.
  final int? id;

  /// The film as the tapped card knew it: its backdrop shows while the page loads.
  final Movie? early;

  @override
  ConsumerState<FilmScreen> createState() => _FilmScreenState();
}

class _FilmScreenState extends ConsumerState<FilmScreen> {
  /// A sensitive film's page opens only after the viewer says so.
  bool _confirmed = false;

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final id = widget.id;
    if (id == null || id <= 0) return _Frame(child: _notFound(s));
    // The taste, the ratings and the list do not depend on the film, so they go out with
    // it instead of after it.
    ref.watch(dnaProvider);
    ref.watch(ratingsProvider);
    ref.watch(watchlistProvider);
    final film = ref.watch(movieProvider(id));
    final detail = film.value;
    if (detail == null) {
      final error = film.error;
      if (film.isLoading || error == null) return _Frame(child: _Skeleton(early: widget.early));
      if (error is ApiException && error.isNotFound) return _Frame(child: _notFound(s));
      return _Frame(
        child: ErrorState(
          message: s.t('movie.error'),
          onRetry: () => ref.invalidate(movieProvider(id)),
        ),
      );
    }
    if (detail.sensitive && !_confirmed) {
      return _Frame(
        child: _SensitiveNotice(
          title: detail.title,
          onShow: () => setState(() => _confirmed = true),
        ),
      );
    }
    return _Frame(overHero: true, child: _FilmPage(detail: detail));
  }

  Widget _notFound(Strings s) => EmptyState(
        message: s.t('movie.notFound'),
        actionLabel: s.t('movie.notFoundCta'),
        onAction: () => context.go('/'),
      );
}

/// The screen with its back button, over the backdrop once the page is drawn.
class _Frame extends StatelessWidget {
  const _Frame({required this.child, this.overHero = false});

  final Widget child;
  final bool overHero;

  @override
  Widget build(BuildContext context) => Scaffold(
        extendBodyBehindAppBar: overHero,
        appBar: AppBar(backgroundColor: overHero ? Colors.transparent : null),
        body: child,
      );
}

double _heroHeight(BuildContext context) =>
    (MediaQuery.sizeOf(context).height * 0.45).clamp(240.0, 480.0);

class _FilmPage extends ConsumerStatefulWidget {
  const _FilmPage({required this.detail});

  final MovieDetail detail;

  @override
  ConsumerState<_FilmPage> createState() => _FilmPageState();
}

class _FilmPageState extends ConsumerState<_FilmPage> {
  bool _rateFailed = false;
  bool _listFailed = false;

  MovieDetail get detail => widget.detail;

  Future<void> _rate(double? current) async {
    if (ref.read(pendingRatingsProvider).containsKey(detail.id)) return; // still saving
    final answer = await showModalBottomSheet<(double, List<String>)>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      showDragHandle: true,
      builder: (context) => _RateSheet(title: detail.title, current: current),
    );
    if (answer == null || !mounted) return;
    final (value, aspects) = answer;
    setState(() => _rateFailed = false);
    // Optimistic: the new score shows at once and rolls back if the request fails.
    final ok = await ref.read(pendingRatingsProvider.notifier).rate(RatingIn(
          movieId: detail.id,
          score: value,
          likedAspects: showsLikedAspects(value) ? aspects : const [],
        ));
    if (mounted) setState(() => _rateFailed = !ok);
  }

  Future<void> _toggleSave(bool saved) async {
    setState(() => _listFailed = false);
    final ok = await ref.read(pendingSavesProvider.notifier).toggle(detail, isSaved: saved);
    if (mounted) setState(() => _listFailed = !ok);
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final mine = ref.watch(myScoreProvider(detail.id));
    final saving = ref.watch(pendingRatingsProvider).containsKey(detail.id);
    final saved = ref.watch(savedIdsProvider).contains(detail.id);
    final tags = [
      if (detail.year != null) '${detail.year}',
      if (detail.runtimeMinutes != null) s.t('common.minutes', {'n': detail.runtimeMinutes!}),
      for (final g in detail.genres) genreLabel(g, s),
    ];
    final mineText =
        mine == null ? null : s.t('movie.yourRating', {'score': formatScore(mine, s.lang)});
    final hasAbout = detail.overview != null || detail.director != null || detail.cast.isNotEmpty;

    return ListView(
      padding: const EdgeInsets.only(bottom: AppSpacing.x5),
      children: [
        SizedBox(
          key: const Key('film.hero'),
          height: _heroHeight(context),
          child: Stack(fit: StackFit.expand, children: [
            Backdrop(movie: detail),
            const BackdropShade(),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x3),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(width: 110, child: Poster(movie: detail, band: detail.band)),
              const SizedBox(width: AppSpacing.x3),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Semantics(
                      header: true,
                      child: Text(detail.title,
                          style: const TextStyle(
                            fontFamily: AppFonts.head,
                            fontWeight: FontWeight.w800,
                            fontSize: 24,
                            height: 1.15,
                            color: AppColors.text,
                          )),
                    ),
                    if (tags.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: AppSpacing.x2,
                        runSpacing: AppSpacing.x2,
                        children: [for (final tag in tags) _Tag(tag)],
                      ),
                    ],
                    if (mineText != null) ...[
                      const SizedBox(height: AppSpacing.x2),
                      Text(mineText,
                          key: const Key('film.myRating'),
                          style: const TextStyle(fontSize: 12, color: AppColors.muted)),
                    ],
                    if (_rateFailed) _FieldError(s.t('movie.rateError')),
                    if (_listFailed) _FieldError(s.t('movie.listError')),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: AppSpacing.x2,
                      runSpacing: AppSpacing.x2,
                      children: [
                        // Not disabled while the rating saves: it says so inside, and a
                        // second press waits.
                        OutlinedButton.icon(
                          key: const Key('film.rate'),
                          onPressed: () => _rate(mine),
                          icon: saving
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2, color: AppColors.muted),
                                )
                              : const Icon(Icons.speed, size: 18),
                          label: Text(saving
                              ? s.t('common.saving')
                              : mineText ?? s.t('movie.rate')),
                        ),
                        OutlinedButton.icon(
                          key: const Key('film.save'),
                          onPressed: () => _toggleSave(saved),
                          icon: Icon(saved ? Icons.bookmark_added : Icons.bookmark_border,
                              size: 18),
                          label: Text(saved ? s.t('movie.onList') : s.t('movie.saveToList')),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.x4),
        _Why(detail: detail),
        if (hasAbout) _About(detail: detail),
        _Compare(detail: detail),
      ],
    );
  }
}

class _Tag extends StatelessWidget {
  const _Tag(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(
          color: AppColors.surface2,
          borderRadius: BorderRadius.circular(99),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          child: Text(text, style: const TextStyle(fontSize: 13, color: AppColors.muted)),
        ),
      );
}

class _FieldError extends StatelessWidget {
  const _FieldError(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: AppSpacing.x2),
        child: Semantics(
          liveRegion: true,
          child: Text(text, style: const TextStyle(fontSize: 13, color: AppColors.red)),
        ),
      );
}

class _Panel extends StatelessWidget {
  const _Panel({required this.child, super.key});
  final Widget child;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(AppSpacing.x3, 0, AppSpacing.x3, AppSpacing.x3),
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(AppRadius.md),
          ),
          child: Padding(padding: const EdgeInsets.all(AppSpacing.x3), child: child),
        ),
      );
}

class _Eyebrow extends StatelessWidget {
  const _Eyebrow(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: AppSpacing.x2),
        child: Semantics(
          header: true,
          child: Text(text.toUpperCase(),
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.9,
                color: AppColors.muted,
              )),
        ),
      );
}

/// "Why you": the band as the heading, the sentence and up to three named traits on their
/// axes, read as one statement. No number, no ring (FR-5, TZ 1.13).
class _Why extends ConsumerWidget {
  const _Why({required this.detail});
  final MovieDetail detail;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    if (detail.match == null) {
      return _Panel(
        key: const Key('film.why'),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Kicker(band: null),
          const SizedBox(height: AppSpacing.x2),
          Text(s.t('movie.noMatch'), style: const TextStyle(color: AppColors.muted)),
        ]),
      );
    }
    final named = _named(detail);
    final side = named.isEmpty ? null : detail.traitSide;
    final gate = ref.watch(explanationGateProvider);
    // With nothing named the API writes no text, so there is nothing to ask for; nor once
    // the API has said no sentence is coming in this run, unless this film already has one.
    final asks =
        side != null && (gate == null || ref.read(explanationProvider(detail.id).exists));
    final explanation = asks ? ref.watch(explanationProvider(detail.id)) : null;
    final writing = explanation != null && explanation.isLoading && !explanation.hasValue;
    final traits = named.map((k) => traitInSentence(k, s)).join(', ');
    final fallback = s.t(
        side == TraitSide.difference ? 'movie.differsFallback' : 'movie.whyYouFallback',
        {'traits': traits});
    final sentence = side == null ? null : (explanation?.value?.text ?? fallback);
    // Today's allowance is used up: the template stands in, and says why.
    final capped =
        side != null && (explanation?.value?.reason ?? gate) == ExplanationReason.dailyCap;
    final film = detail.traits?.scores ?? const <String, int>{};
    final taste = _taste(ref);
    final reduce = MediaQuery.disableAnimationsOf(context);
    return _Panel(
      key: const Key('film.why'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Kicker(band: detail.band, side: side),
          if (writing || sentence != null) const SizedBox(height: 12),
          if (writing)
            Semantics(
              key: const Key('film.explaining'),
              liveRegion: true,
              child: Row(children: [
                if (!reduce) ...[
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.muted),
                  ),
                  const SizedBox(width: AppSpacing.x2),
                ],
                Flexible(
                  child: Text(s.t('movie.explaining'),
                      style: const TextStyle(color: AppColors.muted)),
                ),
              ]),
            )
          else if (sentence != null)
            TweenAnimationBuilder<double>(
              key: ValueKey(sentence),
              tween: Tween(begin: reduce ? 1 : 0, end: 1),
              duration: reduce ? Duration.zero : const Duration(milliseconds: 200),
              builder: (context, opacity, child) => Opacity(opacity: opacity, child: child),
              child: Text(sentence,
                  key: const Key('film.sentence'),
                  style: const TextStyle(
                    fontFamily: AppFonts.head,
                    fontWeight: FontWeight.w700,
                    fontSize: 20,
                    height: 1.3,
                    color: AppColors.text,
                  )),
            ),
          if (capped) ...[
            const SizedBox(height: AppSpacing.x2),
            Text(s.t('movie.explanationsUsedUp'),
                key: const Key('film.capped'),
                style: const TextStyle(fontSize: 12, color: AppColors.muted)),
          ],
          if (named.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x3),
            const AxisLegend(),
            for (final key in named)
              TraitAxis(trait: key, taste: taste == null ? null : taste[key] ?? 0, film: film[key] ?? 0),
          ],
        ],
      ),
    );
  }
}

class _About extends ConsumerWidget {
  const _About({required this.detail});
  final MovieDetail detail;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    Widget fact(String label, String value) => Padding(
          padding: const EdgeInsets.only(top: AppSpacing.x2),
          child: Text.rich(TextSpan(children: [
            TextSpan(text: '$label  ', style: const TextStyle(color: AppColors.muted)),
            TextSpan(text: value),
          ])),
        );
    return Padding(
      key: const Key('film.about'),
      padding: const EdgeInsets.fromLTRB(AppSpacing.x3, AppSpacing.x2, AppSpacing.x3, AppSpacing.x4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _Eyebrow(s.t('movie.overview')),
          if (detail.overview != null) Text(detail.overview!, style: const TextStyle(height: 1.5)),
          if (detail.director != null) fact(s.t('movie.director'), detail.director!),
          if (detail.cast.isNotEmpty) fact(s.t('movie.cast'), detail.cast.join(', ')),
        ],
      ),
    );
  }
}

class _Compare extends ConsumerWidget {
  const _Compare({required this.detail});
  final MovieDetail detail;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final film = detail.traits?.scores;
    if (film == null) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x3),
        child: Text(s.t('movie.traitsPending'), style: const TextStyle(color: AppColors.muted)),
      );
    }
    final taste = _taste(ref);
    final axes = _whyHasAxes(detail);
    return _Panel(
      key: const Key('film.compare'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // "Other" only when Why you shows reasons: otherwise these are the top traits.
          _Eyebrow(axes ? s.t('movie.compareOther') : s.t('movie.compareTop')),
          if (!axes) const AxisLegend(),
          for (final key in comparedTraits(detail))
            TraitAxis(trait: key, taste: taste == null ? null : taste[key] ?? 0, film: film[key] ?? 0),
        ],
      ),
    );
  }
}

/// The rating sheet: the scale, and Cancel / Save rating. Pops (score, liked aspects).
class _RateSheet extends ConsumerStatefulWidget {
  const _RateSheet({required this.title, required this.current});

  final String title;
  final double? current;

  @override
  ConsumerState<_RateSheet> createState() => _RateSheetState();
}

class _RateSheetState extends ConsumerState<_RateSheet> {
  late double _value = widget.current ?? 7;
  List<String> _aspects = const [];

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(AppSpacing.x3, 0, AppSpacing.x3, AppSpacing.x3),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Semantics(
              header: true,
              child: Text(s.t('movie.rateDialog', {'title': widget.title}),
                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
            ),
            const SizedBox(height: AppSpacing.x3),
            RatingInput(
              value: _value,
              onChanged: (v) => setState(() => _value = v),
              aspects: _aspects,
              onAspectsChanged: (a) => setState(() => _aspects = a),
            ),
            const SizedBox(height: AppSpacing.x3),
            // Side by side when they fit, stacked at large text sizes.
            OverflowBar(
              alignment: MainAxisAlignment.end,
              overflowAlignment: OverflowBarAlignment.end,
              spacing: AppSpacing.x2,
              overflowSpacing: AppSpacing.x2,
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(s.t('common.cancel')),
                ),
                FilledButton(
                  onPressed: () => Navigator.of(context).pop((_value, _aspects)),
                  child: Text(s.t('movie.rateSave')),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// The page's shape while it loads: the backdrop (the tapped card's, when there is one),
/// the poster's and title's places, the "why you" panel.
class _Skeleton extends ConsumerWidget {
  const _Skeleton({required this.early});
  final Movie? early;

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
    final film = early;
    return Semantics(
      label: ref.watch(stringsProvider).t('common.loading'),
      child: ExcludeSemantics(
        child: ListView(
          key: const Key('film.skeleton'),
          physics: const NeverScrollableScrollPhysics(),
          children: [
            SizedBox(
              height: _heroHeight(context),
              child: film == null
                  ? const ColoredBox(color: AppColors.surface)
                  : Stack(fit: StackFit.expand, children: [
                      Backdrop(movie: film),
                      const BackdropShade(),
                    ]),
            ),
            Padding(
              padding: const EdgeInsets.all(AppSpacing.x3),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                bar(110, 165),
                const SizedBox(width: AppSpacing.x3),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    bar(180, 28),
                    const SizedBox(height: 12),
                    bar(110, 16),
                  ]),
                ),
              ]),
            ),
            _Panel(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                bar(160, 20),
                const SizedBox(height: 12),
                bar(double.infinity, 18),
                const SizedBox(height: AppSpacing.x2),
                bar(200, 18),
              ]),
            ),
          ],
        ),
      ),
    );
  }
}

/// Before a sensitive film's page (Phase 5, NSFW): what it is, and a choice. No poster,
/// no backdrop: the images are what the warning is about.
class _SensitiveNotice extends ConsumerWidget {
  const _SensitiveNotice({required this.title, required this.onShow});

  final String title;
  final VoidCallback onShow;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return Center(
      key: const Key('film.sensitive'),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.x4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Semantics(
              header: true,
              child: Text(s.t('movie.sensitive.title'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontFamily: AppFonts.head,
                    fontWeight: FontWeight.w800,
                    fontSize: 24,
                  )),
            ),
            const SizedBox(height: AppSpacing.x3),
            Text(s.t('movie.sensitive.body', {'title': title}), textAlign: TextAlign.center),
            const SizedBox(height: AppSpacing.x4),
            Wrap(
              spacing: AppSpacing.x2,
              runSpacing: AppSpacing.x2,
              alignment: WrapAlignment.center,
              children: [
                OutlinedButton(
                  onPressed: () => context.canPop() ? context.pop() : context.go('/'),
                  child: Text(s.t('movie.sensitive.back')),
                ),
                TextButton(onPressed: onShow, child: Text(s.t('movie.sensitive.show'))),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
