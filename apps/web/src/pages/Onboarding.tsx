import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent } from "react";
import { Check } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Icon } from "../components/Icon";
import { Poster } from "../components/Poster";
import { RatingInput, showsLikedAspects } from "../components/RatingInput";
import { EmptyState, ErrorState, Loading, SavingLabel, Skeleton } from "../components/States";
import { OfflineBanner } from "../components/Layout";
import { useT } from "../i18n";
import { useAuth } from "../lib/auth";
import { movieMeta } from "../lib/format";
import {
  clearProgress,
  loadProgress,
  saveProgress,
  type OnboardingProgress,
  type UnsavedRating,
} from "../lib/onboardingStore";
import {
  ONBOARDING_PAGE,
  useForgetRecommendations,
  useOnboardingFilms,
  useRate,
  useRatings,
  useSearch,
} from "../lib/queries";
import type { TraitKey } from "../lib/traits";
import type { Movie } from "../lib/types";

/** The steps in order: a higher number is forward. */
const STEP_ORDER: Record<OnboardingProgress["step"], number> = { pick: 0, rate: 1, done: 2 };

/** FR-3: no recommendations before 10 ratings. */
export const REQUIRED_RATINGS = 10;
const DEFAULT_SCORE = 7;

function Progress({ step }: { step: 1 | 2 | 3 }) {
  const t = useT();
  return (
    <div className="progress-dots" role="img" aria-label={t("onboarding.progress", { step })}>
      {[1, 2, 3].map((n) => (
        <i key={n} className={n <= step ? "on" : ""} />
      ))}
    </div>
  );
}

