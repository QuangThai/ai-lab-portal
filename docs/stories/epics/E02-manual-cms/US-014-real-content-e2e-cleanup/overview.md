# Overview

## Current Behavior

Authenticated publish E2E uses synthetic editor content and leaves published test posts/admin users in Postgres.

## Target Behavior

Use `test-post.md` as realistic CMS content for E2E publish/public rendering and clean up deterministic E2E data after the test run.

## Non-Goals

- No production cleanup endpoint.
- No weakening auth.
- No AI content generation.
