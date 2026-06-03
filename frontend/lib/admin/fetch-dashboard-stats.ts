import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type SessionUser = { id: string; email: string };

export type AdminDashboardStats = {
  blogDrafts: number;
  blogPublished: number;
  blogTotal: number;
  ideasPending: number;
  ideasApproved: number;
  ideasTotal: number;
  showcasesDrafts: number;
  showcasesPublished: number;
  showcasesTotal: number;
};

type BlogPostRow = { status: "draft" | "published" };
type ShowcaseRow = { status: "draft" | "published" };
type IdeaRow = { status: "pending" | "approved" | "rejected" };

async function fetchJson<T>(path: string, user: SessionUser): Promise<T[]> {
  const response = await fetch(`${backendBaseUrl}${path}`, {
    headers: createAdminBoundaryHeaders({ user }),
    cache: "no-store",
  });

  if (!response.ok) {
    return [];
  }

  return (await response.json()) as T[];
}

export async function fetchAdminDashboardStats(user: SessionUser): Promise<AdminDashboardStats> {
  const [posts, showcases, ideas] = await Promise.all([
    fetchJson<BlogPostRow>("/admin/blog-posts", user),
    fetchJson<ShowcaseRow>("/admin/showcases", user),
    fetchJson<IdeaRow>("/admin/blog-ideas", user),
  ]);

  const blogPublished = posts.filter((post) => post.status === "published").length;
  const showcasesPublished = showcases.filter((item) => item.status === "published").length;

  return {
    blogDrafts: posts.length - blogPublished,
    blogPublished,
    blogTotal: posts.length,
    ideasPending: ideas.filter((idea) => idea.status === "pending").length,
    ideasApproved: ideas.filter((idea) => idea.status === "approved").length,
    ideasTotal: ideas.length,
    showcasesDrafts: showcases.length - showcasesPublished,
    showcasesPublished,
    showcasesTotal: showcases.length,
  };
}
