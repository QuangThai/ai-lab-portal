"use client";

import { motion } from "framer-motion";
import { Clock, Edit3, ExternalLink, FileText, Globe } from "lucide-react";

import { AdminContentRow, adminListMotion } from "@/components/admin/admin-content-row";
import { AdminEmptyState } from "@/components/admin/admin-empty-state";
import { AdminStatusBadge } from "@/components/admin/admin-status-badge";
import {
  AdminListActionForm,
  AdminListActionLink,
  AdminListActions,
  AdminListSubmitButton,
} from "@/components/admin/admin-list-actions";
import { adminListPanelClass } from "@/components/admin/admin-ui";
import type { AdminBlogPost } from "./page";

function formatPublishedDate(publishedAt: string | null) {
  if (!publishedAt) return null;
  return new Date(publishedAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

type Props = {
  posts: AdminBlogPost[];
  publishAction: (formData: FormData) => Promise<void>;
  unpublishAction: (formData: FormData) => Promise<void>;
};

export function BlogPostCardList({ posts, publishAction, unpublishAction }: Props) {
  if (posts.length === 0) {
    return (
      <AdminEmptyState
        ctaHref="/admin/blog/editor"
        ctaLabel="New draft"
        description="Create your first draft to start the manual publishing workflow."
        icon={<FileText className="size-6" aria-hidden />}
        title="No blog posts yet"
      />
    );
  }

  return (
    <motion.ul
      variants={adminListMotion.container}
      initial="hidden"
      animate="show"
      className={adminListPanelClass}
    >
      {posts.map((post) => {
        const publishedLabel = formatPublishedDate(post.published_at);

        return (
          <AdminContentRow
            key={post.id}
            meta={
              <div className="flex flex-wrap items-center gap-2">
                <AdminStatusBadge status={post.status} />
                {publishedLabel ? (
                  <span className="text-[11px] text-muted-foreground">Published {publishedLabel}</span>
                ) : null}
              </div>
            }
            title={
              <h2 className="text-lg font-semibold leading-snug tracking-[-0.02em] text-foreground">
                {post.title}
              </h2>
            }
            actions={
              <AdminListActions>
                <AdminListActionLink href={`/admin/blog/${post.id}/edit`}>
                  <Edit3 className="size-3.5" aria-hidden />
                  Open editor
                </AdminListActionLink>

                <AdminListActionForm
                  action={post.status === "published" ? unpublishAction : publishAction}
                >
                  <input name="postId" type="hidden" value={post.id} />
                  <AdminListSubmitButton
                    variant={post.status === "published" ? "outline" : "secondary"}
                  >
                    {post.status === "published" ? (
                      <>
                        <Clock className="size-3.5" aria-hidden />
                        Unpublish
                      </>
                    ) : (
                      <>
                        <Globe className="size-3.5" aria-hidden />
                        Publish
                      </>
                    )}
                  </AdminListSubmitButton>
                </AdminListActionForm>

                {post.status === "published" ? (
                  <AdminListActionLink
                    href={`/blog/${post.slug}`}
                    rel="noopener noreferrer"
                    target="_blank"
                    variant="ghost"
                  >
                    <ExternalLink className="size-3" aria-hidden />
                    View
                  </AdminListActionLink>
                ) : null}
              </AdminListActions>
            }
          >
            <p className="text-sm text-muted-foreground">/{post.slug}</p>
          </AdminContentRow>
        );
      })}
    </motion.ul>
  );
}
