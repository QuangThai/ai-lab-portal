# Design

- Add `GET /admin/blog-posts/{id}` requiring admin identity.
- Add repository `get_by_id()` for in-memory and Postgres repositories.
- Add `/admin/blog/[id]/edit` Next.js route that fetches the post server-side with signed admin headers.
- Reuse `BlogEditor` with initial values and hidden `postId`.
- List page links each row to its edit route.
