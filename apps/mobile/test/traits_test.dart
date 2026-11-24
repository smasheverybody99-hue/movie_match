// lib/data/traits.dart must equal packages/shared/traits.json, in order (CLAUDE.md: the
// file is the single source of truth; the vector order never changes). The JSON is read
// here; no key is copied by hand.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:movie_match/data/traits.dart';
import 'package:movie_match/i18n/messages.g.dart';

void main() {
  final shared = jsonDecode(File('../../packages/shared/traits.json').readAsStringSync())
      as Map<String, dynamic>;
  final keys = [for (final d in shared['dimensions'] as List) (d as Map)['key'] as String];

  test('the same keys in the same order as traits.json', () {
    expect(traitKeys, keys);
  });

  test('every trait has a label in each language', () {
    for (final lang in ['en', 'uz', 'ru']) {
      for (final key in traitKeys) {
        expect(webMessages[lang]![traitLabelKey(key)], isA<String>(), reason: '$lang $key');
      }
    }
  });
}
