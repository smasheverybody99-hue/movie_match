import { createClient, type AuthError, type Session as SupabaseSession } from "@supabase/supabase-js";

/**
 * The slice of Supabase Auth the app uses, behind a small interface so screens and
 * tests never touch the SDK. Supabase issues and refreshes the access token (FR-1:
 * "token expiry refreshes automatically"); the API only verifies it.
 */
export interface Session {
  accessToken: string;
  userId: string;
  email: string | null;
}

export type OAuthProvider = "google" | "apple";

/** Why a sign-in attempt failed, in terms a screen can word for a person. */
export class AuthFailure extends Error {
  constructor(
    readonly kind: "provider_disabled" | "failed",
    message: string,
  ) {
    super(message);
    this.name = "AuthFailure";
  }
}

export interface AuthClient {
  getSession(): Promise<Session | null>;
  /** Called on sign-in, sign-out and every token refresh. Returns an unsubscribe. */
  onChange(listener: (session: Session | null) => void): () => void;
  signInWithOAuth(provider: OAuthProvider): Promise<void>;
  signInWithEmail(email: string): Promise<void>;
  signOut(): Promise<void>;
}

function toSession(session: SupabaseSession | null): Session | null {
  if (!session) return null;
  return {
    accessToken: session.access_token,
    userId: session.user.id,
    email: session.user.email ?? null,
  };
}

function check(error: AuthError | null): void {
  if (!error) return;
  // Supabase answers "Unsupported provider: provider is not enabled" (400) for a
  // provider that is not switched on in the dashboard.
  const disabled = /not enabled|unsupported provider/i.test(error.message);
  throw new AuthFailure(disabled ? "provider_disabled" : "failed", error.message);
}

/** Null when the Supabase URL or anon key is missing: sign-in is then not configured. */
export function createSupabaseAuth(): AuthClient | null {
  const url = import.meta.env.VITE_SUPABASE_URL;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
  if (!url || !anonKey) return null;

  const client = createClient(url, anonKey, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
  });
  const redirectTo = `${window.location.origin}/`;

  return {
    async getSession() {
      const { data } = await client.auth.getSession();
      return toSession(data.session);
    },
    onChange(listener) {
      const { data } = client.auth.onAuthStateChange((_event, session) => {
        listener(toSession(session));
      });
      return () => data.subscription.unsubscribe();
    },
    async signInWithOAuth(provider) {
      const { error } = await client.auth.signInWithOAuth({
        provider,
        options: { redirectTo },
      });
      check(error);
    },
    async signInWithEmail(email) {
      const { error } = await client.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: redirectTo },
      });
      check(error);
    },
    async signOut() {
      const { error } = await client.auth.signOut();
      check(error);
    },
  };
}
