/// What the app asks of Android (MainActivity.kt, channel `movie_match/android`): the
/// share sheet for a text, and a link opened in the browser. Sharing mirrors the web's
/// Share in pages/Dna.tsx: navigator.share, else copy, else say it failed.
library;

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

enum ShareOutcome { shared, copied, failed }

typedef Sharer = Future<ShareOutcome> Function(String text);
typedef LinkOpener = Future<bool> Function(String url);

const _channel = MethodChannel('movie_match/android');

Future<ShareOutcome> shareText(String text) async {
  try {
    await _channel.invokeMethod<bool>('share', {'text': text});
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

/// Opens an https link in the browser; false when it could not.
Future<bool> openLink(String url) async {
  try {
    return await _channel.invokeMethod<bool>('open', {'url': url}) ?? false;
  } on Object {
    return false;
  }
}

/// Tests override these to see what was shared or opened.
final sharerProvider = Provider<Sharer>((ref) => shareText);
final linkOpenerProvider = Provider<LinkOpener>((ref) => openLink);
