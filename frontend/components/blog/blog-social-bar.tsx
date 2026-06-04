"use client";

import { useOptimistic, startTransition, useCallback } from "react";
import Link from "next/link";
import { Bookmark, Heart, MessageSquare } from "lucide-react";

import { cn } from "@/lib/utils";
import type { SocialStats } from "@/lib/blog/social";

type Props = {
  slug: string;
  initialStats: SocialStats | null;
  isAuthenticated: boolean;
  onToggleReaction?: (slug: string, emoji: string) => Promise<void>;
  onToggleBookmark?: (slug: string) => Promise<void>;
};

const EMOJIS = [
  { emoji: "👍", label: "Like" },
  { emoji: "❤️", label: "Love" },
  { emoji: "🚀", label: "Support" },
  { emoji: "👀", label: "Curious" },
  { emoji: "🎯", label: "Insightful" },
];

const EMPTY_STATS: SocialStats = {
  post_id: "",
  reaction_counts: {},
  user_reactions: [],
  is_bookmarked: false,
  comment_count: 0,
};

export function BlogSocialBar({
  slug,
  initialStats,
  isAuthenticated,
  onToggleReaction,
  onToggleBookmark,
}: Props) {
  const [stats, setStats] = useOptimistic(initialStats ?? EMPTY_STATS);

  const handleReaction = useCallback(
    (emoji: string) => {
      if (!isAuthenticated || !onToggleReaction) return;
      startTransition(async () => {
        // Optimistic update
        const isReacting = !stats.user_reactions.includes(emoji);
        setStats((prev) => ({
          ...prev,
          reaction_counts: {
            ...prev.reaction_counts,
            [emoji]: Math.max(0, (prev.reaction_counts[emoji] ?? 0) + (isReacting ? 1 : -1)),
          },
          user_reactions: isReacting
            ? [...prev.user_reactions, emoji]
            : prev.user_reactions.filter((e) => e !== emoji),
        }));
        try {
          await onToggleReaction(slug, emoji);
        } catch {
          // Revert on error — revalidation will fix
        }
      });
    },
    [isAuthenticated, onToggleReaction, setStats, slug, stats],
  );

  const handleBookmark = useCallback(() => {
    if (!isAuthenticated || !onToggleBookmark) return;
    startTransition(async () => {
      setStats((prev) => ({ ...prev, is_bookmarked: !prev.is_bookmarked }));
      try {
        await onToggleBookmark(slug);
      } catch {
        // Revert on error
      }
    });
  }, [isAuthenticated, onToggleBookmark, setStats, slug]);

  if (!isAuthenticated) {
    return (
      <div className="flex items-center gap-4 border-t border-border pt-4 text-sm text-muted-foreground">
        <Link href="/login" className="inline-flex items-center gap-1.5 hover:text-foreground">
          <Heart className="size-4" />
          Sign in to react
        </Link>
        <Link href="/login" className="inline-flex items-center gap-1.5 hover:text-foreground">
          <MessageSquare className="size-4" />
          Sign in to comment
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4 border-t border-border pt-4">
      {/* Reaction emoji bar */}
      <div className="flex flex-wrap items-center gap-2">
        {EMOJIS.map(({ emoji, label }) => {
          const count = stats.reaction_counts[emoji] ?? 0;
          const isActive = stats.user_reactions.includes(emoji);
          return (
            <button
              key={emoji}
              type="button"
              onClick={() => handleReaction(emoji)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition-all",
                isActive
                  ? "border-brand/40 bg-brand/10 text-brand"
                  : "border-border text-muted-foreground hover:border-muted-foreground/30 hover:text-foreground",
              )}
              title={label}
              aria-label={`${label}${count > 0 ? ` (${count})` : ""}`}
            >
              <span className="text-base leading-none" role="img" aria-hidden>
                {emoji}
              </span>
              {count > 0 && <span className="text-xs font-medium tabular-nums">{count}</span>}
            </button>
          );
        })}
      </div>

      {/* Action bar */}
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <button
          type="button"
          onClick={handleBookmark}
          className={cn(
            "inline-flex items-center gap-1.5 transition-colors hover:text-foreground",
            stats.is_bookmarked && "text-brand",
          )}
          aria-label={stats.is_bookmarked ? "Remove bookmark" : "Bookmark this post"}
        >
          <Bookmark className={cn("size-4", stats.is_bookmarked && "fill-current")} />
          {stats.is_bookmarked ? "Saved" : "Save"}
        </button>

        <span className="inline-flex items-center gap-1.5 text-muted-foreground">
          <MessageSquare className="size-4" />
          {stats.comment_count} {stats.comment_count === 1 ? "comment" : "comments"}
        </span>
      </div>
    </div>
  );
}
