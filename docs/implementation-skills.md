# AI Lab Portal Implementation Skills Playbook

This playbook maps available agent skills to the AI Lab Portal roadmap. Use it
before planning or implementing product work so future agents load the right
specialized guidance instead of relying on generic coding patterns.

## Always-On Baseline

For any non-trivial code change:

- `karpathy-guidelines` — keep scope narrow, state assumptions, define proof.
- `srcwalk` — inspect code structure before grep/raw reads.
- `git-workflow-and-versioning` — check changed files and keep changes atomic.
- `incremental-implementation` — land vertical slices, not broad rewrites.
- `test-driven-development` — write or update proof before behavior changes.
- `documentation-and-adrs` — update product docs, story evidence, and decisions
  when contracts or architecture change.

Harness requirements still apply: run feature intake, check the matrix, update
stories/decisions, run available validation, and record a trace.

## Roadmap Skill Map

| Phase | Work | Must Load | Also Consider | Proof Shape |
| --- | --- | --- | --- | --- |
| MVP 0 Foundation | Runtime shell, env, compose, validation | `incremental-implementation`, `test-driven-development`, `ci-cd-and-automation` | `debugging-and-error-recovery` | `python scripts/validate_foundation.py`, story verify |
| Auth Scaffold | Better Auth in Next.js, session cookies, protected admin shell | `security-and-hardening`, `api-and-interface-design`, `source-driven-development`, `test-driven-development` | `browser-testing-with-devtools` or `agent-browser`, `documentation-and-adrs` | Auth route tests, cookie/security config checks, browser smoke |
| Auth-to-FastAPI Boundary | Server-side identity bridge, backend identity parsing, 401/403 semantics | `api-and-interface-design`, `security-and-hardening`, `test-driven-development` | `deprecation-and-migration` if auth shape changes | Contract tests for 401/403, parsed identity tests |
| Admin UI Shell | Authenticated admin layout, navigation, empty states | `impeccable`, `frontend-ui-engineering`, `vercel-react-best-practices` | `vercel-composition-patterns`, `design-taste-frontend` | Playwright/admin route E2E, accessibility checks |
| Manual CMS API | Projects/showcases/blog CRUD, publish/unpublish | `api-and-interface-design`, `security-and-hardening`, `test-driven-development` | `supabase-postgres-best-practices`, `documentation-and-adrs` | Unit + integration API tests, audit proof |
| PostgreSQL Schema | Tables, indexes, migrations, constraints | `supabase-postgres-best-practices`, `api-and-interface-design`, `test-driven-development` | `deprecation-and-migration` for data changes | Alembic migration tests, query/index review |
| Public SEO Pages | `/lab`, `/showcases`, `/blog`, metadata, caching | `frontend-design`, `impeccable`, `frontend-ui-engineering`, `seo-audit`, `performance-optimization` | `ui-ux-pro-max`, `design-taste-frontend`, `browser-testing-with-devtools`, `web-design-guidelines` | Build, Playwright, SEO/a11y checks, cache behavior proof |
| AI Blog Agent | Prompt registry, structured outputs, review workflow | `api-and-interface-design`, `security-and-hardening`, `test-driven-development`, `openai-knowledge` | `source-driven-development`, `documentation-and-adrs` | Schema validation tests, fake provider tests, audit traces |
| AI News Pipeline | Sources, crawling, raw payloads, dedupe, scoring | `security-and-hardening`, `api-and-interface-design`, `supabase-postgres-best-practices` | `debugging-and-error-recovery`, `performance-optimization` | SSRF/url validation tests, worker tests, dedupe tests |
| User-Submitted Links | Public form, rate limits, SSRF-protected async fetch | `security-and-hardening`, `api-and-interface-design`, `test-driven-development` | `browser-testing-with-devtools`, `seo-audit` | Abuse-case tests, rate limit proof, E2E submit smoke |
| Provider Integrations | Firecrawl/Apify/OpenAI/social providers | `source-driven-development`, `security-and-hardening`, `api-and-interface-design` | `openai-docs`, `openai-knowledge`, `deprecation-and-migration` | Contract/fake-provider tests, error categorization tests |
| Release Readiness | Pre-launch validation, risk review, rollback | `shipping-and-launch`, `final-release-review`, `code-review-and-quality` | `performance-optimization`, `seo-audit` | Full validation report, release checklist, rollback notes |

