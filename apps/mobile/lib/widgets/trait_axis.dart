/// One trait on one 0-100 axis, and the key to its two dots. Mirrors TraitAxis, AxisLegend
/// and axisPositions in apps/web/src/components/Traits.tsx: the user's taste is a filled
/// dot with its number above, the film an outlined dot with its number below, the distance
/// between them a line. Shape, not shade, tells them apart. A taste not known yet (null)
/// leaves its dot out rather than drawing it at 0. Screen readers get one label with both
/// values.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart' show Lang;
import '../data/traits.dart';
import '../i18n/i18n.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';

/// The least distance between the two dots' centres: a 12 px dot plus 8 px clear.
const dotGap = 20.0;
const _dot = 12.0;

/// A trait's name inside a sentence. Russian writes common nouns in a list in lower case;
/// labels on their own keep the capital.
String traitInSentence(String key, Strings s) {
  final label = s.t(traitLabelKey(key));
  return s.lang == Lang.ru ? label.toLowerCase() : label;
}

/// Where the two dots' centres sit on an axis `width` px wide. Each sits at its value
/// unless the two would be closer than [dotGap]; then both move apart from their midpoint
/// to exactly [dotGap], and stay inside the axis. The true values stay in the numbers and
/// the label.
({double you, double film}) axisPositions(int you, int film, double width) {
  double at(int v) => width * v / 100;
  final lo = at(you < film ? you : film);
  final hi = at(you < film ? film : you);
  final mid = (lo + hi) / 2;
  final low = (lo < mid - dotGap / 2 ? lo : mid - dotGap / 2).clamp(0.0, width - dotGap);
  final high = (hi > mid + dotGap / 2 ? hi : mid + dotGap / 2).clamp(dotGap, width);
  return you <= film ? (you: low, film: high) : (you: high, film: low);
}

class TraitAxis extends ConsumerWidget {
  const TraitAxis({super.key, required this.trait, required this.taste, required this.film});

  final String trait;
  final int? taste;
  final int film;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final name = s.t(traitLabelKey(trait));
    final you = taste;
    final values = [
      if (you != null) '${s.t('movie.compareYou')} $you',
      '${s.t('movie.compareFilm')} $film',
    ].join(', ');
    return Semantics(
      key: Key('axis.$trait'),
      container: true,
      label: '$name: $values',
      excludeSemantics: true,
      child: Padding(
        padding: const EdgeInsets.only(bottom: AppSpacing.x2),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(name, style: const TextStyle(fontSize: 13, color: AppColors.muted)),
            SizedBox(
              height: 52,
              child: LayoutBuilder(builder: (context, box) {
                // The dots' centres stay half a dot inside each end.
                final width = box.maxWidth - _dot;
                final at = you == null
                    ? (you: null, film: width * film / 100)
                    : axisPositions(you, film, width);
                final youAt = at.you;
                Widget number(double centre, int value, {required bool above}) => Positioned(
                      left: (centre + _dot / 2 - 16).clamp(0.0, box.maxWidth - 32),
                      width: 32,
                      top: above ? 0 : null,
                      bottom: above ? null : 0,
                      child: Text('$value',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 12,
                            fontFamily: AppFonts.mono,
                            color: above ? AppColors.text : AppColors.muted,
                          )),
                    );
                Widget dot(double centre, {required bool filled, required Key key}) => Positioned(
                      key: key,
                      left: centre,
                      top: 26 - _dot / 2,
                      child: Container(
                        width: _dot,
                        height: _dot,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: filled ? AppColors.text : AppColors.bg,
                          border: Border.all(color: AppColors.text, width: 2),
                        ),
                      ),
                    );
                return Stack(
                  clipBehavior: Clip.none,
                  children: [
                    Positioned(
                      left: _dot / 2,
                      right: _dot / 2,
                      top: 25,
                      child: Container(height: 2, color: AppColors.line),
                    ),
                    if (youAt != null) ...[
                      Positioned(
                        left: _dot / 2 + (youAt < at.film ? youAt : at.film),
                        width: (youAt - at.film).abs(),
                        top: 25,
                        child: Container(height: 2, color: AppColors.muted),
                      ),
                      number(youAt, you!, above: true),
                      dot(youAt, filled: true, key: const Key('axis.you')),
                    ],
                    dot(at.film, filled: false, key: const Key('axis.film')),
                    number(at.film, film, above: false),
                  ],
                );
              }),
            ),
          ],
        ),
      ),
    );
  }
}

/// The key to the two dots: you a filled circle, the film an outlined one.
class AxisLegend extends ConsumerWidget {
  const AxisLegend({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    Widget key(bool filled, String label) => Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 10,
              height: 10,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: filled ? AppColors.text : AppColors.bg,
                border: Border.all(color: AppColors.text, width: 2),
              ),
            ),
            const SizedBox(width: 6),
            Text(label, style: const TextStyle(fontSize: 12, color: AppColors.muted)),
          ],
        );
    return ExcludeSemantics(
      key: const Key('axis.legend'),
      child: Padding(
        padding: const EdgeInsets.only(bottom: AppSpacing.x2),
        child: Row(children: [
          key(true, s.t('movie.compareYou')),
          const SizedBox(width: AppSpacing.x3),
          key(false, s.t('movie.compareFilm')),
        ]),
      ),
    );
  }
}
