/// Onboarding — pick → rate → done (FR-3), resumed after an app restart. Mirrors
/// apps/web/src/pages/Onboarding.tsx: no recommendations before 10 ratings; each score is
/// handed to the rating queue and saved in the background, so Next moves on at once; the
/// done button waits only while a score is still on its way and fewer than 10 are saved.
///
/// Phone differences: no "keys 1–9" hint (no keyboard); a second tap on Next within
/// [nextGuard] of the film changing is ignored, as the web ignores the second click of a
/// double click (it would rate the next film at the default without it being looked at).
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../data/api_client.dart';
import '../data/models.dart';
import '../data/onboarding_store.dart';
import '../data/rating_queue.dart';
import '../data/traits.dart';
import '../format.dart';
import '../i18n/i18n.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/poster.dart';
import '../widgets/states.dart';

/// FR-3: no recommendations before 10 ratings.
const requiredRatings = 10;

/// Films per "none of these" page (web: ONBOARDING_PAGE).
const onboardingPage = 60;

/// FR-3: "what did you like?" appears for scores above 8.0.
const likedAspectsAbove = 8.0;

const _defaultScore = 7.0;
const _searchDelay = Duration(milliseconds: 300);
const nextGuard = Duration(milliseconds: 300);

final onboardingFilmsProvider = FutureProvider.family<List<Movie>, int>(
    (ref, offset) => ref.watch(apiClientProvider).onboardingFilms(onboardingPage, offset));

final onboardingSearchProvider = FutureProvider.autoDispose.family<List<Movie>, String>(
    (ref, q) => ref.watch(apiClientProvider).searchMovies(SearchParams(q: q, limit: 30)));

class OnboardingScreen extends ConsumerWidget {
  const OnboardingScreen({super.key, required this.onFinished});

  /// Called after "See my recommendations": the router goes to the feed.
  final VoidCallback onFinished;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Progress is stored per user, so it can only be read once the user is known.
    final userId = ref.watch(userIdProvider);
    if (userId == null) return const Scaffold(body: LoadingState());
    return _Flow(key: ValueKey(userId), userId: userId, onFinished: onFinished);
  }
}

class _Flow extends ConsumerStatefulWidget {
  const _Flow({super.key, required this.userId, required this.onFinished});

  final String userId;
  final VoidCallback onFinished;

  @override
  ConsumerState<_Flow> createState() => _FlowState();
}

class _FlowState extends ConsumerState<_Flow> {
  late OnboardingProgress _progress;

  /// Which way the last step change went, for the slide (docs/ui.md 7); null on arrival,
  /// so nothing slides on the first screen (also after a restart).
  bool? _forward;

  // Pick step: the search field, and the query it settled on.
  final _search = TextEditingController();
  final _searchFocus = FocusNode();
  Timer? _searchTimer;
  String _query = '';

  // Rate step: the film on screen's score and liked aspects; reset when the film changes.
  double _score = _defaultScore;
  List<String> _aspects = const [];
  Timer? _guard;

  @override
  void initState() {
    super.initState();
    _progress = loadProgress(ref.read(localStoreProvider), widget.userId);
    _track(_progress.step);
  }

  RatingQueue? _queue;
  void _onQueue() => setState(() {});

  @override
  void dispose() {
    _queue?.removeListener(_onQueue);
    _search.dispose();
    _searchFocus.dispose();
    _searchTimer?.cancel();
    _guard?.cancel();
    super.dispose();
  }

  // Each step reached, once per app run, for the alpha's completion funnel.
  void _track(OnboardingStep step) => ref
      .read(telemetryProvider)
      .track(OnboardingStepEvent(at: DateTime.now(), step: step));

