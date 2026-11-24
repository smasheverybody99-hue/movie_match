/// 2:3 poster. Mirrors apps/web/src/components/Poster.tsx: under the image, always, the
/// title, the year and the first genre, so the tile says what it is while the image loads,
/// when it fails, or when image.tmdb.org cannot be reached at all (refused from some
/// networks, measured 2026-10-12). The image covers it once it arrives. Decorative for
/// screen readers: the title is the tile's own label.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../format.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import 'match_band.dart';

class Poster extends ConsumerWidget {
  const Poster({super.key, required this.movie, this.size = 'w342', this.band});

  final Movie movie;

  /// The match band; only "strong" is shown (top-left, red), so it stays rare.
  final MatchBand? band;

  /// TMDB width: w185 in grids, w342 for a single large poster.
  final String size;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final url = imageUrl(movie.posterPath, size);
    final meta = [
      if (movie.year != null) '${movie.year}',
      if (movie.genres.isNotEmpty) genreLabel(movie.genres.first, s),
    ].join(' · ');
    return ExcludeSemantics(
      child: AspectRatio(
        aspectRatio: 2 / 3,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.sm),
          child: Stack(
            fit: StackFit.expand,
            children: [
              ColoredBox(
                key: const Key('poster.fallback'),
                color: AppColors.surface2,
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.x2),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.end,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    // Flexible: on a small poster at a large text size the text is cut at
                    // the poster's edge instead of overflowing it.
                    children: [
                      Flexible(
                        child: Text(
                          movie.title,
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppColors.text,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            height: 1.25,
                          ),
                        ),
                      ),
                      if (meta.isNotEmpty)
                        Flexible(
                          child: Text(
                            meta,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: AppColors.muted,
                              fontSize: 11,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              if (url != null)
                Image.network(
                  url,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stack) =>
                      const SizedBox.shrink(),
                ),
              if (showsStrong(band))
                Positioned(top: 6, left: 6, child: BandPill(band: band)),
            ],
          ),
        ),
      ),
    );
  }
}
