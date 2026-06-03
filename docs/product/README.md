# Product Docs

This directory contains the living AI Lab Portal product contract derived from
`SPEC.md`. Keep `SPEC.md` as input material; use these smaller docs, story
packets, decisions, and validation records as the operational source of truth.

Current product docs:

- `overview.md` — product purpose, surfaces, MVP modules, and locked rules.
- `architecture.md` — accepted stack, layering, boundary, and deferred choices.
- `blog-agent.md` — AI Blog Agent workflow, content rules, and MVP acceptance.
- `news-intelligence.md` — AI News ingestion, scoring, deduplication, and safety
  contract.
- `mvp-roadmap.md` — vertical MVP sequence and foundation scope.
- `style-guide.md` — editorial visual language, tokens, and implementation rules.

## Update Rule

When behavior changes:

1. Update the affected product doc.
2. Update or create the story packet.
3. Update durable proof status with `scripts/bin/harness-cli story add` or
   `scripts/bin/harness-cli story update`.
4. Record a decision if the change affects architecture, scope, risk, or a
   previously settled product rule.
