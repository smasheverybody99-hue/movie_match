import { Link } from "react-router-dom";

import { useT } from "../i18n";
import { movieMeta } from "../lib/format";
import type { Movie } from "../lib/types";
import { Poster } from "./Poster";

/** Poster, title (two lines at most), year · runtime. Links to the film page. */
export function MovieCard({ movie, match }: { movie: Movie; match?: number | null }) {
  const t = useT();
  const meta = movieMeta(movie, t);
  return (
    <Link to={`/movie/${movie.id}`} className="card-link movie-card">
      <Poster title={movie.title} path={movie.poster_path} match={match} />
      <div className="movie-card-title">{movie.title}</div>
      {meta && <div className="meta">{meta}</div>}
    </Link>
  );
}
