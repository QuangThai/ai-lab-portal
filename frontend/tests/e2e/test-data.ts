/**
 * Shared test data constants for E2E tests.
 *
 * Centralizes magic strings that appear across multiple test files.
 * Update this file when seed data or fake LLM responses change — tests
 * that import from here will automatically stay in sync.
 */

import { uniqueId } from "./helpers";

// ── Seed data names (from backend/app/admin_seed.py) ──────────
// These must match the seeded showcase/project/blog post titles.
// When admin_seed.py content changes, update these constants.

export const SEED_SHOWCASE_NAME = "Scopelytics";

// ── Fake LLM responses (from backend/app/llm/e2e_fake_responses.py) ──
// These texts are emitted by the fake LLM service when AI_LAB_LLM_E2E_FAKE=true.
// Tests assert on these values to verify pipeline stage outputs.

/** Text rendered in the Draft step after outline approval. */
export const FAKE_DRAFT_SNIPPET = "Semi-auto keeps humans in the loop";

/** Text rendered in the Technical Review step after draft approval. */
export const FAKE_REVIEW_SNIPPET = "Risk: low";

/** Text rendered in the Marketing Metadata step after review approval. */
export const FAKE_MARKETING_SNIPPET = "SEO Title";

/** Seeded project description text used in golden path setup. */
export const E2E_PROJECT_DESCRIPTION = "Analytics platform for game studios";

/** Seeded project content used in golden path setup. */
export const E2E_PROJECT_CONTENT =
  "## Architecture\nUses embeddings and batch scoring pipelines.";

// ── Test-specific constants ───────────────────────────────────

export const E2E_IDEA_TITLE = "E2E Golden Path Blog Idea";
export const E2E_PUBLIC_SLUG = "e2e-golden-path-blog-idea";

/** Generate a unique project slug for E2E tests. */
export function e2eProjectSlug(workerIndex: number): string {
  return `e2e-project-${uniqueId("golden", workerIndex)}`;
}
