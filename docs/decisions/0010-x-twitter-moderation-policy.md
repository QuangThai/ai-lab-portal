# 0010 X/Twitter Moderation and Publish Policy

Date: 2026-06-04

## Status

Accepted

## Context

X/Twitter social data carries higher risk than official RSS/blog sources: spam,
impersonation, context collapse, misinformation, and engagement bait are
prevalent. MVP 5 requires an explicit moderation and publish policy before any
social item reaches the public AI News feed.

The deterministic fake-first filter in `backend/app/social_x.py` (US-054)
already enforces the technical rules. This decision records the durable policy
that governs display, attribution, human review, and takedown behavior.

## Decision

1. **No auto-publish**
   - Every X/Twitter item enters the review queue as a candidate only.
   - No social item may bypass human review.
   - The `SocialLinkFilterDecision.requires_human_review` field must always be
     `true` for accepted items.

2. **Human review required**
   - Every accepted social item must be reviewed by a human admin before public
     display.
   - The admin review UI must show: post text, author metadata (handle, display
     name, follower count, verified status), engagement metrics, source post
     URL, provider run metadata, risk flags, and the AI filter's decision
     reason.
   - Admin actions: approve, reject, flag for takedown, or unpublish.

3. **Attribution rules**
   - Published items must link to the original post URL as the source.
   - Author handle and display name may be shown as attribution.
   - Author follower count, verified status, and engagement metrics may be shown
     but must be clearly labeled as "as of crawl time".
   - Do not display raw provider payloads publicly.

4. **Storage and redisplay**
   - Post text and author metadata may be stored for pipeline processing and
     review.
   - Store the minimum needed for review and public display.
   - Raw provider payloads are stored for audit only, with a defined TTL.
   - Deleted or unavailable posts flagged during refresh must be unpublishable
     by admin action but not automatically removed — a human must confirm.

5. **Spam, impersonation, and low-credibility handling**
   - The social link filter assigns risk flags for: `spam_or_engagement_bait`,
     `unsupported_rumor`, `personal_drama`, `low_author_credibility`.
   - Items with `spam_or_engagement_bait` are rejected pre-ingestion.
   - Items with other risk flags enter review with elevated visibility in the
     admin UI.
   - Review admin must be able to see all risk flags at a glance.

6. **Takedown policy**
   - Any user may request takedown of a social item linked to their content.
   - Takedown requests are handled by admin action (unpublish + delete or
     mark taken-down).
   - A takedown must not require automated action — human confirmation is
     required.

7. **Filter transparency**
   - The reason for rejection or acceptance is recorded and shown to the review
     admin.
   - The filter's topic classification and priority are advisory only — the
     review admin may override them.

8. **Budget and rate-limit policy**
   - Until a real provider budget is accepted, all ingestion uses fake provider
     fixtures.
   - Real provider calls must never be synchronous with public or admin HTTP
     requests.
   - Provider failures (quota exhaustion, network errors, malformed responses)
     must result in queued/failed job statuses and never crash the pipeline or
     block user-facing requests.

## Consequences

Positive:
- Clear policy boundaries mean implementation can proceed without ambiguity.
- The fake-first ingestion (US-055) exercises the same review path that real
  social items will use.
- Risk flags and mandatory human review provide a documented safety layer.

Tradeoffs:
- Human review introduces latency between ingestion and publication, but this is
  acceptable for a curated AI News feed.
- Storage requirements are higher with raw payload retention, mitigated by
  documented TTL.

## Follow-Up

- Add admin review UI affordances for social context (author, engagement, risk
  badges) as a later MVP 5 story (US-057 candidate).
- Review and update this policy after the first real provider sample run and
  terms acceptance.
