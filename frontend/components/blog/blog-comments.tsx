"use client";

import { useState, useOptimistic, startTransition, useCallback } from "react";
import Link from "next/link";
import { Heart, MessageCircle, ChevronUp, ChevronDown, Pencil, Trash2, Check, X } from "lucide-react";

import { CommentTiptapEditor } from "@/components/blog/comment-tiptap-editor";
import { Avatar } from "@/components/public/public-avatar";
import type { BlogCommentPublic } from "@/lib/blog/social";
import { cn } from "@/lib/utils";

type Props = {
  slug: string;
  initialComments: BlogCommentPublic[];
  isAuthenticated: boolean;
  session?: { user: { id: string; name?: string; email: string; image?: string | null } } | null;
  onCreateComment?: (slug: string, content: string, parentId: string | undefined) => Promise<void>;
  onToggleCommentReaction?: (slug: string, commentId: string) => Promise<{ reacted: boolean; count: number }>;
  onEditComment?: (slug: string, commentId: string, content: string) => Promise<BlogCommentPublic>;
  onDeleteComment?: (slug: string, commentId: string) => Promise<{ deleted: boolean }>;
};

type CommentNode = BlogCommentPublic & { replies: CommentNode[] };

const MAX_THREAD_DEPTH = 5;

function formatRelativeTime(dateStr: string): string {
  try {
    const ms = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(ms / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return dateStr;
  }
}

function formatAbsoluteDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

/** Check if content looks like HTML (new TipTap comments) vs plain text (legacy) */
function isHtmlContent(content: string): boolean {
  return /<\/?[a-z][\s>]/.test(content);
}

/** Render comment content safely — TipTap HTML or legacy plain text */
function sanitizeHtml(html: string): string {
  // Strip all HTML tags except a safe subset
  return html
    .replace(/<script[^>]*>[^<]*<\/script>/gi, "")
    .replace(/<\/?[^>]+(>|$)/g, (match) => {
      const tag = match.replace(/<\/?|>/g, "").split(/\s+/)[0].toLowerCase();
      const safeTags = new Set(["b", "i", "em", "strong", "a", "code", "pre", "p", "br", "ul", "ol", "li", "blockquote"]);
      if (safeTags.has(tag) || match.startsWith("</")) return match;
      return "";
    })
    .replace(/<a\s+(?:[^>]*?\s+)?href\s*=\s*"?(?!https?:\/\/|\/|#)([^"]*)"?[^>]*>/gi, "<a href=\"#\">");
}

