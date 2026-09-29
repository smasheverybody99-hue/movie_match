import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { useT, type MessageKey } from "../i18n";
import { useAuth } from "../lib/auth";
import { AuthFailure, type OAuthProvider } from "../lib/supabase";

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function failureMessage(error: unknown): MessageKey {
  return error instanceof AuthFailure && error.kind === "provider_disabled"
    ? "welcome.providerOff"
    : "welcome.error";
}

/**
 * /welcome — one sentence and the sign-in buttons. Google and Apple first, then a
 * passwordless email link. No guest mode (FR-1).
 */
export default function Welcome() {
  const t = useT();
  const auth = useAuth();
  const [emailOpen, setEmailOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [invalid, setInvalid] = useState(false);
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [error, setError] = useState<MessageKey | null>(null);
  const [busy, setBusy] = useState(false);
  const disabled = auth.status === "unconfigured" || busy;

  async function oauth(provider: OAuthProvider) {
    setError(null);
    setBusy(true);
    try {
      await auth.signInWithOAuth(provider); // the browser leaves for the provider
    } catch (e) {
      setError(failureMessage(e));
    } finally {
      setBusy(false);
    }
  }

  async function sendLink(event: FormEvent) {
    event.preventDefault();
    const value = email.trim();
    if (!EMAIL.test(value)) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    setError(null);
    setBusy(true);
    try {
      await auth.signInWithEmail(value);
      setSentTo(value);
    } catch (e) {
      setError(failureMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="welcome" id="main">
      <div className="welcome-inner">
        <span className="brand-mark welcome-mark" aria-hidden="true">
          {t("app.name").slice(0, 1)}
        </span>
        <h1>{t("app.name")}</h1>
        <p className="welcome-tagline">{t("welcome.tagline")}</p>

        {auth.status === "unconfigured" && (
          <p className="state" role="alert">
            {t("welcome.notConfigured")}
          </p>
        )}

        <div className="stack">
          <button type="button" className="btn btn-secondary btn-block" disabled={disabled} onClick={() => void oauth("google")}>
            {t("welcome.google")}
          </button>
          <button type="button" className="btn btn-secondary btn-block" disabled={disabled} onClick={() => void oauth("apple")}>
            {t("welcome.apple")}
          </button>

          {!emailOpen ? (
            <button
              type="button"
              className="btn btn-ghost btn-block"
              disabled={auth.status === "unconfigured"}
              onClick={() => setEmailOpen(true)}
            >
              {t("welcome.email")}
            </button>
          ) : sentTo ? (
            <p role="status">{t("welcome.emailSent", { email: sentTo })}</p>
          ) : (
            <form className="stack" onSubmit={(e) => void sendLink(e)} noValidate>
              <label className="field-label" htmlFor="email">
                {t("welcome.emailLabel")}
              </label>
              <input
                id="email"
                className="field"
                type="email"
                autoComplete="email"
                inputMode="email"
                placeholder={t("welcome.emailPlaceholder")}
                value={email}
                aria-invalid={invalid}
                aria-describedby={invalid ? "email-error" : undefined}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
              />
              {invalid && (
                <p id="email-error" className="field-error">
                  {t("welcome.emailInvalid")}
                </p>
              )}
              <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
                {t("welcome.emailSend")}
              </button>
            </form>
          )}
        </div>

        {error && (
          <p className="field-error" role="alert">
            {t(error)}
          </p>
        )}

        <p className="fine-print">
          {t("welcome.terms")}{" "}
          <Link to="/about" className="link-btn">
            {t("welcome.about")}
          </Link>
        </p>
      </div>
    </main>
  );
}
