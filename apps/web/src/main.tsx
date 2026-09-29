import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { I18nProvider } from "./i18n";
import { AuthProvider } from "./lib/auth";
import { queryClient } from "./lib/queryClient";
import { createSupabaseAuth, type AuthClient } from "./lib/supabase";
import "./styles/tokens.css";
import "./styles/app.css";

async function authClient(): Promise<AuthClient | null> {
  // Dev-only in-memory API and session; see src/dev/mock.ts. Never in a production build.
  if (import.meta.env.DEV && import.meta.env.VITE_MOCK_API === "1") {
    const mock = await import("./dev/mock");
    return mock.install();
  }
  return createSupabaseAuth();
}

const container = document.getElementById("root");
if (!container) throw new Error("#root not found");

void authClient().then((client) => {
  createRoot(container).render(
    <StrictMode>
      <I18nProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider client={client}>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </AuthProvider>
        </QueryClientProvider>
      </I18nProvider>
    </StrictMode>,
  );
});
