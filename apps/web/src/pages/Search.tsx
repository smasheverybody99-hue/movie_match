import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { MovieCard } from "../components/MovieCard";
import { useQuickActions } from "../components/QuickActions";
import { EmptyState, QueryView, Skeleton } from "../components/States";
import { traitLabelKey } from "../components/Traits";
import { useT } from "../i18n";
import type { SearchParams } from "../lib/api";
import { useSearch } from "../lib/queries";
import { TRAIT_KEYS, type TraitKey } from "../lib/traits";

const RUNTIMES = [90, 120, 150] as const;
/** "Strong in X" means the film scores at least this on X — the design's strong band. */
export const STRONG_TRAIT = 70;

interface Filters {
  yearFrom: string;
  yearTo: string;
  maxRuntime: string;
  traits: TraitKey[];
}

const NO_FILTERS: Filters = { yearFrom: "", yearTo: "", maxRuntime: "", traits: [] };

function year(value: string): number | undefined {
  const n = Number(value);
  return value.length === 4 && Number.isInteger(n) && n >= 1870 && n <= 2100 ? n : undefined;
}

export function toParams(q: string, f: Filters): SearchParams {
  return {
    q: q.trim() || undefined,
    yearFrom: year(f.yearFrom),
    yearTo: year(f.yearTo),
    maxRuntime: f.maxRuntime ? Number(f.maxRuntime) : undefined,
    traits: f.traits,
    traitMinimum: STRONG_TRAIT,
  };
}

/** `value`, once it has stopped changing for `ms`: one request per pause, not per key. */
function useDebounced<T>(value: T, ms: number): T {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), ms);
    return () => clearTimeout(timer);
  }, [value, ms]);
  return settled;
}

function hasFilters(f: Filters): boolean {
  return f.yearFrom !== "" || f.yearTo !== "" || f.maxRuntime !== "" || f.traits.length > 0;
}

function GridSkeleton() {
  return (
    <div className="grid">
      {Array.from({ length: 12 }, (_, i) => (
        <div key={i}>
          <Skeleton className="poster" />
          <Skeleton className="skeleton-line" />
        </div>
      ))}
    </div>
  );
}

function FilterPanel({ filters, onChange }: { filters: Filters; onChange: (f: Filters) => void }) {
  const t = useT();
  const set = (patch: Partial<Filters>) => onChange({ ...filters, ...patch });
  return (
    <div className="filters">
      <fieldset>
        <legend>{t("search.yearFrom")} – {t("search.yearTo")}</legend>
        <div className="year-row">
          <div>
            <label className="visually-hidden" htmlFor="year-from">
              {t("search.yearFrom")}
            </label>
            <input
              id="year-from"
              className="field"
              inputMode="numeric"
              maxLength={4}
              placeholder={t("search.yearFrom")}
              value={filters.yearFrom}
              onChange={(e) => set({ yearFrom: e.target.value.replace(/\D/g, "") })}
            />
          </div>
          <div>
            <label className="visually-hidden" htmlFor="year-to">
              {t("search.yearTo")}
            </label>
            <input
              id="year-to"
              className="field"
              inputMode="numeric"
              maxLength={4}
              placeholder={t("search.yearTo")}
              value={filters.yearTo}
              onChange={(e) => set({ yearTo: e.target.value.replace(/\D/g, "") })}
            />
          </div>
        </div>
      </fieldset>
      <div>
        <label className="field-label" htmlFor="runtime">
          {t("search.runtime")}
        </label>
        <select
          id="runtime"
          className="field"
          value={filters.maxRuntime}
          onChange={(e) => set({ maxRuntime: e.target.value })}
        >
          <option value="">{t("search.runtimeAny")}</option>
          {RUNTIMES.map((n) => (
            <option key={n} value={n}>
              {t("search.runtimeUpTo", { n })}
            </option>
          ))}
        </select>
      </div>
      <fieldset>
        <legend>{t("search.traits")}</legend>
        <div className="chip-row">
          {TRAIT_KEYS.map((key) => {
            const on = filters.traits.includes(key);
            return (
              <button
                key={key}
                type="button"
                className="chip"
                aria-pressed={on}
                onClick={() =>
                  set({ traits: on ? filters.traits.filter((k) => k !== key) : [...filters.traits, key] })
                }
              >
                {t(traitLabelKey(key))}
              </button>
            );
          })}
        </div>
      </fieldset>
      {hasFilters(filters) && (
        <button type="button" className="btn btn-ghost" onClick={() => onChange(NO_FILTERS)}>
          {t("search.clear")}
        </button>
      )}
    </div>
  );
}

/**
 * /search — title, year, runtime and trait filters. Streaming providers are not
 * offered: the catalogue has no provider data yet (docs/STATUS.md).
 */
export default function Search() {
  const t = useT();
  const [searchParams] = useSearchParams();
  // The search pill in the shell arrives here with ?q=.
  const [q, setQ] = useState(() => searchParams.get("q") ?? "");
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);
  const typed = useDebounced(q, 250);
  const params = toParams(typed, filters);
  const query = useSearch(params);
  const idle = !params.q && !hasFilters(filters);
  // The same cards as Home's rows, with the same quick Rate and Save.
  const { quickFor, overlay } = useQuickActions();

  return (
    <>
      <h1 className="screen-title">{t("search.title")}</h1>
      <div className="search-bar" role="search">
        <label htmlFor="search-q" className="visually-hidden">
          {t("search.label")}
        </label>
        <input
          id="search-q"
          className="field"
          type="search"
          placeholder={t("search.placeholder")}
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      <div className="search-layout">
        <details className="filters-toggle" open={typeof window !== "undefined" && window.innerWidth >= 900}>
          <summary>{t("search.filters")}</summary>
          <FilterPanel filters={filters} onChange={setFilters} />
        </details>
        <section aria-labelledby="results-title" aria-busy={query.isFetching}>
          <h2 className="section-title" id="results-title">
            {idle ? t("search.popular") : t("search.results")}
          </h2>
          <QueryView query={query} skeleton={<GridSkeleton />} error={t("search.error")}>
            {(movies) =>
              movies.length === 0 ? (
                <EmptyState
                  message={t("search.empty")}
                  action={{
                    label: t("search.clear"),
                    onClick: () => {
                      setQ("");
                      setFilters(NO_FILTERS);
                    },
                  }}
                />
              ) : (
                <ul className="grid" style={{ listStyle: "none", margin: 0, padding: 0 }}>
                  {movies.map((movie) => (
                    <li key={movie.id}>
                      <MovieCard movie={movie} quick={quickFor(movie)} />
                    </li>
                  ))}
                </ul>
              )
            }
          </QueryView>
        </section>
      </div>
      {overlay}
    </>
  );
}
