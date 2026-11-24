/// `recommendation_shown` for the closed alpha (Phase 5): once at least half of a card has
/// been in view for a second (user decision, 2026-11-17). Mirrors useShownRef in
/// apps/web/src/lib/telemetry.ts, which uses IntersectionObserver; here the card measures
/// itself against every scrolling area it sits in (the feed, its row, the hero's pages) and
/// against the screen, whenever one of them scrolls. A screen covered by another route
/// counts as out of view. Telemetry records each film and source once per app run.
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../state/app_state.dart';

const shownRatio = 0.5;
const shownAfter = Duration(seconds: 1);

class ShownTracker extends ConsumerStatefulWidget {
  const ShownTracker({
    super.key,
    required this.movieId,
    required this.source,
    required this.child,
  });

  final int movieId;
  final EventSource source;
  final Widget child;

  @override
  ConsumerState<ShownTracker> createState() => _ShownTrackerState();
}

class _ShownTrackerState extends ConsumerState<ShownTracker> {
  final _positions = <ScrollPosition>[];
  Timer? _wait;
  bool _done = false;
  bool _onScreen = true; // the route is the current one (TickerMode)

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _onScreen = TickerMode.valuesOf(context).enabled;
    _listen();
    _scheduleCheck();
  }

  @override
  void didUpdateWidget(ShownTracker old) {
    super.didUpdateWidget(old);
    if (old.movieId != widget.movieId || old.source != widget.source) {
      _done = false;
      _cancel();
      _scheduleCheck();
    }
  }

  void _listen() {
    for (final p in _positions) {
      p.removeListener(_check);
    }
    _positions.clear();
    BuildContext? at = context;
    while (at != null) {
      final scrollable = Scrollable.maybeOf(at);
      if (scrollable == null) break;
      _positions.add(scrollable.position..addListener(_check));
      at = scrollable.context;
    }
  }

  void _scheduleCheck() =>
      WidgetsBinding.instance.addPostFrameCallback((_) => mounted ? _check() : null);

  double _ratio() {
    final box = context.findRenderObject();
    if (box is! RenderBox || !box.attached || !box.hasSize || box.size.isEmpty) return 0;
    final own = box.localToGlobal(Offset.zero) & box.size;
    var visible = own.intersect(Offset.zero & MediaQuery.sizeOf(context));
    for (final p in _positions) {
      final viewport = p.context.notificationContext?.findRenderObject();
      if (viewport is RenderBox && viewport.attached && viewport.hasSize) {
        visible = visible.intersect(viewport.localToGlobal(Offset.zero) & viewport.size);
      }
    }
    if (visible.width <= 0 || visible.height <= 0) return 0;
    return visible.width * visible.height / (own.width * own.height);
  }

  void _check() {
    if (_done || !mounted) return;
    if (_onScreen && _ratio() >= shownRatio) {
      _wait ??= Timer(shownAfter, _fire);
    } else {
      _cancel();
    }
  }

  void _fire() {
    _wait = null;
    if (!mounted || _done) return;
    if (!_onScreen || _ratio() < shownRatio) return;
    _done = true;
    ref.read(telemetryProvider).track(RecommendationEvent(
          clicked: false,
          at: DateTime.now(),
          movieId: widget.movieId,
          source: widget.source,
        ));
  }

  void _cancel() {
    _wait?.cancel();
    _wait = null;
  }

  @override
  void dispose() {
    _cancel();
    for (final p in _positions) {
      p.removeListener(_check);
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
