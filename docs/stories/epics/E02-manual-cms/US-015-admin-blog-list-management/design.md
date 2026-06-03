# Design

- Add `GET /admin/blog-posts` requiring US-004 admin identity.
- Add `/admin/blog` protected Next.js page.
- Next.js server component checks Better Auth session, signs FastAPI admin headers server-side, and fetches admin list.
- UI shows title, slug, status, published date, and editor link.

No admin secrets are exposed to browser code.
