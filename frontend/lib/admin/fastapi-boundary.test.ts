import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER, createAdminBoundaryHeaders } from "./fastapi-boundary";

process.env.ADMIN_BOUNDARY_SECRET = "test-admin-boundary-secret-at-least-32-chars";

describe("createAdminBoundaryHeaders", () => {
  it("creates a signed admin identity envelope for FastAPI", () => {
    const headers = createAdminBoundaryHeaders(
      {
        user: {
          id: "user_123",
          email: "admin@example.com",
        },
      },
      1_700_000_000,
    );

    assert.equal(headers[ADMIN_SIGNATURE_HEADER].length, 64);
    assert.deepEqual(JSON.parse(headers[ADMIN_IDENTITY_HEADER]), {
      email: "admin@example.com",
      issued_at: 1_700_000_000,
      role: "admin",
      user_id: "user_123",
    });
  });
});
