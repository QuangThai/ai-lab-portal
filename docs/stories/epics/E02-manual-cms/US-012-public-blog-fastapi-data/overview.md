# Overview

## Current Behavior

The public Next.js blog pages render deterministic frontend seed data. US-011 proves editor publish reaches FastAPI, but public pages do not yet read the FastAPI published read API.

## Target Behavior

Public `/blog` and `/blog/[slug]` read published posts from FastAPI public endpoints, so content published through the editor path can appear publicly.

## Non-Goals

- No AI workflow.
- No caching strategy hardening beyond no-store MVP proof.
- No rich SEO metadata expansion.
