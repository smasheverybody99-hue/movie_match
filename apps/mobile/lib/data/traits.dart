/// The Movie DNA dimensions, as the phone knows them.
///
/// This list mirrors packages/shared/traits.json, as apps/web/src/lib/traits.ts does. It is
/// written out because the app bundle cannot reach outside apps/mobile; test/traits_test.dart
/// reads the JSON file and fails when the two differ.
///
/// The ORDER is the vector order used by the API. Never reorder.
library;

const traitKeys = <String>[
  'psychological_complexity',
  'plot_twist',
  'mystery',
  'character_depth',
  'emotional_intensity',
  'pacing',
  'humor',
  'romance',
  'action',
  'violence',
  'visual_style',
  'realism',
  'darkness',
  'ending_ambiguity',
];

/// The message key of a trait's label (`trait.<key>`, generated from the web dictionaries).
String traitLabelKey(String key) => 'trait.$key';
