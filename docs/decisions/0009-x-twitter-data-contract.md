# 0009 X/Twitter Data Contract

Date: 2026-06-04

## Status

Accepted

## Context

MVP 5 requires a normalized data contract for X/Twitter social posts before any
real provider call or ingestion pipeline code can use the data. The contract
must handle the gap between raw provider output (Apify Xquik, Maxime Dupré
Twitter Scraper, or future providers) and the internal AI News pipeline.

The normalized boundary is already implemented in `backend/app/social_x.py`
(US-053) as `NormalizedSocialPost` and `SocialEngagementMetrics` Pydantic
models. This decision records the durable semantics so future provider adapters
and pipeline changes preserve the same contract.

## Decision

1. **Required fields (always non-null)**
   - `provider`: SocialProviderName — identifies the source provider.
   - `provider_actor`: str — identifies the provider actor/version.
   - `post_id`: str — provider's unique post identifier.
   - `post_url`: HttpUrl — permalink to the post on the source platform.
   - `post_text`: str (min_length=1) — the post body text.
   - `author_handle`: str — platform handle (without @ prefix).
   - `source_scope`: SocialPostSourceScope — crawl context metadata.
   - `raw_payload`: dict — the complete original provider payload for audit.

2. **Required but nullable fields**
   - `created_at`: datetime | None — post creation timestamp.
   - `author_display_name`: str | None — display name.
   - `author_verified`: bool | None — platform verification status.
   - `author_followers_count`: int | None (>= 0) — follower count.
   - `lang`: str | None — BCP 47 language tag.
   - `quoted_post_id`, `quoted_post_text`, `quoted_author_handle`: quoted post
     metadata.
   - `conversation_id`: str | None — thread/conversation identifier.

3. **Engagement metrics (all nullable, >= 0)**
   - `like_count`, `repost_count`, `reply_count`, `quote_count`,
     `view_count`, `bookmark_count`.
   - Null indicates the metric was not available from the provider, not that the
     value is zero. Downstream scoring should treat null as unknown/missing
     rather than zero.

4. **URL and media fields**
   - `urls`: list of `SocialPostUrlEntity` with `url` (HttpUrl, required),
     `expanded_url` (HttpUrl | None), `display_url` (str | None).
   - `hashtags`: list of str, extracted from entities.
   - `media_urls`: list of HttpUrl.
   - Only `urls` with valid http/https schemes are accepted. Non-HTTP protocols
     are silently dropped.

5. **Post kind classification**
   - `original` — standalone post.
   - `quote` — post quoting another post (has `quoted_post_*`).
   - `reply` — post replying to another post.
   - `repost` — repost/retweet (no original content).
   - `unknown` — fallback when kind cannot be determined.

6. **Source scope metadata (SocialPostSourceScope)**
   - `provider`: provider name enum.
   - `provider_actor`: specific actor/script name.
   - `source_kind`: `handle` | `search` | `list` | `tweet_url`.
   - `source_value`: the handle, query, list ID, or URL.
   - `matched_query`: optional — which search term matched.
   - `crawl_run_id`: optional — unique crawl run identifier.

7. **Raw payload retention**
   - The complete provider JSON payload is stored as `raw_payload` for audit,
     debugging, and future field extraction.
   - Raw payloads must never be displayed publicly without review.

8. **Deleted, private, or unavailable posts**
   - The provider may return posts that are later deleted or made private.
   - The ingestion pipeline must not reject posts based on current availability
     — review status and source metadata carry the moderation context.
   - A post that returns HTTP 404, 401, or equivalent from the provider during
     refresh should be flagged as `unavailable` in the review queue rather than
     silently dropped.

9. **Provider adapter contract**
   - Every real provider adapter must implement `SocialProviderProtocol`:
     `fetch_posts(scope: SocialPostSourceScope) -> list[NormalizedSocialPost]`.
   - Adapters must raise `ValueError` for invalid/malformed rows.
   - Adapters must never silently drop data — use nullable fields for missing
     values.

## Consequences

Positive:
- New provider adapters can be added without changing downstream pipeline code.
- The data contract has already been verified with fake fixtures (US-053, 7
  tests).
- Null semantics are explicit: null means unknown/not-provided, not zero.

Tradeoffs:
- Raw payload storage adds database cost but is required for audit.
- Provider field name normalization adds adapter complexity but decouples the
  pipeline from provider schema changes.

## Follow-Up

- Add X/Twitter provider adapter tests for quota exhaustion and malformed
  payloads before real provider calls (entry criterion 6).
- Consider raw payload TTL/archival after the review and publish flow settles.
