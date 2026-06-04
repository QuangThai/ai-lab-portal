"use client";

import { useState, useOptimistic, startTransition } from "react";
import { SendHorizonal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { BlogCommentPublic } from "@/lib/blog/social";

type Props = {
  slug: string;
  initialComments: BlogCommentPublic[];
  isAuthenticated: boolean;
  onCreateComment?: (slug: string, content: string, parentId: string | undefined) => Promise<void>;
};

function formatDate(dateStr: string) {
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

function CommentCard({
  comment,
  isAuthenticated,
  onReply,
}: {
  comment: BlogCommentPublic;
  isAuthenticated: boolean;
  onReply?: (parentId: string) => void;
}) {
  return (
    <div className="space-y-1.5" id={`comment-${comment.id}`}>
      <div className="flex items-center gap-2">
        <div className="flex size-6 items-center justify-center rounded-full bg-muted text-[10px] font-medium text-muted-foreground">
          {(comment.user_name ?? "A")[0].toUpperCase()}
        </div>
        <span className="text-sm font-medium">{comment.user_name ?? "Anonymous"}</span>
        <span className="text-xs text-muted-foreground">{formatDate(comment.created_at)}</span>
      </div>
      <p className="ml-8 text-sm leading-relaxed text-foreground/85">{comment.content}</p>
      {isAuthenticated && onReply && (
        <button
          type="button"
          onClick={() => onReply(comment.id)}
          className="ml-8 text-xs text-muted-foreground hover:text-foreground"
        >
          Reply
        </button>
      )}
    </div>
  );
}

export function BlogComments({
  slug,
  initialComments,
  isAuthenticated,
  onCreateComment,
}: Props) {
  const [comments, setComments] = useOptimistic(initialComments);
  const [content, setContent] = useState("");
  const [replyTo, setReplyTo] = useState<string | undefined>(undefined);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim() || !onCreateComment || isSubmitting) return;

    const trimmedContent = content.trim();
    const parentId = replyTo;

    setIsSubmitting(true);
    startTransition(async () => {
      const optimisticComment: BlogCommentPublic = {
        id: `optimistic-${Date.now()}`,
        user_name: "You",
        content: trimmedContent,
        parent_id: parentId ?? null,
        created_at: new Date().toISOString(),
      };
      setComments((prev) => [...prev, optimisticComment]);
      try {
        await onCreateComment(slug, trimmedContent, parentId);
        setContent("");
        setReplyTo(undefined);
      } catch {
        // Revert on error
      } finally {
        setIsSubmitting(false);
      }
    });
  }

  // Sort: oldest first
  const sortedComments = [...comments].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">
        Comments ({comments.length})
      </h3>

      {!isAuthenticated ? (
        <p className="text-sm text-muted-foreground">
          <a href="/login" className="font-medium text-brand underline underline-offset-2 hover:text-brand/80">
            Sign in
          </a>{" "}
          to leave a comment.
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            {replyTo && (
              <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
                <span>Replying to comment</span>
                <button
                  type="button"
                  onClick={() => setReplyTo(undefined)}
                  className="font-medium text-brand hover:text-brand/80"
                >
                  Cancel
                </button>
              </div>
            )}
            <div className="relative">
              <Input
                placeholder={replyTo ? "Write a reply..." : "Share your thoughts..."}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                disabled={isSubmitting}
                className="pr-12"
                maxLength={5000}
              />
              <Button
                type="submit"
                size="icon"
                disabled={!content.trim() || isSubmitting}
                className="absolute right-1 top-1/2 size-8 -translate-y-1/2"
                variant="ghost"
              >
                <SendHorizonal className="size-4" />
              </Button>
            </div>
          </div>
        </form>
      )}

      {sortedComments.length === 0 ? (
        <p className="text-sm text-muted-foreground">No comments yet. Be the first to share your thoughts!</p>
      ) : (
        <div className="flex flex-col gap-4">
          {sortedComments.map((comment) => (
            <CommentCard
              key={comment.id}
              comment={comment}
              isAuthenticated={isAuthenticated}
              onReply={replyTo ? undefined : setReplyTo}
            />
          ))}
        </div>
      )}
    </div>
  );
}
