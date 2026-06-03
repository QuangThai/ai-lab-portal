"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type AdminSession = NonNullable<Awaited<ReturnType<typeof auth.api.getSession>>>;
type GenerationStage = "outline" | "draft" | "technical-review" | "marketing";

async function adminFetch(url: string, init?: RequestInit, session?: AdminSession) {
  return fetch(`${backendBaseUrl}${url}`, {
    ...init,
    headers: {
      ...createAdminBoundaryHeaders({
        user: { id: session!.user.id, email: session!.user.email },
      }),
      ...(init?.headers ?? {}),
    },
  });
}

async function parseResponseDetail(response: Response) {
  try {
    const payload = (await response.json()) as unknown;
    if (payload && typeof payload === "object" && "detail" in payload) {
      return (payload as { detail?: unknown }).detail;
    }
    return payload;
  } catch {
    return undefined;
  }
}

function detailToMessage(detail: unknown, fallback: string) {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && "message" in detail) {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string") return message;
  }
  return fallback;
}

function detailToTaskId(detail: unknown) {
  if (detail && typeof detail === "object" && "task_id" in detail) {
    const taskId = (detail as { task_id?: unknown }).task_id;
    if (typeof taskId === "string") return taskId;
  }
  return undefined;
}

async function runGenerationAction(
  formData: FormData,
  stage: GenerationStage,
  endpoint: (ideaId: string) => string,
) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  const response = await adminFetch(endpoint(ideaId), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  }, session);

  const params = new URLSearchParams({ opStage: stage });
  const detail = await parseResponseDetail(response);

  if (response.status === 202) {
    params.set("opStatus", "queued");
    const taskId = detailToTaskId(detail);
    if (taskId) params.set("taskId", taskId);
    const message = detailToMessage(detail, "Generation queued.");
    params.set("message", message);
  } else if (response.ok) {
    params.set("opStatus", "completed");
    params.set("message", "Generation completed.");
  } else {
    params.set("opStatus", "error");
    params.set("message", detailToMessage(detail, `Generation failed with status ${response.status}.`));
  }

  redirect(`/admin/blog-ideas/${ideaId}?${params.toString()}`);
}

export async function approveIdeaAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "approved" }),
  }, session);
  redirect("/admin/blog-ideas");
}

export async function rejectIdeaAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "rejected" }),
  }, session);
  redirect("/admin/blog-ideas");
}

export async function generateOutlineAction(formData: FormData) {
  await runGenerationAction(formData, "outline", (ideaId) => `/admin/blog-ideas/${ideaId}/generate-outline`);
}

export async function approveOutlineAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ outline_status: "approved" }),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
}

export async function rejectOutlineAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ outline_status: "rejected" }),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
}

export async function generateDraftAction(formData: FormData) {
  await runGenerationAction(formData, "draft", (ideaId) => `/admin/blog-ideas/${ideaId}/generate-draft`);
}

export async function approveDraftAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft_status: "approved" }),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
}

export async function rejectDraftAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft_status: "rejected" }),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
}

export async function reviewTechnicalAction(formData: FormData) {
  await runGenerationAction(formData, "technical-review", (ideaId) => `/admin/blog-ideas/${ideaId}/review-technical`);
}

export async function approveReviewAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ technical_review_status: "approved" }),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
}

export async function rejectReviewAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ technical_review_status: "rejected" }),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
}

export async function generateMarketingAction(formData: FormData) {
  await runGenerationAction(formData, "marketing", (ideaId) => `/admin/blog-ideas/${ideaId}/generate-marketing`);
}

export async function approveMarketingAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ marketing_status: "approved" }),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
}

export async function pollGenerationJobAction(taskId: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const response = await adminFetch(
    `/admin/blog-ideas/generation-jobs/${taskId}`,
    { method: "GET" },
    session,
  );
  if (!response.ok) {
    return {
      status: "failed" as const,
      stage: "unknown",
      error_message: `Job status unavailable (${response.status}).`,
    };
  }
  return (await response.json()) as {
    status: "queued" | "running" | "completed" | "failed";
    stage: string;
    error_message?: string | null;
  };
}

export async function extractClaimsAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}/extract-claims`, { method: "POST" }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
}

export async function updateClaimAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const claimId = formData.get("claimId") as string;
  const ideaId = formData.get("ideaId") as string;
  const evidenceSource = (formData.get("evidenceSource") as string) || undefined;
  const evidenceReference = (formData.get("evidenceReference") as string) || undefined;
  const waive = formData.get("waive") === "on";
  await adminFetch(`/admin/blog-ideas/claims/${claimId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      status: waive ? "waived" : undefined,
      evidence_source_type: evidenceSource,
      evidence_reference: evidenceReference,
    }),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
}

export async function publishToBlogAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  const response = await adminFetch(
    `/admin/blog-ideas/${ideaId}/publish-to-blog`,
    { method: "POST" },
    session,
  );

  const params = new URLSearchParams({ opStage: "publish" });
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    payload = undefined;
  }

  if (response.ok) {
    const body =
      payload && typeof payload === "object"
        ? (payload as {
            blog_post_id?: string;
            slug?: string;
            already_linked?: boolean;
          })
        : {};
    params.set("opStatus", "completed");
    if (body.already_linked) {
      params.set("message", "This idea is already linked to a published blog post.");
    } else {
      params.set("message", "Blog post created and published.");
    }
    if (body.blog_post_id) params.set("blogPostId", body.blog_post_id);
    if (body.slug) params.set("blogSlug", body.slug);
  } else {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? (payload as { detail?: unknown }).detail
        : payload;
    params.set("opStatus", "error");
    params.set(
      "message",
      detailToMessage(detail, `Publish failed with status ${response.status}.`),
    );
  }

  redirect(`/admin/blog-ideas/${ideaId}?${params.toString()}`);
}

export async function rejectMarketingAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ marketing_status: "rejected" }),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
}

export async function createIdeaAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const title = formData.get("title") as string;
  const angle = formData.get("angle") as string;
  const targetReader = formData.get("targetReader") as string;
  const articleGoal = formData.get("articleGoal") as string;

  const response = await adminFetch("/admin/blog-ideas", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      angle,
      target_reader: targetReader,
      article_goal: articleGoal,
    }),
  }, session);

  if (!response.ok) {
    throw new Error(`Failed to create idea: ${response.status}`);
  }

  redirect("/admin/blog-ideas");
}
