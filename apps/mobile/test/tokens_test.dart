// The Dart tokens must equal apps/web/src/styles/tokens.css (CLAUDE.md, docs/ui.md
// "Kod bilan bog'liqlik"). The CSS file is parsed here; no value is copied by hand.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:movie_match/theme/tokens.dart';

/// CSS custom property name -> its Dart counterpart. A colour added to the CSS without
/// an entry here fails the first test.
const colours = <String, Color>{
  'bg': AppColors.bg,
  'surface': AppColors.surface,
  'surface-2': AppColors.surface2,
  'line': AppColors.line,
  'text': AppColors.text,
  'muted': AppColors.muted,
  'faint': AppColors.faint,
  'red': AppColors.red,
  'red-dark': AppColors.redDark,
  'gold': AppColors.gold,
  'green': AppColors.green,
};

const lengths = <String, double>{
  'radius-sm': AppRadius.sm,
  'radius': AppRadius.md,
  'space-1': AppSpacing.x1,
  'space-2': AppSpacing.x2,
  'space-3': AppSpacing.x3,
  'space-4': AppSpacing.x4,
  'space-5': AppSpacing.x5,
};

/// `--name: value;` pairs from the file's `:root` block.
Map<String, String> readRoot(String css) {
  final root = RegExp(r':root\s*\{([^}]*)\}').firstMatch(css);
  if (root == null) throw StateError('no :root block in tokens.css');
  return {
    for (final m in RegExp(r'--([\w-]+)\s*:\s*([^;]+);').allMatches(root.group(1)!))
      m.group(1)!: m.group(2)!.trim(),
  };
}

void main() {
  // `flutter test` runs with apps/mobile as the working directory.
  final css = readRoot(File('../web/src/styles/tokens.css').readAsStringSync());
  final hex = RegExp(r'^#([0-9a-fA-F]{6})$');
  final px = RegExp(r'^(\d+(?:\.\d+)?)px$');

  test('every CSS colour has a Dart token', () {
    final cssColours = css.entries.where((e) => hex.hasMatch(e.value)).map((e) => e.key);
    expect(cssColours.toSet(), colours.keys.toSet());
  });

  for (final entry in colours.entries) {
    test('colour --${entry.key}', () {
      final value = css[entry.key];
      expect(value, isNotNull, reason: '--${entry.key} is missing from tokens.css');
      final rgb = int.parse(hex.firstMatch(value!)!.group(1)!, radix: 16);
      expect(entry.value.toARGB32(), 0xFF000000 | rgb);
    });
  }

  for (final entry in lengths.entries) {
    test('length --${entry.key}', () {
      final value = css[entry.key];
      expect(value, isNotNull, reason: '--${entry.key} is missing from tokens.css');
      expect(double.parse(px.firstMatch(value!)!.group(1)!), entry.value);
    });
  }
}
