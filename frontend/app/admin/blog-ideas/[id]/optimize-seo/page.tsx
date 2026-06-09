import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { AdminDashboardHeader } from "@/components/admin/admin-dashboard-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { auth } from "@/lib/auth/server";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { SeoOptimizeClient } from "./optimize-client";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type SeoChange = {
  section: string;
  before: string;
  after: string;
  rationale: string;
};

type SeoOptimizationResult = {
  id: string;
  blog_idea_id: string;
  changes: SeoChange[];
  overall_summary: string;
  created_at: string;
};

async function fetchOptimization(ideaId: string): Promise<SeoOptimizationResult | null> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return null;

  try {
    const res = await fetch(`${backendBaseUrl}/admin/blog-ideas/${ideaId}/optimize-seo`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...createAdminBoundaryHeaders({
          user: { id: session.user.id, email: session.user.email },
        }),
      },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function OptimizeSeoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const result = await fetchOptimization(id);

  if (!result) {
    return (
      <div className={adminPageStackClass}>
        <AdminDashboardHeader
          title="SEO Optimization"
          description="Could not generate optimization suggestions."
          email={session.user.email}
        />
        <a
          href={`/admin/blog-ideas/${id}`}
          className="inline-flex items-center gap-1.5 text-sm text-brand hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to idea
        </a>
      </div>
    );
  }

  return (
    <div className={adminPageStackClass}>
      <AdminDashboardHeader
        title="SEO Optimization Results"
        description={result.overall_summary}
        email={session.user.email}
      />
      <SeoOptimizeClient ideaId={id} result={result} />
    </div>
  );
}
