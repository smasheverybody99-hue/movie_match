import { Bookmark, BookmarkCheck, ChevronLeft, ChevronRight, Pause, Play, Sparkles } from "lucide-react";
import { useEffect, useId, useState, type KeyboardEvent } from "react";
import { Link } from "react-router-dom";

import { useT } from "../i18n";
import { imageUrl, releaseYear } from "../lib/format";
import { usePrefersReducedMotion } from "../lib/motion";
import type { Movie, Recommendation } from "../lib/types";
import { Icon } from "./Icon";
import { MatchBand } from "./MatchBand";

/** How long one film stays before the next (docs/ui.md, 4a). */
export const HERO_INTERVAL_MS = 7000;
/** The hero shows the top of "For you", at most this many. */
export const HERO_COUNT = 5;

/**
 * One film's backdrop (w780 / w1280), or its poster blurred, or nothing. Only the slides
 * already shown and the next one get an image, so the others do not load up front; the
 * first is the page's LCP image and is fetched at high priority.
 */
function HeroImage({ movie, active, first }: { movie: Movie; active: boolean; first: boolean }) {
  const backdrop = imageUrl(movie.backdrop_path, "w1280");
  const poster = imageUrl(movie.poster_path, "w342");
  const className = active ? "home-hero-img is-active" : "home-hero-img";
  if (backdrop) {
    return (
      <img
        className={className}
        src={backdrop}
        srcSet={`${imageUrl(movie.backdrop_path, "w780")} 780w, ${backdrop} 1280w`}
        sizes="100vw"
        alt=""
        fetchPriority={first ? "high" : "auto"}
      />
    );
  }
  return poster ? <img className={`${className} film-hero-blur`} src={poster} alt="" /> : null;
}

/**
 * Home's hero: the top of "For you", one film at a time, its backdrop across the full
 * width. Title, year and runtime, the match band, and two neutral buttons: "Why it suits
 * me?" (the cached sentence from the recommendations response, opened in place; without
 * one, a link to the film page) and Save. The hero never asks for an explanation: a
 * rotation must not spend money or the daily cap.
 * Rotation: every 7 s; it holds while the pointer or focus is inside, while the sentence
 * is open, and after Pause (WCAG 2.2.2). With reduced motion it never moves on its own
 * and there is no Pause. Prev / next buttons, dots (white for the current film, grey
 * otherwise), and the arrow keys.
 */
export function Hero({
  items,
  saved,
  onToggleSave,
}: {
  items: Recommendation[];
  saved: ReadonlySet<number>;
  onToggleSave: (movie: Movie, isSaved: boolean) => void;
}) {
  const t = useT();
  const reduce = usePrefersReducedMotion();
  const whyId = useId();
  const count = items.length;
  const [index, setIndex] = useState(0);
  const [reached, setReached] = useState(0); // the furthest slide shown, for image loading
  const [paused, setPaused] = useState(false);
  const [held, setHeld] = useState(false);
  const [whyOpen, setWhyOpen] = useState(false);
  const playing = !reduce && !paused && !held && !whyOpen && count > 1;

  const go = (next: number) => {
    const i = (next + count) % count;
    setIndex(i);
    setReached((r) => Math.max(r, i));
    setWhyOpen(false);
  };

  useEffect(() => {
    if (!playing) return;
    const timer = setTimeout(() => {
      const i = (index + 1) % count;
      setIndex(i);
      setReached((r) => Math.max(r, i));
    }, HERO_INTERVAL_MS);
    return () => clearTimeout(timer);
  }, [playing, index, count]);

  const item = items[index];
  if (!item) return null;
  const movie = item.movie;
  const isSaved = saved.has(movie.id);
  const year = releaseYear(movie);
  const tags = [...(year ? [year] : []), ...(movie.runtime_minutes ? [t("common.minutes", { n: movie.runtime_minutes })] : [])];

  const onKeyDown = (event: KeyboardEvent) => {
    if (count < 2 || event.target instanceof HTMLInputElement) return;
    if (event.key === "ArrowRight") go(index + 1);
    else if (event.key === "ArrowLeft") go(index - 1);
  };

  return (
    <section
      className="home-hero"
      aria-roledescription="carousel"
      aria-label={t("hero.label")}
      data-testid="home-hero"
      onMouseEnter={() => setHeld(true)}
      onMouseLeave={() => setHeld(false)}
      onFocus={() => setHeld(true)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setHeld(false);
      }}
      onKeyDown={onKeyDown}
    >
      <div className="home-hero-media" aria-hidden="true">
        {items.map((it, i) =>
          // The slides reached so far and the next one; the rest load when they come up.
          i <= reached + 1 ? <HeroImage key={it.movie.id} movie={it.movie} active={i === index} first={i === 0} /> : null,
        )}
      </div>
      {/* While it rotates the change is not announced; once it holds, it is. */}
      <div className="home-hero-body" aria-live={playing ? "off" : "polite"}>
        <div
          className="home-hero-slide"
          role="group"
          aria-roledescription="slide"
          aria-label={t("hero.slide", { n: index + 1, total: count })}
        >
          <h2 className="home-hero-title">
            <Link to={`/movie/${movie.id}`}>{movie.title}</Link>
          </h2>
          {tags.length > 0 && (
            <ul className="tags">
              {tags.map((tag) => (
                <li key={tag}>{tag}</li>
              ))}
            </ul>
          )}
          {item.band && (
            <p className="home-hero-band">
              <MatchBand band={item.band} />
            </p>
          )}
          {whyOpen && item.explanation && (
            <p className="home-hero-why" id={whyId}>
              {item.explanation}
            </p>
          )}
          <div className="home-hero-actions">
            {item.explanation ? (
              <button
                type="button"
                className="btn btn-secondary"
                aria-expanded={whyOpen}
                aria-controls={whyOpen ? whyId : undefined}
                onClick={() => setWhyOpen((open) => !open)}
              >
                <Icon as={Sparkles} /> {t("hero.why")}
              </button>
            ) : (
              <Link className="btn btn-secondary" to={`/movie/${movie.id}`}>
                <Icon as={Sparkles} /> {t("hero.why")}
              </Link>
            )}
            <button
              type="button"
              className="btn btn-secondary"
              aria-pressed={isSaved}
              onClick={() => onToggleSave(movie, isSaved)}
            >
              <Icon as={isSaved ? BookmarkCheck : Bookmark} /> {isSaved ? t("movie.onList") : t("movie.saveToList")}
            </button>
          </div>
        </div>
        {count > 1 && (
          <div className="home-hero-controls">
            <button type="button" className="hero-ctl" aria-label={t("hero.prev")} onClick={() => go(index - 1)}>
              <Icon as={ChevronLeft} />
            </button>
            <div className="home-hero-dots">
              {items.map((it, i) => (
                <button
                  key={it.movie.id}
                  type="button"
                  className="home-hero-dot"
                  aria-label={t("hero.goTo", { n: i + 1, total: count })}
                  aria-current={i === index ? "true" : undefined}
                  onClick={() => go(i)}
                />
              ))}
            </div>
            <button type="button" className="hero-ctl" aria-label={t("hero.next")} onClick={() => go(index + 1)}>
              <Icon as={ChevronRight} />
            </button>
            {!reduce && (
              <button
                type="button"
                className="hero-ctl"
                aria-label={paused ? t("hero.play") : t("hero.pause")}
                onClick={() => setPaused((p) => !p)}
              >
                <Icon as={paused ? Play : Pause} />
              </button>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
