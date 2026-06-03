"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

async function adminFetch(url: string, init?: RequestInit, session?: Awaited<ReturnType<typeof auth.api.getSession>>) {
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

export async function createNewsSourceAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await adminFetch(
    "/admin/news-sources",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: formData.get("name"),
        source_type: formData.get("sourceType"),
        url_or_identifier: formData.get("url"),
        description: formData.get("description") || null,
        priority: formData.get("priority") || "medium",
        crawl_frequency_minutes: Number(formData.get("crawlFrequency") || 360),
        is_enabled: formData.get("isEnabled") === "on",
        credibility_base_score: Number(formData.get("credibility") || 0.7),
      }),
    },
    session,
  );

  if (!response.ok) {
    throw new Error(`Failed to create news source: ${response.status}`);
  }
  redirect("/admin/news-sources");
}

export async function toggleNewsSourceAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const sourceId = formData.get("sourceId") as string;
  const enabled = formData.get("enabled") === "true";
  await adminFetch(
    `/admin/news-sources/${sourceId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_enabled: enabled }),
    },
    session,
  );
  redirect("/admin/news-sources");
}
