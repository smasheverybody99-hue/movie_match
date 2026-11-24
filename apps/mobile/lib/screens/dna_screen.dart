/// /dna — the taste profile (FR-7). Mirrors apps/web/src/pages/Dna.tsx: the sentence, the
/// radial chart, the three stats, and the exact values under Numbers. Below 10 ratings
/// "rate N more", never empty bars; with 10 but no liked film, what is missing.
///
/// Phone differences: Share opens the phone's share sheet (the parity table), else copies
/// the text, as the web does where there is no sheet.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../data/traits.dart';
import '../format.dart';
import '../i18n/i18n.dart';
import '../share.dart';
import '../state/app_state.dart';
import '../state/film_state.dart';
import '../theme/tokens.dart';
import '../widgets/dna_flower.dart';
import '../widgets/states.dart';
import '../widgets/trait_axis.dart' show traitInSentence;

/// The taste vector as (trait, score), strongest first; ties keep the vector order;
/// unknown keys are left out.
List<(String, int)> sortedTraits(Map<String, int> scores) {
  final known = [for (final k in traitKeys) if (scores.containsKey(k)) (k, scores[k]!)];
  final order = {for (final (i, k) in traitKeys.indexed) k: i};
  known.sort((a, b) {
    final by = b.$2.compareTo(a.$2);
    return by != 0 ? by : order[a.$1]!.compareTo(order[b.$1]!);
  });
  return known;
}

/// The one-sentence summary: the API's when there is one, else the three strongest
/// dimensions, the same numbers the bars show (FR-7's AI sentence is in the backlog).
String summarize(MovieDna dna, Strings s) {
  final summary = dna.summary;
  if (summary != null) return summary;
  final names = sortedTraits(dna.scores).map((e) => traitInSentence(e.$1, s)).toList();
  String at(int i) => i < names.length ? names[i] : '';
  return s.t('dna.summary', {'a': at(0), 'b': at(1), 'c': at(2)});
}

/// Strong, medium or weak: the bar's shade (web: traitBand).
Color _barColor(int value) => value >= 80
    ? AppColors.text
    : value >= 50
        ? AppColors.muted
        : AppColors.faint;

class DnaScreen extends ConsumerWidget {
  const DnaScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final query = ref.watch(dnaProvider);
    final dna = query.value;
    Widget frame(Widget body, {List<Widget> actions = const []}) => Scaffold(
          appBar: AppBar(title: Text(s.t('dna.title')), actions: actions),
          body: body,
        );
    if (dna == null) {
      if (query.hasError && !query.isLoading) {
        return frame(ErrorState(
          message: s.t('dna.error'),
          onRetry: () => ref.invalidate(dnaProvider),
        ));
      }
      return frame(const _Skeleton());
    }
    if (dna.ratingsNeeded > 0) {
      return frame(EmptyState(
        message: s.t('dna.rateMore', {'n': dna.ratingsNeeded}),
        actionLabel: s.t('dna.rateMoreCta'),
        onAction: () => context.go('/onboarding'),
      ));
    }
    final traits = sortedTraits(dna.scores);
    if (traits.isEmpty) {
      return frame(EmptyState(
        message: s.t('dna.noTaste'),
        actionLabel: s.t('dna.rateMoreCta'),
        onAction: () => context.go('/search'),
      ));
    }
    final summary = summarize(dna, s);
    String listed(int n) =>
        traits.take(n).map((e) => '${s.t(traitLabelKey(e.$1))} ${e.$2}').join(', ');
    final shareText = '$summary ${s.t('dna.shareText', {'traits': listed(5)})}';

