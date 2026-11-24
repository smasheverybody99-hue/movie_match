/// The feed's hero: the top of "For you", one film at a time, its backdrop across the full
/// width. Mirrors apps/web/src/components/Hero.tsx: the kicker, the title, year and runtime,
/// then a short sentence (the cached explanation from the recommendations response, else
/// the same free fallback as the film page; the hero never asks for an explanation, so a
/// rotation spends no money and no daily cap). "See why" and Save.
///
/// Rotation every 7 s. It holds while a finger is on the hero and after Pause, and stops
/// once the viewer steers it (a swipe, the dots, prev / next); Play resumes it. With
/// animations turned off on the phone it never moves on its own and has no Pause.
///
/// Phone difference: the slides are swiped (a PageView), as phones do, besides the buttons.
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../data/traits.dart';
import '../format.dart';
import '../i18n/i18n.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import 'backdrop.dart';
import 'match_band.dart';
import 'not_right.dart';
import 'shown.dart';

/// How long one film stays before the next (docs/ui.md, 4a).
const heroInterval = Duration(seconds: 7);

/// The hero shows the top of "For you", at most this many.
const heroCount = 5;

/// The sentence under the kicker, or null: the cached explanation, else the free fallback
/// from the named traits. A film with nothing named gets none rather than a claim with
/// nothing behind it (TZ 1.27).
String? heroSentence(Recommendation item, Strings s) {
  if (item.explanation != null) return item.explanation;
  final side = heroSide(item);
  if (side == null) return null;
  final traits = _named(item).map((key) => s.t(traitLabelKey(key))).join(', ');
  return s.t(side == TraitSide.difference ? 'movie.differsFallback' : 'movie.whyYouFallback',
      {'traits': traits});
}

/// The side the sentence falls on; none when nothing is named.
TraitSide? heroSide(Recommendation item) => _named(item).isEmpty ? null : item.traitSide;

List<String> _named(Recommendation item) =>
    item.namedTraits.where(traitKeys.contains).take(3).toList();

class FeedHero extends ConsumerStatefulWidget {
  const FeedHero({
    super.key,
    required this.items,
    required this.saved,
    required this.onToggleSave,
    required this.onOpen,
  });

  final List<Recommendation> items;
  final Set<int> saved;
  final void Function(Movie movie, bool isSaved) onToggleSave;
  final void Function(Movie movie) onOpen;

  @override
  ConsumerState<FeedHero> createState() => _FeedHeroState();
}

class _FeedHeroState extends ConsumerState<FeedHero> {
  final _pages = PageController();
  int _index = 0;
  bool _paused = false;
  bool _touching = false;
  Timer? _timer;

  int get _count => widget.items.length;

  // From didChangeDependencies: animations off on the phone, and this route on top.
  bool _reduce = false;
  bool _ticking = true;

  bool get _playing => !_reduce && _ticking && !_paused && !_touching && _count > 1;

  void _setPaused(bool value) {
    setState(() => _paused = value);
    _restartTimer();
  }

  /// A person taking control (dots, prev / next, a swipe): the rotation stops, so a slide
  /// never moves under someone who is already steering.
  void _go(int next) {
    _setPaused(true);
    _show((next + _count) % _count);
  }

  void _show(int i) {
    if (!_pages.hasClients) return;
    if (_reduce || (i - _index).abs() != 1) {
      _pages.jumpToPage(i);
    } else {
      _pages.animateToPage(i, duration: const Duration(milliseconds: 400), curve: Curves.easeOut);
    }
  }

