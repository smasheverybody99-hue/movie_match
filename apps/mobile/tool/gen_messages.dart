// Writes lib/i18n/messages.g.dart from the web dictionaries. Run from apps/mobile:
//   dart run tool/gen_messages.dart
import 'dart:io';

import 'web_messages.dart';

void main() {
  final messages = readWebMessages('../web/src/i18n');
  File('lib/i18n/messages.g.dart').writeAsStringSync(generateDart(messages));
  final counts = messages.entries.map((e) => '${e.key} ${e.value.length}').join(', ');
  stdout.writeln('lib/i18n/messages.g.dart: $counts');
}