## Skill Use Rules by Domain

### Authentication and Authorization

Load before editing auth code:

- `security-and-hardening`
- `api-and-interface-design`
- `test-driven-development`
- `source-driven-development` for Better Auth and Next.js docs

Required decisions/proof:

- Never store auth tokens in `localStorage`.
- Use HTTP-only, Secure-in-production, SameSite cookies.
- Treat authentication and authorization as separate layers.
- Backend admin mutations must not trust client-only state.
- Record ADRs for auth boundary or role model changes.

### API and Interface Contracts

Load before adding REST endpoints or frontend/backend contracts:

- `api-and-interface-design`
- `security-and-hardening` if user/admin input is involved
- `test-driven-development`

Required contract shape:

- Boundary validation with Pydantic or equivalent.
- Consistent error envelope and 401/403 semantics.
- Pagination for public list APIs.
- Long-running operations return job IDs.

### Database and Migrations

Load before creating or changing tables/indexes:

- `supabase-postgres-best-practices`
- `api-and-interface-design`
- `test-driven-development`
- `deprecation-and-migration` for destructive or compatibility-sensitive changes

Required proof:

- Alembic migration from empty database.
- Tests for constraints and representative queries.
- Index rationale for public lists, admin queues, dedupe, and job lookup.

### Frontend Product UI

Load before changing UI beyond tiny copy/token edits:

- `frontend-design` for distinctive, polished landing pages, public pages,
  marketing surfaces, and any UI that must look memorable rather than generic.
- `impeccable` for product UI quality, UX hardening, admin/dashboard polish,
  interaction states, accessibility, reusable tokens, and design-system rigor.
- `frontend-ui-engineering` for implementation quality.
- `design-taste-frontend` for anti-slop landing pages, portfolios, and redesigns.
- `ui-ux-pro-max` when available for deeper landing-page/UI-UX polish.
- `vercel-react-best-practices` for React/Next.js performance.
- `vercel-composition-patterns` when component APIs start to sprawl.

Project design source:

- `docs/product/style-guide.md`
- `frontend/app/theme.css`
- `styles/` source references

Required proof:

- `npm run typecheck`, `npm run lint`, `npm run build`.
- Playwright or browser smoke for user-visible changes.

### Public Landing Pages, SEO, and Performance

Load before public page implementation:

- `frontend-design` to set the visual concept, typography, palette, composition,
  and motion direction.
- `impeccable` to harden the UX, accessibility, responsive behavior, UI copy,
  and component craft.
- `design-taste-frontend` for landing-page anti-slop review and bolder visual
  direction.
- `ui-ux-pro-max` for extra UI/UX critique and polish.
- `seo-audit`
- `performance-optimization`
- `frontend-ui-engineering`
- `browser-testing-with-devtools` or `agent-browser`

Required proof:

- Metadata and canonical strategy.
- Published-only visibility checks.
- Fast render/build proof and browser smoke.

### AI and External Provider Workflows

Load before provider, crawler, or model work:

- `security-and-hardening`
- `source-driven-development`
- `api-and-interface-design`
- `test-driven-development`
- `openai-knowledge` / `openai-docs` for OpenAI-specific work

Required proof:

- Treat provider payloads and AI outputs as untrusted.
- Validate structured outputs before application logic.
- Fake provider tests for retries/error categories.
- Raw payload retention and audit/debug records.

## Recommended Next Implementation Slice

Next slice should be **Better Auth scaffold** only:

- Install and configure Better Auth in `frontend/`.
- Add `/api/auth/[...all]` route handler.
- Add auth environment validation placeholders.
- Add protected admin shell behavior or explicit unauthenticated placeholder,
  depending on selected story scope.
- Do not add admin CRUD, role model, or FastAPI admin mutations yet.

Skills to load for that slice:

1. `security-and-hardening`
2. `api-and-interface-design`
3. `source-driven-development`
4. `test-driven-development`
5. `frontend-ui-engineering` if UI changes are included

Expected proof:

- Frontend typecheck/lint/build.
- Auth route/config tests where practical.
- Browser smoke for admin unauthenticated/authenticated behavior.
- Updated story packet and trace.
