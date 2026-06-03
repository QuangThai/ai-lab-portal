# AI Blog Agent Product Contract

## Objective

AI Blog Agent helps the AI Lab produce high-quality, grounded B2B content about
internal AI products, engineering lessons, evaluation practices, AI agents, RAG,
automation, case studies, and market insights.

Target cadence: 1-2 strong posts per month.

## Workflow

```text
Internal project notes/docs/GitHub/meetings
  -> Knowledge Collector Agent
  -> Blog Strategist Agent
  -> Outline Generator Agent
  -> Draft Writer Agent
  -> Technical Reviewer Agent
  -> Marketing Editor Agent
  -> Human Approval
  -> Publish
```

## Status Lifecycle

Core states:

```text
Idea -> Outline -> Draft -> Technical Review -> Marketing Review -> Approved -> Published
```

Optional states:

```text
Rejected | Archived | Needs More Context | Needs Rewrite | Scheduled
```

## Content Rules

- Content must be practical, evidence-based, and business-aware.
- Drafts must avoid hype, unsupported quantified claims, and overpromising
  autonomy or accuracy.
- Blog generation may use only approved context.
- Confidential/restricted project information must not be published without
  explicit approval.
- Quantified claims require evidence or conservative wording.

## Agent Outputs

Important AI outputs must be structured, schema-validated, and stored with:

- provider and model name;
- prompt version id;
- input and output schema versions;
- input payload;
- raw output payload;
- parsed output payload;
- refusal/safety status when applicable;
- validation status;
- retry count;
- token usage, latency, estimated cost;
- created timestamp.

## MVP Acceptance

The Blog MVP is complete when:

- Admin can create a blog idea.
- AI can generate an outline from approved idea/context.
- AI can generate a markdown draft from an approved outline.
- AI technical review identifies unsupported or risky claims.
- AI can generate marketing metadata.
- Human can approve and publish a post.
- Public users can view blog list/detail pages.
- Blog posts support tags, excerpt, author, and publish date.
- Claim evidence handling blocks, rewrites, or explicitly approves unsupported
  claims before publishing.
- Every important AI blog call stores prompt version and AI run metadata.
