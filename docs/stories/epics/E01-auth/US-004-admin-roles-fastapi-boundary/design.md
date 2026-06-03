# Design

## Domain Model

Minimum concepts:

- `AdminIdentity`: a parsed, server-provided identity accepted by FastAPI at the HTTP boundary.
- `AdminRole`: the smallest role vocabulary needed before privileged admin mutations. Initial candidate: `admin`.

Authentication is still owned by Better Auth in Next.js. FastAPI must not trust browser-local tokens or client-provided role strings without a server-side trust boundary.

## Application Flow

1. Browser authenticates with Better Auth through Next.js.
2. Next.js server-side code checks the Better Auth session.
3. For future admin API calls, Next.js sends a server-created identity envelope to FastAPI through an explicit trusted boundary.
4. FastAPI parses and validates the envelope at the HTTP boundary.
5. Application handlers receive a typed `AdminIdentity`, not raw headers or untrusted strings.

## Interface Contract

FastAPI boundary for this story:

- `GET /admin/probe` requires a validated admin identity.
- Next.js server code creates a compact JSON identity envelope and signs it with HMAC-SHA256.
- FastAPI accepts only the signed identity headers:
  - `x-ai-lab-admin-identity`
  - `x-ai-lab-admin-signature`
- The identity envelope contains `user_id`, `email`, `role`, and `issued_at`.
- FastAPI accepts only `role: "admin"` for this MVP boundary.
- FastAPI rejects missing, malformed, tampered, non-admin, or expired identity envelopes.

## Data Model

No durable product tables are required unless discovery proves a local role fixture is necessary. Long-term Better Auth persistence and role storage remain follow-up work if not needed for the boundary smoke slice.

## UI / Platform Impact

No new public UI. The admin shell may gain a boundary smoke/status indicator only if useful for verification.

## Observability

Do not log secrets, cookies, raw tokens, or full identity envelopes. Boundary failures may log non-sensitive operational context only.

Audit logs remain out of scope until privileged mutations exist.

## Alternatives Considered

1. Let FastAPI read Better Auth browser cookies directly.
   - Not preferred because the accepted decision says FastAPI receives identity through an explicit server-side boundary.
2. Send client-stored JWTs from the browser.
   - Rejected because browser-local tokens are not acceptable for the admin surface.
3. Implement a complete role/permission system now.
   - Rejected as too broad before CMS/publishing workflows exist.