function renderCommentContent(content: string): string {
  if (!content) return "";
  const sanitized = sanitizeHtml(content);
  if (isHtmlContent(sanitized)) return sanitized;
  // Legacy plain text: escape and wrap in paragraphs
  const escaped = content
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped
    .split(/\n{2,}/)
    .map((p) => `<p>${p.replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function buildTree(comments: BlogCommentPublic[]): CommentNode[] {
  const nodes = new Map<string, CommentNode>();
  const roots: CommentNode[] = [];

  for (const comment of comments) {
    nodes.set(comment.id, { ...comment, replies: [], reaction_count: comment.reaction_count ?? 0, user_reacted: comment.user_reacted ?? false });
  }

  for (const node of nodes.values()) {
    const parent = node.parent_id ? nodes.get(node.parent_id) : undefined;
    if (parent) parent.replies.push(node);
    else roots.push(node);
  }

  const byDate = (a: CommentNode, b: CommentNode) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
  function sort(nodesToSort: CommentNode[]) {
    nodesToSort.sort(byDate);
    for (const node of nodesToSort) sort(node.replies);
  }
  sort(roots);
  return roots;
}

// ─── Sort toggle ────────────────────────────────────────────────────────

function SortToggle({ sort, onChange }: { sort: "oldest" | "newest"; onChange: (s: "oldest" | "newest") => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(sort === "oldest" ? "newest" : "oldest")}
      className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
    >
      {sort === "oldest" ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
      {sort === "oldest" ? "Oldest first" : "Newest first"}
    </button>
  );
}

// ─── Comment card ───────────────────────────────────────────────────────

function CommentCard({
  node,
  depth,
  slug,
  isAuthenticated,
  currentUserId,
  session,
  onCreateComment,
  onToggleReaction,
  onEditComment,
  onDeleteComment,
}: {
  node: CommentNode;
  depth: number;
  slug: string;
  isAuthenticated: boolean;
  currentUserId?: string;
  session?: { user: { id: string; name?: string; email: string; image?: string | null } } | null;
  onCreateComment?: (slug: string, content: string, parentId: string | undefined) => Promise<void>;
  onToggleReaction?: (slug: string, commentId: string) => Promise<{ reacted: boolean; count: number }>;
  onEditComment?: (slug: string, commentId: string, content: string) => Promise<BlogCommentPublic>;
  onDeleteComment?: (slug: string, commentId: string) => Promise<{ deleted: boolean }>;
}) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isReacted, setIsReacted] = useState(node.user_reacted ?? false);
  const [reactionCount, setReactionCount] = useState(node.reaction_count ?? 0);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const isOwn = currentUserId === node.user_id;
  const canNest = depth < MAX_THREAD_DEPTH - 1;

  const handleReply = useCallback(
    async (content: string) => {
      if (!onCreateComment) return;
      setIsSubmitting(true);
      try {
        await onCreateComment(slug, content, node.id);
        setShowReplyForm(false);
      } finally {
        setIsSubmitting(false);
      }
    },
    [onCreateComment, slug, node.id],
  );

  const handleReaction = useCallback(async () => {
    if (!onToggleReaction || !isAuthenticated) return;
    startTransition(async () => {
      setIsReacted((prev) => !prev);
      setReactionCount((prev) => (isReacted ? Math.max(0, prev - 1) : prev + 1));
      try {
        const result = await onToggleReaction(slug, node.id);
        setIsReacted(result.reacted);
        setReactionCount(result.count);
      } catch {
        setIsReacted((prev) => !prev);
        setReactionCount((prev) => (isReacted ? prev + 1 : Math.max(0, prev - 1)));
      }
    });
  }, [onToggleReaction, isAuthenticated, slug, node.id, isReacted]);

  const handleEditSave = useCallback(async (html: string) => {
    if (!onEditComment) return;
    const text = html.replace(/<[^>]*>/g, "").trim();
    if (!text) return;
    setIsSubmitting(true);
    try {
      await onEditComment(slug, node.id, html);
      setIsEditing(false);
    } finally {
      setIsSubmitting(false);
    }
  }, [onEditComment, slug, node.id]);

  const handleDelete = useCallback(async () => {
    if (!onDeleteComment) return;
    setIsSubmitting(true);
    try {
      await onDeleteComment(slug, node.id);
      setShowDeleteConfirm(false);
    } finally {
      setIsSubmitting(false);
    }
  }, [onDeleteComment, slug, node.id]);

  const showActions = isAuthenticated;

  return (
    <div id={`comment-${node.id}`} className="group/comment">
      <div className={cn("flex gap-3", depth > 0 && "ml-2")}>
        {/* Thread line + avatar column */}
        <div className="flex flex-col items-center shrink-0">
          {depth > 0 ? (
            <div className="flex flex-col items-center">
              <span className="block h-4 w-px bg-gradient-to-b from-border/40 to-transparent" aria-hidden />
              <Avatar src={node.avatar_url} name={node.user_name} size="md" className="ring-2 ring-background" />
            </div>
          ) : (
            <Avatar src={node.avatar_url} name={node.user_name} size="md" className="ring-2 ring-background" />
          )}
        </div>

        {/* Content column — border-l serves as the thread line for nested comments */}
        <div className={cn("min-w-0 flex-1 pb-5", depth > 0 && "border-l border-border/20 pl-4")}>
          {/* Header */}
          <div className="flex items-center gap-2">
            <Link
              href={`/profiles/${node.user_id}`}
              className="text-sm font-semibold text-foreground hover:text-brand transition-colors"
            >
              {node.user_name ?? "Anonymous"}
            </Link>
            <span className="text-xs text-muted-foreground" title={formatAbsoluteDate(node.created_at)}>
              {formatRelativeTime(node.created_at)}
            </span>
            {node.updated_at && node.updated_at !== node.created_at && (
              <span className="text-[11px] font-medium text-muted-foreground/60" title={formatAbsoluteDate(node.updated_at)}>
                · edited
              </span>
            )}

            {/* Actions (always visible on mobile, hover on desktop) */}
            <div className={cn(
              "ml-auto flex items-center gap-0.5",
              "md:opacity-0 md:group-hover/comment:opacity-100 transition-opacity",
              isOwn && "md:opacity-100",
            )}>
              {showActions && (
                <button
                  type="button"
                  onClick={handleReaction}
                  className={cn(
                    "flex items-center gap-1 rounded-md px-1.5 py-1 text-xs transition-colors min-h-[44px]",
                    isReacted ? "text-red-500" : "text-muted-foreground hover:text-foreground hover:bg-muted",
                  )}
                  aria-label={isReacted ? "Remove reaction" : "Like this comment"}
                >
                  <Heart className={cn("size-3.5", isReacted && "fill-current")} />
                  {reactionCount > 0 && <span className="tabular-nums">{reactionCount}</span>}
                </button>
              )}
              {showActions && canNest && (
                <button
                  type="button"
                  onClick={() => setShowReplyForm(!showReplyForm)}
                  className="flex items-center gap-1 rounded-md px-1.5 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors min-h-[44px]"
                >
                  <MessageCircle className="size-3.5" />
                  Reply
                </button>
              )}
              {isOwn && !isEditing && (
                <>
                  <button
                    type="button"
                    onClick={() => setIsEditing(true)}
                    className="flex items-center gap-1 rounded-md px-1.5 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors min-h-[44px]"
                    aria-label="Edit comment"
                  >
                    <Pencil className="size-3.5" />
                  </button>
                  {showDeleteConfirm ? (
                    <span className="flex items-center gap-0.5">
                      <button
                        type="button"
                        onClick={handleDelete}
                        disabled={isSubmitting}
                        className="flex items-center gap-1 rounded-md px-1.5 py-1 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors min-h-[44px]"
                      >
                        <Check className="size-3.5" /> Delete
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowDeleteConfirm(false)}
                        className="flex items-center gap-1 rounded-md px-1.5 py-1 text-xs text-muted-foreground hover:bg-muted transition-colors min-h-[44px]"
                      >
                        <X className="size-3.5" />
                      </button>
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setShowDeleteConfirm(true)}
                      className="flex items-center gap-1 rounded-md px-1.5 py-1 text-xs text-muted-foreground hover:text-red-500 hover:bg-muted transition-colors min-h-[44px]"
                      aria-label="Delete comment"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Content */}
          {isEditing ? (
            <div className="mt-2">
              <CommentTiptapEditor
                onSubmit={handleEditSave}
                autoFocus
                onCancel={() => setIsEditing(false)}
                isSubmitting={isSubmitting}
                session={session}
                initialContent={node.content}
              />
            </div>
          ) : (
            <div className="mt-1.5">
              <div
                className="text-sm leading-7 text-foreground/85 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 prose prose-sm max-w-none dark:prose-invert"
                dangerouslySetInnerHTML={{ __html: renderCommentContent(node.content) }}
              />
            </div>
          )}

          {/* Reply form */}
          {showReplyForm && (
            <div className="mt-4">
              <CommentTiptapEditor
                onSubmit={handleReply}
                placeholder="Write a reply..."
                autoFocus
                onCancel={() => setShowReplyForm(false)}
                isSubmitting={isSubmitting}
                session={session}
              />
            </div>
          )}
        </div>
      </div>

      {/* Nested replies */}
      {node.replies.length > 0 && (
        <div className="ml-3">
          {node.replies.map((reply) => (
            <CommentCard
              key={reply.id}
              node={reply}
              depth={depth + 1}
              slug={slug}
              isAuthenticated={isAuthenticated}
              currentUserId={currentUserId}
              session={session}
              onCreateComment={onCreateComment}
              onToggleReaction={onToggleReaction}
              onEditComment={onEditComment}
              onDeleteComment={onDeleteComment}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main BlogComments component ────────────────────────────────────────

export function BlogComments({
  slug,
  initialComments,
  isAuthenticated,
  session,
  onCreateComment,
  onToggleCommentReaction,
  onEditComment,
  onDeleteComment,
}: Props) {
  const [comments, setComments] = useOptimistic(initialComments);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sort, setSort] = useState<"oldest" | "newest">("oldest");

  const handleCreateComment = useCallback(
    async (content: string) => {
      if (!onCreateComment) return;
      setIsSubmitting(true);
      startTransition(async () => {
        const optimistic: BlogCommentPublic = {
          id: `opt-${Date.now()}`,
          user_id: session?.user.id ?? "me",
          user_name: session?.user.name ?? "You",
          avatar_url: session?.user.image ?? null,
          content,
          parent_id: null,
          created_at: new Date().toISOString(),
          updated_at: null,
          reaction_count: 0,
          user_reacted: false,
        };
        setComments((prev) => [...prev, optimistic]);
        try {
          await onCreateComment(slug, content, undefined);
        } finally {
          setIsSubmitting(false);
        }
      });
    },
    [onCreateComment, setComments, session, slug],
  );

  let tree = buildTree(comments);
  if (sort === "newest") {
    function sortDesc(nodes: CommentNode[]): CommentNode[] {
      nodes.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      for (const node of nodes) sortDesc(node.replies);
      return nodes;
    }
    tree = sortDesc(tree);
  }

  return (
    <div className="space-y-6" id="comments">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-foreground">
          Discussion{" "}
          <span className="text-muted-foreground font-normal">({comments.length})</span>
        </h3>
        {comments.length > 1 && <SortToggle sort={sort} onChange={setSort} />}
      </div>

      {/* Comment form */}
      {isAuthenticated ? (
        <CommentTiptapEditor
          onSubmit={handleCreateComment}
          session={session}
          isSubmitting={isSubmitting}
        />
      ) : (
        <div className="flex gap-4">
          <Avatar name="?" size="md" className="mt-0.5" />
          <div className="flex-1 rounded-2xl border border-dashed border-border/60 bg-card/30 px-6 py-5">
            <p className="text-sm leading-relaxed text-muted-foreground">
              <Link
                href="/login"
                className="font-semibold text-brand underline underline-offset-2 hover:text-brand/80"
              >
                Sign in
              </Link>{" "}
              to join the discussion.
            </p>
          </div>
        </div>
      )}

      {/* Comments */}
      {tree.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-20 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-muted/50 text-muted-foreground/40">
            <MessageCircle className="size-6" />
          </span>
          <div className="space-y-1">
            <p className="text-sm font-semibold text-foreground">No comments yet</p>
            <p className="text-sm text-muted-foreground">Be the first to share your thoughts!</p>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {tree.map((node) => (
            <CommentCard
              key={node.id}
              node={node}
              depth={0}
              slug={slug}
              isAuthenticated={isAuthenticated}
              currentUserId={session?.user.id}
              session={session}
              onCreateComment={onCreateComment}
              onToggleReaction={onToggleCommentReaction}
              onEditComment={onEditComment}
              onDeleteComment={onDeleteComment}
            />
          ))}
        </div>
      )}
    </div>
  );
}
