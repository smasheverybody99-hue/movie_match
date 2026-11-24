/// Sharing a text: the phone's share sheet (MainActivity.kt, channel `movie_match/share`),
/// else the clipboard. Mirrors the web's Share in pages/Dna.tsx: navigator.share, else
/// copy, else say it failed.
library;

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

enum ShareOutcome { shared, copied, failed }

typedef Sharer = Future<ShareOutcome> Function(String text);

const _channel = MethodChannel('movie_match/share');

Future<ShareOutcome> shareText(String text) async {
  try {
    await _channel.invokeMethod<bool>('text', {'text': text});
    return ShareOutcome.shared;
  } on MissingPluginException {
    // No share sheet here (tests, another platform): copy instead.
  } on PlatformException {
    // The sheet would not open: copy instead.
  }
  try {
    await Clipboard.setData(ClipboardData(text: text));
    return ShareOutcome.copied;
  } on Object {
    return ShareOutcome.failed;
  }
}

/// Tests override it to see what was shared.
final sharerProvider = Provider<Sharer>((ref) => shareText);
