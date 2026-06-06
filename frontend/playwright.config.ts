import { defineConfig, devices } from "@playwright/test";

const e2ePort = process.env.E2E_PORT ?? "13100";
const e2eBaseUrl = `http://127.0.0.1:${e2ePort}`;
const e2eAdminBoundarySecret = "e2e-test-admin-boundary-secret-at-least-32-chars";
const e2eDatabaseUrl =
  "postgresql+psycopg://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal";
const e2eRedisUrl = "redis://127.0.0.1:6379/0";

const backendEnvPrefix = [
  `set AI_LAB_ADMIN_BOUNDARY_SECRET=${e2eAdminBoundarySecret}`,
  `set AI_LAB_DATABASE_URL=${e2eDatabaseUrl}`,
  `set AI_LAB_REDIS_URL=${e2eRedisUrl}`,
  "set AI_LAB_LLM_E2E_FAKE=true",
  "set AI_LAB_ENVIRONMENT=development",
].join("&& ");

// Force isolated e2e env so local .env (cloudflare URLs, custom secrets) cannot break tests.
process.env.BETTER_AUTH_SECRET = "test-better-auth-secret-at-least-32-chars";
process.env.BETTER_AUTH_URL = e2eBaseUrl;
process.env.BETTER_AUTH_TRUSTED_ORIGINS = e2eBaseUrl;
process.env.ADMIN_BOUNDARY_SECRET = e2eAdminBoundarySecret;
process.env.DATABASE_URL = "postgresql://ai_lab:ai_lab_dev_password@127.0.0.1:15432/ai_lab_portal";
process.env.AUTH_DATABASE_URL = process.env.DATABASE_URL;

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: e2eBaseUrl,
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: `${backendEnvPrefix}&& cd .. && python -m alembic -c backend/alembic.ini upgrade head && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 18000`,
      url: "http://127.0.0.1:18000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: `set ADMIN_BOUNDARY_SECRET=${e2eAdminBoundarySecret}&& set BETTER_AUTH_SECRET=test-better-auth-secret-at-least-32-chars&& set BETTER_AUTH_URL=${e2eBaseUrl}&& set BETTER_AUTH_TRUSTED_ORIGINS=${e2eBaseUrl}&& npm run dev -- --hostname 127.0.0.1 --port ${e2ePort}`,
      url: e2eBaseUrl,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
