import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { setAccessToken } from "./api";
import type { AuthClient, OAuthProvider, Session } from "./supabase";

export type AuthStatus = "loading" | "signedOut" | "signedIn" | "unconfigured";

interface Auth {
  status: AuthStatus;
  session: Session | null;
  signInWithOAuth: (provider: OAuthProvider) => Promise<void>;
  signInWithEmail: (email: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<Auth | null>(null);

const unconfigured = async () => {
  throw new Error("Sign-in is not configured");
};

/**
 * Holds the Supabase session and pushes its access token into the API client on every
 * change: sign-in, sign-out and each automatic refresh.
 */
export function AuthProvider({
  client,
  children,
}: {
  client: AuthClient | null;
  children: ReactNode;
}) {
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<AuthStatus>(client ? "loading" : "unconfigured");

  useEffect(() => {
    if (!client) return;
    let active = true;
    const apply = (next: Session | null) => {
      if (!active) return;
      setAccessToken(next?.accessToken ?? null);
      setSession(next);
      setStatus(next ? "signedIn" : "signedOut");
    };
    const unsubscribe = client.onChange(apply);
    client.getSession().then(apply, () => apply(null));
    return () => {
      active = false;
      unsubscribe();
    };
  }, [client]);

  const value = useMemo<Auth>(
    () => ({
      status,
      session,
      signInWithOAuth: client ? (p) => client.signInWithOAuth(p) : unconfigured,
      signInWithEmail: client ? (e) => client.signInWithEmail(e) : unconfigured,
      signOut: client ? () => client.signOut() : unconfigured,
    }),
    [client, session, status],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): Auth {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth needs <AuthProvider>");
  return value;
}
