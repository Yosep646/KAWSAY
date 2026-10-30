import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./offline-e2e",
  workers: 1,
  timeout: 120000,
  outputDir: "test-results/offline",
  reporter: [["list"], ["json", { outputFile: "test-results/offline-results.json" }]],
  use: { baseURL: "http://127.0.0.1:15173", trace: "retain-on-failure" },
});
