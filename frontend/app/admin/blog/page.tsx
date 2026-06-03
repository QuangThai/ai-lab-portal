import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { AdminListToolbar } from "@/components/admin/admin-list-toolbar";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { BlogPostCardList } from "./blog-post-card-list";
import { publishFromListAction, unpublishFromListAction } from "./actions";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export type AdminBlogPost = {
  id: string;
  slug: string;
  title: string;
  status: "draft" | "published";
  published_at: string | null;
};

async function listAdminBlogPosts() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/blog-posts`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch admin blog posts: ${response.status}`);
  }

  return (await response.json()) as AdminBlogPost[];
}

export default async function AdminBlogListPage() {
  const posts = await listAdminBlogPosts();
  const publishedCount = posts.filter((post) => post.status === "published").length;
  const draftCount = posts.length - publishedCount;

  return (
    <AdminCmsShell active="blog">
      <div className={adminPageStackClass}>
        <AdminListToolbar
          ctaHref="/admin/blog/editor"
          ctaLabel="New draft"
          description="Manage drafts and published AI Lab articles from one editorial list."
          eyebrow="Content library"
          metrics={[
            { dotClassName: "bg-brand", label: `${publishedCount} live` },
            { dotClassName: "bg-amber-500", label: `${draftCount} drafts` },
            { dotClassName: "bg-muted-foreground", label: `${posts.length} total` },
          ]}
          title="Blog posts"
        />

        <BlogPostCardList
          posts={posts}
          publishAction={publishFromListAction}
          unpublishAction={unpublishFromListAction}
        />
      </div>
    </AdminCmsShell>
  );
}
