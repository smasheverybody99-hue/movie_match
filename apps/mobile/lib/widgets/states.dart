/// The loading and error states every screen shares (web: components/States.tsx).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../state/app_state.dart';
import '../theme/tokens.dart';

class LoadingState extends ConsumerWidget {
  const LoadingState({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => Center(
        child: Semantics(
          label: ref.watch(stringsProvider).t('common.loading'),
          child: const CircularProgressIndicator(color: AppColors.muted),
        ),
      );
}

/// Nothing to show yet, and the way forward (web: EmptyState).
class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.message, this.actionLabel, this.onAction});

  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.x4),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(message, textAlign: TextAlign.center),
              if (actionLabel != null) ...[
                const SizedBox(height: AppSpacing.x3),
                OutlinedButton(onPressed: onAction, child: Text(actionLabel!)),
              ],
            ],
          ),
        ),
      );
}

class ErrorState extends ConsumerWidget {
  const ErrorState({super.key, required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context, WidgetRef ref) => Center(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.x4),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: AppSpacing.x3),
              OutlinedButton(
                onPressed: onRetry,
                child: Text(ref.watch(stringsProvider).t('common.retry')),
              ),
            ],
          ),
        ),
      );
}