  void _update(OnboardingProgress next) {
    final filmChanged = next.step != _progress.step ||
        next.picks.elementAtOrNull(next.index)?.id !=
            _progress.picks.elementAtOrNull(_progress.index)?.id;
    setState(() {
      if (next.step != _progress.step) {
        _forward = next.step.index > _progress.step.index;
        _track(next.step);
      }
      if (filmChanged) {
        _score = _defaultScore;
        _aspects = const [];
        _guard?.cancel();
        _guard = Timer(nextGuard, () => _guard = null);
      }
      _progress = next;
    });
    saveProgress(ref.read(localStoreProvider), widget.userId, next).ignore();
  }

  void _onSearchChanged(String text) {
    setState(() {}); // "none of these" hides as soon as there is text
    _searchTimer?.cancel();
    _searchTimer = Timer(_searchDelay, () => setState(() => _query = text.trim()));
  }

  @override
  Widget build(BuildContext context) {
    final queue = ref.watch(ratingQueueProvider);
    if (!identical(queue, _queue)) {
      _queue?.removeListener(_onQueue);
      _queue = queue..addListener(_onQueue);
    }
    final ratings = ref.watch(ratingsProvider);
    // What the server has, plus what this run saved; minus what is still on its way.
    final server = {for (final r in ratings.value ?? const <Rating>[]) r.movieId};
    final waiting = {for (final u in queue.unsaved) u.movieId};
    final counts = _Counts(
      rated: {...server, ...queue.saved, ...waiting},
      confirmed: {...server, ...queue.saved}.difference(waiting).length,
      queue: queue,
    );

    final s = ref.watch(stringsProvider);
    final (body, foot) = switch (_progress.step) {
      OnboardingStep.pick => (_pickBody(s), _pickFoot(s, counts)),
      OnboardingStep.rate => (_rateBody(s, counts), _rateFoot(s, counts)),
      OnboardingStep.done => (_doneBody(s, counts), null),
    };
    return Scaffold(
      body: SafeArea(
        bottom: false,
        child: _SlideIn(key: ValueKey(_progress.step), forward: _forward, child: body),
      ),
      // The foot bar stays put while the step slides (web: .sticky-foot).
      bottomNavigationBar: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _SaveAlert(failed: queue.failed, onRetry: queue.flush),
            ?foot,
          ],
        ),
      ),
    );
  }

  // --- pick ----------------------------------------------------------------------------

  Widget _pickBody(Strings s) {
    final picked = {for (final m in _progress.picks) m.id};
    final searching = _query.isNotEmpty;
    final films = searching
        ? ref.watch(onboardingSearchProvider(_query))
        : ref.watch(onboardingFilmsProvider(_progress.offset));

    void toggle(Movie movie) => _update(_progress.copyWith(
          picks: picked.contains(movie.id)
              ? [for (final m in _progress.picks) if (m.id != movie.id) m]
              : [..._progress.picks, movie],
        ));

    final Widget content = switch (films) {
      AsyncValue(value: final list?) when list.isEmpty => SliverToBoxAdapter(
          child: searching
              ? Padding(
                  padding: const EdgeInsets.symmetric(vertical: AppSpacing.x3),
                  child: Semantics(
                    liveRegion: true,
                    child: Text(s.t('onboarding.pick.noResults', {'q': _query})),
                  ),
                )
              : EmptyState(
                  message: s.t('onboarding.pick.empty'),
                  actionLabel: s.t('onboarding.pick.search'),
                  onAction: _searchFocus.requestFocus,
                ),
        ),
      AsyncValue(value: final list?) => _PickGrid(films: list, picked: picked, onToggle: toggle),
      AsyncValue(hasError: true) => SliverToBoxAdapter(
          child: ErrorState(
            message: s.t('onboarding.pick.error'),
            onRetry: () => searching
                ? ref.invalidate(onboardingSearchProvider(_query))
                : ref.invalidate(onboardingFilmsProvider(_progress.offset)),
          ),
        ),
      _ => const _GridSkeleton(),
    };

    return CustomScrollView(
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(AppSpacing.x3, AppSpacing.x3, AppSpacing.x3, 0),
          sliver: SliverList.list(children: [
            const _Progress(step: 1),
            _Title(s.t('onboarding.pick.title')),
            const SizedBox(height: AppSpacing.x1),
            Text(s.t('onboarding.pick.subtitle')),
            const SizedBox(height: AppSpacing.x3),
            TextField(
              key: const Key('onboarding.search'),
              controller: _search,
              focusNode: _searchFocus,
              onChanged: _onSearchChanged,
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                hintText: s.t('onboarding.pick.searchPlaceholder'),
                prefixIcon: const Icon(Icons.search, color: AppColors.muted),
                filled: true,
                fillColor: AppColors.surface,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(AppRadius.sm),
                  borderSide: const BorderSide(color: AppColors.line),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.x3),
          ]),
        ),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(AppSpacing.x3, 0, AppSpacing.x3, AppSpacing.x3),
          sliver: content,
        ),
      ],
    );
  }

  Widget _pickFoot(Strings s, _Counts counts) {
    final need = (requiredRatings - counts.rated - _progress.picks.length).clamp(0, requiredRatings);
    final total = (counts.rated + _progress.picks.length).clamp(0, requiredRatings);
    return _Foot(children: [
      Row(
        children: [
          Expanded(
            child: Semantics(
              liveRegion: true,
              child: Text(s.t('onboarding.pick.count', {'n': total}),
                  style: const TextStyle(color: AppColors.muted, fontSize: 13)),
            ),
          ),
          if (_search.text.trim().isEmpty)
            TextButton(
              onPressed: () =>
                  _update(_progress.copyWith(offset: _progress.offset + onboardingPage)),
              child: Text(s.t('onboarding.pick.noneSeen')),
            ),
        ],
      ),
      const SizedBox(height: AppSpacing.x1),
      FilledButton(
        onPressed: need > 0
            ? null
            : () => _update(_progress.copyWith(step: OnboardingStep.rate, index: 0)),
        child: Text(need > 0
            ? s.t('onboarding.pick.needMore', {'n': need})
            : s.t('onboarding.pick.continue')),
      ),
    ]);
  }

  // --- rate ----------------------------------------------------------------------------

  Movie? get _film => _progress.picks.elementAtOrNull(_progress.index);

  void _advance(List<Movie> picks, int index, int rated) {
    if (index < picks.length) {
      _update(_progress.copyWith(picks: picks, index: index));
    } else if (rated >= requiredRatings) {
      _update(_progress.copyWith(step: OnboardingStep.done, picks: const [], index: 0));
    } else {
      _update(_progress.copyWith(picks: const [], index: 0));
    }
  }

  // Next moves on at once: the score is captured here, tied to this film's id, and saved in
  // the background by the queue (web: tester 1, 2026-10-12).
  void _next(_Counts counts) {
    final film = _film;
    if (film == null || _guard != null) return;
    counts.queue.enqueue(UnsavedRating(
      movieId: film.id,
      title: film.title,
      score: _score,
      likedAspects: _score > likedAspectsAbove ? _aspects : const [],
    ));
    // Counted here: the rebuild with the queue's new state comes after this call.
    final rated = counts.rated + (counts.ratedIds.contains(film.id) ? 0 : 1);
    _advance(_progress.picks, _progress.index + 1, rated);
  }

  void _notSeen(_Counts counts) {
    final picks = [
      for (final (i, m) in _progress.picks.indexed)
        if (i != _progress.index) m,
    ];
    _advance(picks, _progress.index, counts.rated);
  }

  Widget _rateBody(Strings s, _Counts counts) {
    final film = _film;
    if (film == null) {
      final need = (requiredRatings - counts.rated).clamp(0, requiredRatings);
      return Padding(
        padding: const EdgeInsets.all(AppSpacing.x3),
        child: Column(children: [
          const _Progress(step: 2),
          Expanded(
            child: EmptyState(
              message: s.t('onboarding.rate.needMore', {'n': need}),
              actionLabel: s.t('onboarding.rate.pickMore'),
              onAction: () => _update(_progress.copyWith(
                  step: OnboardingStep.pick, picks: const [], index: 0)),
            ),
          ),
        ]),
      );
    }
    final lang = s.lang;
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.x3),
      children: [
        const _Progress(step: 2),
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            Expanded(child: _Title(s.t('onboarding.rate.title'))),
            Text(
              s.t('onboarding.rate.position', {'i': _progress.index + 1, 'n': _progress.picks.length}),
              style: const TextStyle(fontFamily: AppFonts.mono, color: AppColors.muted, fontSize: 13),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.x3),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(width: 120, child: Poster(key: ValueKey(film.id), movie: film)),
            const SizedBox(width: AppSpacing.x3),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(film.title,
                      style: const TextStyle(
                        fontFamily: AppFonts.head,
                        fontWeight: FontWeight.w800,
                        fontSize: 22,
                        color: AppColors.text,
                      )),
                  const SizedBox(height: AppSpacing.x1),
                  Text(movieMeta(film, s)),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.x3),
        ExcludeSemantics(
          child: Text(
            formatScore(_score, lang),
            key: const Key('onboarding.score'),
            style: const TextStyle(
              fontFamily: AppFonts.head,
              fontWeight: FontWeight.w800,
              fontSize: 44,
              height: 1,
              color: AppColors.text,
            ),
          ),
        ),
        ExcludeSemantics(child: Text(s.t('onboarding.rate.outOf'))),
        Slider(
          value: _score,
          min: 0.5,
          max: 10,
          divisions: 19,
          activeColor: AppColors.text,
          inactiveColor: AppColors.line,
          thumbColor: AppColors.text,
          semanticFormatterCallback: (v) => '${s.t('onboarding.rate.scoreLabel')}: '
              '${formatScore(v, lang)}',
          onChanged: (v) => setState(() => _score = v),
        ),
        const ExcludeSemantics(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [Text('0.5'), Text('5.0'), Text('10')],
          ),
        ),
        if (_score > likedAspectsAbove) ...[
          const SizedBox(height: AppSpacing.x3),
          Text(s.t('onboarding.rate.liked'),
              style: const TextStyle(color: AppColors.text, fontWeight: FontWeight.w600)),
          const SizedBox(height: AppSpacing.x2),
          Wrap(
            key: const Key('onboarding.likedAspects'),
            spacing: AppSpacing.x2,
            runSpacing: AppSpacing.x2,
            children: [
              for (final key in traitKeys)
                FilterChip(
                  label: Text(s.t(traitLabelKey(key))),
                  selected: _aspects.contains(key),
                  onSelected: (on) => setState(() => _aspects = on
                      ? [..._aspects, key]
                      : [for (final a in _aspects) if (a != key) a]),
                ),
            ],
          ),
        ],
      ],
    );
  }

  Widget? _rateFoot(Strings s, _Counts counts) {
    if (_film == null) return null;
    return _Foot(children: [
      Row(
        children: [
          Expanded(
            child: OutlinedButton(
              onPressed: () => _notSeen(counts),
              child: Text(s.t('onboarding.rate.notSeen'), textAlign: TextAlign.center),
            ),
          ),
          const SizedBox(width: AppSpacing.x2),
          Expanded(
            flex: 2,
            child: FilledButton(
              onPressed: () => _next(counts),
              child: Text(s.t('onboarding.rate.next')),
            ),
          ),
        ],
      ),
    ]);
  }

  // --- done ----------------------------------------------------------------------------

  Future<void> _finish(_Counts counts) async {
    if (!counts.canFinish) return;
    _markDone(ref.read(apiClientProvider)).ignore();
    await clearProgress(ref.read(localStoreProvider), widget.userId);
    // /me and the feed say how many ratings are still needed; the next screen must see the
    // new count, not the cached one that would send the user back here (web: F3 item 1,
    // 2026-10-08).
    ref.invalidate(meProvider);
    ref.invalidate(ratingsProvider);
    ref.invalidate(recommendationsProvider);
    widget.onFinished();
  }

  /// POST /onboarding/done, tried up to four times (web: retry 3).
  static Future<void> _markDone(ApiClient api) async {
    for (var attempt = 0; attempt < 4; attempt++) {
      try {
        await api.onboardingDone();
        return;
      } on Object {
        await Future<void>.delayed(Duration(seconds: 1 << attempt));
      }
    }
  }

  Widget _doneBody(Strings s, _Counts counts) => ListView(
        padding: const EdgeInsets.all(AppSpacing.x3),
        children: [
          const _Progress(step: 3),
          _Title(s.t('onboarding.done.title')),
          const SizedBox(height: AppSpacing.x2),
          Text(s.t('onboarding.done.body', {'n': counts.rated}),
              style: const TextStyle(color: AppColors.text)),
          if (!counts.canFinish && counts.queue.failed.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x2),
            Text(
              s.t('onboarding.done.waiting', {'n': requiredRatings - counts.confirmed}),
              key: const Key('onboarding.waiting'),
            ),
          ],
          const SizedBox(height: AppSpacing.x4),
          FilledButton(
            onPressed: counts.canFinish ? () => _finish(counts) : null,
            child: Text(!counts.canFinish && counts.saving
                ? s.t('common.saving')
                : s.t('onboarding.done.cta')),
          ),
        ],
      );
}

