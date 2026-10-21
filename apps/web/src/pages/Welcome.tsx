import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { FieldError } from "../components/FieldError";
import { Logo } from "../components/Logo";
import { Beams, Magnet, Reveal, ShinyText, SplitText } from "../components/motion";
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
 *
 * The first screen anyone sees, so it carries the motion layer's opening (docs/ui.md,
 * "Harakat v3"): beams drifting behind it, the name arriving letter by letter, a sheen
 * over the sentence, and the buttons one after another. All of it is `transform` and
 * `opacity` over a layout that is already final, and all of it is gone — the screen
 * still complete — with `prefers-reduced-motion: reduce`.
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
      <Beams />
      <div className="welcome-inner">
        <Logo size={48} className="welcome-mark" />
        <SplitText as="h1" text={t("app.name")} by="chars" immediate stagger={0.035} />
        <p className="welcome-tagline">
          <ShinyText>{t("welcome.tagline")}</ShinyText>
        </p>

        {auth.status === "unconfigured" && (
          <p className="state" role="alert">
            {t("welcome.notConfigured")}
          </p>
        )}

        <Reveal className="stack" stagger={0.07} delay={0.2} y={14} immediate>
          <Magnet>
            <button type="button" className="btn btn-secondary btn-block" disabled={disabled} onClick={() => void oauth("google")}>
              {t("welcome.google")}
            </button>
          </Magnet>
          <Magnet>
            <button type="button" className="btn btn-secondary btn-block" disabled={disabled} onClick={() => void oauth("apple")}>
              {t("welcome.apple")}
            </button>
          </Magnet>

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
                <FieldError id="email-error" alert={false}>
                  {t("welcome.emailInvalid")}
                </FieldError>
              )}
              <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
                {t("welcome.emailSend")}
              </button>
            </form>
          )}
        </Reveal>

        {error && (
          <FieldError>{t(error)}</FieldError>
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
