# US-088 Pipeline Stepper UX

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — semi-auto pipeline operator UX (2026-06-06).

## Product Contract

Admin operators see where they are in the blog-ideas pipeline, what to do next,
and can jump to the relevant section without hunting for buttons.

## Acceptance Criteria

1. Detail page shows a **Next action** banner under the pipeline stepper.
2. Banner reflects approve, generate, processing, claims, publish, done, or blocked states.
3. **Go to step** anchor scrolls to the matching pipeline section.
4. Stepper highlights the focused stage when it matches the next action.
5. Marketing gate depends on **technical review approved** (not draft alone).
6. Claims section unlocks after marketing approved; manual extract only when ledger empty.
7. List page removes redundant Outline/Draft quick actions (orchestrator handles flow).
8. Unit tests for next-action resolver.
9. Frontend typecheck and build pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `pipeline-next-action.test.ts` |
| Integration | N/A (UI only) |
| E2E | Covered by US-086 |
| Platform | N/A |
| Release | Frontend quality gate |

## Evidence

- `frontend/app/admin/blog-ideas/lib/pipeline-next-action.ts`
- `frontend/app/admin/blog-ideas/pipeline-next-action-banner.tsx`
- Commit pending
