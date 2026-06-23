"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  AtSign,
  BellDot,
  Check,
  CheckCheck,
  ChevronDown,
  Filter,
  Loader2,
  MessageSquareText,
  UserPlus,
} from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { useNotifications } from "@/components/session-provider";
import { cn } from "@/lib/utils";

// ─── Types ───────────────────────────────────────────────────────────────────

type NotificationSummary = {
  id: string;
  type: "follow" | "comment_reply" | "mention";
  actor_user_id: string;
  actor_email: string | null;
  actor_display_name: string | null;
  resource_id: string;
  resource_type: string;
  preview: string;
  group_key: string;
  link: string;
  read: boolean;
  created_at: string;
};

type Tab = "all" | "unread";
type TypeFilter = "all" | "follow" | "comment_reply" | "mention";

const PAGE_SIZE = 20;

const TYPE_CONFIG = {
  follow: {
    icon: UserPlus,
    label: "followed you",
    gradient: "from-blue-400 to-blue-600",
    dot: "bg-blue-500",
    ring: "ring-blue-300/30",
  },
  comment_reply: {
    icon: MessageSquareText,
    label: "replied to your comment",
    gradient: "from-emerald-400 to-emerald-600",
    dot: "bg-emerald-500",
    ring: "ring-emerald-300/30",
  },
  mention: {
    icon: AtSign,
    label: "mentioned you",
    gradient: "from-amber-400 to-amber-600",
    dot: "bg-amber-500",
    ring: "ring-amber-300/30",
  },
} as const;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatTime(createdAt: string): string {
  const now = Date.now();
  const diff = now - new Date(createdAt).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(createdAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatDateFull(createdAt: string): string {
  return new Date(createdAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ─── Notifications Page ──────────────────────────────────────────────────────

export default function NotificationsPage() {
  const { unreadCount, setUnreadCount, refreshUnreadCount } = useNotifications();

  // State
  const [notifications, setNotifications] = useState<NotificationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [tab, setTab] = useState<Tab>("all");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const offsetRef = useRef(0);
  const mountedRef = useRef(false);

  // ── Fetch ──────────────────────────────────────────────────────────────────

  const fetchNotifications = useCallback(
    async (append = false) => {
      if (!append) {
        setLoading(true);
        offsetRef.current = 0;
      } else {
        setLoadingMore(true);
      }

      try {
        const params = new URLSearchParams();
        if (!append) params.set("offset", "0");
        else params.set("offset", String(offsetRef.current));
        params.set("limit", String(PAGE_SIZE));

        const response = await fetch(`/api/notifications?${params.toString()}`, { cache: "no-store" });
        if (!response.ok) return;

        const data = (await response.json()) as NotificationSummary[];
        if (append) {
          setNotifications((prev) => [...prev, ...data]);
        } else {
          setNotifications(data);
        }

        setHasMore(data.length === PAGE_SIZE);
        offsetRef.current += data.length;
      } catch {
        // ignore
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [],
  );

  // Initial load
  useEffect(() => {
    if (mountedRef.current) return;
    mountedRef.current = true;
    fetchNotifications();
  });

  // Refresh on mount / visibility
  useEffect(() => {
    refreshUnreadCount();
  }, [refreshUnreadCount]);

  // ── Filtered list (client-side) ────────────────────────────────────────────

  const filtered = notifications.filter((n) => {
    if (tab === "unread" && n.read) return false;
    if (typeFilter !== "all" && n.type !== typeFilter) return false;
    return true;
  });

  // ── Actions ────────────────────────────────────────────────────────────────

  const handleMarkRead = async (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    setUnreadCount((prev) => Math.max(0, prev - 1));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });

    try {
      await fetch("/api/notifications", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ path: `${id}/read`, method: "POST" }),
      });
    } catch {
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: false } : n)));
      setUnreadCount((prev) => prev + 1);
    }
  };

  const handleMarkAllRead = async () => {
    const ids = filtered.filter((n) => !n.read).map((n) => n.id);
    if (ids.length === 0) return;

    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnreadCount(0);
    setSelectedIds(new Set());

    try {
      await fetch("/api/notifications", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ path: "read-all", method: "POST" }),
      });
    } catch {
      fetchNotifications();
    }
  };

  const handleMarkSelectedRead = async () => {
    for (const id of selectedIds) {
      await handleMarkRead(id);
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const hasUnreadFiltered = filtered.some((n) => !n.read);

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <PublicPageShell currentPath="/notifications">
      <div className={cn(publicMainWidthClass, "flex flex-col gap-6")}>
        {/* Back */}
        <PublicBackLink href="/blog">Blog</PublicBackLink>

        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold tracking-tight">Notifications</h1>
            <p className="text-sm text-muted-foreground">
              {filtered.length === 0
                ? "No notifications"
                : `${filtered.length} notification${filtered.length === 1 ? "" : "s"}`}
              {unreadCount > 0 && (
                <span className="ml-1.5 text-muted-foreground/60">
                  · {unreadCount} unread
                </span>
              )}
            </p>
          </div>

          {hasUnreadFiltered && (
            <button
              type="button"
              onClick={handleMarkAllRead}
              className="inline-flex items-center gap-1.5 rounded-full border border-border/60 px-3.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-border hover:bg-muted hover:text-foreground"
            >
              <CheckCheck className="size-3.5" />
              Mark all read
            </button>
          )}
        </div>

        {/* Toolbar: Tabs + Type Filter */}
        <div className="flex items-center gap-3">
          {/* Tabs */}
          <div className="flex items-center rounded-xl border border-border/60 bg-card p-0.5 shadow-xs">
            {(["all", "unread"] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={cn(
                  "rounded-[10px] px-3.5 py-1.5 text-xs font-medium transition-all",
                  tab === t
                    ? "bg-brand text-brand-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {t === "all" ? "All" : "Unread"}
                {t === "unread" && unreadCount > 0 && (
                  <span className="ml-1.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-brand/20 px-1 text-[10px] font-bold text-brand">
                    {unreadCount}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Type filter */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="inline-flex items-center gap-1.5 rounded-xl border border-border/60 px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-border hover:bg-muted hover:text-foreground"
              >
                <Filter className="size-3" aria-hidden />
                {typeFilter === "all" ? "All types" : TYPE_CONFIG[typeFilter]?.label ?? typeFilter}
                <ChevronDown className="size-3" aria-hidden />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="min-w-40">
              <DropdownMenuRadioGroup
                value={typeFilter}
                onValueChange={(v) => setTypeFilter(v as TypeFilter)}
              >
                <DropdownMenuRadioItem value="all">All types</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="follow">Follows</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="comment_reply">Comment replies</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="mention">Mentions</DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Batch mark selected read */}
          {selectedIds.size > 0 && (
            <button
              type="button"
              onClick={handleMarkSelectedRead}
              className="inline-flex items-center gap-1.5 rounded-xl border border-border/60 px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-border hover:bg-muted hover:text-foreground"
            >
              <Check className="size-3" />
              Mark {selectedIds.size} read
            </button>
          )}
        </div>

        {/* List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="size-5 animate-spin text-muted-foreground" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-20 text-center">
            <div className="relative mb-2">
              <div className="absolute -inset-4 rounded-full bg-brand/5 blur-xl" aria-hidden />
              <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-brand/10 to-brand/5 ring-1 ring-brand/10">
                <BellDot className="size-7 text-brand/30" aria-hidden />
              </div>
            </div>
            <p className="text-sm font-medium text-foreground/80">
              {tab === "unread" ? "All caught up" : "No notifications yet"}
            </p>
            <p className="max-w-xs text-xs leading-relaxed text-muted-foreground/60">
              {tab === "unread"
                ? "You've read everything. New notifications will appear here."
                : "Follows, comment replies, and mentions will appear here when they come in."}
            </p>
          </div>
        ) : (
          <>
            <div className="flex flex-col divide-y divide-border/50 overflow-hidden rounded-xl border border-border/60 bg-card shadow-xs">
              {filtered.map((notification) => {
                const config = TYPE_CONFIG[notification.type] ?? TYPE_CONFIG.follow;
                const TypeIcon = config.icon;
                const actorName = notification.actor_display_name
                  || notification.actor_email
                  || "Someone";
                const isSelected = selectedIds.has(notification.id);

                return (
                  <div
                    key={notification.id}
                    className={cn(
                      "group relative transition-colors",
                      !notification.read && "bg-gradient-to-r from-accent/30 via-accent/5 to-transparent",
                      isSelected && "bg-accent/20",
                    )}
                  >
                    <div className="flex items-start gap-3 px-4 py-4 sm:px-5 sm:py-3.5">
                      {/* Selection checkbox */}
                      <button
                        type="button"
                        onClick={() => toggleSelect(notification.id)}
                        className={cn(
                          "mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition-colors",
                          isSelected
                            ? "border-brand bg-brand text-brand-foreground"
                            : "border-border hover:border-muted-foreground/30",
                        )}
                        aria-label={isSelected ? "Deselect" : "Select"}
                      >
                        {isSelected && <Check className="size-3" />}
                      </button>

                      {/* Type icon */}
                      <span
                        className={cn(
                          "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br shadow-xs",
                          config.gradient,
                        )}
                      >
                        <TypeIcon className="size-4 text-white" aria-hidden />
                      </span>

                      {/* Content */}
                      <Link
                        href={notification.link || "#"}
                        onClick={() => {
                          if (!notification.read) handleMarkRead(notification.id);
                        }}
                        className="min-w-0 flex-1"
                      >
                        <div className="flex items-start gap-2.5">
                          <div className="min-w-0 flex-1">
                            <p className={cn(
                              "text-sm leading-snug",
                              !notification.read && "font-medium",
                            )}>
                              <span className="text-foreground">{actorName}</span>{" "}
                              <span className="text-muted-foreground">{config.label}</span>
                            </p>

                            {notification.preview && (
                              <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-muted-foreground/70 italic">
                                &ldquo;{notification.preview}&rdquo;
                              </p>
                            )}

                            <p className="mt-1.5 text-[11px] text-muted-foreground/50" title={formatDateFull(notification.created_at)}>
                              {formatTime(notification.created_at)}
                            </p>
                          </div>
                        </div>
                      </Link>

                      {/* Right side: unread dot + actions */}
                      <div className="flex shrink-0 items-center gap-2">
                        {!notification.read && (
                          <span className="h-2 w-2 rounded-full bg-brand" aria-hidden />
                        )}

                        {!notification.read && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMarkRead(notification.id);
                            }}
                            className="flex h-7 w-7 items-center justify-center rounded-full opacity-0 transition-all hover:bg-muted group-hover:opacity-100"
                            aria-label="Mark as read"
                          >
                            <Check className="size-3.5 text-muted-foreground" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Load more */}
            {hasMore && (
              <div className="flex justify-center py-4">
                <button
                  type="button"
                  onClick={() => fetchNotifications(true)}
                  disabled={loadingMore}
                  className="inline-flex items-center gap-2 rounded-full border border-border/60 px-5 py-2 text-xs font-medium text-muted-foreground transition-colors hover:border-border hover:bg-muted hover:text-foreground disabled:opacity-50"
                >
                  {loadingMore ? (
                    <>
                      <Loader2 className="size-3.5 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    <>
                      <ChevronDown className="size-3.5" />
                      Load more
                    </>
                  )}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </PublicPageShell>
  );
}
