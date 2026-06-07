"""Seed the 2 GitHub repos as projects for blog idea generation.

Usage:
    python backend/scripts/seed_repos.py
"""

import sys
import uuid
from datetime import UTC, datetime

from sqlalchemy import insert, select

from backend.app.database import create_database_engine, projects
from backend.app.settings import Settings


def main() -> int:
    settings = Settings()
    engine = create_database_engine(settings)
    now = datetime.now(UTC)

    repos = [
        {
            "id": f"project_{uuid.uuid4().hex[:12]}",
            "slug": "scopelytics-ai-powered",
            "title": "Scopelytics — AI-Powered Game Analytics",
            "description": (
                "AI-powered analytics platform for game studios. "
                "Provides player segmentation, churn prediction, "
                "and actionable insights for game publishers."
            ),
            "content_markdown": (
                "## Scopelytics: AI-Powered Game Analytics\n\n"
                "Scopelytics is an AI-powered analytics solution designed "
                "for game studios to understand player behavior, predict "
                "churn, and optimize game experiences.\n\n"
                "### Key Features\n"
                "- **Player Segmentation**: AI-driven clustering of players "
                "based on behavior patterns, spending habits, and engagement.\n"
                "- **Churn Prediction**: ML models predicting player churn risk.\n"
                "- **Actionable Insights**: Automated recommendations for "
                "retention, monetization, and engagement optimization.\n"
                "- **Real-time Dashboards**: Live analytics dashboards.\n\n"
                "### Tech Stack\n"
                "Python/FastAPI, scikit-learn, XGBoost, PostgreSQL, React/TypeScript\n\n"
                "### AI Capabilities\n"
                "Player behavior clustering, churn prediction with gradient "
                "boosting, automated LLM insight generation, anomaly detection"
            ),
            "status": "published",
            "published_at": now,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": f"project_{uuid.uuid4().hex[:12]}",
            "slug": "ai-workflow-platform",
            "title": "AI Workflow — Multi-Step Agent Pipeline Platform",
            "description": (
                "A platform for building AI-powered multi-step agent "
                "workflows with human-in-the-loop review, structured "
                "output validation, and asynchronous job processing."
            ),
            "content_markdown": (
                "## AI Workflow Platform\n\n"
                "A platform for building, deploying, and monitoring AI "
                "agent workflows with human oversight at every step.\n\n"
                "### Key Features\n"
                "- **Multi-Step Agent Pipelines**: Chain multiple agents.\n"
                "- **Human-in-the-Loop**: Manual review at each stage.\n"
                "- **Structured Output**: Pydantic-validated LLM outputs.\n"
                "- **Async Job Processing**: Celery background tasks.\n"
                "- **Guardrails**: Content safety and claim validation.\n\n"
                "### Tech Stack\n"
                "Python/FastAPI, OpenAI Agents SDK, Celery, Redis, "
                "PostgreSQL, React/Next.js, shadcn/ui\n\n"
                "### AI Capabilities\n"
                "OpenAI Agents SDK integration, structured output extraction, "
                "multi-agent orchestration, real-time streaming, "
                "session persistence for long-running agents"
            ),
            "status": "published",
            "published_at": now,
            "created_at": now,
            "updated_at": now,
        },
    ]

    with engine.begin() as conn:
        for repo in repos:
            existing = conn.execute(
                select(projects.c.id).where(projects.c.slug == repo["slug"])
            ).first()
            if existing:
                print(f"  Already exists: {repo['slug']}")
                continue
            conn.execute(insert(projects).values(**repo))
            print(f"  Created: {repo['title']} ({repo['id']})")

    print(f"\nSeeded {len(repos)} projects successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
