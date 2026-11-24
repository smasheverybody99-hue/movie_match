/// A film's backdrop across the full width, under the feed's hero and the film page's
/// head (web: .home-hero-img, .film-hero): the backdrop, or the poster blurred, or the
/// surface colour; and the gradients that run it into the page.
library;

import 'dart:ui' show ImageFilter;

import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../format.dart';
import '../theme/tokens.dart';

/// The backdrop (w780 on a phone), or the poster blurred, or the surface colour.
class Backdrop extends StatelessWidget {
  const Backdrop({super.key, required this.movie});

  final Movie movie;

  @override
  Widget build(BuildContext context) {
    final backdrop = imageUrl(movie.backdropPath, 'w780');
    final poster = imageUrl(movie.posterPath, 'w342');
    Widget image(String url) => Image.network(
          url,
          fit: BoxFit.cover,
          errorBuilder: (context, error, stack) => const SizedBox.shrink(),
        );
    return ExcludeSemantics(
      child: ColoredBox(
        color: AppColors.surface,
        child: backdrop != null
            ? image(backdrop)
            : poster != null
                ? ImageFiltered(
                    key: const Key('backdrop.blur'),
                    imageFilter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
                    child: image(poster),
                  )
                : null,
      ),
    );
  }
}

/// The web's gradients: into the background at the bottom, on the left, and a little at
/// the top.
class BackdropShade extends StatelessWidget {
  const BackdropShade({super.key});

  @override
  Widget build(BuildContext context) {
    Color bg(double a) => AppColors.bg.withValues(alpha: a);
    return IgnorePointer(
      child: Stack(
        fit: StackFit.expand,
        children: [
          DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.bottomCenter,
                end: Alignment.topCenter,
                colors: [bg(1), bg(0.55), bg(0)],
                stops: const [0, 0.3, 0.6],
              ),
            ),
          ),
          DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [bg(0.8), bg(0)], stops: const [0, 0.5]),
            ),
          ),
          DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [bg(0.45), bg(0)],
                stops: const [0, 0.45],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
