"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import {
  AtSign,
  Bell,
  Check,
  CheckCheck,
  MessageSquare,
  UserPlus,
} from "lucide-react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
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

// ─── Helpers ─────────────────────────────────────────────────────────────────

const TYPE_CONFIG = {
  follow: {
    icon: UserPlus,
    label: "followed you",
    color: "text-blue-500",
    bg: "bg-blue-500/10",
    dot: "bg-blue-500",
  },
  comment_reply: {
    icon: MessageSquare,
    label: "replied to your comment",
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    dot: "bg-emerald-500",
  },
  mention: {
    icon: AtSign,
    label: "mentioned you",
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    dot: "bg-amber-500",
  },
} as const;

function timeAgo(createdAt: string): string {
  const now = Date.now();
  const diff = now - new Date(createdAt).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

function ActorAvatar({
  displayName,
  email,
}: {
  displayName: string | null;
  email: string | null;
}) {
  const name = displayName || email || "?";
  const initial = name.charAt(0).toUpperCase();
  return (
    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted-foreground/20 text-xs font-semibold text-muted-foreground">
      {initial}
    </span>
  );
}

// ─── Component ───────────────────────────────────────────────────────────────

export function NotificationBell() {
  const { unreadCount, setUnreadCount } = useNotifications();
  const [notifications, setNotifications] = useState<NotificationSummary[]>([]);
  const [open, setOpen] = useState(false);

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await fetch("/api/notifications");
      if (response.ok) {
        const data = (await response.json()) as NotificationSummary[];
        setNotifications(data);
        setUnreadCount(data.filter((n) => !n.read).length);
      }
    } catch {
      // ignore
    }
  }, [setUnreadCount]);

  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (isOpen) {
      fetchNotifications().catch(() => {});
    }
  };

  const handleMarkRead = async (notificationId: string) => {
    try {
      await fetch("/api/notifications", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ path: `${notificationId}/read`, method: "POST" }),
      });
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n)),
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      // ignore
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await fetch("/api/notifications", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ path: "read-all", method: "POST" }),
      });
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch {
      // ignore
    }
  };

  const hasUnread = notifications.some((n) => !n.read);

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
          className="relative inline-flex h-10 w-10 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <Bell className="size-4" aria-hidden />
          {unreadCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground ring-2 ring-background">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-96 p-0" sideOffset={8}>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <Bell className="size-4 text-muted-foreground" />
            <span className="text-sm font-semibold">Notifications</span>
            {unreadCount > 0 && (
              <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-muted px-1.5 text-[11px] font-medium text-muted-foreground">
                {unreadCount}
              </span>
            )}
          </div>
          {hasUnread && (
            <button
              type="button"
              onClick={handleMarkAllRead}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              <CheckCheck className="size-3.5" aria-hidden />
              Mark all read
            </button>
          )}
        </div>

        {/* List */}
        <div className="max-h-96 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-4 py-10 text-center">
              <Bell className="size-8 text-muted-foreground/40" aria-hidden />
              <p className="text-sm text-muted-foreground">No notifications yet</p>
              <p className="text-xs text-muted-foreground/60">
                Follows, comment replies, and mentions will appear here
              </p>
            </div>
          ) : (
            notifications.map((notification) => {
              const config = TYPE_CONFIG[notification.type] ?? TYPE_CONFIG.follow;
              const TypeIcon = config.icon;
              const actorName = notification.actor_display_name
                || notification.actor_email
                || "Someone";

              return (
                <div
                  key={notification.id}
                  className={cn(
                    "group relative border-b border-border transition-colors last:border-b-0",
                    !notification.read && "bg-accent/20",
                    notification.read && "opacity-70",
                  )}
                >
                  {/* Clickable content area → navigate */}
                  <Link
                    href={notification.link || "#"}
                    onClick={(e) => {
                      if (!notification.read) {
                        handleMarkRead(notification.id);
                      }
                      // If notification has no link, prevent navigation
                      if (!notification.link) {
                        e.preventDefault();
                      }
                    }}
                    className={cn(
                      "flex items-start gap-3 px-4 py-3 transition-colors hover:bg-muted/50",
                    )}
                  >
                    {/* Type icon (left side indicator) */}
                    <span
                      className={cn(
                        "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                        config.bg,
                      )}
                    >
                      <TypeIcon className={cn("size-3.5", config.color)} aria-hidden />
                    </span>

                    {/* Content */}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start gap-2">
                        <ActorAvatar
                          displayName={notification.actor_display_name}
                          email={notification.actor_email}
                        />
                        <div className="min-w-0 flex-1">
                          <p className={cn("text-sm leading-snug", !notification.read && "font-medium")}>
                            <span className="text-foreground">{actorName}</span>{" "}
                            <span className="text-muted-foreground">{config.label}</span>
                          </p>
                          {/* Preview */}
                          {notification.preview && (
                            <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground/80">
                              &ldquo;{notification.preview}&rdquo;
                            </p>
                          )}
                          {/* Time */}
                          <p className="mt-0.5 text-[11px] text-muted-foreground/60">
                            {timeAgo(notification.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Unread dot */}
                    {!notification.read && (
                      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand" aria-hidden />
                    )}
                  </Link>

                  {/* Mark-read button on hover */}
                  {!notification.read && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        handleMarkRead(notification.id);
                      }}
                      className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full opacity-0 transition-opacity hover:bg-muted group-hover:opacity-100"
                      aria-label="Mark as read"
                    >
                      <Check className="size-3.5 text-muted-foreground" />
                    </button>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        {notifications.length > 0 && (
          <div className="border-t border-border px-4 py-2">
            <Link
              href="/notifications"
              className="block text-center text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              View all notifications
            </Link>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
