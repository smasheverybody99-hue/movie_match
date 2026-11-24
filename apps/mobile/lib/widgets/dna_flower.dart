/// Movie DNA as a radial chart. Mirrors apps/web/src/components/DnaFlower.tsx: one ray per
/// trait from the centre, its length linear in the value, at an angle fixed for everyone
/// (traits.json order, from 12 o'clock, clockwise), so two people's shapes compare at a
/// glance. Monochrome (DNA is not a match, so no red): the three strongest rays fully
/// white, the rest by value, never below 0.4. Faint rings at 50 and 100, and a faint
/// outline through the ray tips. Labels: on a phone only the three strongest, as on the
/// web below 640 px; the exact values are under Numbers. The rays grow on first paint,
/// one after another; not with animations turned off. One image with a summary label.
library;

import 'dart:math' as math;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../data/traits.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';

/// Geometry in the web's viewBox units: x -300..300, y -225..225.
const _viewX = 300.0;
const _viewY = 225.0;
const _inner = 40.0;
const _outer = 170.0;
const _label = 186.0;
const strongestRays = 3;

/// Where a value ends on its ray: linear, from the inner circle to the 100 ring.
double rayLength(num value) => _inner + (value.clamp(0, 100) / 100) * (_outer - _inner);

/// Each trait keeps one angle for everyone, from 12 o'clock, clockwise.
double rayAngle(int index) => -math.pi / 2 + index * 2 * math.pi / traitKeys.length;

/// A ray's brightness: the strongest fully white, the rest 0.4 at 0 to 0.85 at 100.
double rayOpacity(num value, {required bool strongest}) =>
    strongest ? 1 : 0.4 + 0.45 * (value.clamp(0, 100) / 100);

/// The three strongest traits; ties keep the traits.json order.
Set<String> strongestTraits(Map<String, int> scores) {
  final order = [...traitKeys];
  order.sort((a, b) {
    final by = (scores[b] ?? 0).compareTo(scores[a] ?? 0);
    return by != 0 ? by : traitKeys.indexOf(a).compareTo(traitKeys.indexOf(b));
  });
  return order.take(strongestRays).toSet();
}

/// A label of 12 characters or more on two lines, split at the space nearest its middle.
List<String> labelLines(String label) {
  if (label.length < 12 || !label.contains(' ')) return [label];
  final mid = label.length / 2;
  var best = -1;
  for (var i = label.indexOf(' '); i != -1; i = label.indexOf(' ', i + 1)) {
    if (best == -1 || (i - mid).abs() < (best - mid).abs()) best = i;
  }
  return [label.substring(0, best), label.substring(best + 1)];
}

class DnaFlower extends ConsumerStatefulWidget {
  const DnaFlower({super.key, required this.scores, required this.label});

  final Map<String, int> scores;
  final String label;

  @override
  ConsumerState<DnaFlower> createState() => _DnaFlowerState();
}

class _DnaFlowerState extends ConsumerState<DnaFlower> with SingleTickerProviderStateMixin {
  // 14 rays, 40 ms apart, each growing over 400 ms (web: the CSS animation).
  late final _grow = AnimationController(
    vsync: this,
    duration: Duration(milliseconds: traitKeys.length * 40 + 400),
  );

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.disableAnimationsOf(context)) {
      _grow.value = 1;
    } else if (_grow.value == 0 && !_grow.isAnimating) {
      _grow.forward();
    }
  }

  @override
  void dispose() {
    _grow.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final strongest = strongestTraits(widget.scores);
    final labels = {
      for (final key in strongest) key: labelLines(s.t(traitLabelKey(key))),
    };
    return Semantics(
      key: const Key('dna.flower'),
      image: true,
      label: widget.label,
      excludeSemantics: true,
      child: AspectRatio(
        aspectRatio: 4 / 3,
        child: AnimatedBuilder(
          animation: _grow,
          builder: (context, _) => CustomPaint(
            painter: _FlowerPainter(
              scores: widget.scores,
              strongest: strongest,
              labels: labels,
              progress: _grow.value,
              textScaler: MediaQuery.textScalerOf(context),
            ),
          ),
        ),
      ),
    );
  }
}

