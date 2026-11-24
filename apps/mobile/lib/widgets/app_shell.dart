/// The bottom bar under the main sections (web: AppShell's bottom-nav below 640 px). Each
/// section keeps its own stack and scroll position; a film page opens over the bar, full
/// screen, as phone detail pages do (on the web the bar stays under it).
///
/// Sections are added as their screens land (phase-06-mobile.md). The web's Assistant
/// section waits for the user's decision on the assistant in the alpha (TZ 1.38 hides it at
/// the web launch).
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

/// In the web's order (Layout.tsx SECTIONS).
const shellSections = [
  ShellSection('/', 'nav.home', Icons.home_outlined, Icons.home),
  ShellSection('/search', 'nav.search', Icons.search, Icons.search),
];

class AppShell extends ConsumerWidget {
  const AppShell({super.key, required this.shell});

  final StatefulNavigationShell shell;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return Scaffold(
      body: shell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: shell.currentIndex,
        // A second tap on the current section goes back to its start.
        onDestinationSelected: (i) => shell.goBranch(i, initialLocation: i == shell.currentIndex),
        destinations: [
          for (final section in shellSections)
            NavigationDestination(
              icon: Icon(section.icon),
              selectedIcon: Icon(section.selectedIcon),
              label: s.t(section.label),
            ),
        ],
      ),
    );
  }
}
