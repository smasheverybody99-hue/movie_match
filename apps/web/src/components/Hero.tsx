import { Bookmark, BookmarkCheck, ChevronLeft, ChevronRight, Pause, Play, Sparkles } from "lucide-react";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Link } from "react-router-dom";

import { useT } from "../i18n";
import { imageUrl, releaseYear } from "../lib/format";
import { usePrefersReducedMotion } from "../lib/motion";
import type { Movie, Recommendation } from "../lib/types";
import { isTraitKey } from "../lib/traits";
import { Icon } from "./Icon";
import { Kicker } from "./Kicker";
import { useParallax } from "./motion";
import { traitLabelKey } from "./Traits";

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
 * width. Read like the film page's "Why you": the kicker (STRONG MATCH or the neutral
 * one), the title, year and runtime, then a short sentence: the cached explanation from
 * the recommendations response, else the same free fallback as the film page. The hero
 * never asks for an explanation: a rotation must not spend money or the daily cap.
 * Two neutral buttons: "See why" (the film page) and Save.
 * Rotation: every 7 s; it holds while the pointer, a touch or focus is inside and after
 * Pause (WCAG 2.2.2), and it stops once the viewer steers it themselves with the dots,
 * prev / next or the arrow keys (Play resumes it).
 * With reduced motion it never moves on its own and there is no Pause.
 * Prev / next buttons, dots (white for the current film, grey otherwise), arrow keys.
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
  const media = useRef<HTMLDivElement>(null);
  // The backdrop holds a little behind the page as the hero scrolls away. The blurred
  // poster stand-in is left out: its own CSS transform already scales it.
  useParallax(media, { selector: ".home-hero-img:not(.film-hero-blur)" });
  const count = items.length;
  const [index, setIndex] = useState(0);
  const [reached, setReached] = useState(0); // the furthest slide shown, for image loading
  const [paused, setPaused] = useState(false);
  // One flag per reason to hold, not one shared flag: a mouse click inside the hero ends
  // its own touch hold without ending the hover hold, and focus inside survives the
  // pointer leaving.
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [touching, setTouching] = useState(false);
  const playing = !reduce && !paused && !hovered && !focused && !touching && count > 1;

  // Every caller is a person taking control (dots, prev / next, arrow keys), so the
  // rotation stops: a slide must never move under someone who is already steering.
  const go = (next: number) => {
    const i = (next + count) % count;
    setIndex(i);
    setReached((r) => Math.max(r, i));
    setPaused(true);
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
  const named = item.named_traits.filter(isTraitKey).slice(0, 3);
  // The same rule as the film page (TZ 1.23): the side decides the sentence, and a film
  // with nothing named gets none at all rather than a claim with nothing behind it.
  const side = named.length > 0 ? item.trait_side : null;
  const sentence =
    item.explanation ??
    (side === null
      ? null
      : t(side === "difference" ? "movie.differsFallback" : "movie.whyYouFallback", {
          traits: named.map((key) => t(traitLabelKey(key))).join(", "),
        }));
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
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      // Touch has no hover, so a tap had nothing holding the rotation: the slide could
      // change between the finger coming down and the click, and "See why" then opened
      // the next film. The hold starts at pointerdown, which clears the timer before the
      // click; pointerup restarts the 7 s from zero instead of firing what was left. A
      // tap also leaves focus inside the hero, which holds it until focus moves away.
      onPointerDown={() => setTouching(true)}
      onPointerUp={() => setTouching(false)}
      onPointerCancel={() => setTouching(false)}
      onFocus={() => setFocused(true)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setFocused(false);
      }}
      onKeyDown={onKeyDown}
    >
      <div className="home-hero-media" ref={media} aria-hidden="true">
        {items.map((it, i) =>
          // The slides reached so far and the next one; the rest load when they come up.
          i <= reached + 1 ? <HeroImage key={it.movie.id} movie={it.movie} active={i === index} first={i === 0} /> : null,
        )}
      </div>
      {/* While it rotates the change is not announced; once it holds, it is. */}
      <div className="home-hero-body" aria-live={playing ? "off" : "polite"}>
        {/* Keyed by film: each slide is new content, not the last one's text moving (CLS). */}
        <div
          key={movie.id}
          className="home-hero-slide"
          role="group"
          aria-roledescription="slide"
          aria-label={t("hero.slide", { n: index + 1, total: count })}
        >
          <Kicker band={item.band} side={side} as="p" />
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
          {sentence !== null && <p className="home-hero-why">{sentence}</p>}
          <div className="home-hero-actions">
            <Link className="btn btn-secondary" to={`/movie/${movie.id}`}>
              <Icon as={Sparkles} /> {t("hero.why")}
            </Link>
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
