"use server";

import { revalidatePath } from "next/cache";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type AdminSession = NonNullable<Awaited<ReturnType<typeof auth.api.getSession>>>;

async function callBackend(path: string, init: RequestInit, session: AdminSession) {
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

export async function reprocessSubmissionAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const submissionId = formData.get("submissionId");
  if (typeof submissionId !== "string" || submissionId.length === 0) throw new Error("Missing submissionId");

  await callBackend(`/admin/news/submitted-links/${submissionId}/process`, { method: "POST" }, session);
  revalidatePath("/admin/news/submitted-links");
}
