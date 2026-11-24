/// "Not right?" under a recommendation (Phase 5). Mirrors apps/web/src/components/
/// NotRight.tsx and lib/hiddenCards.ts: a reason from four chips, or none. The card leaves
/// the feed at once; the press is stored for the alpha and changes nothing the engine picks.
/// If it does not arrive, the card comes back and the screen says so.
///
/// Phone difference: the chips open in a bottom sheet, not in place under the card (a row
/// card is 140 px wide).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';

/// The chips, in the order the user approved (2026-11-17).
const reasons = [
  FeedbackReason.seen,
  FeedbackReason.notMyGenre,
  FeedbackReason.tooOld,
  FeedbackReason.other,
];

/// Films taken out of the feed after "Not right?". For this app run only, and cleared by
/// pull to refresh (the phone's reload): the press is data for the alpha, not a ranking
/// input, so the next load shows what the engine picks, the film included (user decision,
/// 2026-11-17; TZ 1.31).
class HiddenCards extends Notifier<Set<int>> {
  @override
  Set<int> build() {
    ref.watch(userIdProvider);
    return const {};
  }

  void hide(int id) => state = {...state, id};
  void restore(int id) => state = {...state}..remove(id);
  void clear() => state = const {};
}

final hiddenCardsProvider = NotifierProvider<HiddenCards, Set<int>>(HiddenCards.new);

/// The button's text; also used to size the feed's rows.
const notRightTextStyle = TextStyle(fontSize: 12, fontWeight: FontWeight.w600);

/// The quiet text button; it opens the sheet and sends the answer.
class NotRightButton extends ConsumerWidget {
  const NotRightButton({super.key, required this.movie, required this.source});

  final Movie movie;
  final EventSource source;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return Semantics(
      button: true,
      label: s.t('wrong.openLabel', {'title': movie.title}),
      excludeSemantics: true,
      child: TextButton(
        style: TextButton.styleFrom(
          padding: EdgeInsets.zero,
          minimumSize: const Size(0, 32),
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          foregroundColor: AppColors.muted,
          textStyle: notRightTextStyle,
        ),
        onPressed: () => _open(context, ref),
        child: Text(s.t('wrong.open'), maxLines: 1, overflow: TextOverflow.ellipsis),
      ),
    );
  }

  Future<void> _open(BuildContext context, WidgetRef ref) async {
    final answer = await showModalBottomSheet<_Answer>(
      context: context,
      backgroundColor: AppColors.surface,
      showDragHandle: true,
      builder: (context) => const _Sheet(),
    );
    if (answer == null || !context.mounted) return;
    // The card leaves the tree when it is hidden, and its ref with it: read everything now.
    final s = ref.read(stringsProvider);
    final api = ref.read(apiClientProvider);
    final hidden = ref.read(hiddenCardsProvider.notifier);
    final messenger = ScaffoldMessenger.of(context);
    void notice(String text) => messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(text), duration: const Duration(seconds: 4)));
    hidden.hide(movie.id);
    notice(s.t('wrong.thanks', {'title': movie.title}));
    try {
      await api.markWrong(FeedbackIn(movieId: movie.id, source: source, reason: answer.reason));
    } on Object {
      hidden.restore(movie.id);
      notice(s.t('wrong.error', {'title': movie.title}));
    }
  }
}

/// What the sheet answered: a reason, or none ("Just hide it").
class _Answer {
  const _Answer(this.reason);
  final FeedbackReason? reason;
}

class _Sheet extends ConsumerWidget {
  const _Sheet();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    void answer(FeedbackReason? reason) => Navigator.of(context).pop(_Answer(reason));
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(AppSpacing.x3, 0, AppSpacing.x3, AppSpacing.x3),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(s.t('wrong.question'),
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
            const SizedBox(height: AppSpacing.x3),
            Wrap(
              spacing: AppSpacing.x2,
              runSpacing: AppSpacing.x2,
              children: [
                for (final reason in reasons)
                  ActionChip(
                    label: Text(s.t('wrong.reason.${reason.wire}')),
                    onPressed: () => answer(reason),
                  ),
              ],
            ),
            const SizedBox(height: AppSpacing.x2),
            Row(
              children: [
                TextButton(onPressed: () => answer(null), child: Text(s.t('wrong.skip'))),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(s.t('wrong.cancel')),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
