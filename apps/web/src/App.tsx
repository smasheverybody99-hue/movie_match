import type { ReactNode } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/Layout";
import { Loading, Skeleton } from "./components/States";
import { useT } from "./i18n";
import { useAuth } from "./lib/auth";
import Dna from "./pages/Dna";
import Feed from "./pages/Feed";
import MoviePage from "./pages/MoviePage";
import Onboarding from "./pages/Onboarding";
import Profile, { AboutPage } from "./pages/Profile";
import Search from "./pages/Search";
import Watchlist from "./pages/Watchlist";
import Welcome from "./pages/Welcome";

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
  return <>{children}</>;
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
        <Route path="movie/:id" element={<MoviePage />} />
        <Route path="watchlist" element={<Watchlist />} />
        <Route path="dna" element={<Dna />} />
        <Route path="profile" element={<Profile />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
