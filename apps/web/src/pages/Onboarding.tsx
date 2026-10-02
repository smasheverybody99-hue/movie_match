import { useCallback, useEffect, useMemo, useState } from "react";
import { Check } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { FieldError } from "../components/FieldError";
import { Icon } from "../components/Icon";
import { Poster } from "../components/Poster";
import { RatingInput, showsLikedAspects } from "../components/RatingInput";
import { EmptyState, ErrorState, Loading, Skeleton } from "../components/States";
import { OfflineBanner } from "../components/Layout";
import { useT } from "../i18n";
import { useAuth } from "../lib/auth";
import { movieMeta } from "../lib/format";
import {
  clearProgress,
  loadProgress,
  saveProgress,
  type OnboardingProgress,
} from "../lib/onboardingStore";
import { ONBOARDING_PAGE, useOnboardingFilms, useRate, useRatings, useSearch } from "../lib/queries";
import type { TraitKey } from "../lib/traits";
import type { Movie } from "../lib/types";

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
}: {
  progress: OnboardingProgress;
  update: (next: Partial<OnboardingProgress>) => void;
  ratedCount: number;
}) {
  const t = useT();
  const rate = useRate();
  const [value, setValue] = useState(DEFAULT_SCORE);
  const [aspects, setAspects] = useState<TraitKey[]>([]);
  const movie = progress.picks[progress.index];

  useEffect(() => {
    setValue(DEFAULT_SCORE);
    setAspects([]);
    rate.reset();
    // A new film starts from the default score and a clean error state.
  }, [movie?.id]);

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

  async function next() {
    if (!movie) return;
    try {
      await rate.mutateAsync({
        movie_id: movie.id,
        score: value,
        liked_aspects: showsLikedAspects(value) ? aspects : [],
      });
    } catch {
      return; // the error message is shown; the user can try again
    }
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
      {rate.isError && (
        <FieldError>{t("onboarding.rate.saveError")}</FieldError>
      )}

      <div className="sticky-foot">
        <div className="sticky-foot-inner foot-actions">
          <button type="button" className="btn btn-ghost" onClick={notSeen} disabled={rate.isPending}>
            {t("onboarding.rate.notSeen")}
          </button>
          <button type="button" className="btn btn-primary" onClick={() => void next()} disabled={rate.isPending}>
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
  const ratedCount = ratings.data?.length ?? 0;
  const [progress, setProgress] = useState<OnboardingProgress>(() => loadProgress(userId));

  const update = useCallback(
    (next: Partial<OnboardingProgress>) => {
      setProgress((current) => {
        const merged = { ...current, ...next };
        saveProgress(userId, merged);
        return merged;
      });
    },
    [userId],
  );

  function finish() {
    clearProgress(userId);
    navigate("/", { replace: true });
  }

  return (
    <>
      <OfflineBanner />
      <main className="onboarding" id="main">
        {progress.step === "pick" && <PickStep progress={progress} update={update} ratedCount={ratedCount} />}
        {progress.step === "rate" && <RateStep progress={progress} update={update} ratedCount={ratedCount} />}
        {progress.step === "done" && (
          <>
            <Progress step={3} />
            <h1 className="screen-title">{t("onboarding.done.title")}</h1>
            <p>{t("onboarding.done.body", { n: ratedCount })}</p>
            <button type="button" className="btn btn-primary" onClick={finish} autoFocus>
              {t("onboarding.done.cta")}
            </button>
          </>
        )}
      </main>
    </>
  );
}
