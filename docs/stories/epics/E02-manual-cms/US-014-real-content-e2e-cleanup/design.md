# Design

## Real Content

Use `test-post.md` as realistic blog/editor content. The E2E title is `Pi and Codex Agent Workflow Tips` with an `e2e-agent-tips-*` slug.

## Cleanup

Use Playwright-side Postgres cleanup through the test database connection:

- delete `blog_posts` with E2E slug prefix;
- delete related `audit_events`;
- delete E2E Better Auth users/sessions/accounts by email prefix.

No production cleanup route is added.
