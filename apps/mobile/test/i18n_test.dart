// The app's strings are the web's (apps/web/src/i18n/*.ts). messages.g.dart is generated
// from them; this test reads the web files again and fails when the two differ, the way
// tokens_test.dart does for colours. Fix: `dart run tool/gen_messages.dart`.
import 'dart:ui' show Locale;

import 'package:flutter_test/flutter_test.dart';
import 'package:movie_match/data/models.dart';
import 'package:movie_match/i18n/i18n.dart';
import 'package:movie_match/i18n/messages.g.dart';

import '../tool/web_messages.dart';

void main() {
  test('messages.g.dart equals the web dictionaries', () {
    final web = readWebMessages('../web/src/i18n');
    expect(webMessages.keys, web.keys);
    for (final lang in web.keys) {
      expect(webMessages[lang], web[lang], reason: 'run dart run tool/gen_messages.dart');
    }
  });

  test('every language has exactly the English keys', () {
    final en = webMessages['en']!.keys.toSet();
    for (final lang in ['uz', 'ru']) {
      expect(webMessages[lang]!.keys.toSet(), en, reason: lang);
    }
  });

  test('the parser refuses what it does not understand', () {
    expect(() => parseMessages('export const en = { "a": `b` };', 'en'), throwsFormatException);
    expect(() => parseMessages('export const en = { "a": { one: "x" } };', 'en'),
        throwsFormatException);
    expect(parseMessages('export const en = {\n  // note\n  "a":\n    "it\'s",\n};', 'en'),
        {'a': "it's"});
  });

  group('t()', () {
    test('fills placeholders', () {
      expect(const Strings(Lang.en).t('welcome.emailSent', {'email': 'a@b.uz'}),
          'We sent a link to a@b.uz. Open your inbox and tap it.');
    });

    test('picks the plural form by n', () {
      const en = Strings(Lang.en);
      expect(en.t('onboarding.rate.needMore', {'n': 1}), contains('1 more rating.'));
      expect(en.t('onboarding.rate.needMore', {'n': 3}), contains('3 more ratings.'));
    });

    test('Russian plural categories', () {
      expect([1, 2, 5, 11, 21, 22, 25, 112].map((n) => pluralCategory(Lang.ru, n)),
          ['one', 'few', 'many', 'many', 'one', 'few', 'many', 'many']);
    });

    test('an unknown key shows itself', () {
      expect(const Strings(Lang.uz).t('no.such.key'), 'no.such.key');
    });

    test('device locale picks the language, English by default', () {
      expect(langForLocale(const Locale('uz')), Lang.uz);
      expect(langForLocale(const Locale('ru', 'RU')), Lang.ru);
      expect(langForLocale(const Locale('de')), Lang.en);
      expect(langForLocale(null), Lang.en);
    });
  });
}
