import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";
import { ExternalLink, RefreshCw } from "lucide-react";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { AdminBackLink } from "@/components/admin/admin-back-link";
import { AdminCard, AdminCardBody, AdminCardSection } from "@/components/admin/admin-card";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

import { reprocessSubmissionAction } from "../actions";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type SubmittedLinkDetail = {
  id: string;
  url: string;
  url_normalized: string;
  submitter_name: string | null;
  submitter_email: string | null;
  note: string | null;
  suggested_category: string | null;
  rate_limit_key: string;
  status: "submitted" | "processing" | "duplicate" | "failed" | "in_review";
  processing_error: string | null;
  raw_item_id: string | null;
  review_item_id: string | null;
  created_at: string;
  updated_at: string;
};

async function getSubmittedLink(id: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/news/submitted-links/${id}`, {
    headers: createAdminBoundaryHeaders({ user: { id: session.user.id, email: session.user.email } }),
    cache: "no-store",
  });

  if (response.status === 404) return undefined;
  if (!response.ok) throw new Error(`Failed to fetch submission: ${response.status}`);
  return (await response.json()) as SubmittedLinkDetail;
}

const statusColorMap: Record<string, string> = {
  submitted: "bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/25",
  processing: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/25",
  duplicate: "bg-gray-500/10 text-gray-700 dark:text-gray-300 border-gray-500/25",
  failed: "bg-red-500/10 text-red-700 dark:text-red-300 border-red-500/25",
  in_review: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/25",
};

export default async function AdminSubmittedLinkDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const item = await getSubmittedLink(id);
  if (!item) notFound();

  return (
    <AdminCmsShell active="submitted-links">
      <div className={adminPageStackClass}>
        <AdminPageHeader
          actions={<AdminBackLink href="/admin/news/submitted-links">Back to submissions</AdminBackLink>}
          description={`Submission from ${item.submitter_name || item.submitter_email || "anonymous"}.`}
          eyebrow="Content pipeline"
          metaText={item.status}
          title="Submitted link"
        />

        <div className="grid gap-6 md:grid-cols-2">
          <AdminCard>
            <AdminCardSection title="Submission details" />
            <AdminCardBody className="flex flex-col gap-4">
              <div>
                <p className="text-xs font-medium text-muted-foreground">URL</p>
                <a
                  className="mt-1 inline-flex items-center gap-1 break-all text-sm text-brand underline underline-offset-2 hover:text-brand/80"
                  href={item.url}
                  rel="noopener noreferrer"
                  target="_blank"
                >
                  {item.url}
                  <ExternalLink className="size-3 shrink-0" />
                </a>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground">Normalized URL</p>
                <p className="mt-1 text-sm">{item.url_normalized}</p>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground">Status</p>
                <span className={cn("mt-1 inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium", statusColorMap[item.status])}>
                  {item.status === "in_review" ? "In review" : item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Created</p>
                  <p className="mt-1 text-sm">{new Date(item.created_at).toLocaleString("en-US")}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Updated</p>
                  <p className="mt-1 text-sm">{new Date(item.updated_at).toLocaleString("en-US")}</p>
                </div>
              </div>
            </AdminCardBody>
          </AdminCard>

          <AdminCard>
            <AdminCardSection title="Submitter info" />
            <AdminCardBody className="flex flex-col gap-4">
              {item.submitter_name && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Name</p>
                  <p className="mt-1 text-sm">{item.submitter_name}</p>
                </div>
              )}
              {item.submitter_email && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Email</p>
                  <p className="mt-1 text-sm">{item.submitter_email}</p>
                </div>
              )}
              {item.note && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Note</p>
                  <p className="mt-1 whitespace-pre-wrap text-sm">{item.note}</p>
                </div>
              )}
              {item.suggested_category && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Suggested category</p>
                  <p className="mt-1 text-sm">{item.suggested_category}</p>
                </div>
              )}
              <div>
                <p className="text-xs font-medium text-muted-foreground">Rate limit key</p>
                <p className="mt-1 text-sm font-mono text-muted-foreground">{item.rate_limit_key}</p>
              </div>
            </AdminCardBody>
          </AdminCard>
        </div>

        {item.processing_error && (
          <AdminCard>
            <AdminCardSection title="Processing error" />
            <AdminCardBody>
              <p className="text-sm text-red-600">{item.processing_error}</p>
            </AdminCardBody>
          </AdminCard>
        )}

        <AdminCard>
          <AdminCardSection title="Pipeline links" />
          <AdminCardBody className="flex flex-col gap-4">
            {item.raw_item_id && (
              <div>
                <p className="text-xs font-medium text-muted-foreground">Raw item ID</p>
                <p className="mt-1 font-mono text-xs text-muted-foreground">{item.raw_item_id}</p>
              </div>
            )}
            {item.review_item_id && (
              <div>
                <p className="text-xs font-medium text-muted-foreground">Review item</p>
                <a
                  className="mt-1 inline-flex items-center gap-1 text-sm text-brand underline underline-offset-2 hover:text-brand/80"
                  href={`/admin/news-review?reviewId=${item.review_item_id}`}
                >
                  {item.review_item_id}
                  <ExternalLink className="size-3" />
                </a>
              </div>
            )}
            {!item.raw_item_id && !item.review_item_id && (
              <p className="text-sm text-muted-foreground">No pipeline items yet. Processing may still be pending or may have failed.</p>
            )}
          </AdminCardBody>
        </AdminCard>

        <div className="flex gap-3">
          <form action={reprocessSubmissionAction}>
            <input name="submissionId" type="hidden" value={item.id} />
            <button
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              type="submit"
            >
              <RefreshCw className="size-4" />
              Reprocess
            </button>
          </form>
        </div>
      </div>
    </AdminCmsShell>
  );
}
