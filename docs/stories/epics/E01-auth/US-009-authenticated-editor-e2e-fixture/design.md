# Design

## Fixture Strategy

Use the real Better Auth login/session path in test mode whenever possible. Avoid production-visible bypasses.

Preferred shape:

1. Seed a deterministic test admin account in the Better Auth database used by Playwright.
2. Login through `/admin/login` using the real form/API route.
3. Exercise authenticated editor behavior through normal browser navigation.

Fallback shape if Better Auth seeding is too expensive for this slice:

- Add a test-only Playwright setup helper that creates a session through documented Better Auth test utilities or route behavior.
- The helper must be gated by `NODE_ENV === "test"` or an explicit E2E-only environment variable.

## Security Rules

- Do not expose `ADMIN_BOUNDARY_SECRET` to browser code.
- Do not add a production auth bypass.
- Do not trust browser-provided roles.
- Keep FastAPI admin identity signing in Next.js server code.

## E2E Flow

1. Start test stack/server with deterministic auth env.
2. Login as test admin.
3. Navigate to `/admin/blog/editor`.
4. Assert editor fields, toolbar, and workflow actions render.
5. Submit save/publish if backend availability and fixture persistence make the flow deterministic.

## Stop Conditions

Pause if Better Auth fixture setup requires undocumented schema assumptions or production-visible bypass behavior.
