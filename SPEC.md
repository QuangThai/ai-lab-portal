# SPEC.md

# AI Lab Portal Specification

## 1. Overview

### 1.1 Project Name

**AI Lab Portal**

### 1.2 Purpose

The company is repositioning itself from a traditional **IT Outsource / Offshore Development** provider into an **AI/LLM Lab**. To support this positioning, the company needs a public-facing and internal platform that demonstrates real AI capabilities, showcases AI products, and continuously publishes high-quality AI-related content.

The AI Lab Portal has two primary goals:

1. **Build credibility with potential clients** by showing what the company has built with AI, how the team thinks about AI product development, and how it evaluates and improves AI systems.
2. **Create a repeatable content and intelligence engine** that helps sales, marketing, and leadership stay aligned with the AI market and turn internal work into public case studies.

The platform consists of two main modules:

1. **AI Blog Agent**
2. **AI News Intelligence Feed**

These two modules should work together. The AI News Intelligence Feed discovers and filters important AI trends, while the AI Blog Agent converts internal experience, product work, and market trends into high-quality blog posts.

---

## 2. Business Context

### 2.1 Current Positioning

The company has historically been perceived as an IT outsource or offshore development team. This positioning is useful for software delivery, but it does not fully communicate the company's ability to build AI-native products, AI workflows, LLM-powered systems, and intelligent automation.

### 2.2 Desired Positioning

The desired positioning is:

> We are an AI/LLM Lab helping businesses design, build, evaluate, and deploy practical AI products.

The company should be seen as a team that can:

- Build AI-powered products.
- Design LLM workflows.
- Create AI agents.
- Build RAG systems.
- Build AI evaluation frameworks.
- Automate research and business workflows.
- Integrate AI into existing products and operations.
- Evaluate AI output quality, reliability, and risk.
- Build real business-facing AI systems, not only demos.

### 2.3 Why This Portal Matters

The portal is not only a marketing website. It is also a practical showcase of the company's AI capabilities.

By building the portal, the company demonstrates experience in:

- AI agent workflows.
- Web crawling.
- AI-based filtering and scoring.
- Content generation.
- Deduplication using embeddings.
- Human-in-the-loop approval.
- CMS workflows.
- Scheduled background jobs.
- LLM evaluation.
- AI-assisted sales and marketing operations.

---

## 3. Product Vision

### 3.1 Vision Statement

The AI Lab Portal is a public and internal platform that turns the company's AI work, internal projects, and AI market research into high-quality public content, curated AI intelligence, and sales-ready proof of capability.

### 3.2 Product Principles

1. **Practical over hype**
   - Content should focus on real systems, real lessons, and real business value.
   - Avoid vague statements like “AI will change everything.”

2. **Evidence-based claims**
   - Blog posts should avoid unsupported performance claims.
   - If numbers are used, the source or measurement method should be clear.

3. **Human-in-the-loop by default**
   - AI may generate drafts and filter news, but humans should approve important public content.

4. **Quality over quantity**
   - The blog should publish 1–2 strong posts per month rather than many low-quality posts.
   - The AI news feed should show curated, filtered, relevant updates rather than raw noise.

5. **Reusable showcase**
   - The system itself should be presentable as a company showcase.
   - The company should be able to explain the architecture, workflows, filters, evaluation methods, and business value behind the system.

---

## 4. Scope

### 4.1 In Scope

The platform includes:

- Public AI Lab landing page.
- Public showcases page.
- Public blog listing page.
- Blog detail page.
- AI Blog Agent workflow.
- Blog idea, outline, draft, review, and publish workflow.
- AI News Intelligence Feed.
- Crawling from selected AI-related sources.
- AI-based filtering, scoring, summarization, and deduplication.
- User-submitted link flow.
- Internal admin dashboard for review and approval.
- Source management.
- Topic/tag management.
- Basic analytics for content and news items.

### 4.2 Out of Scope for MVP

The following are not required for the initial MVP:

- Fully autonomous blog publishing without human review.
- Large-scale crawling of the entire web.
- Complex personalization for every visitor.
- Paid newsletter functionality.
- Advanced CRM integration.
- Multi-language publishing, unless explicitly prioritized.
- Real-time social media engagement tracking at large scale.
- Fine-tuned custom LLM models.
- Full enterprise user management.

### 4.3 Implementation-Ready MVP Definition

This specification is implementation-ready only when a story can be built against explicit contracts for data, APIs, security, provider behavior, and validation. The MVP must therefore be implemented in vertical slices rather than by building every module in this document at once.

Locked MVP assumptions:

- The product is a web application with public pages and an internal admin dashboard.
- Public content must be fast, SEO-friendly, and safe to cache.
- Admin operations must require authentication and role-based authorization.
- All public publishing actions require human approval in MVP.
- All external provider payloads are untrusted and must be parsed before use.
- All AI-generated structured outputs must be schema-validated before application logic consumes them.
- All crawler and AI jobs must be asynchronous and retryable.
- Raw external input must be retained before normalization so the system can be debugged and audited.
- Auto-reject is allowed in MVP only for clearly low-quality or duplicate items; auto-approve must remain disabled until evaluation data proves acceptable quality.

Implementation sequence:

1. Foundation and manual editorial CMS.
2. Public AI Lab, showcase, and blog pages.
3. AI-assisted blog workflow.
4. RSS / official-source AI News ingestion.
5. Firecrawl article extraction and AI scoring.
6. X/Twitter ingestion after provider strategy is confirmed.

The first implementation slice should not start with X/Twitter crawling because that path has higher uncertainty around rate limits, source quality, cost, and provider terms.

---

## 5. Main Modules

## 5.1 Module 1: AI Blog Agent

### 5.1.1 Objective

The AI Blog Agent helps the company consistently produce high-quality blog posts about:

- Internal AI products.
- AI product development lessons.
- LLM workflow design.
- AI evaluation.
- AI agents.
- RAG systems.
- AI automation.
- Case studies.
- Technical lessons learned.
- Market insights related to company capabilities.

The target publishing frequency is **1–2 blog posts per month**.

### 5.1.2 Blog Agent Goals

The Blog Agent should:

- Convert internal project information into blog ideas.
- Generate structured outlines.
- Produce first drafts.
- Review drafts for technical accuracy and claim risk.
- Improve drafts for marketing readability.
- Create metadata such as title, excerpt, SEO title, and social media snippets.
- Support human review before publishing.

### 5.1.3 Blog Content Categories

The blog should support the following categories:

1. **AI Product Case Study**
   - Example: Building Scopelytics as an AI-powered business analysis product.

2. **AI Evaluation**
   - Example: Applying an AI evaluation framework to improve Scopelytics output quality.

3. **AI Engineering Notes**
   - Example: Designing structured output validation for LLM pipelines.

4. **AI Agent Workflow**
   - Example: Building an AI research and content generation agent.

5. **AI Lab Positioning**
   - Example: From offshore development to AI/LLM Lab.

6. **AI Market Insight**
   - Example: What recent AI agent trends mean for business workflow automation.

7. **Showcase Deep Dive**
   - Example: Voice-first AI interview system with STT, TTS, scoring, and review workflow.

---

## 6. AI Blog Agent Workflow

### 6.1 End-to-End Workflow

```text
Internal project notes / docs / GitHub / meeting notes
        ↓
Knowledge Collector Agent
        ↓
Blog Strategist Agent
        ↓
Outline Generator Agent
        ↓
Draft Writer Agent
        ↓
Technical Reviewer Agent
        ↓
Marketing Editor Agent
        ↓
Human Approval
        ↓
Publish to Blog
```

### 6.2 Blog Status Lifecycle

Each blog post should move through the following states:

```text
Idea → Outline → Draft → Technical Review → Marketing Review → Approved → Published
```

Optional states:

```text
Rejected
Archived
Needs More Context
Needs Rewrite
Scheduled
```

### 6.3 Blog Workflow State Definitions

| Status | Description |
|---|---|
| Idea | A rough topic or article idea has been created. |
| Outline | A structured article outline has been generated or manually written. |
| Draft | A full draft exists. |
| Technical Review | The article is being reviewed for technical accuracy. |
| Marketing Review | The article is being edited for readability, positioning, and CTA. |
| Approved | The article is approved for publishing. |
| Scheduled | The article is scheduled for a future publish date. |
| Published | The article is publicly available. |
| Rejected | The article should not be published. |
| Archived | The article is no longer active but kept for reference. |
| Needs More Context | More internal information is required before continuing. |
| Needs Rewrite | The article needs substantial rewriting. |

---

## 7. Blog Agent Sub-Agents

## 7.1 Knowledge Collector Agent

### 7.1.1 Purpose

The Knowledge Collector Agent gathers and structures information from internal sources so that blog posts are grounded in real company work.

### 7.1.2 Inputs

Possible inputs:

- GitHub repositories.
- README files.
- Product requirement documents.
- Technical specifications.
- Meeting transcripts.
- Demo scripts.
- Screenshots.
- Internal notes.
- Product changelogs.
- Customer discovery notes.
- Evaluation results.
- Architecture diagrams.

### 7.1.3 Outputs

The output should be structured as JSON.

Example:

```json
{
  "project_name": "Scopelytics",
  "project_summary": "An AI-powered analysis system for turning business input into structured pre-sales insights.",
  "ai_capabilities": [
    "AI analysis generation",
    "Evaluation framework",
    "Structured output validation",
    "Human review workflow"
  ],
  "technical_highlights": [
    "LLM prompt pipeline",
    "Quality scoring",
    "Fallback handling",
    "Business-specific output schema"
  ],
  "business_value": [
    "Reduce manual analysis time",
    "Improve pre-sales requirement review",
    "Standardize output quality"
  ],
  "risks_or_limitations": [
    "Output quality still requires human review",
    "Evaluation criteria may need domain-specific tuning"
  ]
}
```

### 7.1.4 Functional Requirements

The system should allow an admin to:

- Add project context manually.
- Upload or paste notes.
- Link to internal documents or repositories.
- Ask the agent to extract key AI-related highlights.
- Review extracted facts before using them in a blog post.

---

## 7.2 Blog Strategist Agent

### 7.2.1 Purpose

The Blog Strategist Agent decides the angle, audience, and goal of a blog post.

### 7.2.2 Inputs

- Project summary.
- Extracted knowledge from Knowledge Collector Agent.
- Company positioning.
- Target audience.
- Related AI trends.
- Desired content type.

### 7.2.3 Output

Example:

```json
{
  "recommended_angle": "AI Evaluation",
  "target_reader": "CTO, product manager, or founder evaluating AI adoption",
  "article_goal": "Show that the company can design practical quality-control workflows for LLM products.",
  "suggested_titles": [
    "How We Applied AI Evaluation to Improve Scopelytics Output Quality",
    "Building a Practical Evaluation Workflow for an LLM-Powered Analysis Product",
    "What We Learned Evaluating AI-Generated Business Analysis"
  ],
  "positioning_notes": [
    "Avoid claiming the system is fully autonomous",
    "Emphasize human-in-the-loop review",
    "Explain evaluation as a practical engineering discipline"
  ]
}
```

---

## 7.3 Outline Generator Agent

### 7.3.1 Purpose

The Outline Generator Agent creates a structured article outline.

### 7.3.2 Default Blog Structure

```text
1. Context
2. Problem
3. Why a normal software approach was not enough
4. AI/LLM approach
5. Architecture or workflow
6. Evaluation and quality control
7. Lessons learned
8. Business value
9. What we are improving next
```

### 7.3.3 Output Example

```json
{
  "title": "How We Applied AI Evaluation to Improve Scopelytics Output Quality",
  "outline": [
    {
      "section": "Context",
      "points": [
        "Scopelytics helps structure pre-sales analysis from raw business input.",
        "The product relies on AI-generated analysis, so output quality matters."
      ]
    },
    {
      "section": "Problem",
      "points": [
        "LLM output can vary between runs.",
        "Business-facing output must be consistent and reviewable."
      ]
    }
  ]
}
```

---

## 7.4 Draft Writer Agent

### 7.4.1 Purpose

The Draft Writer Agent creates a complete first draft based on approved context and outline.

### 7.4.2 Writing Guidelines

The draft should:

- Be professional and B2B-oriented.
- Avoid excessive hype.
- Avoid unsupported numerical claims.
- Explain real engineering and product decisions.
- Highlight business value.
- Be readable by both technical and non-technical stakeholders.
- Avoid leaking confidential customer or internal information.

### 7.4.3 Tone

Preferred tone:

- Practical.
- Clear.
- Calm.
- Experienced.
- Technical but accessible.
- Business-aware.

Avoid:

- Overly promotional tone.
- Generic AI buzzwords.
- Unverified claims.
- Overpromising autonomy or accuracy.

---

## 7.5 Technical Reviewer Agent

### 7.5.1 Purpose

The Technical Reviewer Agent checks a draft for technical accuracy, unsupported claims, vague statements, and risk.

### 7.5.2 Review Dimensions

The reviewer should check:

- Technical correctness.
- Unsupported performance claims.
- Misleading descriptions of AI capabilities.
- Missing limitations.
- Security or confidentiality risks.
- Overly broad claims.
- Whether examples are grounded in real project information.

### 7.5.3 Output Example

