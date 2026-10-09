import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Dialog, DialogCancel } from "../components/Dialog";
import { FieldError } from "../components/FieldError";
import { LANGS, useI18n, useT } from "../i18n";
import { useAuth } from "../lib/auth";
import { useDeleteAccount } from "../lib/queries";

/** TMDB attribution: required on the free tier from the day the app is public (docs/legal.md). */
export function About() {
  const t = useT();
  return (
    <section aria-labelledby="about-title">
      <h2 className="section-title" id="about-title">
        {t("profile.about")}
      </h2>
      <p>{t("profile.tmdb")}</p>
      <p>
        <a href="https://www.themoviedb.org/" target="_blank" rel="noreferrer">
          {t("profile.tmdbLink")}
        </a>
      </p>
    </section>
  );
}

/** /about — public, linked from /welcome. */
export function AboutPage() {
  const t = useT();
  return (
    <main className="welcome" id="main">
      <div className="welcome-inner">
        <h1 className="screen-title">{t("app.name")}</h1>
        <About />
        <Link to="/welcome" className="btn btn-ghost">
          {t("nav.back")}
        </Link>
      </div>
    </main>
  );
}

/** /profile — language, sign out, delete account, about. */
export default function Profile() {
  const t = useT();
  const { lang, setLang } = useI18n();
  const auth = useAuth();
  const navigate = useNavigate();
  const remove = useDeleteAccount();
  const [confirming, setConfirming] = useState(false);

  async function signOut() {
    await auth.signOut().catch(() => undefined);
    navigate("/welcome", { replace: true });
  }

  return (
    <>
      <h1 className="screen-title">{t("profile.title")}</h1>
      {auth.session?.email && <p className="muted">{auth.session.email}</p>}

      <fieldset className="aspects">
        <legend className="field-label">{t("profile.language")}</legend>
        <div className="chip-row">
          {LANGS.map((code) => (
            <button
              key={code}
              type="button"
              className="chip"
              aria-pressed={lang === code}
              lang={code}
              onClick={() => setLang(code)}
            >
              {t(`lang.${code}`)}
            </button>
          ))}
        </div>
      </fieldset>

      <div className="stack" style={{ maxWidth: 320, marginTop: 24 }}>
        <button type="button" className="btn btn-secondary" onClick={() => void signOut()}>
          {t("profile.signOut")}
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => setConfirming(true)}>
          {t("profile.delete")}
        </button>
      </div>

      <About />

      {confirming && (
        <Dialog title={t("profile.delete")} onClose={() => setConfirming(false)}>
          <p>{t("profile.deleteConfirm")}</p>
          {remove.isError && (
            <FieldError>{t("profile.deleteError")}</FieldError>
          )}
          <div className="foot-actions">
            <DialogCancel>{t("common.cancel")}</DialogCancel>
            <button
              type="button"
              className="btn btn-primary"
              disabled={remove.isPending}
              onClick={() => remove.mutate(undefined, { onSuccess: () => void signOut() })}
            >
              {t("profile.deleteYes")}
            </button>
          </div>
        </Dialog>
      )}
    </>
  );
}