/// The numbers every step needs, read once per build.
class _Counts {
  _Counts({required Set<int> rated, required this.confirmed, required this.queue})
      : ratedIds = rated;

  /// Films rated: on the server, saved this run, or on their way.
  final Set<int> ratedIds;
  int get rated => ratedIds.length;

  /// Scores the server has confirmed.
  final int confirmed;
  final RatingQueue queue;

  /// Every score saved, or 10 already on the server: the rest stay queued and keep being
  /// retried. Below 10 the feed could only send the user back here.
  bool get canFinish => queue.unsaved.isEmpty || confirmed >= requiredRatings;
  bool get saving => queue.unsaved.length > queue.failed.length;
}

// --- pieces ------------------------------------------------------------------------------

class _Title extends StatelessWidget {
  const _Title(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Semantics(
        header: true,
        child: Text(text,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 26)),
      );
}

/// Three bars, the reached ones white (web: .progress-dots).
class _Progress extends ConsumerWidget {
  const _Progress({required this.step});

  final int step;

  @override
  Widget build(BuildContext context, WidgetRef ref) => Semantics(
        label: ref.watch(stringsProvider).t('onboarding.progress', {'step': step}),
        child: Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.x3),
          child: Row(
            children: [
              for (var n = 1; n <= 3; n++) ...[
                if (n > 1) const SizedBox(width: AppSpacing.x1),
                Expanded(
                  child: Container(
                    height: 3,
                    decoration: BoxDecoration(
                      color: n <= step ? AppColors.text : AppColors.line,
                      borderRadius: BorderRadius.circular(99),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      );
}

/// Posters to pick: about 84 px wide or more, as many columns as fit (web: .grid).
class _PickGrid extends ConsumerWidget {
  const _PickGrid({required this.films, required this.picked, required this.onToggle});

  final List<Movie> films;
  final Set<int> picked;
  final void Function(Movie) onToggle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return SliverLayoutBuilder(builder: (context, constraints) {
      const gap = 10.0;
      final width = constraints.crossAxisExtent;
      final columns = ((width + gap) / (84 + gap)).floor().clamp(1, 12);
      final tile = (width - gap * (columns - 1)) / columns;
      return SliverGrid.builder(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: columns,
          crossAxisSpacing: gap,
          mainAxisSpacing: gap,
          // poster + two lines of title + the border
          mainAxisExtent: (tile - 4) * 1.5 + 42 * MediaQuery.textScalerOf(context).scale(1),
        ),
        itemCount: films.length,
        itemBuilder: (context, i) {
          final movie = films[i];
          final on = picked.contains(movie.id);
          return Semantics(
            button: true,
            toggled: on,
            label: on ? s.t('onboarding.pick.selected', {'title': movie.title}) : movie.title,
            excludeSemantics: true,
            child: GestureDetector(
              key: ValueKey('pick.${movie.id}'),
              onTap: () => onToggle(movie),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  border: Border.all(color: on ? AppColors.text : Colors.transparent, width: 2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Stack(
                      children: [
                        Poster(movie: movie, size: 'w185'),
                        if (on)
                          Positioned(
                            top: 6,
                            right: 6,
                            child: Container(
                              width: 22,
                              height: 22,
                              decoration: const BoxDecoration(
                                  color: AppColors.text, shape: BoxShape.circle),
                              child: const Icon(Icons.check, size: 14, color: AppColors.bg),
                            ),
                          ),
                      ],
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(2, 4, 2, 0),
                      child: Text(movie.title,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppColors.text,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            height: 1.25,
                          )),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      );
    });
  }
}

class _GridSkeleton extends ConsumerWidget {
  const _GridSkeleton();

  @override
  Widget build(BuildContext context, WidgetRef ref) => SliverToBoxAdapter(
        child: Semantics(
          key: const Key('onboarding.loading'),
          label: ref.watch(stringsProvider).t('common.loading'),
          child: Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              for (var i = 0; i < 12; i++)
                Container(
                  width: 96,
                  height: 144,
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                  ),
                ),
            ],
          ),
        ),
      );
}

/// The fixed bar at the bottom (web: .sticky-foot).
class _Foot extends StatelessWidget {
  const _Foot({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: const BoxDecoration(
          color: AppColors.surface,
          border: Border(top: BorderSide(color: AppColors.line)),
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(AppSpacing.x3, 10, AppSpacing.x3, 12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: children,
          ),
        ),
      );
}

/// Scores the server has not taken: named, with Try again, above the foot bar; it stays
/// until they are saved (web: SaveAlert).
class _SaveAlert extends ConsumerWidget {
  const _SaveAlert({required this.failed, required this.onRetry});

  final List<UnsavedRating> failed;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (failed.isEmpty) return const SizedBox.shrink();
    final s = ref.watch(stringsProvider);
    return Semantics(
      liveRegion: true,
      child: Container(
        key: const Key('onboarding.saveAlert'),
        color: AppColors.surface2,
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x3, vertical: AppSpacing.x2),
        child: Row(
          children: [
            Expanded(
              child: Text(
                s.t('onboarding.rate.unsaved', {'titles': failed.map((u) => u.title).join(', ')}),
                style: const TextStyle(color: AppColors.text),
              ),
            ),
            const SizedBox(width: AppSpacing.x2),
            OutlinedButton(onPressed: onRetry, child: Text(s.t('common.retry'))),
          ],
        ),
      ),
    );
  }
}

/// A new step slides in: 24 px and opacity over 200 ms, forward from the right, back from
/// the left (docs/ui.md 7). Nothing moves on arrival.
class _SlideIn extends StatefulWidget {
  const _SlideIn({super.key, required this.forward, required this.child});

  final bool? forward;
  final Widget child;

  @override
  State<_SlideIn> createState() => _SlideInState();
}

class _SlideInState extends State<_SlideIn> with SingleTickerProviderStateMixin {
  late final _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 200),
    value: widget.forward == null ? 1 : 0,
  )..forward();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final from = widget.forward == false ? -24.0 : 24.0;
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final t = Curves.easeOut.transform(_controller.value);
        return Opacity(
          opacity: t,
          child: Transform.translate(offset: Offset(from * (1 - t), 0), child: child),
        );
      },
      child: widget.child,
    );
  }
}
