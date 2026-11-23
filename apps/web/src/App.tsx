import { lazy, Suspense, type ReactNode } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";

import { DataNoticeGate } from "./components/DataNotice";
import { AppShell } from "./components/Layout";
import { Loading, Skeleton } from "./components/States";
import { useT } from "./i18n";
import { useAuth } from "./lib/auth";
import Feed from "./pages/Feed";
import MoviePage from "./pages/MoviePage";
import Welcome from "./pages/Welcome";

// The pages a visit lands on stay in the main bundle: Welcome, Home and the film page
// (a shared link). The rest load when first opened, so a cold film page downloads and
// runs less before its first paint (F3 item 5, LCP).
const Assistant = lazy(() => import("./pages/Assistant"));
const Dna = lazy(() => import("./pages/Dna"));
const Onboarding = lazy(() => import("./pages/Onboarding"));
const Profile = lazy(() => import("./pages/Profile"));
const AboutPage = lazy(() => import("./pages/Profile").then((m) => ({ default: m.AboutPage })));
const Search = lazy(() => import("./pages/Search"));
const Watchlist = lazy(() => import("./pages/Watchlist"));

function PageSkeleton() {
  const t = useT();
  return (
    <main className="page" aria-label={t("app.loadingPage")}>
      <Loading>
        <Skeleton className="skeleton-line" style={{ width: 200, height: 24 }} />
        <Skeleton style={{ height: 240, marginTop: 16 }} />
      </Loading>
    </main>
  );
}

/** Every screen after /welcome needs a session (FR-1: no guest mode). */
function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  if (status === "loading") return <PageSkeleton />;
  if (status !== "signedIn") return <Navigate to="/welcome" replace />;
  // The alpha's data notice comes before anything that could send data (ADR 0004).
  return <DataNoticeGate loading={<PageSkeleton />}>{children}</DataNoticeGate>;
}

function PublicOnly({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  if (status === "loading") return <PageSkeleton />;
  if (status === "signedIn") return <Navigate to="/" replace />;
  return <>{children}</>;
}

function NotFound() {
  const t = useT();
  return (
    <div className="state">
      <h1 className="screen-title">{t("notFound.title")}</h1>
      <Link to="/" className="btn btn-primary">
        {t("notFound.cta")}
      </Link>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route
          path="/welcome"
          element={
            <PublicOnly>
              <Welcome />
            </PublicOnly>
          }
        />
        <Route path="/about" element={<AboutPage />} />
        <Route
          path="/onboarding"
          element={
            <RequireAuth>
              <Onboarding />
            </RequireAuth>
          }
        />
        <Route
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route index element={<Feed />} />
          <Route path="search" element={<Search />} />
          <Route path="assistant" element={<Assistant />} />
          <Route path="movie/:id" element={<MoviePage />} />
          <Route path="watchlist" element={<Watchlist />} />
          <Route path="dna" element={<Dna />} />
          <Route path="profile" element={<Profile />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
