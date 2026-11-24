/// /profile — language, sign out, delete account, about. Mirrors apps/web/src/pages/
/// Profile.tsx; /about is the same About section on its own, public, linked from Welcome
/// (TMDB attribution: required from the day the app is public, docs/legal.md).
///
/// Phone differences: profile opens from the person icon in each section's top bar (web:
/// the avatar in the top bar); the TMDB link opens in the phone's browser.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../platform.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';

const tmdbUrl = 'https://www.themoviedb.org/';

/// The person icon in a section's top bar: opens the profile.
class ProfileButton extends ConsumerWidget {
  const ProfileButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => IconButton(
    tooltip: ref.watch(stringsProvider).t('nav.profile'),
    icon: const Icon(Icons.account_circle_outlined),
    onPressed: () => context.push('/profile'),
  );
}

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  Future<void> _signOut() async {
    // Signed out, the router goes to Welcome.
    await ref.read(authClientProvider)?.signOut().catchError((Object _) {});
  }

  Future<void> _delete() async {
    final deleted = await showDialog<bool>(
      context: context,
      builder: (context) => const _DeleteDialog(),
    );
    if (deleted == true) await _signOut();
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final lang = ref.watch(langProvider);
    final email = ref.watch(sessionProvider).value?.email;
    return Scaffold(
      appBar: AppBar(title: Text(s.t('profile.title'))),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.x3),
        children: [
          if (email != null) Text(email, style: const TextStyle(color: AppColors.muted)),
          const SizedBox(height: AppSpacing.x4),
          Text(s.t('profile.language'), style: const TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: AppSpacing.x2),
          Wrap(
            spacing: AppSpacing.x2,
            runSpacing: AppSpacing.x2,
            children: [
              // Each language named in itself, in the web's order.
              for (final code in Lang.values)
                ChoiceChip(
                  key: Key('profile.lang.${code.name}'),
                  label: Text(s.t('lang.${code.name}')),
                  selected: lang == code,
                  showCheckmark: false,
                  onSelected: (_) => ref.read(langChoiceProvider.notifier).choose(code),
                ),
            ],
          ),
          const SizedBox(height: AppSpacing.x4),
          Align(
            alignment: Alignment.centerLeft,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 320),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  OutlinedButton(onPressed: _signOut, child: Text(s.t('profile.signOut'))),
                  const SizedBox(height: AppSpacing.x2),
                  TextButton(onPressed: _delete, child: Text(s.t('profile.delete'))),
                ],
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.x4),
          const AboutSection(),
        ],
      ),
    );
  }
}

class _DeleteDialog extends ConsumerStatefulWidget {
  const _DeleteDialog();

  @override
  ConsumerState<_DeleteDialog> createState() => _DeleteDialogState();
}

class _DeleteDialogState extends ConsumerState<_DeleteDialog> {
  bool _busy = false;
  bool _failed = false;

  Future<void> _confirm() async {
    setState(() {
      _busy = true;
      _failed = false;
    });
    try {
      await ref.read(apiClientProvider).deleteAccount();
      if (mounted) Navigator.of(context).pop(true);
    } on Object {
      if (mounted) {
        setState(() {
          _busy = false;
          _failed = true;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    return AlertDialog(
      // At large text sizes the warning is taller than a small phone: it scrolls.
      scrollable: true,
      title: Text(s.t('profile.delete')),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.t('profile.deleteConfirm')),
          if (_failed) ...[
            const SizedBox(height: AppSpacing.x2),
            Semantics(
              liveRegion: true,
              child: Text(s.t('profile.deleteError'), style: const TextStyle(color: AppColors.red)),
            ),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.of(context).pop(false),
          child: Text(s.t('common.cancel')),
        ),
        FilledButton(
          key: const Key('profile.deleteYes'),
          onPressed: _busy ? null : _confirm,
          child: Text(s.t('profile.deleteYes')),
        ),
      ],
    );
  }
}

/// TMDB attribution, and the link to TMDB.
class AboutSection extends ConsumerWidget {
  const AboutSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Semantics(
          header: true,
          child: Text(
            s.t('profile.about'),
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          ),
        ),
        const SizedBox(height: AppSpacing.x2),
        Text(s.t('profile.tmdb')),
        const SizedBox(height: AppSpacing.x2),
        Semantics(
          link: true,
          child: InkWell(
            key: const Key('about.tmdb'),
            onTap: () => ref.read(linkOpenerProvider)(tmdbUrl),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: AppSpacing.x2),
              child: Text(
                s.t('profile.tmdbLink'),
                style: const TextStyle(decoration: TextDecoration.underline),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// /about — public, linked from Welcome.
class AboutScreen extends ConsumerWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
    appBar: AppBar(title: Text(ref.watch(stringsProvider).t('app.name'))),
    body: ListView(padding: const EdgeInsets.all(AppSpacing.x3), children: const [AboutSection()]),
  );
}
