/// Display helpers shared by the screens. Mirrors apps/web/src/lib/format.ts and genres.ts.
library;

import 'data/models.dart';
import 'i18n/i18n.dart';

const _tmdbImages = 'https://image.tmdb.org/t/p';

/// TMDB image URL for a stored path, or null. Sizes are TMDB's fixed widths
/// (w185, w342, w780, w1280).
String? imageUrl(String? path, String size) => path == null ? null : '$_tmdbImages/$size$path';

/// "2010 · 138m": whatever of year and runtime is known.
String movieMeta(Movie movie, Strings s) => [
      if (movie.year != null) '${movie.year}',
      if (movie.runtimeMinutes != null) s.t('common.minutes', {'n': movie.runtimeMinutes!}),
    ].join(' · ');

/// One decimal in the language's own way: 8 -> "8.0" in English, "8,0" in Russian and
/// Uzbek (as Intl.NumberFormat gives it on the web).
String formatScore(double value, Lang lang) {
  final text = value.toStringAsFixed(1);
  return lang == Lang.en ? text : text.replaceAll('.', ',');
}

/// TMDB's genre names, as the API sends them (English, from ingestion).
const _genreKeys = <String, String>{
  'Action': 'genre.action',
  'Adventure': 'genre.adventure',
  'Animation': 'genre.animation',
  'Comedy': 'genre.comedy',
  'Crime': 'genre.crime',
  'Documentary': 'genre.documentary',
  'Drama': 'genre.drama',
  'Family': 'genre.family',
  'Fantasy': 'genre.fantasy',
  'History': 'genre.history',
  'Horror': 'genre.horror',
  'Music': 'genre.music',
  'Mystery': 'genre.mystery',
  'Romance': 'genre.romance',
  'Science Fiction': 'genre.science_fiction',
  'Thriller': 'genre.thriller',
  'TV Movie': 'genre.tv_movie',
  'War': 'genre.war',
  'Western': 'genre.western',
};

/// A genre in the interface language; a name TMDB adds later is shown as sent.
String genreLabel(String name, Strings s) {
  final key = _genreKeys[name];
  return key == null ? name : s.t(key);
}
