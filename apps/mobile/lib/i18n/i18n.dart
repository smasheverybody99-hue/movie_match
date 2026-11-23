/// Strings for the screens. They come from the web dictionaries (messages.g.dart is
/// generated from apps/web/src/i18n/*.ts), so web and mobile say the same thing in the
/// same three languages. Mirrors t() in apps/web/src/i18n/index.tsx.
library;

import 'dart:ui' show Locale;

import '../data/models.dart' show Lang;
import 'messages.g.dart';

/// The language for a device locale: Uzbek or Russian when the phone uses them, English
/// otherwise (TZ 1.8: English is the default).
Lang langForLocale(Locale? locale) => switch (locale?.languageCode) {
      'uz' => Lang.uz,
      'ru' => Lang.ru,
      _ => Lang.en,
    };

/// CLDR cardinal category for an integer, as Intl.PluralRules gives it for these
/// languages: English and Uzbek one/other; Russian one/few/many.
String pluralCategory(Lang lang, int n) {
  if (lang != Lang.ru) return n == 1 ? 'one' : 'other';
  final mod10 = n % 10;
  final mod100 = n % 100;
  if (mod10 == 1 && mod100 != 11) return 'one';
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'few';
  return 'many';
}

class Strings {
  const Strings(this.lang);

  final Lang lang;

  /// The message for `key` with `{name}` placeholders filled from `params`. A plural picks
  /// its form from `params['n']`. A key missing in this language falls back to English,
  /// then to the key itself, so a gap shows up on screen instead of crashing.
  String t(String key, [Map<String, Object> params = const {}]) {
    final message = webMessages[lang.name]?[key] ?? webMessages['en']![key];
    String text;
    if (message is String) {
      text = message;
    } else if (message is Map<String, String>) {
      final n = params['n'];
      final category = n is int ? pluralCategory(lang, n) : 'other';
      text = message[category] ?? message['other']!;
    } else {
      return key;
    }
    return text.replaceAllMapped(
      RegExp(r'\{(\w+)\}'),
      (m) => params.containsKey(m.group(1)) ? '${params[m.group(1)]}' : m.group(0)!,
    );
  }
}
