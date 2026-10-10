import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, type RenderOptions } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { vi } from "vitest";

import { I18nProvider } from "../i18n";
import type { Api } from "../lib/api";
import { AuthProvider } from "../lib/auth";
import type { AuthClient, Session } from "../lib/supabase";
import type { Lang } from "../lib/types";

/**
 * A query client for tests: no retries and no caching between tests, so a
 * failing request fails immediately instead of being retried for seconds.
 */
/**
 * `staleTime` 0 by default, so a test sees every refetch. A test that counts requests the
 * way production makes them passes the app's own (lib/queryClient.ts, 60 s): with 0, every
 * component that mounts later refetches what is already there.
 */
export function createTestQueryClient({ staleTime = 0 }: { staleTime?: number } = {}): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity, staleTime },
      mutations: { retry: false },
    },
  });
}

export const TEST_SESSION: Session = {
  accessToken: "test-token",
  userId: "user-1",
  email: "tester@example.com",
};

/** A Supabase stand-in that is already signed in (or not, with `session: null`). */
export function fakeAuthClient(session: Session | null = TEST_SESSION): AuthClient {
  return {
    getSession: vi.fn(async () => session),
    onChange: vi.fn(() => () => {}),
    signInWithOAuth: vi.fn(async () => {}),
    signInWithEmail: vi.fn(async () => {}),
    signOut: vi.fn(async () => {}),
  };
}

/** Renders the current path, so a test can assert where a screen navigated to. */
function Location() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
}

interface Options extends Omit<RenderOptions, "wrapper"> {
  /** The URL to start at. */
  route?: string;
  /** The route pattern `ui` is mounted on, e.g. "/movie/:id". */
  path?: string;
  lang?: Lang;
  auth?: AuthClient | null;
  queryClient?: QueryClient;
}

export function renderWithProviders(
  ui: ReactElement,
  { route = "/", path = "/", lang = "en", auth, queryClient, ...options }: Options = {},
) {
  const client = queryClient ?? createTestQueryClient();
  const authClient = auth === undefined ? fakeAuthClient() : auth;

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <I18nProvider lang={lang}>
        <QueryClientProvider client={client}>
          <AuthProvider client={authClient}>
            <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
          </AuthProvider>
        </QueryClientProvider>
      </I18nProvider>
    );
  }

  const tree = (
    <Routes>
      <Route path={path} element={ui} />
      <Route path="*" element={<Location />} />
    </Routes>
  );
  return { queryClient: client, ...render(tree, { wrapper: Wrapper, ...options }) };
}

/** The path the app navigated to, once it has left the screen under test. */
export async function navigatedTo(): Promise<string> {
  return (await screen.findByTestId("location")).textContent ?? "";
}

/** Every method of `api` as a vi.fn(), for `vi.mock("../lib/api", ...)`. */
export function mockedApi(actual: Api): Api {
  return Object.fromEntries(Object.keys(actual).map((key) => [key, vi.fn()])) as unknown as Api;
}

/** A promise that never settles: keeps a query in its loading state. */
export function pending<T>(): Promise<T> {
  return new Promise<T>(() => {});
}
