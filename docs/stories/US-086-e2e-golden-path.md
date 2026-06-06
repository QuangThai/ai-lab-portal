# US-086 E2E Golden Path Generate to Publish

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — end-to-end proof for the paid blog agent workflow (2026-06-06).

## Product Contract

An admin operator can generate a blog idea from a published project, walk the
semi-auto pipeline (approve gates + orchestrated stages), publish to the CMS,
and read the post on the public blog — without calling OpenAI in CI/E2E.

## Acceptance Criteria

1. E2E seeds a published project and generates an idea from `/admin/blog-ideas/new`.
2. Semi-auto approve chain runs: outline → draft → technical review → marketing → claims.
3. Admin publishes to blog when claim gate is clear.
4. Public `/blog/{slug}` renders the published title and draft body.
5. Playwright uses deterministic fake LLM (`AI_LAB_LLM_E2E_FAKE=true`) and Celery worker.
6. Test cleans up DB rows (idea, claims, jobs, post, project, admin user).

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `marketing_metadata_for_storage` via tasks |
| Integration | Celery + fake LLM in E2E webServer |
| E2E | `frontend/tests/e2e/blog-agent-golden-path.spec.ts` |
| Platform | `scripts/e2e-preflight.sh` before Playwright |
| Release | `CI=1 npm run test:e2e -- blog-agent-golden-path` |

## Evidence

- `backend/app/llm/e2e_fake_responses.py`
- `frontend/tests/e2e/blog-agent-golden-path.spec.ts`
- `frontend/playwright.config.ts` — worker + fake LLM env
