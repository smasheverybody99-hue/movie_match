import { Bookmark, Dna, House, Search, type LucideIcon } from "lucide-react";
import { useState, type FormEvent } from "react";
import { NavLink, Outlet, useLocation, useMatch, useNavigate } from "react-router-dom";

import { useT, type MessageKey } from "../i18n";
import { useAuth } from "../lib/auth";
import { useOnline } from "../lib/useOnline";
import { Icon } from "./Icon";
import { Logo } from "./Logo";

/**
 * Four of the design's five sections: the Assistant arrives in Phase 4. Web: left
 * sidebar from 640px; below that a top bar and a bottom bar (design system, desktop).
 */
const SECTIONS: { to: string; label: MessageKey; icon: LucideIcon; end?: boolean }[] = [
  { to: "/", label: "nav.home", icon: House, end: true },
  { to: "/search", label: "nav.search", icon: Search },
  { to: "/dna", label: "nav.dna", icon: Dna },
  { to: "/watchlist", label: "nav.watchlist", icon: Bookmark },
];

/**
 * Search pill, top right on wide screens (design brief v2). Enter opens the search
 * screen with the text; on the search screen itself the pill steps aside for its own
 * field.
 */
function TopSearch() {
  const t = useT();
  const navigate = useNavigate();
  const onSearch = useMatch("/search");
  const [q, setQ] = useState("");
  if (onSearch) return null;

  function submit(event: FormEvent) {
    event.preventDefault();
    const text = q.trim();
    navigate(text ? `/search?q=${encodeURIComponent(text)}` : "/search");
    setQ("");
  }

  return (
    <form role="search" className="top-search" onSubmit={submit}>
      <Icon as={Search} size={18} />
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={t("search.placeholder")}
        aria-label={t("search.label")}
      />
    </form>
  );
}

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

/** The mark and the name; the link carries the accessible name, so the mark is decorative. */
function Brand({ size }: { size: number }) {
  const t = useT();
  return (
    <NavLink to="/" className="brand" aria-label={t("app.name")}>
      <Logo size={size} className="brand-logo" />
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
  const location = useLocation();
  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        {t("nav.skipToContent")}
      </a>
      <aside className="sidebar">
        <Brand size={32} />
        <nav aria-label={t("nav.label")}>
          <ul className="nav-list">
            {SECTIONS.map((s) => (
              <li key={s.to}>
                <NavLink to={s.to} end={s.end} className="nav-link">
                  <span className="nav-icon">
                    <Icon as={s.icon} />
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
          <Brand size={28} />
          <NavLink to="/profile" className="avatar-link" aria-label={t("nav.profile")}>
            <Avatar />
          </NavLink>
        </header>
        <div className="page-top">
          <TopSearch />
        </div>
        <main id="main" className="page" tabIndex={-1}>
          {/* Keyed by path: a new page is new content and fades in (120 ms, opacity only:
              a transform would carry the page's fixed bars with it). The shell stays. */}
          <div key={location.pathname} className="page-enter">
            <Outlet />
          </div>
        </main>
        <nav className="bottom-nav" aria-label={t("nav.label")}>
          {SECTIONS.map((s) => (
            <NavLink key={s.to} to={s.to} end={s.end}>
              <span className="nav-icon">
                <Icon as={s.icon} size={22} />
              </span>
              {t(s.label)}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
}
