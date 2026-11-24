/// A film in a grid (search results): the poster, its title in two lines at most, year ·
/// runtime; a tap opens the film page. Web: MovieCard without a recommendation source.
/// On the web the card's quick Rate / Save need a hovering mouse; on a touch screen a tap
/// opens the film there too, so the phone has none.
library;

import 'dart:math' as math;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../format.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import 'poster.dart';

const filmTileTitleStyle = TextStyle(fontSize: 13, fontWeight: FontWeight.w600, height: 1.3);
const filmTileMetaStyle = TextStyle(fontSize: 12, color: AppColors.muted);

/// The height of `lines` lines of `style` at the phone's text size, for lists and grids
/// that need a tile's height up front.
double textLinesHeight(BuildContext context, TextStyle style, int lines) {
  final painter = TextPainter(
    text: TextSpan(
      text: List.filled(lines, 'Ag').join('\n'),
      style: DefaultTextStyle.of(context).style.merge(style),
    ),
    textScaler: MediaQuery.textScalerOf(context),
    textDirection: TextDirection.ltr,
  )..layout();
  final height = painter.height;
  painter.dispose();
  return height;
}

/// Columns for a grid `width` px wide: as many 84 px tiles as fit with 10 px gaps (web:
/// `repeat(auto-fill, minmax(84px, 1fr))`), at least two.
int gridColumns(double width) => math.max(2, ((width + 10) / (84 + 10)).floor());

class FilmTile extends ConsumerWidget {
  const FilmTile({super.key, required this.movie});

  final Movie movie;

  /// The tile's height for a tile `width` px wide.
  static double heightFor(BuildContext context, double width) =>
      width * 1.5 +
      AppSpacing.x2 +
      textLinesHeight(context, filmTileTitleStyle, 2) +
      textLinesHeight(context, filmTileMetaStyle, 1) +
      AppSpacing.x1;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final meta = movieMeta(movie, s);
    return Semantics(
      button: true,
      label: [movie.title, meta].where((x) => x.isNotEmpty).join(', '),
      excludeSemantics: true,
      child: InkWell(
        onTap: () => context.push('/movie/${movie.id}', extra: movie),
        borderRadius: BorderRadius.circular(AppRadius.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Poster(movie: movie, size: 'w185'),
            const SizedBox(height: AppSpacing.x2),
            Text(movie.title,
                maxLines: 2, overflow: TextOverflow.ellipsis, style: filmTileTitleStyle),
            if (meta.isNotEmpty)
              Text(meta, maxLines: 1, overflow: TextOverflow.ellipsis, style: filmTileMetaStyle),
          ],
        ),
      ),
    );
  }
}
