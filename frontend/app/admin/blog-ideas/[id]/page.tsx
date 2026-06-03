import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { BlogIdeaDetailView, type BlogIdeaDetail } from "../idea-detail-view";
import {
  approveOutlineAction,
  rejectOutlineAction,
  generateOutlineAction,
  generateDraftAction,
  approveDraftAction,
  rejectDraftAction,
  reviewTechnicalAction,
  approveReviewAction,
  rejectReviewAction,
  generateMarketingAction,
  approveMarketingAction,
  rejectMarketingAction,
} from "../actions";


const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

async function getBlogIdea(id: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/blog-ideas/${id}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (response.status === 404) return undefined;
  if (!response.ok) throw new Error(`Failed to fetch idea: ${response.status}`);
  return (await response.json()) as BlogIdeaDetail;
}

export default async function AdminBlogIdeaDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const idea = await getBlogIdea(id);
  if (!idea) notFound();

  return (
    <AdminCmsShell active="ideas">
      <BlogIdeaDetailView
        idea={idea}
        actions={{
          approveIdea: approveOutlineAction,
          rejectIdea: rejectOutlineAction,
          generateOutline: generateOutlineAction,
          approveOutline: approveOutlineAction,
          rejectOutline: rejectOutlineAction,
          generateDraft: generateDraftAction,
          approveDraft: approveDraftAction,
          rejectDraft: rejectDraftAction,
          reviewTechnical: reviewTechnicalAction,
          approveReview: approveReviewAction,
          rejectReview: rejectReviewAction,
          generateMarketing: generateMarketingAction,
          approveMarketing: approveMarketingAction,
          rejectMarketing: rejectMarketingAction,
        }}
      />
    </AdminCmsShell>
  );
}
