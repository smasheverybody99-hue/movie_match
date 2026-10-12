"""Response pieces several routers build the same way."""

from app.models import Movie
from app.schemas import MovieOut


def movie_out(movie: Movie, genres: dict[int, list[str]]) -> MovieOut:
    """A film for a list, with its genres (from services.movies.genre_names)."""
    out = MovieOut.model_validate(movie)
    out.genres = genres.get(movie.id, [])
    return out