    return frame(
      actions: [_ShareButton(text: shareText)],
      RefreshIndicator(
        onRefresh: () => ref.refresh(dnaProvider.future).then((_) {}, onError: (Object _) {}),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(AppSpacing.x3, AppSpacing.x3, AppSpacing.x3, AppSpacing.x5),
          children: [
            Text('“$summary”',
                key: const Key('dna.summary'),
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontFamily: AppFonts.head,
                  fontStyle: FontStyle.italic,
                  fontWeight: FontWeight.w700,
                  fontSize: 18,
                  height: 1.45,
                )),
            const SizedBox(height: AppSpacing.x3),
            DnaFlower(
              scores: dna.scores,
              label: s.t('dna.chartLabel', {'traits': listed(3)}),
            ),
            const SizedBox(height: AppSpacing.x3),
            Semantics(
              container: true,
              label: s.t('dna.stats'),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _Stat(s.t('dna.statFilms'), '${dna.ratingCount}'),
                  const SizedBox(width: AppSpacing.x2),
                  _Stat(s.t('dna.statAverage'),
                      dna.averageRating == null ? '—' : formatScore(dna.averageRating!, s.lang)),
                  const SizedBox(width: AppSpacing.x2),
                  _Stat(s.t('dna.statGenre'),
                      dna.topGenre == null ? '—' : genreLabel(dna.topGenre!, s)),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.x3),
            // A plain disclosure, closed until opened: the chart's text alternative too.
            Theme(
              data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                key: const Key('dna.numbers'),
                title: Text(s.t('dna.numbers')),
                tilePadding: EdgeInsets.zero,
                childrenPadding: const EdgeInsets.only(bottom: AppSpacing.x2),
                children: [for (final (key, value) in traits) _TraitBar(trait: key, value: value)],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Expanded(
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(AppRadius.md),
          ),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(fontSize: 12, color: AppColors.muted)),
                const SizedBox(height: AppSpacing.x1),
                Text(value,
                    style: const TextStyle(
                      fontFamily: AppFonts.head,
                      fontWeight: FontWeight.w800,
                      fontSize: 20,
                    )),
              ],
            ),
          ),
        ),
      );
}

/// One trait: label, value, a bar shaded by strength (not quality). Web: TraitBar.
class _TraitBar extends ConsumerWidget {
  const _TraitBar({required this.trait, required this.value});
  final String trait;
  final int value;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final name = ref.watch(stringsProvider).t(traitLabelKey(trait));
    return Semantics(
      key: Key('dna.bar.$trait'),
      container: true,
      label: '$name: $value',
      excludeSemantics: true,
      child: Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Expanded(child: Text(name, style: const TextStyle(fontSize: 13))),
              Text('$value',
                  style: const TextStyle(fontSize: 13, fontFamily: AppFonts.mono, color: AppColors.muted)),
            ]),
            const SizedBox(height: 6),
            ClipRRect(
              borderRadius: BorderRadius.circular(99),
              child: Stack(children: [
                Container(height: 6, color: AppColors.surface2),
                FractionallySizedBox(
                  widthFactor: value.clamp(0, 100) / 100,
                  child: Container(height: 6, color: _barColor(value)),
                ),
              ]),
            ),
          ],
        ),
      ),
    );
  }
}

class _ShareButton extends ConsumerWidget {
  const _ShareButton({required this.text});
  final String text;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return IconButton(
      tooltip: s.t('dna.share'),
      icon: const Icon(Icons.share_outlined),
      onPressed: () async {
        final messenger = ScaffoldMessenger.of(context);
        final outcome = await ref.read(sharerProvider)(text);
        if (outcome == ShareOutcome.shared) return;
        messenger
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(
            content: Text(outcome == ShareOutcome.copied ? s.t('dna.copied') : s.t('dna.shareError')),
          ));
      },
    );
  }
}

class _Skeleton extends ConsumerWidget {
  const _Skeleton();

  @override
  Widget build(BuildContext context, WidgetRef ref) => Semantics(
        label: ref.watch(stringsProvider).t('common.loading'),
        child: ExcludeSemantics(
          child: ListView(
            key: const Key('dna.skeleton'),
            physics: const NeverScrollableScrollPhysics(),
            padding: const EdgeInsets.all(AppSpacing.x3),
            children: [
              Center(
                child: Container(
                  width: 240,
                  height: 22,
                  decoration: BoxDecoration(
                    color: AppColors.surface2,
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.x3),
              const AspectRatio(
                aspectRatio: 4 / 3,
                child: Center(
                  child: AspectRatio(
                    aspectRatio: 1,
                    child: DecoratedBox(
                      decoration: BoxDecoration(color: AppColors.surface2, shape: BoxShape.circle),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
}
