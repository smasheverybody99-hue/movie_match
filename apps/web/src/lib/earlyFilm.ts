import { useEffect, useState } from "react";

import type { EarlyEntry, EarlyFilm } from "./earlyFilmScript";

declare global {
  interface Window {
    __mmEarlyFilm?: EarlyEntry;
  }
}

/** The early answer for this film, once it is in; null before, without one, or for another film. */
export function useEarlyFilm(id: number): EarlyFilm | null {
  const entry = typeof window === "undefined" ? undefined : window.__mmEarlyFilm;
  const mine = entry && entry.id === id ? entry : undefined;
  const [film, setFilm] = useState<{ id: number; film: EarlyFilm } | null>(null);
  useEffect(() => {
    if (!mine) return;
    let live = true;
    void mine.film.then((f) => {
      if (live && f) setFilm({ id: mine.id, film: { backdrop_path: f.backdrop_path, poster_path: f.poster_path } });
    });
    return () => {
      live = false;
    };
  }, [mine]);
  return film && film.id === id ? film.film : null;
}
