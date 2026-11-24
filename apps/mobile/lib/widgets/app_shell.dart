/// The bottom bar under the main sections (web: AppShell's bottom-nav below 640 px). Each
/// section keeps its own stack and scroll position; a film page opens over the bar, full
/// screen, as phone detail pages do (on the web the bar stays under it).
///
/// The Assistant section shows only while the server offers it (`/me` assistant_enabled;
/// the user's decision of 2026-11-24): on in the alpha, gone at the AI-free web launch
/// (TZ 1.38) without a new APK. Until /me answers, and when it does not say, it is hidden.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../state/app_state.dart';

class ShellSection {
  const ShellSection(this.path, this.label, this.icon, this.selectedIcon);

  final String path;
  final String label;
  final IconData icon;
  final IconData selectedIcon;
}

const assistantPath = '/assistant';

/// In the web's order (Layout.tsx SECTIONS); the router's branches follow it.
const shellSections = [
  ShellSection('/', 'nav.home', Icons.home_outlined, Icons.home),
  ShellSection('/search', 'nav.search', Icons.search, Icons.search),
  ShellSection(assistantPath, 'nav.assistant', Icons.auto_awesome_outlined, Icons.auto_awesome),
  ShellSection('/dna', 'nav.dna', Icons.blur_circular_outlined, Icons.blur_circular),
  ShellSection('/watchlist', 'nav.watchlist', Icons.bookmark_border, Icons.bookmark),
];

class AppShell extends ConsumerWidget {
  const AppShell({super.key, required this.shell});

  final StatefulNavigationShell shell;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final assistant = ref.watch(meProvider).value?.assistantEnabled ?? false;
    // Branch indexes of the sections shown, in order.
    final shown = [
      for (final (i, section) in shellSections.indexed)
        if (section.path != assistantPath || assistant) i,
    ];
    var selected = shown.indexOf(shell.currentIndex);
    if (selected == -1) {
      // On the Assistant after the server turned it off: back to Home.
      selected = 0;
      WidgetsBinding.instance.addPostFrameCallback((_) => shell.goBranch(0));
    }
    return Scaffold(
      body: shell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: selected,
        // A second tap on the current section goes back to its start.
        onDestinationSelected: (j) =>
            shell.goBranch(shown[j], initialLocation: shown[j] == shell.currentIndex),
        destinations: [
          for (final i in shown)
            NavigationDestination(
              icon: Icon(shellSections[i].icon),
              selectedIcon: Icon(shellSections[i].selectedIcon),
              label: s.t(shellSections[i].label),
            ),
        ],
      ),
    );
  }
}
