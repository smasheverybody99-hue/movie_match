/// The 0.5-step, 10-point scale and, above 8.0, "what did you like?". Mirrors
/// apps/web/src/components/RatingInput.tsx; shared by onboarding and the film page's rating
/// sheet. No "keys 1-9" hint: a phone has no keyboard for it.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../data/traits.dart';
import '../format.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';

/// FR-3: "what did you like?" appears for scores above 8.0.
const likedAspectsAbove = 8.0;

bool showsLikedAspects(double value) => value > likedAspectsAbove;

class RatingInput extends ConsumerWidget {
  const RatingInput({
    super.key,
    required this.value,
    required this.onChanged,
    required this.aspects,
    required this.onAspectsChanged,
  });

  final double value;
  final ValueChanged<double> onChanged;
  final List<String> aspects;
  final ValueChanged<List<String>> onAspectsChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final lang = s.lang;
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ExcludeSemantics(
          child: Text(
            formatScore(value, lang),
            key: const Key('rating.score'),
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
          value: value,
          min: 0.5,
          max: 10,
          divisions: 19,
          activeColor: AppColors.text,
          inactiveColor: AppColors.line,
          thumbColor: AppColors.text,
          semanticFormatterCallback: (v) => '${s.t('onboarding.rate.scoreLabel')}: '
              '${formatScore(v, lang)}',
          onChanged: onChanged,
        ),
        const ExcludeSemantics(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [Text('0.5'), Text('5.0'), Text('10')],
          ),
        ),
        if (showsLikedAspects(value)) ...[
          const SizedBox(height: AppSpacing.x3),
          Text(s.t('onboarding.rate.liked'),
              style: const TextStyle(color: AppColors.text, fontWeight: FontWeight.w600)),
          const SizedBox(height: AppSpacing.x2),
          Wrap(
            key: const Key('rating.likedAspects'),
            spacing: AppSpacing.x2,
            runSpacing: AppSpacing.x2,
            children: [
              for (final key in traitKeys)
                FilterChip(
                  label: Text(s.t(traitLabelKey(key))),
                  selected: aspects.contains(key),
                  onSelected: (on) => onAspectsChanged(
                      on ? [...aspects, key] : [for (final a in aspects) if (a != key) a]),
                ),
            ],
          ),
        ],
      ],
    );
  }
}
