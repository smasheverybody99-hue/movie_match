import { NavLink, Outlet } from "react-router-dom";

import { useT, type MessageKey } from "../i18n";
import { useAuth } from "../lib/auth";
import { useOnline } from "../lib/useOnline";

/**
 * Four of the design's five sections: the Assistant arrives in Phase 4. Web: left
 * sidebar from 640px; below that a top bar and a bottom bar (design system, desktop).
 */
const SECTIONS: { to: string; label: MessageKey; icon: string; end?: boolean }[] = [
  { to: "/", label: "nav.home", icon: "🏠", end: true },
  { to: "/search", label: "nav.search", icon: "🔍" },
  { to: "/dna", label: "nav.dna", icon: "🧬" },
  { to: "/watchlist", label: "nav.watchlist", icon: "🔖" },
];

export function OfflineBanner() {
  const t = useT();
  const online = useOnline();
  if (online) return null;
  return (
    <div className="offline-banner" role="status">
      {t("common.offline")}
    </div>
  );
}

function Brand() {
  const t = useT();
  return (
    <NavLink to="/" className="brand" aria-label={t("app.name")}>
      <span className="brand-mark" aria-hidden="true">
        {t("app.name").slice(0, 1)}
      </span>
      <span aria-hidden="true">{t("app.name").toUpperCase()}</span>
    </NavLink>
  );
}

function Avatar() {
  const { session } = useAuth();
  const letter = (session?.email ?? "?").slice(0, 1).toUpperCase();
  return (
    <span className="avatar" aria-hidden="true">
      {letter}
    </span>
  );
}

export function AppShell() {
  const t = useT();
  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        {t("nav.skipToContent")}
      </a>
      <aside className="sidebar">
        <Brand />
        <nav aria-label={t("nav.label")}>
          <ul className="nav-list">
            {SECTIONS.map((s) => (
              <li key={s.to}>
                <NavLink to={s.to} end={s.end} className="nav-link">
                  <span className="nav-icon" aria-hidden="true">
                    {s.icon}
                  </span>
                  {t(s.label)}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="sidebar-foot">
          <NavLink to="/profile" className="nav-link">
            <Avatar />
            {t("nav.profile")}
          </NavLink>
        </div>
      </aside>

      <div className="main">
        <OfflineBanner />
        <header className="topbar">
          <Brand />
          <NavLink to="/profile" className="avatar-link" aria-label={t("nav.profile")}>
            <Avatar />
          </NavLink>
        </header>
        <main id="main" className="page" tabIndex={-1}>
          <Outlet />
        </main>
        <nav className="bottom-nav" aria-label={t("nav.label")}>
          {SECTIONS.map((s) => (
            <NavLink key={s.to} to={s.to} end={s.end}>
              <span className="nav-icon" aria-hidden="true">
                {s.icon}
              </span>
              {t(s.label)}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
}
