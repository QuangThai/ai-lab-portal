# Exec Plan

1. Add Playwright helpers to read `test-post.md` and clean E2E DB rows.
2. Update authenticated editor E2E to publish real content and assert public visibility.
3. Run full verification.

Risk: high-risk due to test DB cleanup, auth users, and public content visibility.
