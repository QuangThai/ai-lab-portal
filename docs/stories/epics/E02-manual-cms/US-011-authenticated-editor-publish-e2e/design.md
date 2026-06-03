# Design

## Flow

1. Playwright signs up/signs in through Better Auth.
2. Browser opens `/admin/blog/editor`.
3. Browser submits editor form.
4. Next.js server action validates Better Auth session and signs FastAPI admin headers server-side.
5. FastAPI admin API creates/publishes the post and records audit.
6. Editor shows a visible success state for E2E assertion.

## Security Rules

- Browser never receives `ADMIN_BOUNDARY_SECRET`.
- No auth bypass.
- FastAPI remains the mutation/audit source.
