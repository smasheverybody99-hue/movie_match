import {
  AuthClient as SupabaseAuthClient,
  type AuthError,
  type Session as SupabaseSession,
} from "@supabase/auth-js";

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

type SupabaseAuthOptions = ConstructorParameters<typeof SupabaseAuthClient>[0];

/**
 * The auth client exactly as `createClient` from supabase-js 2.117 built it, without the
 * realtime, storage, postgrest and functions clients the app never used (~33 KB gzip).
 * Changing any of these signs people out or breaks sign-in:
 * - storageKey: supabase-js's `sb-<project ref>-auth-token`; auth-js on its own would
 *   use `supabase.auth.token` and every saved session would be lost;
 * - url: `<project>/auth/v1`;
 * - headers: the anon key as `apikey` and as the bearer token;
 * - flowType "implicit": the Google and email links come back with the token in the URL
 *   fragment, which detectSessionInUrl reads.
 * The test checks these against createClient itself.
 */
export function authClientOptions(supabaseUrl: string, anonKey: string): SupabaseAuthOptions {
  const trimmed = supabaseUrl.trim();
  const base = new URL(trimmed.endsWith("/") ? trimmed : `${trimmed}/`);
  return {
    url: new URL("auth/v1", base).href,
    storageKey: `sb-${base.hostname.split(".")[0]}-auth-token`,
    headers: { Authorization: `Bearer ${anonKey}`, apikey: anonKey },
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    flowType: "implicit",
  };
}

/** Null when the Supabase URL or anon key is missing: sign-in is then not configured. */
export function createSupabaseAuth(): AuthClient | null {
  const url = import.meta.env.VITE_SUPABASE_URL;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    // For whoever deploys; the person on /welcome only reads that sign-in is unavailable.
    console.error("Sign-in is not configured: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are needed.");
    return null;
  }

  const auth = new SupabaseAuthClient(authClientOptions(url, anonKey));
  const redirectTo = `${window.location.origin}/`;

  return {
    async getSession() {
      const { data } = await auth.getSession();
      return toSession(data.session);
    },
    onChange(listener) {
      const { data } = auth.onAuthStateChange((_event, session) => {
        listener(toSession(session));
      });
      return () => data.subscription.unsubscribe();
    },
    async signInWithOAuth(provider) {
      const { error } = await auth.signInWithOAuth({
        provider,
        options: { redirectTo },
      });
      check(error);
    },
    async signInWithEmail(email) {
      const { error } = await auth.signInWithOtp({
        email,
        options: { emailRedirectTo: redirectTo },
      });
      check(error);
    },
    async signOut() {
      const { error } = await auth.signOut();
      check(error);
    },
  };
}
