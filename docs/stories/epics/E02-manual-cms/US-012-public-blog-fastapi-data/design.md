# Design

## Flow

1. FastAPI remains the source for public published blog data.
2. Next.js public blog pages fetch `GET /public/blog-posts` and `GET /public/blog-posts/{slug}` server-side.
3. Public pages do not expose admin headers or secrets.
4. E2E publishes through the authenticated editor then verifies `/blog` includes the new post.

## Tradeoff

Use dynamic/no-store fetch for MVP proof. A later story can add ISR/cache tags once persistence and invalidation are stable.
