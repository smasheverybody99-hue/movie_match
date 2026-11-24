/// The closed alpha's data notice (ADR 0004, the free-tier exception of 2026-11-17).
/// Mirrors apps/web/src/components/DataNotice.tsx: every tester accepts it once after
/// signing in, before any screen that could send something; the acceptance is stored on
/// the server. Declining signs out. When the API stops asking for it
/// (data_notice_required false) nobody sees it. A phone that has seen this account accept
/// goes straight through while /me loads.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/states.dart';

class DataNoticeGate extends ConsumerWidget {
  const DataNoticeGate({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final memory = ref.watch(noticeMemoryProvider);
    final userId = ref.watch(userIdProvider) ?? '';
    final me = ref.watch(meProvider);

    final data = me.value;
    if (data != null) {
      if (!data.dataNoticeRequired || data.dataNoticeAcceptedAt != null) {
        if (data.dataNoticeAcceptedAt != null && !memory.accepted(userId)) {
          memory.remember(userId);
        }
        return child;
      }
      return Scaffold(body: SafeArea(child: _Notice(userId: userId)));
    }
    if (memory.accepted(userId)) return child;
    if (me.hasError) {
      return Scaffold(
        body: ErrorState(message: s.t('notice.error'), onRetry: () => ref.invalidate(meProvider)),
      );
    }
    return const Scaffold(body: LoadingState());
  }
}

class _Notice extends ConsumerStatefulWidget {
  const _Notice({required this.userId});

  final String userId;

  @override
  ConsumerState<_Notice> createState() => _NoticeState();
}

class _NoticeState extends ConsumerState<_Notice> {
  bool _saving = false;
  bool _failed = false;

  Future<void> _accept() async {
    if (_saving) return;
    setState(() {
      _saving = true;
      _failed = false;
    });
    try {
      await ref.read(apiClientProvider).acceptDataNotice();
      await ref.read(noticeMemoryProvider).remember(widget.userId);
      ref.invalidate(meProvider);
    } on Object {
      if (mounted) setState(() => _failed = true);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final theme = Theme.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.x4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(s.t('notice.title'), style: theme.textTheme.headlineMedium),
          const SizedBox(height: AppSpacing.x3),
          Text(s.t('notice.body'), style: const TextStyle(color: AppColors.text, height: 1.5)),
          const SizedBox(height: AppSpacing.x3),
          Text(s.t('notice.busy')),
          if (_failed) ...[
            const SizedBox(height: AppSpacing.x3),
            Text(s.t('notice.saveError'),
                key: const Key('notice.saveError'), style: const TextStyle(color: AppColors.gold)),
          ],
          const SizedBox(height: AppSpacing.x4),
          FilledButton(
            onPressed: _saving ? null : _accept,
            child: Text(_saving ? s.t('common.saving') : s.t('notice.accept')),
          ),
          const SizedBox(height: AppSpacing.x2),
          TextButton(
            onPressed: () => ref.read(authClientProvider)?.signOut(),
            child: Text(s.t('notice.decline')),
          ),
        ],
      ),
    );
  }
}
