"use server";

import { headers } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

async function callBackend(path: string, init: RequestInit) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...createAdminBoundaryHeaders({ user: { id: session.user.id, email: session.user.email } }),
      ...init.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Backend request failed: ${response.status}`);
  return response.json();
}

export async function approveCommentAction(formData: FormData) {
  const commentId = formData.get("commentId");
  if (typeof commentId !== "string") throw new Error("Missing commentId");
  await callBackend(`/admin/blog-comments/${commentId}/approve`, { method: "POST" });
  revalidatePath("/admin/blog-comments");
}

export async function rejectCommentAction(formData: FormData) {
  const commentId = formData.get("commentId");
  if (typeof commentId !== "string") throw new Error("Missing commentId");
  await callBackend(`/admin/blog-comments/${commentId}/reject`, { method: "POST" });
  revalidatePath("/admin/blog-comments");
}
