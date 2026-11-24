/// The match band and the heading over a recommendation's sentence. Mirrors
/// apps/web/src/components/MatchBand.tsx and Kicker.tsx.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';

/// The band the UI shows (FR-5, TZ 1.16): "strong" only, the user's few closest films. The
/// API still sends "good" (ordering, and so the decision is easy to undo), but it is not
/// drawn: on the web Home it appeared on 68% of the pages, so it told nothing apart.
bool showsStrong(MatchBand? band) => band == MatchBand.strong;

/// "Strong match" as a red pill (top-left on posters); nothing otherwise.
class BandPill extends ConsumerWidget {
  const BandPill({super.key, required this.band});

  final MatchBand? band;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (!showsStrong(band)) return const SizedBox.shrink();
    return DecoratedBox(
      decoration: BoxDecoration(
        color: AppColors.red,
        borderRadius: BorderRadius.circular(99),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        child: Text(
          ref.watch(stringsProvider).t('band.strong'),
          style: const TextStyle(
            color: AppColors.bg,
            fontSize: 11,
            fontWeight: FontWeight.w700,
            height: 1.5,
          ),
        ),
      ),
    );
  }
}

/// The heading a sentence completes (TZ 1.25): why the film suits the viewer, or how it
/// differs. Red "STRONG MATCH" for one of the viewer's closest films, unless the sentence
/// under it describes the film's differences: then the neutral difference heading, because
/// red over "this film differs from you" is the pairing TZ 1.23/1.24 removed. With nothing
/// named there is no sentence, but the band is still true and keeps the red heading.
class Kicker extends ConsumerWidget {
  const Kicker({super.key, required this.band, this.side});

  final MatchBand? band;
  final TraitSide? side;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strong = showsStrong(band) && side != TraitSide.difference;
    final key = strong
        ? 'band.strongHeading'
        : switch (side) {
            TraitSide.reason => 'movie.whyKickerReason',
            TraitSide.difference => 'movie.whyKickerDifference',
            null => 'movie.whyKicker',
          };
    return Text(
      ref.watch(stringsProvider).t(key).toUpperCase(),
      style: TextStyle(
        color: strong ? AppColors.red : AppColors.muted,
        fontSize: 15,
        fontWeight: FontWeight.w800,
        letterSpacing: 1.5,
        height: 1.3,
      ),
    );
  }
}
