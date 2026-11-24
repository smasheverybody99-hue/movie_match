package com.moviematch.movie_match

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Two things the app asks of Android (lib/platform.dart), so no share or URL package is
 * needed: `share` opens the chooser for a plain text (Movie DNA), `open` opens an https
 * link in the browser (TMDB, on the About screen).
 */
class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "movie_match/android")
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "share" -> {
                        val text = call.argument<String>("text")
                        if (text == null) {
                            result.error("no_text", "text is required", null)
                        } else {
                            val send = Intent(Intent.ACTION_SEND).apply {
                                type = "text/plain"
                                putExtra(Intent.EXTRA_TEXT, text)
                            }
                            startActivity(Intent.createChooser(send, null))
                            result.success(true)
                        }
                    }
                    "open" -> {
                        val url = call.argument<String>("url")
                        if (url == null || !url.startsWith("https://")) {
                            result.error("bad_url", "an https url is required", null)
                        } else {
                            try {
                                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                                result.success(true)
                            } catch (e: ActivityNotFoundException) {
                                result.error("no_browser", e.message, null)
                            }
                        }
                    }
                    else -> result.notImplemented()
                }
            }
    }
}