```json
{
  "overall_risk": "medium",
  "issues": [
    {
      "severity": "high",
      "type": "unsupported_claim",
      "text": "The system reduces manual review time by 80%.",
      "reason": "No measurement data is provided.",
      "suggestion": "Change to: We observed a noticeable reduction in manual review effort during internal testing."
    },
    {
      "severity": "medium",
      "type": "missing_limitation",
      "text": "The AI automatically produces final business recommendations.",
      "reason": "The system still requires human review.",
      "suggestion": "Mention the human-in-the-loop review step."
    }
  ],
  "approval_recommendation": "needs_revision"
}
```

---

## 7.6 Marketing Editor Agent

### 7.6.1 Purpose

The Marketing Editor Agent improves the draft for readability, positioning, and distribution.

### 7.6.2 Responsibilities

The agent should generate:

- Final title suggestions.
- SEO title.
- Meta description.
- Blog excerpt.
- CTA.
- LinkedIn post.
- X/Twitter post.
- Newsletter snippet.

### 7.6.3 Output Example

```json
{
  "blog_title": "How We Applied AI Evaluation to Improve Scopelytics Output Quality",
  "seo_title": "AI Evaluation Framework for LLM Product Development",
  "meta_description": "A practical look at how our team designed an evaluation workflow to improve the reliability of AI-generated business analysis in Scopelytics.",
  "excerpt": "A practical look at how our team designed an evaluation workflow to improve the reliability of AI-generated business analysis in Scopelytics.",
  "linkedin_post": "We have been building Scopelytics as part of our AI Lab work...",
  "x_post": "We applied an AI evaluation workflow to improve Scopelytics output quality. Here is what we learned...",
  "cta": "Interested in building a practical AI workflow for your business? Contact our AI/LLM Lab."
}
```

---

# 8. Module 2: AI News Intelligence Feed

## 8.1 Objective

The AI News Intelligence Feed is a curated page that displays high-quality AI/LLM news, updates, tools, papers, and market insights discovered from selected sources.

The feed should not be a raw crawler output. It should be a filtered intelligence layer that selects useful AI updates according to the company's standards.

### 8.2 Public Positioning

The public page should be positioned as:

> Curated AI/LLM updates selected by our AI Lab.

### 8.3 Internal Value

Internally, the news feed helps the company:

- Track AI trends.
- Discover blog ideas.
- Monitor model releases.
- Track AI agent and evaluation trends.
- Support sales conversations.
- Stay informed about competitors and market direction.

---

# 9. AI News Feed Sources

## 9.1 Source Types

The system should support the following source types:

1. X/Twitter accounts.
2. X/Twitter keyword search.
3. Hacker News.
4. Reddit communities.
5. GitHub trending repositories.
6. GitHub releases.
7. Arxiv or research feeds.
8. Papers with Code.
9. Official company blogs.
10. RSS feeds.
11. User-submitted links.

## 9.2 Priority Source Examples

### 9.2.1 Official AI Sources

- OpenAI blog.
- Anthropic news/blog.
- Google DeepMind blog.
- Meta AI blog.
- Mistral AI blog.
- Hugging Face blog.
- Microsoft AI blog.
- NVIDIA AI blog.

### 9.2.2 Community and Developer Sources

- Hacker News.
- Reddit LocalLLaMA.
- Reddit MachineLearning.
- GitHub trending.
- Papers with Code.
- Arxiv AI/ML categories.

### 9.2.3 X/Twitter Sources

The admin should be able to maintain a list of high-quality AI accounts to crawl.

Each source account should have:

- Handle.
- Display name.
- Follower count.
- Source type.
- Topic focus.
- Credibility score.
- Active/inactive status.
- Last crawled timestamp.

---

# 10. AI News Crawling Workflow

## 10.1 End-to-End Workflow

```text
Crawler
  ↓
Raw Post Store
  ↓
URL / Content Extractor
  ↓
Deduplication
  ↓
Relevance Filter
  ↓
Quality Scoring
  ↓
AI Summary
  ↓
Human / AI Moderation
  ↓
Published AI News Feed
```

## 10.2 Crawler Responsibilities

The crawler should:

- Fetch posts from configured sources.
- Fetch linked URLs when available.
- Store raw content before processing.
- Track crawl metadata.
- Avoid processing the same item multiple times.
- Respect rate limits.
- Support source-specific crawl intervals.

## 10.3 Recommended Crawl Frequency

| Source | Frequency |
|---|---|
| X/Twitter high-priority accounts | 5–15 minutes |
| X/Twitter keyword search | 15–30 minutes |
| Hacker News / Reddit | 30–60 minutes |
| Official blogs / RSS | 30–60 minutes |
| GitHub trending | 1–3 hours |
| Arxiv / papers | 6–12 hours |
| User-submitted links | Near realtime |

## 10.4 Crawl Tools

Possible tools:

| Tool | Usage |
|---|---|
| Apify | Crawl X/Twitter, Reddit, Hacker News, and structured sites. |
| Firecrawl | Extract article content from URLs and web pages. |
| RSS Parser | Fetch official blogs and publication feeds. |
| GitHub API | Fetch repositories, releases, stars, and trending signals. |
| Custom Scraper | Handle sources not supported by external tools. |

## 10.5 Provider Strategy and Crawl Contracts

### 10.5.1 Source Order for MVP

The MVP should start with low-risk, high-signal sources before adding social crawling:

1. Official AI lab blogs and RSS feeds.
2. GitHub releases and selected repositories.
3. Hacker News / Reddit only if source quality is acceptable.
4. X/Twitter accounts and searches only after the provider strategy is explicitly configured.

### 10.5.2 X/Twitter Strategy

X/Twitter ingestion is valuable but must be treated as a provider-specific integration, not a generic crawler.

Allowed strategies:

| Strategy | Use When | Notes |
|---|---|---|
| Official X API | The required account/search data is available under the selected X API plan. | Prefer for compliance and stable field semantics. |
| Apify actor | Official API access is insufficient and the chosen actor is tested. | Must track actor id, run id, dataset id, cost, and failure rate. |
| Hybrid | Official API handles core account/search data and Apify fills selected gaps. | Requires clear source attribution and duplicate handling. |

Before implementation, the selected strategy must define:

- Source account list and keyword queries.
- Required fields and nullable fields.
- Rate limits and crawl interval by endpoint or actor.
- Cost budget per day and per month.
- Provider terms and operational risk owner.
- Fallback behavior when a provider fails or returns partial data.

### 10.5.3 Engagement Metric Availability

Engagement fields are source-dependent and must not be assumed to exist for every item.

Normalized metrics:

```json
{
  "likes": 1200,
  "reposts": 320,
  "replies": 80,
  "quotes": 40,
  "bookmarks": null,
  "views": null,
  "captured_at": "2026-06-01T10:05:00Z",
  "source_metric_names": {
    "likes": "public_metrics.like_count",
    "reposts": "public_metrics.retweet_count"
  }
}
```

Rules:

- Missing metrics must be stored as `null`, not `0`.
- Every engagement snapshot must include `captured_at`.
- Velocity calculations require at least two snapshots.
- Provider raw metric names must be preserved for debugging.
- Scoring must degrade gracefully when views, bookmarks, or follower counts are unavailable.

### 10.5.4 Firecrawl Contract

Firecrawl should be used for extracting clean article content from URLs and selected web pages.

Required behavior:

- Use markdown output for article extraction when possible.
- Store the original URL, final URL, canonical URL, title, author, site name, extracted markdown, extracted text, and extraction timestamp.
- Store provider response metadata and raw extraction payload in object storage when payloads are large.
- Use provider cache controls such as max-age only when freshness requirements allow it.
- Treat Firecrawl structured extraction as untrusted provider output and validate it against application schemas.
- Use asynchronous or batch extraction for multi-URL jobs instead of blocking public or admin requests.

### 10.5.5 Apify Contract

Apify should be used through explicit actor/task contracts.

Required behavior:

- Prefer `Authorization: Bearer <token>` over token query parameters.
- Store actor id, task id if used, run id, default dataset id, started time, finished time, and run status.
- Poll run status or receive webhook completion; do not rely on synchronous runs for jobs that may exceed provider timeout.
- Read dataset items with pagination.
- Persist raw dataset items before normalization.
- Use exponential backoff with jitter on 429 and transient provider failures.
- Record provider cost estimates when available.
- Use named datasets or copy data into system storage if retention must exceed provider defaults.

---

# 11. AI News Filtering and Scoring

## 11.1 Scoring Overview

Each crawled item should be processed through several scoring dimensions:

1. Source credibility score.
2. Engagement score.
3. Relevance score.
4. Novelty score.
5. Technical depth score.
6. Business value score.
7. Spam risk score.
8. Duplicate score.
9. Final publish score.

## 11.2 Source Credibility Score

### 11.2.1 Purpose

Source credibility estimates whether the author or source is likely to produce valuable AI content.

### 11.2.2 Signals

| Signal | Description |
|---|---|
| Follower count | Larger audience can indicate influence. |
| Known expert | Whether the account belongs to a researcher, engineer, founder, or credible AI practitioner. |
| Company affiliation | Association with AI labs, research institutions, or reputable companies. |
| Historical quality | Past posts from this source were useful. |
| Topic consistency | Source regularly posts about AI/ML/LLM topics. |
| Originality | Source often shares original analysis rather than reposting others. |

### 11.2.3 Example Formula

```text
source_credibility_score =
  follower_score * 0.20 +
  known_expert_score * 0.25 +
  affiliation_score * 0.20 +
  historical_quality_score * 0.20 +
  topic_consistency_score * 0.10 +
  originality_score * 0.05
```

Score range: `0.0` to `1.0`.

---

## 11.3 Engagement Score

### 11.3.1 Purpose

Engagement score estimates how much attention or discussion a post is receiving.

### 11.3.2 Signals

| Signal | Description |
|---|---|
| Views | Reach of the post. |
| Likes | General interest. |
| Reposts | Perceived value or shareability. |
| Replies | Discussion level. |
| Bookmarks | Strong value signal if available. |
| Engagement velocity | How quickly engagement is growing. |
| Engagement rate | Engagement relative to follower count. |

### 11.3.3 Example Formula

```text
engagement_score =
  log(views + 1) * 0.20 +
  log(likes + 1) * 0.25 +
  log(reposts + 1) * 0.25 +
  log(replies + 1) * 0.15 +
  velocity_score * 0.15
```

The raw score should be normalized to `0.0`–`1.0`.

---

## 11.4 Relevance Score

### 11.4.1 Purpose

Relevance score estimates whether the content is related to the company's AI/LLM Lab positioning.

### 11.4.2 High-Priority Topics

- LLM.
- AI Agent.
- Coding Agent.
- Evaluation.
- RAG.
- Model release.
- Open-source model.
- AI infrastructure.
- Prompt engineering.
- AI product development.
- Enterprise AI adoption.
- Multimodal AI.
- Voice AI.
- AI workflow automation.
- AI safety and reliability.
- LLM observability.
- Agent evaluation.
- AI-assisted software engineering.

### 11.4.3 Medium-Priority Topics

- AI startup.
- AI funding.
- AI tools.
- AI design.
- Productivity tools.
- AI UX.
- AI market adoption.

### 11.4.4 Low-Priority Topics

- Generic AI motivation.
- Meme AI.
- Crypto AI hype.
- AI drama unrelated to product or engineering.
- Generic tool lists.
- Low-value prompt packs.
- Affiliate-style AI content.

### 11.4.5 Output Example

```json
{
  "relevance_score": 0.91,
  "topics": ["LLM", "AI Agent", "Evaluation"],
  "reason": "The post discusses evaluation techniques for agentic workflows, which is directly related to the company's AI Lab positioning."
}
```

---

## 11.5 Novelty Score

### 11.5.1 Purpose

Novelty score estimates whether the item contains genuinely new or useful information.

### 11.5.2 Novelty Signals

The item is more novel if it includes:

- A new model release.
- A new benchmark result.
- A new paper.
- A new open-source repository.
- A new product/API update.
- A new technical method.
- A new enterprise AI use case.
- A new evaluation approach.
- A meaningful comparison between models/tools.

### 11.5.3 Output Example

```json
{
  "novelty_score": 0.87,
  "reason": "The post introduces a new evaluation method for agentic workflows, not just a generic opinion."
}
```

---

## 11.6 Technical Depth Score

### 11.6.1 Purpose

Technical depth score estimates whether the item contains substantive technical information.

### 11.6.2 High Technical Depth Examples

- Architecture explanation.
- Benchmark methodology.
- Evaluation framework.
- Code repository.
- Paper summary with method details.
- Production lessons.
- Debugging or reliability insight.
- Model comparison with evidence.

### 11.6.3 Low Technical Depth Examples

- Generic statement about AI.
- Meme.
- Motivational post.
- List of tools without explanation.
- Pure announcement without substance.

---

## 11.7 Business Value Score

### 11.7.1 Purpose

Business value score estimates whether the item can help the company create better products, write better content, or support client conversations.

### 11.7.2 Strong Business Value Signals

- Useful for AI product design.
- Useful for enterprise AI adoption.
- Useful for sales conversations.
- Useful for internal roadmap decisions.
- Useful for blog idea generation.
- Useful for client education.
- Shows practical use cases.
- Shows market movement.

---

## 11.8 Spam Risk Score

### 11.8.1 Purpose

Spam risk score estimates whether the item is low quality, promotional, misleading, or irrelevant.

### 11.8.2 Spam Signals

Items should be penalized if they contain:

- Generic “10 AI tools to make money” style content.
- Affiliate links.
- Clickbait claims.
- No original source.
- Reposted content without attribution.
- Crypto/AI hype.
- Scam-like language.
- Excessive emoji or promotional language.
- Misleading benchmark claims.
- Low-quality prompt packs.
- Unverified rumors.

