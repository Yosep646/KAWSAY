/// <reference types="vitest" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { offlineShell } from "./scripts/offline-shell.mjs";

export default defineConfig({
  plugins: [react(), offlineShell()],
  server: { port: 5173, proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true } } },
  test: { include: ["src/**/*.test.{ts,tsx}"], environment: "jsdom", globals: true, setupFiles: ["./src/test/setup.ts"] },
});
