import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { ExternalLink, RefreshCw, Eye as EyeIcon } from "lucide-react";

import { AdminContentRow } from "@/components/admin/admin-content-row";
import { AdminEmptyState } from "@/components/admin/admin-empty-state";
import { AdminListActionLink, AdminListActions, AdminListActionForm, AdminListSubmitButton } from "@/components/admin/admin-list-actions";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminListToolbar } from "@/components/admin/admin-list-toolbar";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

import { reprocessSubmissionAction } from "./actions";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export type SubmittedLinkSummary = {
  id: string;
  url: string;
  url_normalized: string;
  submitter_name: string | null;
  submitter_email: string | null;
  note: string | null;
  suggested_category: string | null;
  status: "submitted" | "processing" | "duplicate" | "failed" | "in_review";
  processing_error: string | null;
  raw_item_id: string | null;
  review_item_id: string | null;
  created_at: string;
  updated_at: string;
};

async function listSubmittedLinks() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/news/submitted-links`, {
    headers: createAdminBoundaryHeaders({ user: { id: session.user.id, email: session.user.email } }),
    cache: "no-store",
  });

  if (!response.ok) throw new Error(`Failed to fetch submitted links: ${response.status}`);
  return (await response.json()) as SubmittedLinkSummary[];
}

function StatusBadge({ status }: { status: SubmittedLinkSummary["status"] }) {
  const colorMap: Record<string, string> = {
    submitted: "bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/25",
    processing: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/25",
    duplicate: "bg-gray-500/10 text-gray-700 dark:text-gray-300 border-gray-500/25",
    failed: "bg-red-500/10 text-red-700 dark:text-red-300 border-red-500/25",
    in_review: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/25",
  };

  return (
    <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium", colorMap[status] || "")}>
      {status === "in_review" ? "In review" : status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return null;
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export default async function AdminSubmittedLinksListPage() {
  const items = await listSubmittedLinks();

  const counts = {
    total: items.length,
    submitted: items.filter((i) => i.status === "submitted").length,
    inReview: items.filter((i) => i.status === "in_review").length,
    failed: items.filter((i) => i.status === "failed").length,
    duplicate: items.filter((i) => i.status === "duplicate").length,
  };

  return (
      <div className={adminPageStackClass}>
        <AdminListToolbar
          description="User-submitted AI news links awaiting review, processing, or marked as duplicate or failed."
          eyebrow="Content pipeline"
          metrics={[
            { dotClassName: "bg-brand", label: `${counts.submitted} pending` },
            { dotClassName: "bg-emerald-500", label: `${counts.inReview} in review` },
            { dotClassName: "bg-red-500", label: `${counts.failed} failed` },
            { dotClassName: "bg-muted-foreground", label: `${counts.total} total` },
          ]}
          title="Submitted links"
        />

        {items.length === 0 ? (
          <AdminEmptyState
            description="User-submitted links will appear here once the public submission form receives its first URL."
            icon={<ExternalLink className="size-6" aria-hidden />}
            title="No submissions yet"
          />
        ) : (
          <div className="flex flex-col divide-y divide-border rounded-xl border bg-card">
            {items.map((item) => (
              <AdminContentRow
                key={item.id}
                meta={
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={item.status} />
                    {formatDate(item.created_at) && (
                      <span className="text-[11px] text-muted-foreground">{formatDate(item.created_at)}</span>
                    )}
                  </div>
                }
                title={
                  <div className="flex items-start gap-2">
                    <span className="max-w-lg truncate text-sm font-medium">{item.url}</span>
                  </div>
                }
                actions={
                  <AdminListActions>
                    <AdminListActionLink href={`/admin/news/submitted-links/${item.id}`}>
                      <EyeIcon className="size-3.5" aria-hidden />
                      View
                    </AdminListActionLink>

                    <AdminListActionForm action={reprocessSubmissionAction}>
                      <input name="submissionId" type="hidden" value={item.id} />
                      <AdminListSubmitButton variant="outline">
                        <RefreshCw className="size-3.5" aria-hidden />
                        Reprocess
                      </AdminListSubmitButton>
                    </AdminListActionForm>

                    <AdminListActionLink href={item.url} rel="noopener noreferrer" target="_blank" variant="ghost">
                      <ExternalLink className="size-3" aria-hidden />
                      Open
                    </AdminListActionLink>
                  </AdminListActions>
                }
              >
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                  {item.submitter_name && <span>By {item.submitter_name}</span>}
                  {item.suggested_category && <span>Category: {item.suggested_category}</span>}
                  {item.processing_error && <span className="text-red-600">Error: {item.processing_error}</span>}
                </div>
              </AdminContentRow>
            ))}
          </div>
        )}
      </div>
  );
}
