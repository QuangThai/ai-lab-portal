# US-089 Run Next Stage Orchestrator

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — semi-auto pipeline (2026-06-06).

## Product Contract

After each admin approval gate, the server action approves the gate and
automatically triggers the next pipeline stage so operators do not manually click
separate generate buttons.

## Acceptance Criteria

1. Approve idea → PATCH approved + POST generate-outline (202 polling when async).
2. Approve outline → PATCH + POST generate-draft.
3. Approve draft → PATCH + POST review-technical.
4. Accept review → PATCH + POST generate-marketing.
5. Approve marketing → PATCH + POST extract-claims (sync).
6. All approve actions redirect to `/admin/blog-ideas/{id}` with operational query params.
7. Approve button labels reflect chained behavior (e.g. "Approve & generate draft").
8. Detail page wires `approveIdea` to `approveIdeaAction` (not outline action).
9. Pending ideas on detail page expose approve/reject controls.
10. Unit test for pipeline gate → next stage mapping.
11. Frontend typecheck, lint, and build pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `pipeline-next-stage.test.ts` |
| Integration | Existing blog-ideas generation endpoints |
| E2E | Covered by US-086 |
| Platform | N/A |
| Release | Frontend quality gate |

## Evidence

- `frontend/app/admin/blog-ideas/lib/pipeline-next-stage.ts`
- `frontend/app/admin/blog-ideas/actions.ts` — `approveAndRunNext`
- Commit pending
