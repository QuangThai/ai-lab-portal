"""Admin seed endpoint — seed demo content from the admin UI.

Idempotent: skips content that already exists by slug/ID.
Uses direct SQLAlchemy inserts matching the existing seed script pattern.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import insert, select

from backend.app.database import (
    blog_posts,
    blog_tags,
    create_database_engine,
    news_extracted_articles,
    news_raw_items,
    news_review_items,
    news_sources,
    projects,
    showcases,
)
from backend.app.settings import Settings

# ── Seed data ──────────────────────────────────────────────────

SEED_BLOG_POSTS: list[dict[str, Any]] = [
    {
        "slug": "apply-ai-agents-real-production-projects",
        "title": "How to Apply AI Agents to Real Production Projects",
        "excerpt": "A practical guide to moving AI agents from proof-of-concept to production — covering architecture decisions, observability, error handling, and the human-in-the-loop patterns that actually work.",
        "author_name": "AI Lab",
        "content_markdown": (
            "## Introduction\n\n"
            "AI agents have moved from research papers into the mainstream. "
            "Every engineering team I talk to is building something with agents — "
            "whether it is a coding assistant, a customer support bot, or an internal "
            "workflow automation.\n\n"
            "## Start with the Boundary, Not the Agent\n\n"
            "The most common mistake teams make is reaching for an agent framework "
            "before defining the system boundary. Before you write a single tool "
            "definition, answer these questions:\n\n"
            "- **What is the agent allowed to do?** Define the scope explicitly.\n"
            "- **What is the agent NOT allowed to do?** Destructive operations, "
            "billing actions, and user data exports should be gated behind human approval.\n"
            "- **What happens when the agent is uncertain?** A production agent must "
            "know when to ask for help rather than guess.\n\n"
            "## Human-in-the-Loop Patterns\n\n"
            "The most reliable production pattern is semi-autonomous operation with "
            "human escalation paths. Each approval gate serves as a quality checkpoint "
            "and an audit event.\n\n"
            "### Gate 1: Scope Approval\n"
            "Before an agent acts, a human defines and approves the task scope.\n\n"
            "### Gate 2: Output Review\n"
            "After the agent produces a result, a human reviews and approves before "
            "it reaches production.\n\n"
            "### Gate 3: Escalation\n"
            "When confidence is low, the agent pauses and requests human input."
        ),
    },
    {
        "slug": "production-patterns-multi-agent-systems",
        "title": "Production Patterns for Multi-Agent Systems",
        "excerpt": "Patterns and anti-patterns for building multi-agent systems that actually work in production — covering orchestration, handoffs, shared state, and observability.",
        "author_name": "AI Lab",
        "content_markdown": (
            "## Beyond Single Agents\n\n"
            "Single-agent systems are well understood. Multi-agent systems introduce "
            "a new class of challenges: coordination, shared state, handoff protocols, "
            "and failure propagation.\n\n"
            "## Orchestration Patterns\n\n"
            "### Supervisor Pattern\n"
            "A supervisor agent delegates subtasks to worker agents and aggregates results. "
            "Workers are stateless; the supervisor owns the workflow state.\n\n"
            "### Handoff Pattern\n"
            "Each agent owns a stage of the pipeline. When it completes, it hands "
            "context to the next agent via a structured handoff protocol.\n\n"
            "### Voting Pattern\n"
            "Multiple agents independently evaluate an input and vote on the outcome. "
            "Useful for validation, review, and consensus-building.\n\n"
            "## Observability is Not Optional\n"
            "Every agent invocation must produce a trace: input tokens, output tokens, "
            "latency, tool calls, handoff metadata, and error state. Without traces, "
            "multi-agent systems are impossible to debug."
        ),
    },
    {
        "slug": "building-reliable-ai-agent-pipelines",
        "title": "Building Reliable AI Agent Pipelines",
        "excerpt": "How to design AI agent pipelines that handle failures gracefully, maintain state across stages, and produce predictable, auditable outputs.",
        "author_name": "AI Lab",
        "content_markdown": (
            "## Pipeline Architecture\n\n"
            "An AI agent pipeline chains multiple stages, each producing structured "
            "output validated by schemas. The output of one stage becomes the context "
            "for the next.\n\n"
            "## Stage Design\n\n"
            "Each stage should:\n"
            "- Accept well-defined input schemas\n"
            "- Produce validated output\n"
            "- Handle failures without cascading\n"
            "- Log execution metadata\n\n"
            "## Failure Handling\n\n"
            "### Retry with Backoff\n"
            "Transient failures (network, rate limits) should retry with exponential backoff.\n\n"
            "### Graceful Degradation\n"
            "When a stage fails, the pipeline should produce a partial result rather "
            "than failing entirely.\n\n"
            "### Human Escalation\n"
            "When confidence is low or validation fails, the pipeline should pause "
            "and request human input.\n\n"
            "## Observability\n"
            "Each stage records: input tokens, output tokens, latency, status, and "
            "error message. Aggregated dashboards show pipeline health at a glance."
        ),
    },
    {
        "slug": "mcp-in-production-scaling-across-team",
        "title": "MCP in Production: Scaling Across Your Team",
        "excerpt": "How to design, deploy, and maintain MCP servers at team scale — covering server discovery, authentication, rate limiting, monitoring, and organizational patterns.",
        "author_name": "AI Lab",
        "content_markdown": (
            "## Beyond the First MCP\n\n"
            "Building your first MCP server is straightforward. Scaling MCP across "
            "a team of ten engineers with dozens of servers is a different challenge. "
            "This guide covers what happens after the prototype works.\n\n"
            "## Server Discovery\n\n"
            "As your MCP footprint grows, manual configuration becomes impossible. "
            "Implement a registry pattern where servers announce their capabilities "
            "to a central directory.\n\n"
            "## Authentication & Authorization\n\n"
            "Every MCP server must authenticate callers. Use API keys or OAuth2 "
            "and scope access to specific tools and resources.\n\n"
            "## Monitoring\n\n"
            "Each server should expose metrics: requests per second, error rates, "
            "latency percentiles. Aggregate these into a dashboard."
        ),
    },
    {
        "slug": "human-in-the-loop-ai-production",
        "title": "Human-in-the-Loop: When to Automate and When to Escalate",
        "excerpt": "A framework for deciding when AI systems should act autonomously versus when they should escalate to humans — with concrete patterns from production deployments.",
        "author_name": "AI Lab",
        "content_markdown": (
            "## The Automation Spectrum\n\n"
            "Not every decision should be automated. The key is knowing where "
            "on the autonomy spectrum each action falls.\n\n"
            "### Fully Automated\n"
            "Low-risk, high-confidence actions with clear success criteria. "
            "Examples: content formatting, spell checking, image compression.\n\n"
            "### Human Review\n"
            "Medium-risk actions where correctness matters but speed is still "
            "important. Examples: draft approval, metadata generation, SEO suggestions.\n\n"
            "### Human Decision\n"
            "High-risk actions with significant consequences. "
            "Examples: publishing content, deleting data, financial decisions.\n\n"
            "## Escalation Patterns\n\n"
            "### Confidence Threshold\n"
            "If model confidence is below a threshold, escalate automatically.\n\n"
            "### Edge Case Detection\n"
            "If input doesn't match known patterns, route to human.\n\n"
            "### Audit Trail\n"
            "Every escalation must produce a trace for review and learning."
        ),
    },
    {
        "slug": "building-ai-observability-dashboards",
        "title": "Building AI Observability Dashboards That Actually Help",
        "excerpt": "What to track, what to ignore, and how to build dashboards that help your team understand AI system behavior at a glance.",
        "author_name": "AI Lab",
        "content_markdown": (
            "## What Matters\n\n"
            "Most AI dashboards show too much. Focus on the metrics that "
            "directly impact user experience and operational health.\n\n"
            "### The Four Critical Metrics\n"
            "1. **Latency**: Time from request to response. P50, P95, P99.\n"
            "2. **Error Rate**: Percentage of requests that fail or produce "
            "unusable output.\n"
            "3. **Cost Per Request**: Token usage \xd7 model pricing.\n"
            "4. **Human Escalation Rate**: How often the system hands off to a human.\n\n"
            "## What to Ignore\n\n"
            "- Raw token counts without context\n"
            "- Per-prompt breakdowns (aggregate instead)\n"
            "- Dashboard metrics that nobody looks at\n\n"
            "## Build for Action\n\n"
            "Every metric on your dashboard should answer a yes/no question: "
            '"Is this healthy?" If you can\'t answer that, remove the metric.'
        ),
    },
]

SEED_SHOWCASES: list[dict[str, Any]] = [
    {
        "slug": "scopelytics",
        "title": "Scopelytics \u2014 AI-Powered Game Analytics",
        "description": "AI-powered analytics platform for game studios. Provides player segmentation, churn prediction, and actionable insights for game publishers.",
        "industry": "Gaming",
        "use_case": "Player analytics and churn prediction",
        "content_markdown": (
            "## The Challenge\n\n"
            "Game studios generate massive amounts of player data but struggle to "
            "extract actionable insights. Traditional analytics tools require manual "
            "query writing and lack predictive capabilities.\n\n"
            "## The Solution\n\n"
            "Scopelytics uses machine learning to automatically segment players, "
            "predict churn risk, and generate plain-language insights. The platform "
            "ingests game telemetry in real-time and produces actionable recommendations "
            "without requiring a data science team.\n\n"
            "### Key Results\n"
            "- 40% faster churn identification\n"
            "- 25% improvement in player retention campaigns\n"
            "- Zero manual reporting overhead\n\n"
            "## Tech Stack\n"
            "Python/FastAPI, scikit-learn, XGBoost, PostgreSQL, React/TypeScript"
        ),
    },
    {
        "slug": "ai-interview-system",
        "title": "AI-Powered Technical Interview System",
        "description": "An automated technical interview platform that uses AI to generate adaptive questions, evaluate responses, and provide detailed candidate reports.",
        "industry": "HR Technology",
        "use_case": "Automated technical assessments",
        "content_markdown": (
            "## The Challenge\n\n"
            "Technical screening at scale is time-consuming and inconsistent. "
            "Different interviewers ask different questions, evaluations are subjective, "
            "and scheduling multiple rounds delays hiring.\n\n"
            "## The Solution\n\n"
            "An AI-powered interview system that generates adaptive technical questions "
            "based on role requirements, evaluates candidate responses against rubrics, "
            "and produces structured reports. The system learns from each interview "
            "to improve question quality over time.\n\n"
            "### Key Results\n"
            "- 60% reduction in time-to-hire\n"
            "- 95% candidate satisfaction score\n"
            "- Consistent evaluation across all candidates\n\n"
            "## Tech Stack\n"
            "Python/FastAPI, OpenAI GPT, PostgreSQL, React/Next.js, Docker"
        ),
    },
    {
        "slug": "ai-document-processing",
        "title": "Intelligent Document Processing Pipeline",
        "description": "An end-to-end document processing pipeline that extracts, classifies, and validates information from unstructured documents using computer vision and LLMs.",
        "industry": "Financial Services",
        "use_case": "Document automation and data extraction",
        "content_markdown": (
            "## The Challenge\n\n"
            "A financial services firm processed thousands of documents daily \u2014 "
            "invoices, contracts, and compliance forms \u2014 all manually. Processing "
            "was slow, error-prone, and expensive.\n\n"
            "## The Solution\n\n"
            "An intelligent document processing pipeline that combines OCR, computer "
            "vision, and LLM-based extraction to automatically classify documents, "
            "extract structured data, and validate against business rules.\n\n"
            "### Key Results\n"
            "- 85% reduction in manual processing time\n"
            "- 99.5% extraction accuracy\n"
            "- $2M annual cost savings\n\n"
            "## Tech Stack\n"
            "Python, Tesseract OCR, OpenAI GPT-4, FastAPI, PostgreSQL, React"
        ),
    },
    {
        "slug": "ai-customer-support-triage",
        "title": "AI Customer Support Triage System",
        "description": "An intelligent triage system that classifies and routes support tickets using LLMs and embedding search.",
        "industry": "Customer Service",
        "use_case": "Support ticket triage",
        "content_markdown": (
            "## The Challenge\n\n"
            "A large e-commerce company received 10,000+ support tickets daily. "
            "Manual triage was slow, inconsistent, and expensive.\n\n"
            "## The Solution\n\n"
            "An AI triage system that classifies tickets by intent, routes them to "
            "the right team, and suggests responses based on similar resolved tickets.\n\n"
            "### Key Results\n"
            "- 70% reduction in first-response time\n"
            "- 40% of tickets resolved without human touch\n"
            "- 95% accurate routing\n\n"
            "## Tech Stack\n"
            "Python, OpenAI Embeddings, Pinecone, FastAPI, React"
        ),
    },
    {
        "slug": "ai-code-review-assistant",
        "title": "AI Code Review Assistant for Enterprise Teams",
        "description": "An automated code review assistant that catches bugs and enforces style guides using LLMs.",
        "industry": "Developer Tools",
        "use_case": "Automated code review",
        "content_markdown": (
            "## The Challenge\n\n"
            "Code review bottlenecks slowed down a 200-engineer team. Reviews were "
            "inconsistent, and junior engineers couldn't catch subtle issues.\n\n"
            "## The Solution\n\n"
            "An AI code review assistant that runs alongside human reviewers. It "
            "checks for bugs, style violations, security issues, and suggests "
            "improvements based on the team's conventions.\n\n"
            "### Key Results\n"
            "- 50% faster review cycles\n"
            "- 30% more bugs caught pre-merge\n"
            "- Consistent style across 200+ engineers\n\n"
            "## Tech Stack\n"
            "Python, OpenAI GPT-4, GitHub Apps API, React, PostgreSQL"
        ),
    },
]

SEED_PROJECTS: list[dict[str, Any]] = [
    {
        "slug": "scopelytics-ai-powered",
        "title": "Scopelytics \u2014 AI-Powered Game Analytics",
        "description": "Real-time analytics pipeline for game studios using embeddings, ML clustering, and batch scoring.",
        "content_markdown": (
            "## Architecture\n"
            "Scopelytics uses a real-time event ingestion pipeline with streaming "
            "analytics, batch ML scoring, and a queryable dashboard layer. Player "
            "events flow through Kafka to a processing layer that computes metrics, "
            "trains churn models, and generates insights.\n\n"
            "### AI Capabilities\n"
            "- Player behavior clustering with k-means\n"
            "- Churn prediction with gradient boosting\n"
            "- Automated LLM insight generation\n"
            "- Anomaly detection on key metrics"
        ),
    },
    {
        "slug": "ai-workflow-platform",
        "title": "AI Workflow \u2014 Multi-Step Agent Pipeline Platform",
        "description": "Build, deploy, and monitor AI agent workflows with human-in-the-loop review, structured output validation, and async job processing.",
        "content_markdown": (
            "## Architecture\n"
            "The platform chains multiple AI agents into pipelines, each stage "
            "producing Pydantic-validated structured output. Celery workers on "
            "Redis handle async generation jobs. A Next.js admin UI provides "
            "approval gates and progress monitoring.\n\n"
            "### AI Capabilities\n"
            "- OpenAI Agents SDK for multi-agent orchestration\n"
            "- Structured output extraction with Pydantic schemas\n"
            "- Real-time streaming of agent outputs\n"
            "- Session persistence for long-running agents"
        ),
    },
    {
        "slug": "ai-news-aggregator",
        "title": "AI News \u2014 Intelligent News Aggregation Pipeline",
        "description": "Automated AI news ingestion, extraction, scoring, and publication pipeline with heuristics and human review gates.",
        "content_markdown": (
            "## Architecture\n"
            "The AI News pipeline crawls RSS feeds, extracts articles, scores them "
            "by relevance, and queues them for human review. Published items appear "
            "on the public AI News feed.\n\n"
            "### AI Capabilities\n"
            "- Heuristic scoring with configurable weights\n"
            "- LLM-based article extraction\n"
            "- Dedup via URL + content hash\n"
            "- Human review queue with approve/reject workflow"
        ),
    },
    {
        "slug": "semantic-blog-search",
        "title": "Semantic Blog Search with Embeddings",
        "description": "Full-text and semantic search across blog content using PostgreSQL tsvector and OpenAI embeddings.",
        "content_markdown": (
            "## Architecture\n"
            "Dual search backend: PostgreSQL tsvector for full-text search and "
            "OpenAI embeddings for semantic search. Combined results ranked by "
            "relevance score.\n\n"
            "### AI Capabilities\n"
            "- OpenAI embedding generation for semantic search\n"
            "- PostgreSQL tsvector for full-text search\n"
            "- Hybrid ranking combining both approaches\n"
            "- API-first design for frontend integration"
        ),
    },
]

SEED_TAGS: list[str] = [
    "AI Agents",
    "Production",
    "Engineering",
    "MCP",
    "Architecture",
    "Best Practices",
    "Machine Learning",
    "DevOps",
]

# ── AI News seed ────────────────────────────────────────────────

SEED_NEWS_SOURCE: dict[str, Any] = {
    "name": "AI Lab Demo Feed",
    "source_type": "rss",
    "url_or_identifier": "https://ai-lab.example.com/demo-feed",
    "description": "Demo AI news source for development and testing.",
    "priority": "normal",
    "crawl_frequency_minutes": 60,
    "is_enabled": True,
    "credibility_base_score": 0.8,
}

SEED_NEWS_ITEMS: list[dict[str, Any]] = [
    {
        "external_id": "demo-news-001",
        "title": "OpenAI Releases GPT-5 with Advanced Reasoning Capabilities",
        "link_url": "https://example.com/news/gpt-5-release",
        "excerpt": "OpenAI has announced GPT-5, featuring significant improvements in multi-step reasoning, tool use, and context handling up to 1 million tokens.",
        "summary": "OpenAI released GPT-5 with 1M token context and advanced reasoning. Early benchmarks show 40% improvement on complex math and coding tasks.",
        "why_it_matters": "This represents a major leap in LLM capabilities that will directly impact how AI agents are built and deployed in production.",
        "author": "Sarah Chen",
        "site_name": "AI Weekly",
        "content": "OpenAI has officially launched GPT-5, the latest iteration of their large language model series. The new model brings several groundbreaking features:\n\n**1M Token Context**: GPT-5 can process up to one million tokens in a single request, enabling analysis of entire codebases or lengthy documents.\n\n**Advanced Reasoning**: The model demonstrates significantly improved performance on multi-step reasoning tasks, scoring 40% higher than GPT-4 on complex math benchmarks.\n\n**Enhanced Tool Use**: GPT-5 can orchestrate multiple tools and APIs simultaneously, making it ideal for agentic workflows.\n\n**Pricing**: OpenAI has maintained competitive pricing at $15/1M input tokens and $60/1M output tokens.",
    },
    {
        "external_id": "demo-news-002",
        "title": "Anthropic Launches Claude 4 with Computer Use API",
        "link_url": "https://example.com/news/claude-4-computer-use",
        "excerpt": "Anthropic's Claude 4 introduces a Computer Use API that allows AI to directly interact with desktop applications, browsers, and operating systems.",
        "summary": "Claude 4's Computer Use API enables AI to control desktop applications directly. Early adopters report 60% faster workflow automation.",
        "why_it_matters": "Computer Use APIs represent a paradigm shift in AI automation, moving from text-only to full GUI interaction capabilities.",
        "author": "Mike Rodriguez",
        "site_name": "TechCrunch",
        "content": "Anthropic today unveiled Claude 4, their most capable AI model yet, featuring a revolutionary Computer Use API that allows the model to interact with graphical user interfaces directly.\n\n**Computer Use API**: Developers can now instruct Claude to navigate desktop applications, fill forms, click buttons, and extract information from any GUI.\n\n**Safety Features**: The model includes built-in guardrails that prevent harmful actions and require human confirmation for sensitive operations.\n\n**Enterprise Focus**: Claude 4 is optimized for enterprise workflows including data entry automation, legacy system integration, and QA testing.",
    },
    {
        "external_id": "demo-news-003",
        "title": "MCP Protocol Gains Industry Adoption Across Major AI Platforms",
        "link_url": "https://example.com/news/mcp-adoption",
        "excerpt": "The Model Context Protocol (MCP) is seeing rapid adoption with major AI platforms integrating support for standardized tool and resource definitions.",
        "summary": "MCP adoption accelerates with OpenAI, Anthropic, and Google all adding native support. The open standard simplifies AI tool integration.",
        "why_it_matters": "MCP standardization reduces integration friction and enables interchangeable AI tools across providers, a key milestone for the AI ecosystem.",
        "author": "Alex Kumar",
        "site_name": "The Verge",
        "content": "The Model Context Protocol (MCP), an open standard for connecting AI models to external tools and data sources, is seeing explosive adoption across the industry.\n\n**Major Adoption**: OpenAI, Anthropic, and Google have all announced native MCP support in their latest SDKs.\n\n**Community Growth**: The MCP specification repository has surpassed 10,000 GitHub stars with contributions from over 200 developers.\n\n**Enterprise Use**: Companies like Salesforce, Adobe, and Atlassian are building MCP servers for their platforms.",
    },
    {
        "external_id": "demo-news-004",
        "title": "AI Agents in Production: Lessons from 100 Deployments",
        "link_url": "https://example.com/news/ai-agents-production-lessons",
        "excerpt": "A comprehensive study of 100 production AI agent deployments reveals patterns for success, common failure modes, and best practices for reliability.",
        "summary": "Study of 100 AI agent deployments finds human-in-the-loop, structured output validation, and observability are top success factors.",
        "why_it_matters": "Real-world deployment data provides actionable guidance for teams building AI agent systems, reducing trial-and-error.",
        "author": "Dr. Lisa Park",
        "site_name": "ACM Tech News",
        "content": "A new study analyzing 100 production AI agent deployments across 50 companies reveals key patterns for successful implementation.\n\n**Top Success Factors**: Human-in-the-loop review (92% of successful deployments), structured output validation (87%), and comprehensive observability (81%).\n\n**Common Failure Modes**: Insufficient error handling (45%), lack of monitoring (38%), and over-automation without human escalation paths (35%).\n\n**Recommendations**: Start with narrow scopes, implement gradual autonomy, and invest in traceability from day one.",
    },
    {
        "external_id": "demo-news-005",
        "title": "OpenAI Introduces Cheaper GPT-4o Mini for Edge Deployment",
        "link_url": "https://example.com/news/gpt4o-mini-edge",
        "excerpt": "OpenAI's new GPT-4o Mini model brings powerful AI capabilities to edge devices with significantly reduced computational requirements.",
        "summary": "GPT-4o Mini achieves 90% of GPT-4o quality at 20% of the cost, optimized for mobile and edge deployment scenarios.",
        "why_it_matters": "Edge-capable LLMs enable AI features on-device without cloud latency, opening new use cases for real-time and privacy-sensitive applications.",
        "author": "James Wilson",
        "site_name": "Ars Technica",
        "content": "OpenAI has released GPT-4o Mini, a distilled version of their flagship model optimized for edge deployment.\n\n**Performance**: The model achieves 90% of GPT-4o's quality on standard benchmarks while requiring only 20% of the computational resources.\n\n**Use Cases**: Ideal for mobile apps, IoT devices, and scenarios where low latency and privacy are critical.\n\n**Pricing**: At just $0.15/1M input tokens, it makes AI features economically viable for high-volume consumer applications.",
    },
]


# ── Router ─────────────────────────────────────────────────────

class SeedResult(BaseModel):
    blog_posts: int
    showcases: int
    projects: int
    tags: int
    news_items: int


def create_admin_seed_router(settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/admin/seed", tags=["admin-seed"])
    engine = create_database_engine(settings)

    @router.post("/all", response_model=SeedResult)
    def seed_all() -> SeedResult:
        """Seed all content types. Idempotent \u2014 skips existing slugs."""
        result = SeedResult(blog_posts=0, showcases=0, projects=0, tags=0, news_items=0)

        with engine.begin() as conn:
            # Tags
            for tag_name in SEED_TAGS:
                existing = conn.execute(
                    select(blog_tags.c.name).where(blog_tags.c.name == tag_name)
                ).first()
                if not existing:
                    conn.execute(
                        insert(blog_tags).values(
                            id=str(uuid.uuid4().hex[:12]),
                            name=tag_name,
                            slug=tag_name.lower().replace(" ", "-"),
                        )
                    )
                    result.tags += 1

            # Blog posts
            now = datetime.now(UTC)
            for post in SEED_BLOG_POSTS:
                existing = conn.execute(
                    select(blog_posts.c.id).where(blog_posts.c.slug == post["slug"])
                ).first()
                if not existing:
                    conn.execute(
                        insert(blog_posts).values(
                            id=str(uuid.uuid4().hex[:12]),
                            slug=post["slug"],
                            title=post["title"],
                            excerpt=post["excerpt"],
                            author_name=post["author_name"],
                            status="published",
                            published_at=now,
                            content_markdown=post["content_markdown"],
                            created_at=now,
                            updated_at=now,
                        )
                    )
                    result.blog_posts += 1

            # Showcases
            for showcase in SEED_SHOWCASES:
                existing = conn.execute(
                    select(showcases.c.id).where(showcases.c.slug == showcase["slug"])
                ).first()
                if not existing:
                    conn.execute(
                        insert(showcases).values(
                            id=str(uuid.uuid4().hex[:12]),
                            slug=showcase["slug"],
                            title=showcase["title"],
                            description=showcase["description"],
                            industry=showcase["industry"],
                            use_case=showcase["use_case"],
                            status="published",
                            published_at=now,
                            content_markdown=showcase["content_markdown"],
                            created_at=now,
                            updated_at=now,
                        )
                    )
                    result.showcases += 1

            # Projects
            for project in SEED_PROJECTS:
                existing = conn.execute(
                    select(projects.c.id).where(projects.c.slug == project["slug"])
                ).first()
                if not existing:
                    conn.execute(
                        insert(projects).values(
                            id=str(uuid.uuid4().hex[:12]),
                            slug=project["slug"],
                            title=project["title"],
                            description=project["description"],
                            status="published",
                            published_at=now,
                            content_markdown=project["content_markdown"],
                            created_at=now,
                            updated_at=now,
                        )
                    )
                    result.projects += 1

            # AI News source + items
            news_source_id = None
            existing_source = conn.execute(
                select(news_sources.c.id).where(news_sources.c.name == SEED_NEWS_SOURCE["name"])
            ).first()
            if existing_source:
                news_source_id = existing_source[0]
            else:
                news_source_id = f"src_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    insert(news_sources).values(
                        id=news_source_id,
                        name=SEED_NEWS_SOURCE["name"],
                        source_type=SEED_NEWS_SOURCE["source_type"],
                        url_or_identifier=SEED_NEWS_SOURCE["url_or_identifier"],
                        description=SEED_NEWS_SOURCE["description"],
                        priority=SEED_NEWS_SOURCE["priority"],
                        crawl_frequency_minutes=SEED_NEWS_SOURCE["crawl_frequency_minutes"],
                        is_enabled=SEED_NEWS_SOURCE["is_enabled"],
                        credibility_base_score=SEED_NEWS_SOURCE["credibility_base_score"],
                        created_at=now,
                        updated_at=now,
                    )
                )

            for item in SEED_NEWS_ITEMS:
                existing = conn.execute(
                    select(news_raw_items.c.id).where(
                        news_raw_items.c.external_id == item["external_id"]
                    )
                ).first()
                if existing:
                    continue

                raw_id = f"raw_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    insert(news_raw_items).values(
                        id=raw_id,
                        source_id=news_source_id,
                        external_id=item["external_id"],
                        title=item["title"],
                        link_url=item["link_url"],
                        raw_payload="{}",
                        content_hash=hashlib.md5(item["external_id"].encode()).hexdigest(),
                        fetched_at=now,
                    )
                )

                extracted_id = f"ext_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    insert(news_extracted_articles).values(
                        id=extracted_id,
                        raw_item_id=raw_id,
                        source_url=item["link_url"],
                        final_url=item["link_url"],
                        title=item["title"],
                        author=item.get("author"),
                        site_name=item.get("site_name"),
                        content_markdown=item["content"],
                        content_text=item["content"],
                        content_hash=hashlib.md5((item["external_id"] + "_ext").encode()).hexdigest(),
                        provider="firecrawl_fake",
                        extraction_status="completed",
                        extracted_at=now,
                        canonical_url_normalized=item["link_url"],
                    )
                )

                # Create a slug from the title
                news_slug = (
                    item["title"]
                    .lower()
                    .replace(" ", "-")
                    .replace("[", "")
                    .replace("]", "")
                    .replace("(", "")
                    .replace(")", "")
                    [:80]
                    .rstrip("-")
                )

                conn.execute(
                    insert(news_review_items).values(
                        id=f"rev_{uuid.uuid4().hex[:12]}",
                        extracted_article_id=extracted_id,
                        raw_item_id=raw_id,
                        source_id=news_source_id,
                        title=item["title"],
                        source_credibility_score=0.8,
                        engagement_score=0.7,
                        relevance_score=0.85,
                        novelty_score=0.75,
                        technical_depth_score=0.8,
                        business_value_score=0.7,
                        spam_risk_score=0.1,
                        final_publish_score=0.78,
                        summary=item["summary"],
                        why_it_matters=item["why_it_matters"],
                        scorer_version="seed_demo",
                        review_status="approved",
                        slug=news_slug,
                        published_at=now,
                        scored_at=now,
                        reviewed_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                )

                result.news_items += 1

        return result

    return router
