import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { getAuthEnvironment } from "./env";

function withEnv(overrides: Record<string, string>, callback: () => void) {
  const previous = { ...process.env };
  process.env = { ...previous, ...overrides };

  try {
    callback();
  } finally {
    process.env = previous;
  }
}

describe("getAuthEnvironment", () => {
  it("uses safe local defaults for scaffold validation", () => {
    withEnv(
      {
        BETTER_AUTH_SECRET: "",
        BETTER_AUTH_URL: "",
        DATABASE_URL: "",
        AUTH_DATABASE_URL: "",
        BETTER_AUTH_TRUSTED_ORIGINS: "",
        BETTER_AUTH_API_KEY: "",
        ADMIN_BOUNDARY_SECRET: "",
      },
      () => {
        const env = getAuthEnvironment();

        assert.equal(env.betterAuthSecret, "development-better-auth-secret-at-least-32-chars");
        assert.equal(env.betterAuthUrl, "http://127.0.0.1:13000");
        assert.equal(env.databaseUrl, "postgresql://ai_lab:ai_lab_dev_password@127.0.0.1:15432/ai_lab_portal");
        assert.deepEqual(env.trustedOrigins, ["http://127.0.0.1:13000"]);
        assert.equal(env.betterAuthApiKey, undefined);
        assert.equal(env.adminBoundarySecret, "development-admin-boundary-secret-at-least-32-chars");
      },
    );
  });

  it("parses explicit trusted origins and dashboard API key", () => {
    withEnv(
      {
        BETTER_AUTH_URL: "http://localhost:3000",
        BETTER_AUTH_TRUSTED_ORIGINS: "http://localhost:3000, http://127.0.0.1:13000",
        BETTER_AUTH_API_KEY: "dash_test_key",
        ADMIN_BOUNDARY_SECRET: "admin-boundary-secret-at-least-32-chars",
      },
      () => {
        const env = getAuthEnvironment();

        assert.deepEqual(env.trustedOrigins, ["http://localhost:3000", "http://127.0.0.1:13000"]);
        assert.equal(env.betterAuthApiKey, "dash_test_key");
        assert.equal(env.adminBoundarySecret, "admin-boundary-secret-at-least-32-chars");
      },
    );
  });
});
