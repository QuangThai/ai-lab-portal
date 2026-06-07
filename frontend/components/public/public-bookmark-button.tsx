"use client";

import { useRouter, usePathname } from "next/navigation";
import { useCallback, useEffect, useState, startTransition } from "react";
import { Bookmark } from "lucide-react";

import { cn } from "@/lib/utils";

type PublicBookmarkButtonProps = {
  slug: string;
};

export function PublicBookmarkButton({ slug }: PublicBookmarkButtonProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isBookmarked, setIsBookmarked] = useState(false);

  // Re-fetch bookmark state on navigation (e.g. after bookmarking on detail page)
  useEffect(() => {
    let cancelled = false;
    fetch("/api/auth/get-session")
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return;
        setIsAuthenticated(!!data?.user);
        if (data?.user) {
          fetch(`/api/bookmarks/check/${slug}`)
            .then((r) => r.json())
            .then((bData) => { if (!cancelled) setIsBookmarked(!!bData); })
            .catch(() => {});
        }
      })
      .catch(() => { if (!cancelled) setIsAuthenticated(false); });
    return () => { cancelled = true; };
  }, [slug, pathname]); // pathname dependency: re-fetch on page navigation

  const handleToggle = useCallback(async () => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    startTransition(async () => {
      setIsBookmarked((prev) => !prev);
      try {
        const res = await fetch(`/api/bookmarks/toggle/${slug}`, {
          method: "POST",
        });
        if (!res.ok) {
          setIsBookmarked((prev) => !prev);
        }
      } catch {
        setIsBookmarked((prev) => !prev);
      }
    });
  }, [isAuthenticated, slug, router]);

  if (isAuthenticated === null) {
    return (
      <span className="flex h-9 w-9 items-center justify-center">
        <span className="size-4 rounded bg-muted animate-pulse" />
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        e.preventDefault();
        handleToggle();
      }}
      className={cn(
        "flex h-9 w-9 items-center justify-center rounded-full transition-colors cursor-pointer",
        isBookmarked
          ? "text-brand hover:bg-brand/10"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
      aria-label={isBookmarked ? "Remove bookmark" : "Bookmark this post"}
    >
      <Bookmark className={cn("size-4", isBookmarked && "fill-current")} />
    </button>
  );
}
