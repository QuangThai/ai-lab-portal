import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { Check, ExternalLink, X } from "lucide-react";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { AdminContentRow } from "@/components/admin/admin-content-row";
import { AdminEmptyState } from "@/components/admin/admin-empty-state";
import {
  AdminListActionForm,
  AdminListActionLink,
  AdminListActions,
  AdminListSubmitButton,
} from "@/components/admin/admin-list-actions";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminListToolbar } from "@/components/admin/admin-list-toolbar";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

import { approveCommentAction, rejectCommentAction } from "./actions";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type AdminComment = {
  id: string;
  post_id: string;
  post_title: string;
  user_id: string;
  user_email: string | null;
  user_name: string | null;
  content: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
};

async function listComments() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/blog-comments`, {
    headers: createAdminBoundaryHeaders({ user: { id: session.user.id, email: session.user.email } }),
    cache: "no-store",
  });

  if (!response.ok) throw new Error(`Failed to fetch comments: ${response.status}`);
  return (await response.json()) as AdminComment[];
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StatusBadge({ status }: { status: AdminComment["status"] }) {
  const colorMap: Record<string, string> = {
    pending: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/25",
    approved: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/25",
    rejected: "bg-red-500/10 text-red-700 dark:text-red-300 border-red-500/25",
  };

  return (
    <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium", colorMap[status] || "")}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export default async function AdminBlogCommentsPage() {
  const comments = await listComments();

  const counts = {
    total: comments.length,
    pending: comments.filter((c) => c.status === "pending").length,
    approved: comments.filter((c) => c.status === "approved").length,
    rejected: comments.filter((c) => c.status === "rejected").length,
  };

  return (
    <AdminCmsShell active="blog-comments">
      <div className={adminPageStackClass}>
        <AdminListToolbar
          description="Comments on blog posts from registered users. Approve or reject pending items."
          eyebrow="Blog"
          metrics={[
            { dotClassName: "bg-amber-500", label: `${counts.pending} pending` },
            { dotClassName: "bg-emerald-500", label: `${counts.approved} approved` },
            { dotClassName: "bg-muted-foreground", label: `${counts.total} total` },
          ]}
          title="Comments"
        />

        {comments.length === 0 ? (
          <AdminEmptyState
            description="No comments yet. Comments will appear once users start engaging with blog posts."
            icon={<ExternalLink className="size-6" aria-hidden />}
            title="No comments"
          />
        ) : (
          <div className="flex flex-col divide-y divide-border rounded-xl border bg-card">
            {comments.map((comment) => (
              <AdminContentRow
                key={comment.id}
                meta={
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={comment.status} />
                    <span className="text-[11px] text-muted-foreground">{formatDate(comment.created_at)}</span>
                  </div>
                }
                title={
                  <div className="line-clamp-2 text-sm">
                    {comment.content}
                  </div>
                }
                actions={
                  <AdminListActions>
                    {comment.status === "pending" && (
                      <>
                        <AdminListActionForm action={approveCommentAction}>
                          <input name="commentId" type="hidden" value={comment.id} />
                          <AdminListSubmitButton variant="brand">
                            <Check className="size-3.5" aria-hidden />
                            Approve
                          </AdminListSubmitButton>
                        </AdminListActionForm>

                        <AdminListActionForm action={rejectCommentAction}>
                          <input name="commentId" type="hidden" value={comment.id} />
                          <AdminListSubmitButton variant="destructive">
                            <X className="size-3.5" aria-hidden />
                            Reject
                          </AdminListSubmitButton>
                        </AdminListActionForm>
                      </>
                    )}
                    <AdminListActionLink href={`/blog/${comment.post_title || comment.post_id}`}>
                      <ExternalLink className="size-3.5" aria-hidden />
                      View post
                    </AdminListActionLink>
                  </AdminListActions>
                }
              >
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                  {comment.user_name && <span>By {comment.user_name}</span>}
                  {comment.user_email && <span>{comment.user_email}</span>}
                </div>
              </AdminContentRow>
            ))}
          </div>
        )}
      </div>
    </AdminCmsShell>
  );
}