### 11.8.3 Output Example

```json
{
  "spam_risk": 0.74,
  "reasons": [
    "Generic AI tool list",
    "No original source",
    "High promotional language",
    "Contains affiliate-like CTA"
  ]
}
```

---

## 11.9 Publish Decision

### 11.9.1 Basic Publish Rule

A news item can be considered for publishing if:

```text
quality_score > 0.70
relevance_score > 0.75
spam_risk < 0.35
duplicate_status != "duplicate"
```

### 11.9.2 Final Publish Score

Example formula:

```text
final_publish_score =
  source_credibility_score * 0.15 +
  engagement_score * 0.15 +
  relevance_score * 0.25 +
  novelty_score * 0.15 +
  technical_depth_score * 0.10 +
  business_value_score * 0.15 -
  spam_risk * 0.20
```

The score should be normalized to `0.0`–`1.0`.

### 11.9.3 Publish Statuses

| Status | Description |
|---|---|
| Raw | Crawled but not processed. |
| Processing | AI filters are running. |
| Candidate | Passed basic filter and awaits moderation. |
| Published | Publicly visible. |
| Rejected | Rejected due to low quality or irrelevance. |
| Duplicate | Duplicate of another item. |
| Needs Review | Requires human decision. |
| Archived | No longer shown in main feed. |

## 11.10 Scoring Calibration and Evaluation

The scoring formulas in this specification are starting heuristics, not permanent truth. They must be calibrated with human-labeled data before any high-impact automation is enabled.

### 11.10.1 Human Label Dataset

The system should support a labeled evaluation dataset for news quality.

Required labels:

```text
ACCEPT
REJECT_LOW_RELEVANCE
REJECT_SPAM
REJECT_DUPLICATE
NEEDS_REVIEW
```

Each labeled item should include:

- Raw post id.
- Extracted article id when available.
- Human label.
- Human relevance score.
- Human quality score.
- Human spam judgment.
- Human duplicate judgment.
- Labeler id.
- Label notes.
- Created timestamp.

### 11.10.2 Minimum Eval Gate Before Automation

Before enabling auto-reject beyond exact duplicates, the system should have:

- At least 100 human-labeled news items.
- Coverage across official sources, social posts, user-submitted links, spam, duplicates, and borderline cases.
- Measured precision for accepted candidates.
- Measured false-reject rate for valuable items.
- Human override rate tracked for at least two review cycles.

Before enabling auto-approve, the system should have:

- At least 500 human-labeled items.
- Stable scoring prompts across at least two prompt versions.
- Human agreement rate above the configured threshold.
- False-positive review showing brand, confidentiality, and spam risk is acceptable.

Auto-approve remains out of scope for MVP.

### 11.10.3 Evaluation Metrics

Track these metrics per scoring prompt version and scoring configuration version:

- Candidate precision.
- Recall against human-accepted items where measurable.
- Spam false-negative rate.
- Valuable-item false-reject rate.
- Duplicate grouping accuracy.
- Human override rate.
- Average scoring latency.
- Structured-output validation failure rate.
- Cost per processed item.

### 11.10.4 LLM-as-Judge Use

LLM-as-judge may be used to assist evaluation, but it must not replace human labels for launch decisions. LLM graders should use explicit rubrics, structured outputs, and stable prompt versions. Where possible, use pass/fail, classification, or pairwise comparison tasks rather than open-ended judgments.

---

# 12. Deduplication

## 12.1 Purpose

AI news is often reposted by many accounts. The system should avoid showing the same event repeatedly.

## 12.2 Deduplication Layers

### 12.2.1 URL-Level Deduplication

If multiple posts link to the same URL, they should be grouped together.

### 12.2.2 Text Similarity Deduplication

If multiple posts have very similar content, they should be grouped together using embeddings.

Example logic:

```text
embedding(post_content + linked_article_title + summary)
```

If cosine similarity is greater than a configured threshold, such as `0.88`, the items should be treated as duplicates or near-duplicates.

### 12.2.3 Event-Level Deduplication

Different posts may describe the same event using different wording. The system should classify the event.

Example:

```json
{
  "event_name": "OpenAI released a new model",
  "duplicate_group_id": "openai-new-model-2026-06"
}
```

### 12.2.4 Display Logic

The public page should show the best item in a duplicate group and optionally show other related sources.

Example:

```text
Also discussed by: @user1, @user2, @user3
```

---

# 13. User-Submitted Links

## 13.1 Objective

Users or internal team members should be able to submit AI-related links for review.

## 13.2 Submission Form Fields

Required:

- URL.

Optional:

- Submitter name.
- Submitter email.
- Note: why this link is worth reading.
- Suggested category.
- Suggested tags.

## 13.3 User Submission Workflow

```text
User submits URL
  ↓
Fetch content
  ↓
Extract title/content/author/date
  ↓
AI classify topic
  ↓
Check duplicate
  ↓
Score quality
  ↓
Human approve or auto approve
  ↓
Show on feed
```

## 13.4 AI Review Output

Example:

```json
{
  "accepted": true,
  "reason": "Relevant to AI evaluation and agent workflow.",
  "duplicate": false,
  "suggested_summary": "The article explains a practical evaluation method for AI agents.",
  "suggested_tags": ["AI Evaluation", "Agent"]
}
```

## 13.5 User-Submitted Link Safety Requirements

User-submitted links are untrusted input and must be processed through the same security boundary as crawled URLs.

Requirements:

- Accept only `http` and `https` URLs.
- Normalize and canonicalize URLs before deduplication.
- Apply rate limits per IP and per submitter email when available.
- Use idempotency keys or content hashes to prevent duplicate submissions.
- Fetch submitted URLs only from worker jobs, never inline in public request handlers.
- Apply SSRF protection before every network fetch and after every redirect.
- Set fetch timeout, maximum redirect count, maximum response size, and allowed content types.
- Do not expose raw fetched responses directly to public users.
- Store submission audit metadata, including submitter info if provided, IP-derived rate-limit key, created timestamp, and processing status.
- Require human approval before a user-submitted link appears publicly in MVP.

---

# 14. Public Website Structure

## 14.1 Recommended Routes

```text
/
  Home

/lab
  AI/LLM Lab positioning

/showcases
  List of AI products/showcases

/showcases/scopelytics
  Scopelytics case study

/showcases/ai-interview
  Voice-first AI interview case study

/blog
  AI Lab blog

/blog/[slug]
  Blog detail

/ai-news
  Curated AI news feed

/ai-news/submit
  User submit link

/contact
  Sales contact
```

## 14.2 Key Public Pages

### 14.2.1 `/lab`

Purpose:

- Explain the company's AI/LLM Lab positioning.
- Introduce capabilities.
- Explain the lab methodology.
- Link to showcases, blog, and contact.

Suggested sections:

1. Hero section.
2. What we build.
3. AI Lab capability map.
4. Our approach.
5. Featured showcases.
6. Latest blog posts.
7. CTA.

### 14.2.2 `/showcases`

Purpose:

- Show AI products and internal projects.
- Turn company work into client-facing proof.

Showcase card fields:

- Title.
- Short description.
- AI capabilities.
- Business value.
- Status.
- Link to detail page.

### 14.2.3 `/blog`

Purpose:

- Publish AI Lab articles.
- Build credibility.
- Support sales and marketing.

Blog card fields:

- Title.
- Excerpt.
- Cover image.
- Tags.
- Author.
- Published date.
- Reading time.

### 14.2.4 `/ai-news`

Purpose:

- Display curated AI/LLM updates.
- Show that the company is actively monitoring AI trends.

News card fields:

- Title.
- Summary.
- Why it matters.
- Source.
- Topic tags.
- Score.
- Original link.
- Related links.
- Published time.

Example card:

```text
New open-source coding model reaches strong SWE-bench performance

Summary:
A new model release shows competitive results on coding-agent benchmarks and may become useful for internal developer automation workflows.

Why it matters:
This could affect how AI/LLM Labs choose models for code generation, testing, and agentic coding pipelines.

Tags:
LLM, Coding Agent, Open Source Model, Evaluation

Source:
X / GitHub / Paper

Score:
Relevance 92 · Quality 84 · Novelty 88
```

---

# 15. Admin Dashboard

## 15.1 Purpose

The admin dashboard allows internal users to manage blog content, AI news candidates, sources, topics, showcases, and publishing workflows.

## 15.2 Admin Sections

Recommended sections:

1. Dashboard overview.
2. Blog ideas.
3. Blog drafts.
4. Blog review queue.
5. Published blog posts.
6. News candidates.
7. Published news.
8. Rejected news.
9. Duplicate groups.
10. Sources.
11. Topics/tags.
12. User-submitted links.
13. Showcases.
14. Settings.

## 15.3 Admin Dashboard Metrics

The dashboard should show:

- Number of blog ideas.
- Number of drafts awaiting review.
- Number of news candidates.
- Number of published news items.
- Number of rejected news items.
- Duplicate rate.
- Average relevance score.
- Top topics this week.
- Top sources by accepted items.
- Blog publishing cadence.

---

# 16. Data Model

## 16.1 Main Entities

```text
User
Project
Showcase
BlogIdea
BlogPost
BlogDraftVersion
BlogReview
NewsSource
RawPost
ExtractedContent
CuratedNewsItem
NewsDuplicateGroup
Topic
Tag
EvaluationScore
UserSubmittedLink
CrawlJob
CrawlRun
```

---

## 16.2 User

