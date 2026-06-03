"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type AdminSession = NonNullable<Awaited<ReturnType<typeof auth.api.getSession>>>;

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
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}/generate-outline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
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
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}/generate-draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
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
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}/review-technical`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
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
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const ideaId = formData.get("ideaId") as string;
  await adminFetch(`/admin/blog-ideas/${ideaId}/generate-marketing`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  }, session);
  redirect(`/admin/blog-ideas/${ideaId}`);
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