class _FlowerPainter extends CustomPainter {
  _FlowerPainter({
    required this.scores,
    required this.strongest,
    required this.labels,
    required this.progress,
    required this.textScaler,
  });

  final Map<String, int> scores;
  final Set<String> strongest;
  final Map<String, List<String>> labels;
  final double progress;
  final TextScaler textScaler;

  @override
  void paint(Canvas canvas, Size size) {
    final scale = math.min(size.width / (2 * _viewX), size.height / (2 * _viewY));
    canvas.translate(size.width / 2, size.height / 2);
    canvas.scale(scale);

    final ring = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..color = AppColors.line;
    canvas.drawCircle(Offset.zero, rayLength(50), ring);
    canvas.drawCircle(Offset.zero, _outer, ring);

    final total = traitKeys.length * 40 + 400;
    double grown(int i) => ((progress * total - i * 40) / 400).clamp(0.0, 1.0);

    // The outline through the tips, after the rays.
    final outline = Path();
    for (final (i, key) in traitKeys.indexed) {
      final r = rayLength(scores[key] ?? 0);
      final p = Offset(r * math.cos(rayAngle(i)), r * math.sin(rayAngle(i)));
      i == 0 ? outline.moveTo(p.dx, p.dy) : outline.lineTo(p.dx, p.dy);
    }
    outline.close();
    final shown = grown(traitKeys.length - 1);
    canvas.drawPath(outline, Paint()..color = AppColors.text.withValues(alpha: 0.06 * shown));
    canvas.drawPath(
      outline,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5
        ..strokeJoin = StrokeJoin.round
        ..color = Color.lerp(AppColors.line, AppColors.muted, 0.4)!.withValues(alpha: shown),
    );

    for (final (i, key) in traitKeys.indexed) {
      final value = scores[key] ?? 0;
      final top = strongest.contains(key);
      final a = rayAngle(i);
      final dir = Offset(math.cos(a), math.sin(a));
      final end = _inner + (rayLength(value) - _inner) * grown(i);
      canvas.drawLine(
        dir * _inner,
        dir * end,
        Paint()
          ..strokeWidth = top ? 8 : 6
          ..strokeCap = StrokeCap.round
          ..color = AppColors.text.withValues(alpha: rayOpacity(value, strongest: top)),
      );
      final text = labels[key];
      if (text != null) _paintLabel(canvas, text, dir);
    }
  }

  void _paintLabel(Canvas canvas, List<String> lines, Offset dir) {
    final painter = TextPainter(
      text: TextSpan(
        text: lines.join('\n'),
        style: const TextStyle(
          fontFamily: AppFonts.body,
          fontSize: 20,
          fontWeight: FontWeight.w700,
          height: 1.2,
          color: AppColors.text,
        ),
      ),
      textAlign: dir.dx.abs() < 0.2 ? TextAlign.center : (dir.dx > 0 ? TextAlign.left : TextAlign.right),
      textDirection: TextDirection.ltr,
      textScaler: textScaler,
    )..layout();
    final at = dir * _label;
    // Left half: the text ends at the ray; right half: starts there; top and bottom: centred.
    final dx = dir.dx.abs() < 0.2 ? -painter.width / 2 : (dir.dx > 0 ? 0.0 : -painter.width);
    // Above the centre the block grows upwards, below it downwards.
    final dy = dir.dy < -0.2 ? -painter.height : (dir.dy > 0.2 ? 0.0 : -painter.height / 2);
    // Kept inside the chart's box, so a long name is never cut by the screen's edge.
    final x = (at.dx + dx).clamp(-_viewX, _viewX - painter.width);
    final y = (at.dy + dy).clamp(-_viewY, _viewY - painter.height);
    painter.paint(canvas, Offset(x, y));
    painter.dispose();
  }

  @override
  bool shouldRepaint(_FlowerPainter old) =>
      old.progress != progress || old.scores != scores || old.textScaler != textScaler;
}