function PickGrid({
  films,
  picked,
  onToggle,
}: {
  films: Movie[];
  picked: Set<number>;
  onToggle: (movie: Movie) => void;
}) {
  const t = useT();
  return (
    <div className="grid">
      {films.map((movie) => {
        const on = picked.has(movie.id);
        return (
          <button
            key={movie.id}
            type="button"
            className="pick-tile"
            aria-pressed={on}
            aria-label={on ? t("onboarding.pick.selected", { title: movie.title }) : movie.title}
            onClick={() => onToggle(movie)}
          >
            <Poster title={movie.title} path={movie.poster_path} size="w185" />
            {on && (
              <span className="check" aria-hidden="true">
                <Icon as={Check} size={14} />
              </span>
            )}
            <span className="pick-title" aria-hidden="true">
              {movie.title}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function GridSkeleton() {
  return (
    <Loading>
      <div className="grid">
        {Array.from({ length: 12 }, (_, i) => (
          <Skeleton key={i} className="poster" />
        ))}
      </div>
    </Loading>
  );
}

function PickStep({
  progress,
  update,
  ratedCount,
}: {
  progress: OnboardingProgress;
  update: (next: Partial<OnboardingProgress>) => void;
  ratedCount: number;
}) {
  const t = useT();
  const [q, setQ] = useState("");
  const films = useOnboardingFilms(progress.offset);
  const search = useSearch({ q: q.trim(), limit: 30 });
  const searching = q.trim().length > 0;
  const picked = useMemo(() => new Set(progress.picks.map((m) => m.id)), [progress.picks]);
  const need = Math.max(REQUIRED_RATINGS - ratedCount - progress.picks.length, 0);
  const total = Math.min(ratedCount + progress.picks.length, REQUIRED_RATINGS);

  function toggle(movie: Movie) {
    update({
      picks: picked.has(movie.id)
        ? progress.picks.filter((m) => m.id !== movie.id)
        : [...progress.picks, movie],
    });
  }

  function body() {
    const query = searching ? search : films;
    if (query.data !== undefined) {
      if (query.data.length === 0) {
        return searching ? (
          <p role="status">{t("onboarding.pick.noResults", { q: q.trim() })}</p>
        ) : (
          <EmptyState
            message={t("onboarding.pick.empty")}
            action={{
              label: t("onboarding.pick.search"),
              onClick: () => document.getElementById("onboarding-search")?.focus(),
            }}
          />
        );
      }
      return <PickGrid films={query.data} picked={picked} onToggle={toggle} />;
    }
    if (query.isPending && query.fetchStatus !== "paused") return <GridSkeleton />;
    return (
      <ErrorState
        message={query.fetchStatus === "paused" ? t("common.offlineNoCache") : t("onboarding.pick.error")}
        onRetry={() => void query.refetch()}
      />
    );
  }

  return (
    <>
      <Progress step={1} />
      <h1 className="screen-title">{t("onboarding.pick.title")}</h1>
      <p className="muted">{t("onboarding.pick.subtitle")}</p>
      <label htmlFor="onboarding-search" className="visually-hidden">
        {t("onboarding.pick.search")}
      </label>
      <input
        id="onboarding-search"
        className="field"
        type="search"
        placeholder={t("onboarding.pick.searchPlaceholder")}
        value={q}
        onChange={(e) => setQ(e.target.value)}
        style={{ marginBottom: 16 }}
      />
      {body()}

      <div className="sticky-foot">
        <div className="sticky-foot-inner">
          <div className="foot-meta">
            <span aria-live="polite">{t("onboarding.pick.count", { n: total })}</span>
            {!searching && (
              <button
                type="button"
                className="link-btn"
                onClick={() => update({ offset: progress.offset + ONBOARDING_PAGE })}
              >
                {t("onboarding.pick.noneSeen")}
              </button>
            )}
          </div>
          <button
            type="button"
            className="btn btn-primary btn-block"
            disabled={need > 0}
            onClick={() => update({ step: "rate", index: 0 })}
          >
            {need > 0 ? t("onboarding.pick.needMore", { n: need }) : t("onboarding.pick.continue")}
          </button>
        </div>
      </div>
    </>
  );
}

function RateStep({
  progress,
  update,
  ratedCount,
  onRate,
}: {
  progress: OnboardingProgress;
  update: (next: Partial<OnboardingProgress>) => void;
  ratedCount: number;
  /** Hands the score to Flow, which saves it under this film's id. */
  onRate: (rating: UnsavedRating) => void;
}) {
  const t = useT();
  const [value, setValue] = useState(DEFAULT_SCORE);
  const [aspects, setAspects] = useState<TraitKey[]>([]);
  const movie = progress.picks[progress.index];

  const onChange = useCallback((next: number) => setValue(next), []);

  if (!movie) {
    const need = Math.max(REQUIRED_RATINGS - ratedCount, 0);
    return (
      <>
        <Progress step={2} />
        <EmptyState
          message={t("onboarding.rate.needMore", { n: need })}
          action={{ label: t("onboarding.rate.pickMore"), onClick: () => update({ step: "pick", picks: [], index: 0 }) }}
        />
      </>
    );
  }

  function advance(picks: Movie[], index: number, rated: number) {
    if (index < picks.length) update({ picks, index });
    else if (rated >= REQUIRED_RATINGS) update({ step: "done", picks: [], index: 0 });
    else update({ picks: [], index: 0 });
  }

  // Next moves on at once: the score is captured here, tied to this film's id, and saved
  // in the background (Flow). Waiting for the save kept this film on screen, so a number
  // pressed for the next film changed this one's score instead (tester 1, 2026-10-12).
  function next(event: MouseEvent) {
    if (!movie) return;
    // The second click of a double click lands on the next film's button: ignore it, or that
    // film would be rated at the default without being looked at.
    if (event.detail > 1) return;
    onRate({
      movie_id: movie.id,
      title: movie.title,
      score: value,
      liked_aspects: showsLikedAspects(value) ? aspects : [],
    });
    advance(progress.picks, progress.index + 1, ratedCount + 1);
  }

  function notSeen() {
    const picks = progress.picks.filter((_, i) => i !== progress.index);
    advance(picks, progress.index, ratedCount);
  }

  return (
    <>
      <Progress step={2} />
      <div className="title-row">
        <h1 className="screen-title">{t("onboarding.rate.title")}</h1>
        <span className="mono meta">
          {t("onboarding.rate.position", { i: progress.index + 1, n: progress.picks.length })}
        </span>
      </div>
      <div className="rate-card">
        <Poster title={movie.title} path={movie.poster_path} eager />
        <div>
          <h2 className="film-title" style={{ fontSize: 22 }}>
            {movie.title}
          </h2>
          <div className="meta">{movieMeta(movie, t)}</div>
        </div>
      </div>
      <RatingInput value={value} onChange={onChange} aspects={aspects} onAspectsChange={setAspects} />

      <div className="sticky-foot">
        <div className="sticky-foot-inner foot-actions">
          <button type="button" className="btn btn-ghost" onClick={notSeen}>
            {t("onboarding.rate.notSeen")}
          </button>
          <button type="button" className="btn btn-primary" onClick={next}>
            {t("onboarding.rate.next")}
          </button>
        </div>
      </div>
    </>
  );
}

/** /onboarding — pick → rate → done (FR-3). Resumes after a reload. */
export default function Onboarding() {
  const { session } = useAuth();
  // Progress is stored per user, so it can only be read once the session is known.
  if (!session) return <GridSkeleton />;
  return <Flow key={session.userId} userId={session.userId} />;
}

function Flow({ userId }: { userId: string }) {
  const t = useT();
  const navigate = useNavigate();
  const ratings = useRatings();
  const forgetRecommendations = useForgetRecommendations();
  const ratedCount = ratings.data?.length ?? 0;
  const { mutateAsync: rate } = useRate();
  const [progress, setProgress] = useState<OnboardingProgress>(() => loadProgress(userId));
  // Films whose last save failed: named in the alert, sent again by its button.
  const [failed, setFailed] = useState<ReadonlySet<number>>(() => new Set());
  // Which way the last step change went, for the slide (docs/ui.md 7): forward from the
  // right, back from the left. Nothing slides on the first screen (also after a reload).
  const [shown, setShown] = useState(progress.step);
  const [slide, setSlide] = useState<"forward" | "back" | null>(null);
  if (progress.step !== shown) {
    setSlide(STEP_ORDER[progress.step] > STEP_ORDER[shown] ? "forward" : "back");
    setShown(progress.step);
  }

  const patch = useCallback(
    (change: (current: OnboardingProgress) => OnboardingProgress) => {
      setProgress((current) => {
        const next = change(current);
        saveProgress(userId, next);
        return next;
      });
    },
    [userId],
  );
  const update = useCallback(
    (next: Partial<OnboardingProgress>) => patch((current) => ({ ...current, ...next })),
    [patch],
  );

  /** Sends one film's score; it stays in `unsaved` (and in storage) until the server has it. */
  const send = useCallback(
    (rating: UnsavedRating) => {
      setFailed((current) => without(current, rating.movie_id));
      const { title: _title, ...body } = rating;
      rate(body).then(
        () =>
          patch((current) => ({
            ...current,
            unsaved: (current.unsaved ?? []).filter((u) => u.movie_id !== rating.movie_id),
          })),
        () => setFailed((current) => new Set(current).add(rating.movie_id)),
      );
    },
    [rate, patch],
  );

  const onRate = useCallback(
    (rating: UnsavedRating) => {
      patch((current) => ({
        ...current,
        unsaved: [...(current.unsaved ?? []).filter((u) => u.movie_id !== rating.movie_id), rating],
      }));
      send(rating);
    },
    [patch, send],
  );

  // Scores the last visit left unconfirmed (closed tab, lost connection) go out again, once.
  const resent = useRef(false);
  useEffect(() => {
    if (resent.current) return;
    resent.current = true;
    for (const rating of progress.unsaved ?? []) send(rating);
  }, [progress.unsaved, send]);

  const unsaved = progress.unsaved ?? [];
  const failedRatings = unsaved.filter((u) => failed.has(u.movie_id));
  const saving = unsaved.length > failedRatings.length;

  function finish() {
    if (unsaved.length > 0) return; // every score is on the server first
    clearProgress(userId);
    // The feed loads afresh: a cached one from before these ratings would send us back here.
    forgetRecommendations();
    navigate("/", { replace: true });
  }

  return (
    <>
      <OfflineBanner />
      <main className="onboarding" id="main">
        {/* Keyed by step: each step is new content sliding in; the fixed foot bar stays put. */}
        <div key={progress.step} className={slide ? `step step-${slide}` : "step"}>
          {progress.step === "pick" && <PickStep progress={progress} update={update} ratedCount={ratedCount} />}
          {progress.step === "rate" && (
            // Keyed by film: each film starts from the default score and a clean error state.
            // (An effect that reset them ran after the first paint and could undo a score
            // given in between.)
            <RateStep
              key={progress.picks[progress.index]?.id ?? "none"}
              progress={progress}
              update={update}
              ratedCount={ratedCount}
              onRate={onRate}
            />
          )}
          {progress.step === "done" && (
            <>
              <Progress step={3} />
              <h1 className="screen-title">{t("onboarding.done.title")}</h1>
              <p>{t("onboarding.done.body", { n: ratedCount })}</p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={finish}
                aria-disabled={unsaved.length > 0 || undefined}
                autoFocus
              >
                <SavingLabel saving={saving}>{t("onboarding.done.cta")}</SavingLabel>
              </button>
            </>
          )}
        </div>
        {failedRatings.length > 0 && (
          // Fixed above the foot bar: it appears without moving the page (CLS 0).
          <div className="save-alert" role="alert">
            <span>{t("onboarding.rate.unsaved", { titles: failedRatings.map((u) => u.title).join(", ") })}</span>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => failedRatings.forEach(send)}>
              {t("common.retry")}
            </button>
          </div>
        )}
      </main>
    </>
  );
}

function without(set: ReadonlySet<number>, id: number): ReadonlySet<number> {
  if (!set.has(id)) return set;
  const next = new Set(set);
  next.delete(id);
  return next;
}