```json
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "role": "admin | editor | reviewer | viewer",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.3 Project

Represents an internal or client-facing project that can be used for showcases or blog content.

```json
{
  "id": "uuid",
  "name": "Scopelytics",
  "slug": "scopelytics",
  "summary": "AI-powered business analysis system.",
  "status": "internal | public | archived",
  "ai_capabilities": ["LLM", "Evaluation", "Structured Output"],
  "business_value": ["Reduce manual analysis", "Improve pre-sales workflow"],
  "confidentiality_level": "public | internal | restricted",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.4 Showcase

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "title": "Scopelytics",
  "slug": "scopelytics",
  "short_description": "An AI-powered analysis platform for business requirement review.",
  "full_description": "markdown",
  "ai_capabilities": ["LLM", "Evaluation", "Workflow Automation"],
  "business_value": ["Faster analysis", "More consistent output"],
  "cover_image_url": "string",
  "status": "draft | published | archived",
  "published_at": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.5 BlogIdea

```json
{
  "id": "uuid",
  "title": "How We Applied AI Evaluation to Improve Scopelytics Output Quality",
  "source_type": "manual | ai_generated | news_trend | project_based",
  "source_id": "uuid | null",
  "target_reader": "CTO, founder, product manager",
  "angle": "AI Evaluation",
  "goal": "Show AI Lab capability in quality control for LLM systems.",
  "status": "idea | approved | rejected | converted_to_draft",
  "created_by": "uuid",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.6 BlogPost

```json
{
  "id": "uuid",
  "title": "string",
  "slug": "string",
  "excerpt": "string",
  "content_markdown": "markdown",
  "cover_image_url": "string",
  "author_id": "uuid",
  "status": "idea | outline | draft | technical_review | marketing_review | approved | scheduled | published | archived",
  "seo_title": "string",
  "meta_description": "string",
  "tags": ["AI Evaluation", "LLM", "Scopelytics"],
  "related_project_ids": ["uuid"],
  "published_at": "datetime",
  "scheduled_at": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.7 BlogDraftVersion

```json
{
  "id": "uuid",
  "blog_post_id": "uuid",
  "version_number": 1,
  "content_markdown": "markdown",
  "created_by": "user | ai_agent",
  "agent_name": "Draft Writer Agent",
  "change_summary": "Initial AI-generated draft.",
  "created_at": "datetime"
}
```

---

## 16.8 BlogReview

```json
{
  "id": "uuid",
  "blog_post_id": "uuid",
  "review_type": "technical | marketing | legal | editorial",
  "reviewer_type": "human | ai_agent",
  "reviewer_id": "uuid | null",
  "overall_risk": "low | medium | high",
  "approval_recommendation": "approve | needs_revision | reject",
  "issues": [
    {
      "severity": "high",
      "type": "unsupported_claim",
      "text": "The system reduces manual review time by 80%.",
      "reason": "No measurement data is provided.",
      "suggestion": "Use softer wording unless measurement data exists."
    }
  ],
  "created_at": "datetime"
}
```

---

## 16.9 NewsSource

```json
{
  "id": "uuid",
  "source_type": "twitter | rss | reddit | hackernews | github | arxiv | website | manual",
  "name": "OpenAI Blog",
  "url": "https://openai.com/blog",
  "handle": "@example",
  "description": "Official OpenAI updates.",
  "topic_focus": ["LLM", "AI Product", "Research"],
  "credibility_score": 0.95,
  "crawl_frequency_minutes": 60,
  "is_active": true,
  "last_crawled_at": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.10 RawPost

```json
{
  "id": "uuid",
  "source_id": "uuid",
  "external_id": "string",
  "source_type": "twitter | rss | reddit | hackernews | github | arxiv | website | manual",
  "author_name": "string",
  "author_handle": "string",
  "author_followers": 120000,
  "post_url": "string",
  "raw_text": "string",
  "linked_urls": ["string"],
  "posted_at": "datetime",
  "views": 450000,
  "likes": 3200,
  "reposts": 800,
  "replies": 140,
  "bookmarks": 500,
  "raw_payload": {},
  "created_at": "datetime"
}
```

---

## 16.11 ExtractedContent

```json
{
  "id": "uuid",
  "raw_post_id": "uuid",
  "url": "string",
  "title": "string",
  "author": "string",
  "published_at": "datetime",
  "content_text": "string",
  "content_markdown": "markdown",
  "summary": "string",
  "extraction_status": "success | failed | partial",
  "extraction_error": "string | null",
  "created_at": "datetime"
}
```

---

## 16.12 CuratedNewsItem

```json
{
  "id": "uuid",
  "raw_post_id": "uuid",
  "duplicate_group_id": "uuid | null",
  "title": "New open-source coding model reaches strong SWE-bench performance",
  "slug": "new-open-source-coding-model-swe-bench",
  "summary": "A new model release shows competitive results on coding-agent benchmarks.",
  "why_it_matters": "This may affect how teams choose models for coding-agent workflows.",
  "topics": ["LLM", "Coding Agent", "Open Source Model", "Evaluation"],
  "source_credibility_score": 0.90,
  "engagement_score": 0.82,
  "relevance_score": 0.92,
  "novelty_score": 0.88,
  "technical_depth_score": 0.80,
  "business_value_score": 0.78,
  "spam_risk": 0.10,
  "final_publish_score": 0.86,
  "status": "raw | processing | candidate | published | rejected | duplicate | needs_review | archived",
  "published_at": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.13 NewsDuplicateGroup

```json
{
  "id": "uuid",
  "event_name": "OpenAI released a new model",
  "canonical_news_item_id": "uuid",
  "item_ids": ["uuid"],
  "related_sources": [
    {
      "source_name": "X/Twitter",
      "author_handle": "@example",
      "url": "string"
    }
  ],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.14 Topic

```json
{
  "id": "uuid",
  "name": "AI Evaluation",
  "slug": "ai-evaluation",
  "priority": "high | medium | low",
  "description": "Methods and workflows for evaluating AI output quality and reliability.",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.15 UserSubmittedLink

```json
{
  "id": "uuid",
  "url": "string",
  "submitter_name": "string | null",
  "submitter_email": "string | null",
  "note": "string | null",
  "suggested_category": "string | null",
  "ai_review_result": {},
  "status": "submitted | processing | candidate | published | rejected | duplicate",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.16 CrawlJob

```json
{
  "id": "uuid",
  "source_id": "uuid",
  "job_type": "twitter_account | twitter_keyword | rss | reddit | hackernews | github | arxiv | website",
  "schedule": "cron expression",
  "is_active": true,
  "last_run_at": "datetime",
  "next_run_at": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 16.17 CrawlRun

```json
{
  "id": "uuid",
  "crawl_job_id": "uuid",
  "status": "running | success | failed | partial",
  "items_found": 100,
  "items_created": 25,
  "items_skipped": 75,
  "error_message": "string | null",
  "started_at": "datetime",
  "finished_at": "datetime"
}
```

---

# 17. AI Prompts and Structured Outputs

## 17.1 General Requirements

All AI operations should use structured output where possible.

The system should:

- Use JSON schema for scoring tasks.
- Prefer provider-native structured outputs with strict schema enforcement when available.
- Generate JSON schemas from Pydantic models where possible to avoid schema drift.
- Store raw AI output for debugging.
- Store parsed AI output for application logic.
- Handle invalid AI output gracefully.
- Retry when output does not match schema.
- Handle provider refusals or safety blocks as first-class outcomes, not parsing failures.
- Validate business rules after schema validation because schema-valid output can still be factually wrong.
- Track model name, prompt version, and timestamp.

## 17.2 Prompt Versioning

Each AI prompt should have:

- Prompt name.
- Version.
- Purpose.
- Input schema.
- Output schema.
- Model used.
- Last updated timestamp.

Example prompt names:

- `blog_knowledge_extraction_v1`
- `blog_outline_generation_v1`
- `blog_draft_generation_v1`
- `blog_technical_review_v1`
- `news_relevance_scoring_v1`
- `news_spam_detection_v1`
- `news_summary_generation_v1`
- `news_event_dedup_v1`

## 17.3 Structured Output Policy

All structured AI calls must follow this policy:

```text
Prompt version
  -> Provider request
  -> Raw provider response
  -> Schema validation
  -> Business validation
  -> Parsed output stored for application use
```

Required stored fields for every important AI call:

- Provider.
- Model name.
- Prompt version id.
- Input schema version.
- Output schema version.
- Input payload.
- Raw output payload.
- Parsed output payload.
- Refusal or safety status if present.
- Validation status.
- Retry count.
- Token usage.
- Latency.
- Estimated cost.
- Created timestamp.

Retry policy:

- Retry transient provider errors.
- Retry schema-invalid responses when the provider did not refuse.
- Do not retry safety refusals blindly.
- Do not retry deterministic business validation failures without changing input or prompt version.
- Cap retries per task and store the final failure reason.

Prompt safety requirements:

- Prompts must instruct the model to ignore instructions found in crawled content, submitted links, comments, articles, or internal documents.
- Crawler content and user-submitted content must be treated as data, not instructions.
- Blog generation prompts must include confidentiality and unsupported-claim constraints.
- News scoring prompts must include a clear rubric for relevance, quality, spam, duplicate risk, and uncertainty.

---

# 18. Blog Agent Requirements

## 18.1 Functional Requirements

### FR-BLOG-001: Create Blog Idea

The system shall allow an admin or AI agent to create a blog idea.

### FR-BLOG-002: Generate Blog Ideas from Project

The system shall generate blog ideas based on an internal project or showcase.

### FR-BLOG-003: Generate Blog Ideas from News Trends

The system shall generate blog ideas based on recurring or high-scoring AI news topics.

### FR-BLOG-004: Generate Outline

The system shall generate an outline for an approved blog idea.

### FR-BLOG-005: Generate Draft

The system shall generate a complete markdown draft from an outline and approved context.

### FR-BLOG-006: Technical Review

The system shall run an AI technical review on each draft before approval.

### FR-BLOG-007: Marketing Review

The system shall generate marketing edits, SEO metadata, and social snippets.

### FR-BLOG-008: Human Approval

The system shall require human approval before publishing a blog post.

### FR-BLOG-009: Version History

The system shall store multiple draft versions.

### FR-BLOG-010: Publish Blog Post

The system shall publish approved blog posts to the public blog page.

### FR-BLOG-011: Schedule Blog Post

The system should allow approved blog posts to be scheduled for future publishing.

### FR-BLOG-012: Related Showcase Linking

The system should allow blog posts to link to related showcases.

---

# 19. AI News Requirements

## 19.1 Functional Requirements

### FR-NEWS-001: Manage Sources

The system shall allow admins to create, update, activate, and deactivate news sources.

### FR-NEWS-002: Scheduled Crawling

The system shall crawl sources based on configured intervals.

### FR-NEWS-003: Store Raw Posts

The system shall store raw crawled posts before AI processing.

### FR-NEWS-004: Extract Linked Content

The system shall extract content from linked URLs when available.

### FR-NEWS-005: Score Relevance

The system shall score each item for relevance to AI/LLM Lab topics.

### FR-NEWS-006: Score Quality

The system shall score each item for quality, novelty, technical depth, and business value.

### FR-NEWS-007: Detect Spam

The system shall detect and reject likely spam or low-quality content.

### FR-NEWS-008: Detect Duplicates

The system shall detect duplicates using URL, text similarity, and event-level classification.

### FR-NEWS-009: Generate Summary

The system shall generate a concise summary and “why it matters” explanation.

### FR-NEWS-010: Candidate Queue

The system shall place high-scoring items into a candidate review queue.

### FR-NEWS-011: Publish News Item

The system shall allow admins to publish selected candidate items.

### FR-NEWS-012: Auto-Reject Low-Quality Items

The system should auto-reject items below configured thresholds.

### FR-NEWS-013: User-Submitted Links

The system shall allow users or internal team members to submit links for review.

### FR-NEWS-014: Topic Filtering

The public AI News page shall allow filtering by topic.

### FR-NEWS-015: Source Filtering

The admin dashboard should allow filtering news by source.

---

# 20. Non-Functional Requirements

## 20.1 Performance

- Public pages should load quickly.
- Blog and news listing pages should support pagination or infinite scroll.
- Crawling jobs should run asynchronously.
- AI processing should not block public page rendering.

## 20.2 Reliability

- Failed crawl jobs should be logged.
- Failed AI scoring jobs should be retryable.
- The system should avoid losing raw crawled data.
- Duplicate detection should be deterministic where possible.

## 20.3 Security

- Admin dashboard must require authentication.
- Role-based access control should be supported.
- Public users should not access unpublished drafts.
- Internal project context should not be exposed accidentally.
- API keys for crawlers and LLM providers must be stored securely.

## 20.4 Privacy and Confidentiality

- Blog generation must not leak confidential project or client information.
- Each project should have a confidentiality level.
- Restricted project content should require explicit approval before being used in public content.

## 20.5 Observability

The system should track:

- Crawl job status.
- AI processing status.
- Prompt version.
- Model used.
- Token usage.
- Processing errors.
- Number of accepted/rejected news items.
- Duplicate rate.

## 20.6 Maintainability

- Prompts should be versioned.
- Scoring thresholds should be configurable.
- Sources should be configurable from admin dashboard.
- Crawlers should be modular.
- AI scoring pipelines should be testable independently.

## 20.7 Compliance and Provider Reliability

- Provider-specific behavior must be isolated behind adapters.
- The system must tolerate missing engagement metrics and partial provider responses.
- Crawl schedules must respect provider rate limits and configured budgets.
- Provider API keys must never be exposed to public clients or logged.
- Provider errors must be categorized as transient, rate-limited, authentication, validation, or permanent failures.
- External provider payload schemas must be validated before normalization.

## 20.8 Content Safety and Brand Trust

- Blog posts must not publish unsupported quantified claims.
- Public content generated from internal project data must respect confidentiality level.
- News summaries must link back to original sources and avoid overstating claims.
- AI-generated content must be attributable as internally reviewed content, not autonomous publication.
- The system should preserve enough evidence for reviewers to understand why content was accepted, rejected, or edited.

---

# 21. Technical Architecture

## 21.1 Architecture Goals

The technical architecture should support three product goals:

1. **Public credibility**
   - Blog, showcase, AI Lab, and AI News pages must be fast, clean, and reliable.
   - Public content should be SEO-friendly and shareable.

2. **Internal AI workflow automation**
   - The system should automate idea generation, drafting, crawling, filtering, scoring, summarization, and deduplication.
   - Humans should remain in control of final publishing decisions.

3. **Showcase value**
   - The architecture itself should be explainable to clients as a practical example of an AI workflow system.
   - The company should be able to say: “This is how we build AI-enabled operational systems.”

The architecture should be modular enough to later reuse parts of the system for client work, such as crawler pipelines, AI scoring engines, content workflow systems, and evaluation dashboards.

---

## 21.2 Recommended Tech Stack

### 21.2.1 Frontend

Recommended stack:

- **Next.js** for the public website and admin frontend.
- **TypeScript** for type safety.
- **Tailwind CSS** for fast UI development.
- **shadcn/ui** or a similar component library for admin dashboard components.
- **MDX or markdown rendering** for blog content.
- **Server-side rendering / static generation** for SEO-heavy public pages.

Frontend responsibilities:

- Render public website pages.
- Render blog listing and blog detail pages.
- Render showcase listing and showcase detail pages.
- Render AI News Intelligence Feed.
- Render admin dashboard.
- Provide forms for blog review, news approval, source management, topic management, and user-submitted links.

Recommended public routes:

```text
/
/lab
/showcases
/showcases/[slug]
/blog
/blog/[slug]
/ai-news
/ai-news/[slug]
/ai-news/submit
/contact
```

Recommended admin routes:

```text
/admin
/admin/blog/ideas
/admin/blog/drafts
/admin/blog/drafts/[id]
/admin/news/raw
/admin/news/review
/admin/news/published
/admin/news/sources
/admin/topics
/admin/showcases
/admin/settings/scoring
/admin/settings/prompts
/admin/jobs
```

---

### 21.2.2 Backend API

The backend API should use:

- **Python FastAPI** as the main API framework.
- **Pydantic** for request/response validation and structured AI output validation.
- **SQLAlchemy 2.x** or **SQLModel** for ORM.
- **Alembic** for database migrations.
- **PostgreSQL** as the primary relational database.
- **pgvector** for embedding storage and semantic deduplication.
- **Redis** for cache, rate limiting, and queue backend.
- **Celery** or **RQ/ARQ** for background workers.

FastAPI responsibilities:

- Public content API.
- Admin dashboard API.
- Blog workflow API.
- News workflow API.
- Source management API.
- Topic management API.
- User-submitted link API.
- Prompt/version management API.
- Job monitoring API.
- Authentication and authorization.

Recommended API style:

- REST API for MVP.
- JSON request/response.
- OpenAPI documentation generated by FastAPI.
- Internal service functions separated from route handlers.

GraphQL is not required for MVP. REST is simpler, easier to maintain, and sufficient for the initial product.

---

### 21.2.3 Background Workers

The platform requires asynchronous jobs because crawling, AI processing, embedding generation, and summarization can be slow and unreliable.

Recommended stack:

- **Celery** with Redis broker for MVP.
- Optional future upgrade to RabbitMQ if the job system becomes more complex.
- Separate worker queues by workload type.

Recommended queues:

```text
default
crawler
extractor
embedding
ai_scoring
ai_writing
dedup
publisher
maintenance
```

Worker responsibilities:

- Crawl external sources.
- Fetch article content.
- Extract readable text.
- Generate embeddings.
- Detect duplicates.
- Score relevance, quality, novelty, credibility, spam risk, and technical depth.
- Generate summaries and “why it matters”.
- Generate blog outlines and drafts.
- Run AI review checks.
- Retry failed jobs.
- Update job status and error logs.

---

### 21.2.4 Database

Primary database:

- **PostgreSQL**.

Extensions:

- **pgvector** for embedding similarity search.
- Optional: `pg_trgm` for fuzzy text matching.
- Optional: full-text search using PostgreSQL `tsvector` for admin search.

Database responsibilities:

- Store projects/showcases.
- Store blog ideas, outlines, drafts, reviews, and published posts.
- Store news sources.
- Store raw crawled posts.
- Store extracted articles.
- Store curated news items.
- Store embeddings.
- Store duplicate groups.
- Store scoring outputs.
- Store prompts and prompt versions.
- Store crawl jobs and processing jobs.
- Store admin users and roles.

---

### 21.2.5 Object Storage

Recommended storage:

- **Cloudflare R2**, **AWS S3**, or any S3-compatible object storage.

Object storage should be used for:

- Raw HTML snapshots.
- Crawled page screenshots if needed.
- Uploaded blog images.
- Showcase images.
- Extracted article markdown snapshots.
- Large JSON payloads from crawlers.
- Debug artifacts for AI processing.

Object storage should not replace PostgreSQL. PostgreSQL should store metadata and references to object storage keys.

---

### 21.2.6 AI Layer

Recommended AI layer:

- LLM provider abstraction layer.
- Embedding provider abstraction layer.
- Prompt registry.
- Structured output validation with Pydantic models.
- Retry and fallback logic.
- Token usage tracking.

Supported LLM providers:

- OpenAI.
- Anthropic.
- Google Gemini.
- Optional future local/open-source model provider.

The system should not hard-code one provider inside business logic. Route handlers and workers should call internal services such as:

```text
llm_service.generate_structured_output(...)
embedding_service.embed_text(...)
blog_agent_service.generate_outline(...)
news_ai_service.score_item(...)
```

This makes it easier to switch models later.

---

### 21.2.7 Crawling Layer

Recommended crawling sources:

- **Apify** for X/Twitter, Reddit, Hacker News, and structured crawls.
- **Firecrawl** for article extraction, documentation pages, and general webpages.
- **RSS parser** for official AI blogs.
- **GitHub API** for repositories, releases, stars, and trending-like signals.
- Optional custom scrapers for specific sources.

The crawling layer should be isolated from the rest of the system. Each crawler should normalize data into a common `RawPost` or `RawSourceItem` format.

Common normalized fields:

```json
{
  "source_type": "x_twitter",
  "source_name": "X/Twitter",
  "external_id": "post_123",
  "author_name": "Example Researcher",
  "author_handle": "example_ai",
  "author_followers": 120000,
  "content": "Post text here...",
  "urls": ["https://example.com/article"],
  "posted_at": "2026-06-01T10:00:00Z",
  "engagement": {
    "likes": 1200,
    "reposts": 320,
    "replies": 80,
    "views": 100000
  },
  "raw_payload_key": "s3://..."
}
```

---

### 21.2.8 Authentication and Authorization

MVP authentication options:

- Auth.js/NextAuth on the frontend with backend JWT validation.
- Or FastAPI-managed authentication with secure HTTP-only cookies.
- Or integration with Google Workspace if the company already uses it.

Recommended roles:

| Role | Permissions |
|---|---|
| Admin | Manage users, settings, prompts, sources, publish content. |
| Editor | Create, edit, review, approve blog/news content. |
| Reviewer | Review drafts and news items, add comments, approve/reject. |
| Viewer | Read internal dashboard only. |

Public users should only access published content.

---

### 21.2.9 Deployment

Recommended MVP deployment:

- Frontend: Vercel, Cloudflare Pages, or containerized Next.js.
- Backend FastAPI: Docker container on Render, Fly.io, Railway, AWS ECS, GCP Cloud Run, or Kubernetes.
- PostgreSQL: Managed PostgreSQL provider.
- Redis: Managed Redis provider.
- Workers: Separate Docker process running Celery workers.
- Scheduler: Celery Beat, managed cron, or Kubernetes CronJob.
- Object storage: Cloudflare R2 or AWS S3.

Recommended production setup:

```text
Frontend App       → Next.js
Backend API        → FastAPI container
Worker Service     → Celery worker container
Scheduler          → Celery Beat / Cron container
Database           → Managed PostgreSQL + pgvector
Queue/Cache        → Managed Redis
Object Storage     → S3/R2
Monitoring         → Sentry + OpenTelemetry + provider logs
```

---

## 21.3 High-Level System Architecture

```text
                                 ┌─────────────────────────────┐
                                 │         Public Users         │
                                 └──────────────┬──────────────┘
                                                │
                                                ▼
                                 ┌─────────────────────────────┐
                                 │        Next.js Website       │
                                 │ Blog / News / Showcases      │
                                 └──────────────┬──────────────┘
                                                │
                                                ▼
                                 ┌─────────────────────────────┐
                                 │      Python FastAPI API      │
                                 │ Public + Admin APIs          │
                                 └───────┬────────┬────────────┘
                                         │        │
                         ┌───────────────┘        └────────────────┐
                         ▼                                         ▼
              ┌──────────────────────┐                 ┌──────────────────────┐
              │ PostgreSQL + pgvector │                 │ Redis Queue / Cache  │
              │ System of record      │                 │ Async job backend    │
              └──────────┬───────────┘                 └──────────┬───────────┘
                         │                                         │
                         ▼                                         ▼
              ┌──────────────────────┐                 ┌──────────────────────┐
              │ S3/R2 Object Storage │                 │ Celery Worker Pool   │
              │ Raw content/assets   │                 │ Crawl / AI / Dedup   │
              └──────────────────────┘                 └──────────┬───────────┘
                                                                   │
                   ┌───────────────────────────────────────────────┼──────────────────────────────────────────┐
                   ▼                                               ▼                                          ▼
        ┌──────────────────────┐                       ┌──────────────────────┐                  ┌──────────────────────┐
        │ External Crawlers    │                       │ AI Providers         │                  │ External APIs        │
        │ Apify / Firecrawl    │                       │ LLM + Embeddings     │                  │ GitHub / RSS / etc.  │
        └──────────────────────┘                       └──────────────────────┘                  └──────────────────────┘
```

---

## 21.4 Backend Service Architecture

The FastAPI backend should be organized into domain services rather than placing business logic directly inside route handlers.

Recommended backend layers:

```text
API Routes
  ↓
Application Services
  ↓
Domain Services
  ↓
Repositories
  ↓
Database / External Providers
```

### 21.4.1 API Routes

API routes handle:

- Request validation.
- Authentication and authorization.
- Calling application services.
- Returning response DTOs.

Routes should not contain scoring logic, AI prompts, crawler logic, or database-heavy business logic.

### 21.4.2 Application Services

Application services coordinate workflows.

Examples:

- `BlogWorkflowService`
- `NewsWorkflowService`
- `CrawlOrchestrationService`
- `ReviewWorkflowService`
- `PublishingService`

### 21.4.3 Domain Services

Domain services contain business logic.

Examples:

- `RelevanceScoringService`
- `QualityScoringService`
- `DeduplicationService`
- `PromptRenderingService`
- `BlogAgentService`
- `NewsSummarizationService`
- `ConfidentialityGuardService`

### 21.4.4 Repositories

Repositories encapsulate database access.

Examples:

- `BlogPostRepository`
- `NewsItemRepository`
- `RawPostRepository`
- `SourceRepository`
- `TopicRepository`
- `PromptVersionRepository`
- `JobRunRepository`

---

## 21.5 FastAPI API Surface

### 21.5.1 Public Content APIs

```http
GET /api/public/blog-posts
GET /api/public/blog-posts/{slug}
GET /api/public/showcases
GET /api/public/showcases/{slug}
GET /api/public/ai-news
GET /api/public/ai-news/{slug}
POST /api/public/submitted-links
```

### 21.5.2 Blog Admin APIs

```http
GET    /api/admin/blog/ideas
POST   /api/admin/blog/ideas
GET    /api/admin/blog/ideas/{id}
PATCH  /api/admin/blog/ideas/{id}
POST   /api/admin/blog/ideas/{id}/generate-outline
POST   /api/admin/blog/ideas/{id}/generate-draft

GET    /api/admin/blog/drafts
GET    /api/admin/blog/drafts/{id}
PATCH  /api/admin/blog/drafts/{id}
POST   /api/admin/blog/drafts/{id}/technical-review
POST   /api/admin/blog/drafts/{id}/marketing-review
POST   /api/admin/blog/drafts/{id}/approve
POST   /api/admin/blog/drafts/{id}/publish
POST   /api/admin/blog/drafts/{id}/archive
```

### 21.5.3 News Admin APIs

```http
GET    /api/admin/news/raw-posts
GET    /api/admin/news/raw-posts/{id}
POST   /api/admin/news/raw-posts/{id}/process

GET    /api/admin/news/review-items
GET    /api/admin/news/review-items/{id}
POST   /api/admin/news/review-items/{id}/approve
POST   /api/admin/news/review-items/{id}/reject
POST   /api/admin/news/review-items/{id}/mark-duplicate
POST   /api/admin/news/review-items/{id}/rescore

GET    /api/admin/news/published
PATCH  /api/admin/news/published/{id}
POST   /api/admin/news/published/{id}/unpublish
```

### 21.5.4 Source and Topic APIs

```http
GET    /api/admin/sources
POST   /api/admin/sources
GET    /api/admin/sources/{id}
PATCH  /api/admin/sources/{id}
POST   /api/admin/sources/{id}/enable
POST   /api/admin/sources/{id}/disable
POST   /api/admin/sources/{id}/run-crawl

GET    /api/admin/topics
POST   /api/admin/topics
PATCH  /api/admin/topics/{id}
DELETE /api/admin/topics/{id}
```

### 21.5.5 Prompt and Scoring Settings APIs

```http
GET    /api/admin/prompts
POST   /api/admin/prompts
GET    /api/admin/prompts/{id}
POST   /api/admin/prompts/{id}/create-version
POST   /api/admin/prompts/{id}/activate-version

GET    /api/admin/scoring-settings
PATCH  /api/admin/scoring-settings
```

### 21.5.6 Job Monitoring APIs

```http
GET    /api/admin/jobs
GET    /api/admin/jobs/{id}
POST   /api/admin/jobs/{id}/retry
POST   /api/admin/jobs/{id}/cancel
```

### 21.5.7 API Contract Standards

All list endpoints must support pagination.

Default pagination request shape:

```http
GET /api/public/ai-news?page=1&pageSize=20&topic=llm&sortBy=publishedAt&sortOrder=desc
```

Default paginated response shape:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 0,
    "totalPages": 0
  }
}
```

Default error response shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request.",
    "details": {}
  }
}
```

HTTP status rules:

| Status | Use |
|---:|---|
| 400 | Malformed request. |
| 401 | Not authenticated. |
| 403 | Authenticated but not authorized. |
| 404 | Resource not found. |
| 409 | Conflict, duplicate, invalid state transition, or idempotency conflict. |
| 422 | Semantically invalid input. |
| 429 | Rate limit exceeded. |
| 500 | Internal error without leaking implementation details. |

API rules:

- Public endpoints must only return published content.
- Admin endpoints must enforce authentication and role-based authorization.
- Admin mutation endpoints must write audit logs.
- External provider payloads must not be returned directly from public APIs.
- `PATCH` endpoints must support partial updates and preserve omitted fields.
- Publish, approve, reject, retry, cancel, and unpublish actions must validate current state before transition.
- Long-running operations should return a job id rather than blocking until completion.
- User-submitted link creation should be idempotent by normalized URL and submitter/rate-limit key.

---

## 21.6 Suggested Backend Folder Structure

```text
backend/
  app/
    main.py
    core/
      config.py
      security.py
      logging.py
      errors.py
      database.py
      celery_app.py
    api/
      deps.py
      public/
        blog.py
        showcases.py
        news.py
        submitted_links.py
      admin/
        blog.py
        news.py
        sources.py
        topics.py
        prompts.py
        scoring_settings.py
        jobs.py
    models/
      user.py
      blog.py
      showcase.py
      news.py
      source.py
      topic.py
      prompt.py
      job.py
      audit.py
    schemas/
      blog.py
      showcase.py
      news.py
      source.py
      topic.py
      prompt.py
      job.py
    repositories/
      blog_repository.py
      news_repository.py
      source_repository.py
      topic_repository.py
      prompt_repository.py
      job_repository.py
    services/
      blog_workflow_service.py
      blog_agent_service.py
      news_workflow_service.py
      news_scoring_service.py
      crawler_service.py
      extraction_service.py
      deduplication_service.py
      embedding_service.py
      llm_service.py
      prompt_service.py
      publishing_service.py
      confidentiality_guard_service.py
    workers/
      crawl_tasks.py
      extraction_tasks.py
      embedding_tasks.py
      scoring_tasks.py
      blog_tasks.py
      maintenance_tasks.py
    prompts/
      blog_outline.md
      blog_draft.md
      technical_review.md
      marketing_review.md
      news_relevance_score.md
      news_quality_score.md
      news_summary.md
      spam_detection.md
    tests/
      unit/
      integration/
  alembic/
  Dockerfile
  pyproject.toml
  README.md
```

---

## 21.7 Frontend Folder Structure

```text
frontend/
  app/
    page.tsx
    lab/
      page.tsx
    showcases/
      page.tsx
      [slug]/page.tsx
    blog/
      page.tsx
      [slug]/page.tsx
    ai-news/
      page.tsx
      [slug]/page.tsx
      submit/page.tsx
    admin/
      page.tsx
      blog/
      news/
      sources/
      topics/
      prompts/
      jobs/
  components/
    public/
      BlogCard.tsx
      NewsCard.tsx
      ShowcaseCard.tsx
      TopicBadge.tsx
    admin/
      DataTable.tsx
      ReviewPanel.tsx
      ScoreBreakdown.tsx
      JobStatusBadge.tsx
      PromptEditor.tsx
  lib/
    api-client.ts
    auth.ts
    formatters.ts
  types/
    blog.ts
    news.ts
    showcase.ts
    source.ts
```

---

## 21.8 Database Design Details

The following entities are recommended for MVP and near-term scalability.

### 21.8.1 Blog Tables

#### `blog_ideas`

Stores potential blog ideas.

Key fields:

```text
id
source_type                 -- manual, news_trend, internal_project, ai_suggested
title
angle
target_reader
objective                   -- credibility, sales, technical, case_study, market_insight
related_project_id
related_news_item_ids
status                      -- idea, selected, archived
created_by
created_at
updated_at
```

#### `blog_drafts`

Stores generated and edited blog drafts.

Key fields:

```text
id
blog_idea_id
title
slug
outline_markdown
content_markdown
excerpt
seo_title
seo_description
status                      -- outline, draft, technical_review, marketing_review, approved, published, archived
technical_review_result_json
marketing_review_result_json
claim_risk_score
confidentiality_risk_score
published_at
created_at
updated_at
```

#### `blog_draft_versions`

Stores draft history.

Key fields:

```text
id
blog_draft_id
version_number
content_markdown
change_summary
created_by
created_at
```

---

### 21.8.2 Showcase Tables

#### `projects`

Stores internal AI projects and product work.

Key fields:

```text
id
name
slug
summary
problem_statement
solution_summary
ai_capabilities_json
technical_highlights_json
business_value_json
confidentiality_level       -- public, internal, restricted
status                      -- draft, approved, published, archived
created_at
updated_at
```

#### `showcases`

Stores public showcase pages.

Key fields:

```text
id
project_id
title
slug
hero_summary
content_markdown
industry
use_case
tags
status
published_at
created_at
updated_at
```

---

### 21.8.3 News Tables

#### `news_sources`

Stores configured crawl sources.

Key fields:

```text
id
name
source_type                 -- x_twitter, rss, github, reddit, hn, website, user_submit
url_or_identifier
description
priority                    -- high, medium, low
crawl_frequency_minutes
is_enabled
credibility_base_score
last_crawled_at
created_at
updated_at
```

#### `raw_posts`

Stores raw crawled posts or source items.

Key fields:

```text
id
source_id
source_type
external_id
author_name
author_handle
author_followers
content_text
urls_json
posted_at
engagement_json
raw_payload_object_key
crawl_job_id
processing_status           -- raw, extracted, embedded, scored, rejected, review, published, failed
created_at
updated_at
```

#### `extracted_articles`

Stores extracted content from URLs found in raw posts.

Key fields:

```text
id
raw_post_id
url
canonical_url
title
author
published_at
site_name
content_markdown
content_text
content_hash
object_storage_key
created_at
updated_at
```

#### `news_items`

Stores AI-scored, reviewable or published news items.

Key fields:

```text
id
raw_post_id
primary_url
title
slug
summary
why_it_matters
topics_json
relevance_score
quality_score
novelty_score
engagement_score
source_credibility_score
technical_depth_score
spam_risk_score
final_score
status                      -- review, approved, rejected, published, archived
rejection_reason
duplicate_group_id
published_at
created_at
updated_at
```

#### `content_embeddings`

Stores embeddings for deduplication and search.

Key fields:

```text
id
entity_type                 -- raw_post, article, news_item, blog_post
entity_id
embedding vector
embedding_model
content_hash
created_at
```

#### `duplicate_groups`

Stores event-level or semantic duplicate groups.

Key fields:

```text
id
group_key
canonical_news_item_id
summary
created_at
updated_at
```

---

### 21.8.4 Prompt and Evaluation Tables

#### `prompts`

```text
id
name
description
task_type                   -- blog_outline, blog_draft, news_scoring, spam_detection, etc.
is_active
created_at
updated_at
```

#### `prompt_versions`

```text
id
prompt_id
version_number
model_provider
model_name
system_prompt
user_prompt_template
output_schema_json
temperature
max_tokens
is_active
created_at
updated_at
```

#### `ai_runs`

Stores every important AI call for observability and reproducibility.

```text
id
prompt_version_id
entity_type
entity_id
model_provider
model_name
input_json
output_json
parsed_output_json
status                      -- success, failed, validation_failed
error_message
input_tokens
output_tokens
total_cost_estimate
latency_ms
created_at
```

---

### 21.8.5 Job and Audit Tables

#### `job_runs`

```text
id
job_type                    -- crawl, extract, embed, score, summarize, generate_blog, publish
status                      -- queued, running, success, failed, retrying, cancelled
entity_type
entity_id
attempt_count
error_message
started_at
finished_at
created_at
updated_at
```

#### `audit_logs`

```text
id
actor_user_id
action
entity_type
entity_id
before_json
after_json
created_at
```

### 21.8.6 Provider Run and Metric Tables

#### `provider_runs`

Stores external crawler or extraction provider executions.

```text
id
provider                    -- apify, firecrawl, x_api, github, rss, custom
provider_resource_type       -- actor, task, endpoint, crawl, scrape, batch
provider_resource_id         -- actor id, task id, endpoint name, etc.
provider_run_id
provider_dataset_id
source_id
job_run_id
status                      -- queued, running, success, partial_success, failed, rate_limited, cancelled
request_json
response_metadata_json
raw_payload_object_key
cost_estimate
started_at
finished_at
created_at
updated_at
```

#### `engagement_snapshots`

Stores time-based engagement metrics for velocity scoring.

```text
id
raw_post_id
provider
metrics_json                 -- normalized nullable metrics
source_metric_names_json      -- provider field mapping
captured_at
created_at
```

#### `news_eval_items`

Stores human labels for scoring calibration.

```text
id
raw_post_id
extracted_article_id
news_item_id
human_label                  -- accept, reject_low_relevance, reject_spam, reject_duplicate, needs_review
human_relevance_score
human_quality_score
human_spam_judgment
human_duplicate_judgment
label_notes
labeled_by
created_at
```

#### `scoring_experiments`

Stores evaluation runs for prompt and scoring configuration changes.

```text
id
prompt_version_id
scoring_config_version
sample_size
candidate_precision
valuable_item_false_reject_rate
spam_false_negative_rate
duplicate_accuracy
human_agreement_rate
average_latency_ms
average_cost_per_item
created_at
```

#### `blog_claims`

Stores claim-level evidence for public blog quality control.

```text
id
blog_draft_id
claim_text
claim_type                  -- performance, architecture, client_outcome, benchmark, opinion, product_capability
evidence_source_type         -- internal_doc, measurement, public_url, reviewer_note, none
evidence_reference
risk_level                  -- low, medium, high
approval_status             -- pending, approved, rejected, rewritten
reviewer_user_id
created_at
updated_at
```

### 21.8.7 Required Constraints and Indexes

Implementation must include database constraints and indexes that protect idempotency, performance, and public content safety.

Required uniqueness constraints:

```text
users.email
projects.slug
showcases.slug
blog_drafts.slug
news_sources(source_type, url_or_identifier)
raw_posts(source_id, external_id)
extracted_articles.canonical_url
news_items.slug
content_embeddings(entity_type, entity_id, embedding_model)
prompts.name
prompt_versions(prompt_id, version_number)
```

Required indexes:

```text
blog_drafts(status, published_at)
projects(status, confidentiality_level)
showcases(status, published_at)
news_sources(is_enabled, priority)
raw_posts(processing_status, posted_at)
raw_posts(source_type, posted_at)
extracted_articles(content_hash)
news_items(status, published_at)
news_items(final_score)
news_items(duplicate_group_id)
job_runs(status, job_type, created_at)
audit_logs(entity_type, entity_id, created_at)
provider_runs(provider, status, created_at)
engagement_snapshots(raw_post_id, captured_at)
news_eval_items(human_label, created_at)
```

Vector index requirements:

- Use pgvector cosine distance for text embedding similarity unless a future decision changes the metric.
- Create a vector index for the exact embedding model and dimensions used in production.
- HNSW is preferred for frequently queried, incrementally updated similarity search if memory is acceptable.
- IVFFlat is acceptable for batch-loaded datasets but should be created after enough data exists.
- Exact similarity can be used first during MVP if dataset size is small; approximate index tuning should be benchmarked before launch at larger scale.

Data integrity rules:

- `raw_posts.external_id` may be null only for sources that cannot provide stable ids; in that case a deterministic content/source hash must be stored and made unique per source.
- `news_items.status = published` requires `published_at`.
- Published blog drafts and news items must have unique slugs.
- Restricted project content must not be linked to public blog output unless explicitly approved.
- Deleting source data should be soft-delete or archive by default to preserve auditability.

---

## 21.9 News Processing Architecture

### 21.9.1 End-to-End News Pipeline

```text
Scheduled Crawl Job
  ↓
Fetch Source Items
  ↓
Normalize Raw Posts
  ↓
Store Raw Payload
  ↓
Extract Linked Articles
  ↓
Canonicalize URLs
  ↓
Generate Content Hash
  ↓
Generate Embeddings
  ↓
Run Duplicate Detection
  ↓
Run AI Scoring
  ↓
Generate Summary + Why It Matters
  ↓
Apply Auto-Reject Rules
  ↓
Send to Review Queue
  ↓
Human Approves
  ↓
Publish to AI News Page
```

### 21.9.2 Auto-Reject Rules

A news item should be auto-rejected before human review if:

```text
spam_risk_score >= 0.70
relevance_score < 0.45
quality_score < 0.40
is_exact_duplicate = true
source_is_blocked = true
content_language_not_supported = true
```

A news item should go to review if:

```text
relevance_score >= 0.70
quality_score >= 0.65
spam_risk_score < 0.45
is_duplicate = false
```

A news item can be auto-approved later, after enough confidence is gained, if:

```text
final_score >= 0.85
source_credibility_score >= 0.80
spam_risk_score < 0.25
relevance_score >= 0.80
quality_score >= 0.75
```

For MVP, auto-approve should be disabled. Human approval is required.

---

## 21.10 Blog Agent Architecture

### 21.10.1 End-to-End Blog Pipeline

```text
Manual Idea / Internal Project / News Trend
  ↓
Idea Enrichment
  ↓
Knowledge Collection
  ↓
Outline Generation
  ↓
Human Outline Review
  ↓
Draft Generation
  ↓
Technical AI Review
  ↓
Human Technical Review
  ↓
Marketing AI Review
  ↓
Human Marketing Review
  ↓
Approval
  ↓
Publishing
  ↓
Social Snippet Generation
```

### 21.10.2 Blog Agent Inputs

Possible inputs:

- Manual notes.
- Internal project summary.
- Showcase record.
- GitHub README or changelog.
- Product requirement document.
- Meeting transcript.
- AI News trends.
- User-selected source links.

### 21.10.3 Blog Agent Outputs

Expected outputs:

```text
Blog idea
Blog angle
Target reader
Outline
Draft markdown
Technical review report
Marketing review report
SEO title
SEO description
Excerpt
LinkedIn post
X/Twitter post
Suggested hero image prompt
Suggested internal links
Suggested CTA
```

---

## 21.11 AI Scoring and Evaluation Architecture

AI scoring should use structured output. Every scoring prompt should return JSON that matches a Pydantic schema.

### 21.11.1 Example News Score Schema

```python
from pydantic import BaseModel, Field
from typing import List

class NewsScore(BaseModel):
    relevance_score: float = Field(ge=0, le=1)
    quality_score: float = Field(ge=0, le=1)
    novelty_score: float = Field(ge=0, le=1)
    technical_depth_score: float = Field(ge=0, le=1)
    spam_risk_score: float = Field(ge=0, le=1)
    topics: List[str]
    summary: str
    why_it_matters: str
    reasons: List[str]
    risks: List[str]
```

### 21.11.2 Example Blog Review Schema

```python
from pydantic import BaseModel, Field
from typing import List

class ClaimRisk(BaseModel):
    claim: str
    risk_level: str
    reason: str
    suggested_rewrite: str

class BlogTechnicalReview(BaseModel):
    technical_accuracy_score: float = Field(ge=0, le=1)
    claim_risk_score: float = Field(ge=0, le=1)
    clarity_score: float = Field(ge=0, le=1)
    unsupported_claims: List[ClaimRisk]
    missing_context: List[str]
    recommended_changes: List[str]
    approval_recommendation: str
```

### 21.11.3 Prompt Versioning Requirement

Every AI-generated output should store:

- Prompt name.
- Prompt version.
- Model provider.
- Model name.
- Input payload.
- Output payload.
- Parsed JSON.
- Validation result.
- Token usage.
- Timestamp.

This is important because the system itself is an AI showcase. The team should be able to explain and debug why a piece of content was approved or rejected.

---

## 21.12 Deduplication Architecture

Deduplication should combine deterministic and semantic methods.

### 21.12.1 Dedup Layers

| Layer | Method | Use Case |
|---|---|---|
| Exact URL | Canonical URL match | Same article shared many times. |
| Content hash | Hash normalized text | Same article with tracking params removed. |
| Text similarity | Embedding cosine similarity | Similar posts with rewritten text. |
| Event-level AI classification | LLM groups same event | Different sources discussing the same model release or research update. |

### 21.12.2 Suggested Similarity Thresholds

```text
cosine_similarity >= 0.95 → near-exact duplicate
cosine_similarity >= 0.88 → likely duplicate
cosine_similarity >= 0.78 → possible same topic, needs AI event grouping
```

### 21.12.3 Canonicalization Rules

Before storing URLs, the system should:

- Remove UTM parameters.
- Normalize trailing slashes.
- Resolve redirects when possible.
- Convert mobile URLs to canonical desktop URLs where possible.
- Lowercase hostnames.
- Preserve path case only when required.

---

## 21.13 Crawl Scheduling Architecture

### 21.13.1 Crawl Frequency by Source Type

| Source Type | Suggested Frequency | Notes |
|---|---:|---|
| High-priority X/Twitter accounts | 5–15 minutes | Only for selected accounts. |
| X/Twitter keyword search | 15–30 minutes | Use cautiously due to noise and cost. |
| Official AI blogs / RSS | 30–60 minutes | Low cost, high reliability. |
| GitHub releases | 1–3 hours | Useful for model/tool releases. |
| Hacker News / Reddit | 30–60 minutes | Needs strong spam/noise filtering. |
| Arxiv / Papers | 6–12 hours | Less frequent but high-value. |
| User-submitted links | Near realtime | Process after submission. |

### 21.13.2 Crawl Backoff

The system should automatically back off when:

- A source returns rate-limit errors.
- A crawler fails repeatedly.
- The source has not produced new content for multiple runs.
- The source is low priority.

### 21.13.3 Crawl Job States

```text
scheduled
queued
running
success
partial_success
failed
retrying
disabled
```

---

## 21.14 Caching and Performance

### 21.14.1 Public Page Caching

Public pages should be cache-friendly:

- Blog listing can be statically generated or ISR-based.
- Blog detail pages can be statically generated after publishing.
- AI News listing can use server-side rendering with short cache TTL.
- AI News detail pages can be cached after publishing.

Recommended cache behavior:

| Page | Cache Strategy |
|---|---|
| `/` | Static / ISR |
| `/lab` | Static / ISR |
| `/showcases` | Static / ISR |
| `/showcases/[slug]` | Static / ISR |
| `/blog` | ISR |
| `/blog/[slug]` | Static after publish |
| `/ai-news` | SSR or ISR with 1–5 min TTL |
| `/ai-news/[slug]` | Static after publish |

### 21.14.2 API Caching

Use Redis for:

- Source configuration cache.
- Topic configuration cache.
- Public news feed cache.
- Public blog listing cache.
- Rate limiting.
- Idempotency keys for user-submitted links.

---

## 21.15 Observability and Monitoring

The system should track both traditional software metrics and AI workflow metrics.

### 21.15.1 Application Monitoring

Recommended tools:

- Sentry for exceptions.
- OpenTelemetry for traces.
- Structured JSON logs.
- Provider logs from deployment platform.

Track:

- API latency.
- API error rate.
- Worker job failure rate.
- Queue depth.
- Database query latency.
- Redis latency.
- Crawl success/failure rate.

### 21.15.2 AI Monitoring

Track:

- Model provider.
- Model name.
- Prompt version.
- Token usage.
- Estimated cost.
- Latency.
- JSON validation failure rate.
- Retry count.
- Average quality score.
- Average spam risk score.
- Accepted/rejected item ratio.
- Human override rate.

### 21.15.3 Content Quality Monitoring

Track:

- Number of blog ideas generated.
- Number of blog drafts created.
- Number of drafts approved.
- Number of drafts rejected.
- Time from idea to publish.
- Number of news items crawled.
- Number of news items published.
- Duplicate rate.
- Top topics.
- Top sources.

---

## 21.16 Security Architecture

### 21.16.1 API Security

Requirements:

- All admin APIs require authentication.
- Role-based authorization is required for publish actions.
- Sensitive routes must have audit logs.
- API keys must never be exposed to the frontend.
- User-submitted links must be validated and rate-limited.
- SSRF protection is required for URL fetching.

### 21.16.2 SSRF Protection for Crawling

When fetching user-submitted URLs or crawled URLs, the system must block:

- Private IP ranges.
- Localhost.
- Metadata service IPs.
- Internal network hostnames.
- Non-HTTP/HTTPS schemes.

Required SSRF controls:

- Parse URLs with a trusted URL parser; do not use regex-only URL validation.
- Allow only `http` and `https` schemes.
- Resolve DNS before fetching and block private, loopback, link-local, multicast, reserved, and metadata service IP ranges.
- Re-check DNS/IP after redirects and block if the final target is unsafe.
- Limit redirects and consider disabling redirects for high-risk sources.
- Enforce request timeout, connect timeout, maximum response size, and allowed content types.
- Do not fetch from localhost, internal hostnames, internal service discovery domains, or cloud metadata endpoints.
- Do not forward admin cookies, internal auth headers, or secrets to fetched URLs.
- Do not return raw fetched responses directly to users.
- Log accepted and blocked fetch decisions with normalized URL, resolved IP, reason, and job id.
- Prefer network egress restrictions or proxy-level allow/deny rules in production.

### 21.16.3 Secret Management

Secrets should be stored in:

- Deployment platform secret manager.
- Cloud provider secret manager.
- `.env` only for local development.

Secrets include:

- LLM API keys.
- Apify token.
- Firecrawl API key.
- Database URL.
- Redis URL.
- Object storage credentials.
- Auth secrets.

---

## 21.17 Configuration Management

The following values should be configurable without code changes:

- Crawl frequency per source.
- Source enabled/disabled status.
- Scoring thresholds.
- Topic priority.
- Blocked keywords.
- Blocked domains.
- Trusted domains.
- Prompt active version.
- Default LLM model per task.
- Auto-reject thresholds.
- Auto-approve thresholds.
- Provider rate-limit settings.
- Provider daily and monthly budget limits.
- Retry count and backoff settings per provider/task type.
- SSRF fetch limits such as timeout, max redirects, max response size, and allowed content types.
- Evaluation gates for enabling auto-reject or auto-approve.

Configuration can be stored in PostgreSQL and cached in Redis.

Configuration changes that affect crawling, scoring, auto-reject, auto-approve, authentication, authorization, or public publishing must be audit logged.

---

## 21.18 Local Development Setup

Recommended local services:

```text
Docker Compose
  - frontend
  - backend
  - worker
  - scheduler
  - postgres
  - redis
  - minio optional, for S3-compatible local storage
```

Example local commands:

```bash
# Backend
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# Worker
uv run celery -A app.core.celery_app worker --loglevel=info

# Scheduler
uv run celery -A app.core.celery_app beat --loglevel=info

# Frontend
cd frontend
pnpm install
pnpm dev
```

`uv` is recommended for Python dependency management, but Poetry or pip-tools are also acceptable.

---

## 21.19 CI/CD Requirements

Minimum CI checks:

- Backend lint.
- Backend type check if using mypy/pyright.
- Backend unit tests.
- Backend migration check.
- Frontend lint.
- Frontend type check.
- Frontend build.
- Docker build.

Recommended deployment flow:

```text
Pull Request
  ↓
CI checks
  ↓
Review
  ↓
Merge to main
  ↓
Build Docker images
  ↓
Run migrations
  ↓
Deploy backend + workers
  ↓
Deploy frontend
  ↓
Smoke test
```

---

## 21.20 Architecture Decisions for MVP

### Decision 1: Use Python FastAPI for API

Reason:

- Strong fit for AI workflows.
- Good async support.
- Excellent Pydantic integration.
- Easy integration with LLM SDKs, embeddings, crawlers, and data processing.
- Auto-generated OpenAPI docs.

### Decision 2: Use PostgreSQL + pgvector

Reason:

- One primary database can support relational content data and embedding search.
- Good enough for MVP semantic deduplication.
- Avoids adding a separate vector database too early.

### Decision 3: Use Celery + Redis for Workers

Reason:

- Mature Python ecosystem.
- Works well with FastAPI architecture.
- Supports retries and queue separation.
- Simple enough for MVP.

### Decision 4: Human Approval Required for Public Publishing

Reason:

- Reduces brand risk.
- Prevents accidental publication of wrong or confidential information.
- Ensures content quality while the system is still learning.

### Decision 5: Store Prompt Versions and AI Runs

Reason:

- Needed for debugging.
- Needed for evaluation.
- Makes the system more credible as an AI Lab showcase.

### Decision 6: Start AI News with Official Sources Before X/Twitter

Reason:

- Official blogs, RSS feeds, GitHub releases, and selected websites are lower-risk and easier to validate.
- X/Twitter has higher provider, rate-limit, metric-availability, and noise risk.
- The first AI News slice should prove extraction, scoring, deduplication, and review before adding social ingestion complexity.

### Decision 7: Use Firecrawl for Article Extraction, Not as the System of Record

Reason:

- Firecrawl is useful for turning web pages into markdown or structured data.
- The portal must still store normalized article metadata, extracted content, raw payload references, and extraction status in its own database.
- Firecrawl outputs are external provider responses and must be validated before use.

### Decision 8: Use Apify Only Behind Explicit Actor/Task Contracts

Reason:

- Apify actor outputs vary by actor and can change over time.
- Every Apify integration must declare actor/task id, input schema, output normalization schema, dataset handling, retry behavior, and cost/rate expectations.
- This keeps X/Twitter or other social crawlers replaceable.

### Decision 9: Use Human-Labeled Eval Data Before Strong Automation

Reason:

- AI scoring is probabilistic and must be calibrated against company-specific taste and relevance.
- Auto-approve can create brand risk and is not allowed in MVP.
- Auto-reject beyond exact duplicates should be gated by human-labeled evaluation data.

### Decision 10: Treat User-Submitted URLs and Crawled URLs as SSRF Risk

Reason:

- URL fetching can reach internal networks if not controlled.
- The crawler must validate schemes, DNS/IP resolution, redirects, response limits, and network egress.
- Fetching must run in workers, not inline in public request handlers.

### Decision 11: Use Google Workspace OAuth or FastAPI-Managed Secure Sessions for MVP Auth

Reason:

- The admin dashboard is internal and does not need complex enterprise user management in MVP.
- If the company uses Google Workspace, Google OAuth plus backend role mapping is preferred.
- Otherwise, FastAPI-managed secure HTTP-only sessions are acceptable.
- The final auth choice must be made before implementing admin routes because it affects API security, frontend session handling, and deployment configuration.

---

# 22. AI Lab Capability Map

The company should repeatedly use a simple framework to explain its AI Lab approach.

## 22.1 Framework

```text
1. Discover
   Understand business workflow and AI opportunity.

2. Prototype
   Build fast AI proof-of-concept.

3. Evaluate
   Measure output quality, safety, and reliability.

4. Integrate
   Connect AI into existing systems.

5. Operate
   Monitor, improve, and iterate after launch.
```

## 22.2 Usage

This framework should appear in:

- `/lab` page.
- Sales deck.
- Blog posts.
- Showcase pages.
- Client proposals.

---

# 23. Content Strategy

## 23.1 Publishing Cadence

Target:

- 1–2 blog posts per month.
- AI News page updated continuously based on crawl schedule and review rules.

## 23.2 Six-Month Blog Plan

### Month 1

1. From Offshore Development to AI/LLM Lab: Why We Are Repositioning
2. Building Scopelytics: Turning Business Inputs into AI-Powered Analysis

### Month 2

3. How We Applied AI Evaluation to Improve Scopelytics Output Quality
4. Designing Human-in-the-Loop Review for AI Products

### Month 3

5. Building a Voice-First AI Interview System with LLM, STT, and TTS
6. What We Learned About AI Scoring and Candidate Evaluation

### Month 4

7. How We Built an AI News Intelligence Pipeline
8. Deduplication and Quality Filtering for AI News Crawling

### Month 5

9. Practical RAG Lessons from Internal AI Product Development
10. How We Think About AI Reliability Before Shipping to Clients

### Month 6

11. Building AI Agents for Internal Research and Content Operations
12. Our AI Lab Playbook: From Idea to Prototype to Production

---

# 24. MVP Roadmap

The MVP roadmap is intentionally split into implementation slices. Each slice should be independently shippable and verifiable.

## 24.1 MVP 0: Foundation

### Objective

Create the application foundation needed for later product slices.

### Features

- Next.js public/admin frontend shell.
- FastAPI backend with health endpoint and OpenAPI documentation.
- PostgreSQL connection and Alembic migration setup.
- Redis connection.
- Celery worker and scheduler setup.
- Basic structured JSON logging.
- Environment configuration validation.
- Docker Compose for local development.

### Success Criteria

- Backend health endpoint returns success.
- Frontend dev server renders the base shell.
- Database migrations run from empty database.
- Worker can execute a smoke-test job.
- Secrets are loaded from environment variables and never committed.

---

## 24.2 MVP 1: Manual AI Lab CMS and Public Pages

### Objective

Launch a credible AI Lab web presence before adding AI automation.

### Features

- `/lab` public page.
- `/showcases` and showcase detail pages.
- `/blog` and blog detail pages.
- Admin CRUD for projects, showcases, and blog posts.
- Manual publish/unpublish workflow.
- Basic tags and SEO metadata.
- Public page caching strategy.

### Deliverables

```text
/lab
/showcases
/showcases/scopelytics
/showcases/ai-interview-system
/blog
/blog/how-we-built-scopelytics
/blog/ai-evaluation-framework-for-scopelytics
```

### Success Criteria

- At least 2 public AI Lab articles are published manually.
- At least 2 showcases are published.
- Public users can view only published content.
- Admin publish/unpublish actions are authenticated and audit logged.
- Public pages build or render with the selected caching strategy.

---

## 24.3 MVP 2: AI-Assisted Blog Workflow

### Objective

Add AI assistance to the editorial workflow while keeping humans in control.

### Features

- Blog idea creation.
- AI outline generation with structured output.
- AI draft generation from approved context.
- Technical review agent.
- Marketing review agent.
- Claim extraction and claim evidence ledger.
- Human review and approval workflow.
- Prompt version and AI run tracking.

### Success Criteria

- AI can generate an outline from an approved idea and context.
- AI can generate a markdown draft from an approved outline.
- Technical review identifies unsupported or risky claims.
- Quantified claims require evidence before publishing.
- Human approval is required before public publication.
- Every important AI call stores prompt version, model, input, raw output, parsed output, validation status, token usage, latency, and cost estimate.

---

## 24.4 MVP 3: AI News Ingestion from Official Sources

### Objective

Prove the AI News pipeline with lower-risk sources before adding X/Twitter.

### Features

- Source management for RSS, official blogs, GitHub releases, and selected websites.
- Scheduled crawling.
- Raw post storage.
- Firecrawl extraction for linked articles and web pages.
- URL canonicalization and content hashing.
- URL-level and content-hash deduplication.
- AI relevance, quality, novelty, technical depth, business value, and spam scoring.
- AI summary and “why it matters”.
- Candidate review queue.
- Public `/ai-news` page.

### Success Criteria

- Admin can configure and enable/disable official sources.
- Scheduled jobs fetch and store raw source items.
- Linked articles are extracted asynchronously and safely.
- High-quality candidates appear in a review queue.
- Admin can approve/reject candidates.
- Published AI news appears on `/ai-news`.
- Duplicate exact URLs and identical content hashes are grouped or suppressed.
- Auto-approve remains disabled.

---

## 24.5 MVP 4: User-Submitted Links

### Objective

Allow internal team members or public users to submit AI-related links safely.

### Features

- Public `/ai-news/submit` form.
- URL validation and rate limiting.
- SSRF-protected asynchronous fetching.
- Duplicate detection against existing articles/news items.
- AI review output.
- Human approval before publish.

### Success Criteria

- User-submitted links create reviewable records.
- Unsafe URLs are blocked and logged.
- Duplicate submissions are detected idempotently.
- Submitted links do not appear publicly until approved.

---

## 24.6 MVP 5: X/Twitter Intelligence

### Objective

Add high-signal X/Twitter intelligence after the core pipeline is proven.

### Features

- Provider strategy selection: official X API, Apify actor, or hybrid.
- Source account and keyword query configuration.
- Engagement metric normalization with nullable fields.
- Engagement snapshots and velocity scoring.
- Provider run tracking.
- Provider rate-limit, cost, and backoff handling.
- Social duplicate grouping.

### Success Criteria

- Selected provider strategy is configured and documented in the spec or a decision record.
- Provider runs store run ids, dataset ids where applicable, raw payload references, status, and cost estimate.
- Missing metrics do not break scoring.
- Crawl frequency respects provider rate limits and budget.
- X/Twitter items enter the same review queue as other sources.

---

## 24.7 Post-MVP: Full AI Intelligence Engine

### Objective

Turn the platform into a deeper internal intelligence and content generation system.

### Features

- Trending topic detection.
- Topic clustering.
- Source credibility learning from historical acceptance rate.
- Auto weekly AI digest.
- Auto blog idea generation from news trends.
- Auto LinkedIn/X post generation from published blogs.
- Analytics dashboard.
- Newsletter support.
- Better event-level deduplication.

### Success Criteria

- The system identifies important AI trends.
- Blog ideas are generated from news trends.
- Weekly digest can be produced automatically.
- Sales and marketing teams can use the content in outreach.

---

# 25. Acceptance Criteria

## 25.0 Global Implementation Acceptance Criteria

The system is considered implementation-ready when every implemented slice satisfies:

- Public routes expose only published content.
- Admin routes require authentication.
- Role-based authorization protects publish, approve, reject, source settings, prompt settings, scoring settings, and user management actions.
- List APIs are paginated.
- API errors follow the standard error envelope.
- External provider responses are validated before normalization.
- Raw external payloads are stored or referenced before processing.
- Long-running work returns job ids and runs asynchronously.
- Important mutations create audit logs.
- Secrets are never exposed to frontend code or logs.
- Tests cover the implemented success criteria for the slice.

## 25.1 Blog MVP Acceptance Criteria

The Blog MVP is considered complete when:

- Admin can create a blog idea.
- AI can generate an outline from a blog idea.
- AI can generate a draft from an outline.
- AI can run a technical review.
- AI can generate marketing metadata.
- Human can approve and publish a post.
- Public users can view blog list and blog detail pages.
- Blog posts support tags, excerpt, author, and publish date.
- Blog generation uses approved context only.
- Quantified claims are extracted into the claim ledger.
- Unsupported claims are blocked, rewritten, or explicitly approved before publishing.
- Every important AI blog call stores prompt version and AI run metadata.

## 25.2 AI News MVP Acceptance Criteria

The AI News MVP is considered complete when:

- Admin can configure news sources.
- Scheduled crawler can fetch raw posts.
- System stores raw crawled data.
- System extracts linked article content.
- System scores relevance, quality, novelty, and spam risk.
- System detects URL-level duplicates.
- System detects embedding-level near duplicates.
- High-quality candidates appear in review queue.
- Admin can approve/reject candidates.
- Published news appears on `/ai-news`.
- Public users can filter news by topic.
- Users can submit links.
- Source crawls respect configured intervals, provider limits, and backoff settings.
- Firecrawl extraction runs asynchronously and stores extraction metadata.
- Engagement metrics are nullable and captured with timestamps.
- Provider run records exist for provider-backed crawls/extractions.
- AI scoring stores prompt version, raw output, parsed output, validation status, latency, token usage, and cost estimate.
- Auto-approve is disabled.
- Auto-reject beyond exact duplicates is not enabled until the evaluation gate is met.
- SSRF protections are enforced for submitted and crawled URLs.

## 25.3 Showcase Acceptance Criteria

The showcase module is considered complete when:

- Admin can create and edit showcase pages.
- Public users can view showcase list and detail pages.
- Showcase pages display AI capabilities and business value.
- Blog posts can link to showcases.
- Restricted projects cannot be published as showcases without explicit approval.
- Showcase slugs are unique.

## 25.4 Evaluation Acceptance Criteria

The AI scoring system is considered safe for MVP review usage when:

- Scoring outputs pass structured-output validation.
- Human reviewers can see score reasons and source evidence.
- Human accept/reject/duplicate labels can be stored.
- Prompt versions and scoring configuration versions can be compared.
- False positives, false rejects, and human override rate can be measured.

The system is not considered safe for auto-approval until the post-MVP evaluation gate is satisfied.

---

# 26. Risks and Mitigations

## 26.1 Risk: AI Generates Generic Content

### Problem

AI-generated blog posts may become generic and fail to show real expertise.

### Mitigation

- Require project-specific input.
- Use human review.
- Use technical reviewer agent.
- Prefer case studies over generic thought leadership.

## 26.2 Risk: Unsupported Marketing Claims

### Problem

The blog may claim measurable business impact without data.

### Mitigation

- Technical reviewer flags unsupported claims.
- Require evidence for numbers.
- Use conservative wording when data is unavailable.

## 26.3 Risk: News Feed Becomes Noisy

### Problem

Crawled news may contain spam, duplicate posts, or low-value AI hype.

### Mitigation

- Use multi-layer scoring.
- Use duplicate detection.
- Maintain high-quality source lists.
- Require human approval in MVP.

## 26.4 Risk: Crawling Cost and Rate Limits

### Problem

Frequent crawling can increase cost and hit rate limits.

### Mitigation

- Use different crawl frequencies by source priority.
- Cache results.
- Store raw posts.
- Avoid unnecessary recrawls.

## 26.5 Risk: Confidential Information Leakage

### Problem

Internal project information may accidentally appear in public blog content.

### Mitigation

- Use confidentiality level on projects.
- Require human approval.
- Add sensitive information checker.
- Avoid using restricted internal docs directly in public output.

## 26.6 Risk: SSRF Through Crawled or Submitted URLs

### Problem

The system fetches URLs from external posts and user submissions. Unsafe URL fetching could access localhost, private networks, or cloud metadata services.

### Mitigation

- Enforce the SSRF controls in section 21.16.2.
- Fetch URLs only from worker jobs with strict timeout and response size limits.
- Block private, loopback, link-local, reserved, and metadata IP ranges before and after redirects.
- Log blocked fetches for review.
- Prefer network egress controls in production.

## 26.7 Risk: Provider Lock-In or Provider Output Drift

### Problem

Apify actors, Firecrawl extraction output, X API fields, and other provider responses may change or fail, breaking ingestion or scoring.

### Mitigation

- Isolate providers behind adapters.
- Validate provider payloads before normalization.
- Store raw payload references for debugging.
- Track provider runs and failure rates.
- Keep source-specific normalization tests.
- Design normalized fields to allow nullable metrics.

## 26.8 Risk: AI Scoring Rejects Valuable Content

### Problem

Over-aggressive spam, relevance, or duplicate filters may hide useful AI news from reviewers.

### Mitigation

- Keep auto-approve disabled in MVP.
- Gate auto-reject with human-labeled evaluation data.
- Track false-reject rate and human overrides.
- Send borderline items to `Needs Review` rather than rejecting them.
- Preserve rejected items for audit and recovery.

## 26.9 Risk: Prompt Injection from Crawled Content

### Problem

Crawled pages, social posts, and submitted links may contain instructions that try to manipulate AI scoring or blog generation prompts.

### Mitigation

- Treat crawled and submitted content as data, not instructions.
- Include prompt-level instruction hierarchy and injection warnings.
- Use structured outputs and schema validation.
- Do not allow model output to directly execute tools, publish content, or change settings.
- Require human approval for public publication.

---

# 27. Future Enhancements

Potential future features:

- AI newsletter generator.
- Sales email generator based on blog/showcase content.
- Client-specific AI trend briefings.
- Competitor monitoring.
- AI product opportunity detector.
- Internal AI knowledge base.
- Slack integration for AI news alerts.
- CRM integration.
- Advanced analytics for content performance.
- Multi-language blog support.
- Auto-generate presentation decks from blog posts and showcases.

---

# 28. Research-Backed Implementation References

The following official or authoritative documentation informed the implementation requirements in this specification:

- Firecrawl documentation for scraping, crawling, batch extraction, markdown extraction, cache age, and structured extraction: `https://docs.firecrawl.dev/`
- Apify API documentation for actors, runs, datasets, schedules, pagination, authentication, and rate-limit handling: `https://docs.apify.com/api/v2`
- X API documentation for recent search, fields, metrics, expansions, and rate limits: `https://docs.x.com/x-api/`
- OpenAI API documentation for Structured Outputs, Evals, graders, and evaluation best practices: `https://developers.openai.com/`
- FastAPI documentation for OpenAPI docs, validation patterns, security, and background-task caveats: `https://fastapi.tiangolo.com/`
- Celery documentation for distributed task queues, workers, retries, rate limits, time limits, and periodic tasks: `https://docs.celeryq.dev/`
- pgvector documentation for vector storage, cosine distance, HNSW, IVFFlat, and indexing tradeoffs: `https://github.com/pgvector/pgvector`
- Next.js documentation for ISR, static rendering, revalidation, caching behavior, and platform caveats: `https://nextjs.org/docs`
- OWASP SSRF Prevention Cheat Sheet and OWASP Top 10 SSRF guidance for URL-fetching security: `https://cheatsheetseries.owasp.org/` and `https://owasp.org/Top10/`

Implementation should re-check the exact provider and framework documentation when versions, plans, or selected providers are finalized.

---

# 29. Summary

The AI Lab Portal is both a marketing asset and an internal AI capability showcase.

It has two major modules:

1. **AI Blog Agent**
   - Converts internal project knowledge and AI experience into high-quality public blog posts.
   - Supports idea, outline, draft, review, and publish workflow.
   - Helps the company publish 1–2 strong AI-related posts per month.

2. **AI News Intelligence Feed**
   - Crawls AI-related sources.
   - Filters content using relevance, quality, novelty, engagement, credibility, and spam detection.
   - Removes duplicates.
   - Publishes a curated AI news page.
   - Feeds market trends back into the blog idea generation workflow.

Together, these modules help the company shift perception from an offshore IT vendor to a practical AI/LLM Lab with real product development, AI evaluation, and intelligent automation capabilities.
