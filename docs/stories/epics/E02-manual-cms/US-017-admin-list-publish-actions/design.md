# Design

Add Next.js server actions for publish/unpublish on `/admin/blog`. Actions check Better Auth session, sign FastAPI admin headers server-side, call existing FastAPI admin endpoints, then revalidate/redirect back to the list.

No browser-side admin secrets.
