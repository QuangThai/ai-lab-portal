# Overview

## Current Behavior

FastAPI blog mutations use an in-memory repository at runtime, so published content does not survive process restart.

## Target Behavior

Runtime non-test FastAPI uses SQLAlchemy/PostgreSQL-backed blog and audit persistence. Tests can still inject in-memory repositories for deterministic proof.

## Non-Goals

- No advanced caching/ISR.
- No admin editor redesign.
- No AI workflow.