  void _restartTimer() {
    _timer?.cancel();
    _timer = null;
    if (!mounted || !_playing) return;
    _timer = Timer(heroInterval, () {
      if (mounted) _show((_index + 1) % _count);
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _reduce = MediaQuery.disableAnimationsOf(context);
    _ticking = TickerMode.valuesOf(context).enabled;
    _restartTimer();
  }

  @override
  void didUpdateWidget(FeedHero old) {
    super.didUpdateWidget(old);
    // A slide taken out ("Not right?") can leave the index past the end: hold the last one.
    if (_count > 0 && _index >= _count) {
      _index = _count - 1;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_pages.hasClients) _pages.jumpToPage(_index);
      });
    }
    if (old.items.length != _count) _restartTimer();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pages.dispose();
    super.dispose();
  }

  void _setTouching(bool value) {
    setState(() => _touching = value);
    _restartTimer();
  }

  @override
  Widget build(BuildContext context) {
    if (_count == 0) return const SizedBox.shrink();
    final s = ref.watch(stringsProvider);
    // As on the web, about half the screen; plus the controls, and plus what larger text
    // adds to the ~220 px of text and buttons, so nothing is cut off at any text size.
    final text = MediaQuery.textScalerOf(context);
    final height =
        (MediaQuery.sizeOf(context).height * 0.48).clamp(280.0, 520.0) + 72 + text.scale(220) - 220;
    return Semantics(
      container: true,
      label: s.t('hero.label'),
      child: SizedBox(
        height: height,
        child: Listener(
          // A finger on the hero holds it, so the slide cannot change under a tap; lifting
          // it starts the 7 s again from zero.
          onPointerDown: (_) => _setTouching(true),
          onPointerUp: (_) => _setTouching(false),
          onPointerCancel: (_) => _setTouching(false),
          child: Stack(
            children: [
              NotificationListener<ScrollStartNotification>(
                onNotification: (n) {
                  if (n.dragDetails != null) _setPaused(true);
                  return false;
                },
                child: PageView.builder(
                  controller: _pages,
                  itemCount: _count,
                  onPageChanged: (i) {
                    setState(() => _index = i);
                    _restartTimer();
                  },
                  itemBuilder: (context, i) => _Slide(
                    key: ValueKey(widget.items[i].movie.id),
                    item: widget.items[i],
                    label: s.t('hero.slide', {'n': i + 1, 'total': _count}),
                    saved: widget.saved.contains(widget.items[i].movie.id),
                    onToggleSave: widget.onToggleSave,
                    onOpen: widget.onOpen,
                  ),
                ),
              ),
              if (_count > 1)
                Positioned(
                  left: AppSpacing.x3,
                  right: AppSpacing.x3,
                  bottom: AppSpacing.x3,
                  child: Row(
                    children: [
                      _Control(
                        icon: Icons.chevron_left,
                        label: s.t('hero.prev'),
                        onTap: () => _go(_index - 1),
                      ),
                      for (var i = 0; i < _count; i++)
                        Semantics(
                          button: true,
                          selected: i == _index,
                          label: s.t('hero.goTo', {'n': i + 1, 'total': _count}),
                          excludeSemantics: true,
                          child: InkResponse(
                            key: Key('hero.dot.$i'),
                            onTap: () => _go(i),
                            radius: 16,
                            child: Padding(
                              padding: const EdgeInsets.all(8),
                              child: DecoratedBox(
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: i == _index ? AppColors.text : AppColors.faint,
                                ),
                                child: const SizedBox(width: 8, height: 8),
                              ),
                            ),
                          ),
                        ),
                      _Control(
                        icon: Icons.chevron_right,
                        label: s.t('hero.next'),
                        onTap: () => _go(_index + 1),
                      ),
                      if (!_reduce)
                        _Control(
                          icon: _paused ? Icons.play_arrow : Icons.pause,
                          label: _paused ? s.t('hero.play') : s.t('hero.pause'),
                          onTap: () => _setPaused(!_paused),
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

class _Control extends StatelessWidget {
  const _Control({required this.icon, required this.label, required this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => IconButton(
        tooltip: label,
        onPressed: onTap,
        icon: Icon(icon, color: AppColors.text),
        style: IconButton.styleFrom(
          backgroundColor: AppColors.bg.withValues(alpha: 0.5),
          side: const BorderSide(color: AppColors.muted),
        ),
      );
}

class _Slide extends ConsumerWidget {
  const _Slide({
    super.key,
    required this.item,
    required this.label,
    required this.saved,
    required this.onToggleSave,
    required this.onOpen,
  });

  final Recommendation item;
  final String label;
  final bool saved;
  final void Function(Movie movie, bool isSaved) onToggleSave;
  final void Function(Movie movie) onOpen;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final movie = item.movie;
    final sentence = heroSentence(item, s);
    final meta = movieMeta(movie, s);
    final theme = Theme.of(context);
    return ShownTracker(
      movieId: movie.id,
      source: EventSource.forYou,
      child: Semantics(
        container: true,
        label: label,
        child: Stack(
          fit: StackFit.expand,
          children: [
            Backdrop(movie: movie),
            const BackdropShade(),
            Padding(
              // Room at the bottom for the controls, which do not move with the slides.
              padding: const EdgeInsets.fromLTRB(AppSpacing.x3, 0, AppSpacing.x3, 72),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Kicker(band: item.band, side: heroSide(item)),
                  const SizedBox(height: AppSpacing.x2),
                  Semantics(
                    header: true,
                    child: Text(
                      movie.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.headlineMedium
                          ?.copyWith(fontSize: 26, height: 1.1, color: AppColors.text),
                    ),
                  ),
                  if (meta.isNotEmpty) ...[
                    const SizedBox(height: AppSpacing.x2),
                    Text(meta, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
                  ],
                  if (sentence != null) ...[
                    const SizedBox(height: AppSpacing.x2),
                    Text(
                      sentence,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontFamily: AppFonts.head,
                        fontWeight: FontWeight.w700,
                        fontSize: 15,
                        height: 1.35,
                        color: AppColors.text,
                      ),
                    ),
                  ],
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: AppSpacing.x2,
                    runSpacing: AppSpacing.x2,
                    children: [
                      OutlinedButton.icon(
                        onPressed: () => onOpen(movie),
                        icon: const Icon(Icons.auto_awesome, size: 18),
                        label: Text(s.t('hero.why')),
                      ),
                      OutlinedButton.icon(
                        onPressed: () => onToggleSave(movie, saved),
                        icon: Icon(saved ? Icons.bookmark_added : Icons.bookmark_border, size: 18),
                        label: Text(saved ? s.t('movie.onList') : s.t('movie.saveToList')),
                      ),
                    ],
                  ),
                  NotRightButton(movie: movie, source: EventSource.forYou),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
