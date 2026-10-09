import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";

import { preconnectLinks } from "./src/lib/preconnect";

const appRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig(({ mode }) => {
  // .env files plus VITE_* from the environment (the Pages build), as import.meta.env sees them
  const env = loadEnv(mode, appRoot, "VITE_");
  return {
    plugins: [
      react(),
      {
        name: "preconnect-api-and-auth",
        transformIndexHtml: () => preconnectLinks([env.VITE_API_URL, env.VITE_SUPABASE_URL]),
      },
    ],
    server: { port: 5173 },
  };
});
