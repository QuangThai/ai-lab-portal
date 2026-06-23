"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  AtSign,
  Bell,
  BellDot,
  Check,
  CheckCheck,
  MessageSquareText,
  UserPlus,
} from "lucide-react";
import {
  AnimatePresence,
  motion,
  type Variants,
} from "framer-motion";

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

// ─── Design tokens per type ──────────────────────────────────────────────────

const TYPE_CONFIG = {
  follow: {
    icon: UserPlus,
    label: "followed you",
    gradient: "from-blue-400 to-blue-600",
    glow: "shadow-blue-500/20",
    dot: "bg-blue-500",
    ring: "ring-blue-300/30",
  },
  comment_reply: {
    icon: MessageSquareText,
    label: "replied to your comment",
    gradient: "from-emerald-400 to-emerald-600",
    glow: "shadow-emerald-500/20",
    dot: "bg-emerald-500",
    ring: "ring-emerald-300/30",
  },
  mention: {
    icon: AtSign,
    label: "mentioned you",
    gradient: "from-amber-400 to-amber-600",
    glow: "shadow-amber-500/20",
    dot: "bg-amber-500",
    ring: "ring-amber-300/30",
  },
} as const;

// ─── Helpers ─────────────────────────────────────────────────────────────────

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
  gradientRing,
}: {
  displayName: string | null;
  email: string | null;
  gradientRing: string;
}) {
  const name = displayName || email || "?";
  const initial = name.charAt(0).toUpperCase();
  return (
    <span
      className={cn(
        "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold shadow-xs ring-1",
        gradientRing,
        "bg-gradient-to-br from-muted-foreground/20 to-muted-foreground/10 text-muted-foreground",
      )}
    >
      {initial}
    </span>
  );
}

// ─── Empty State ─────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="relative flex flex-col items-center gap-3 px-6 py-14 text-center"
    >
      {/* Decorative orb */}
      <div className="relative mb-2">
        <div className="absolute -inset-4 rounded-full bg-brand/5 blur-xl" aria-hidden />
        <div className="relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-brand/10 to-brand/5 ring-1 ring-brand/10">
          <Bell className="size-6 text-brand/40" aria-hidden />
        </div>
      </div>
      <p className="text-sm font-medium text-foreground/80">All caught up</p>
      <p className="max-w-48 text-xs leading-relaxed text-muted-foreground/60">
        Follows, replies, and mentions will appear here when they come in
      </p>
    </motion.div>
  );
}

// ─── List item variants ──────────────────────────────────────────────────────

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 8, scale: 0.98 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: i * 0.035,
      duration: 0.3,
      ease: [0.22, 1, 0.36, 1],
    },
  }),
};

// ─── Main Component ──────────────────────────────────────────────────────────

export function NotificationBell() {
  const { unreadCount, setUnreadCount } = useNotifications();
  const [notifications, setNotifications] = useState<NotificationSummary[]>([]);
  const [open, setOpen] = useState(false);
  const [animatingCount, setAnimatingCount] = useState(0);
  const prevUnreadRef = useRef(unreadCount);

  // Track badge count for animation
  useEffect(() => {
    if (unreadCount !== prevUnreadRef.current) {
      setAnimatingCount(unreadCount);
      prevUnreadRef.current = unreadCount;
    }
  }, [unreadCount]);

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
    setNotifications((prev) =>
      prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n)),
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
    try {
      await fetch("/api/notifications", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ path: `${notificationId}/read`, method: "POST" }),
      });
    } catch {
      // Revert on failure
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: false } : n)),
      );
      setUnreadCount((prev) => prev + 1);
    }
  };

  const handleMarkAllRead = async () => {
    const prevWas = notifications.map((n) => n.read);
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnreadCount(0);
    try {
      await fetch("/api/notifications", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ path: "read-all", method: "POST" }),
      });
    } catch {
      // Revert on failure
      setNotifications((prev) => prev.map((n, i) => ({ ...n, read: prevWas[i] })));
      setUnreadCount(prevWas.filter((r) => !r).length);
    }
  };

  const hasUnread = notifications.some((n) => !n.read);

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <motion.button
          type="button"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.94 }}
          aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
          className="relative inline-flex h-10 w-10 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          {unreadCount > 0 ? (
            <BellDot className="size-[18px]" aria-hidden />
          ) : (
            <Bell className="size-[18px]" aria-hidden />
          )}
          <AnimatePresence mode="popLayout">
            {unreadCount > 0 && (
              <motion.span
                key={animatingCount}
                initial={{ scale: 0.4, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.4, opacity: 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 25 }}
                className="absolute -right-0.5 -top-0.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground ring-[3px] ring-background"
              >
                {unreadCount > 9 ? "9+" : unreadCount}
              </motion.span>
            )}
          </AnimatePresence>
        </motion.button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        sideOffset={10}
        className="w-[380px] overflow-hidden border-border/60 bg-card/95 p-0 shadow-xl shadow-black/5 backdrop-blur-xl"
      >
        {/* ── Header ────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between border-b border-border/40 px-4 py-3.5">
          <div className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand/10">
              <Bell className="size-3.5 text-brand" aria-hidden />
            </span>
            <span className="text-sm font-semibold tracking-tight">Notifications</span>
            {unreadCount > 0 && (
              <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-brand/10 px-1.5 text-[11px] font-medium text-brand">
                {unreadCount}
              </span>
            )}
          </div>
          {hasUnread && (
            <motion.button
              type="button"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.96 }}
              onClick={handleMarkAllRead}
              className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <CheckCheck className="size-3" aria-hidden />
              Mark all read
            </motion.button>
          )}
        </div>

        {/* ── List ──────────────────────────────────────────────────── */}
        <div className="max-h-[420px] overflow-y-auto overscroll-contain">
          {notifications.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="divide-y divide-border/30">
              <AnimatePresence initial>
                {notifications.map((notification, i) => {
                  const config = TYPE_CONFIG[notification.type] ?? TYPE_CONFIG.follow;
                  const TypeIcon = config.icon;
                  const actorName = notification.actor_display_name
                    || notification.actor_email
                    || "Someone";

                  return (
                    <div
                      key={notification.id}
                      className={cn(
                        "group relative",
                        !notification.read && "bg-gradient-to-r from-accent/40 via-accent/10 to-transparent",
                      )}
                    >
                      <motion.div
                        custom={i}
                        variants={itemVariants}
                        initial="hidden"
                        animate="visible"
                      >
                        <Link
                          href={notification.link || "#"}
                          onClick={(e) => {
                            if (!notification.read) {
                              handleMarkRead(notification.id);
                            }
                            if (!notification.link) {
                              e.preventDefault();
                            }
                          }}
                          className={cn(
                            "flex items-start gap-3 px-4 py-3.5 transition-colors hover:bg-muted/40",
                            notification.read && "opacity-70",
                          )}
                        >
                          {/* Type icon badge */}
                          <span
                            className={cn(
                              "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br shadow-xs",
                              config.gradient,
                              config.glow,
                            )}
                          >
                            <TypeIcon className="size-4 text-white" aria-hidden />
                          </span>

                          {/* Content */}
                          <div className="min-w-0 flex-1">
                            <div className="flex items-start gap-2.5">
                              <ActorAvatar
                                displayName={notification.actor_display_name}
                                email={notification.actor_email}
                                gradientRing={config.ring}
                              />
                              <div className="min-w-0 flex-1">
                                <p className={cn(
                                  "text-sm leading-snug tracking-tight",
                                  !notification.read && "font-medium",
                                )}>
                                  <span className="text-foreground">{actorName}</span>{" "}
                                  <span className="text-muted-foreground">{config.label}</span>
                                </p>

                                {/* Preview */}
                                <AnimatePresence>
                                  {notification.preview && (
                                    <motion.p
                                      initial={{ opacity: 0, height: 0 }}
                                      animate={{ opacity: 1, height: "auto" }}
                                      className="mt-1 line-clamp-2 text-xs leading-relaxed text-muted-foreground/70 italic"
                                    >
                                      &ldquo;{notification.preview}&rdquo;
                                    </motion.p>
                                  )}
                                </AnimatePresence>

                                {/* Time */}
                                <p className="mt-1 text-[11px] text-muted-foreground/50">
                                  {timeAgo(notification.created_at)}
                                </p>
                              </div>
                            </div>
                          </div>

                          {/* Unread indicator */}
                          {!notification.read && (
                            <motion.span
                              layoutId={`dot-${notification.id}`}
                              className="mt-2 h-2 w-2 shrink-0 rounded-full bg-brand"
                              aria-hidden
                            />
                          )}
                        </Link>
                      </motion.div>

                      {/* Hover mark-read button */}
                      <AnimatePresence>
                        {!notification.read && (
                          <motion.button
                            type="button"
                            initial={{ opacity: 0, scale: 0.8 }}
                            whileHover={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            onClick={(e) => {
                              e.stopPropagation();
                              e.preventDefault();
                              handleMarkRead(notification.id);
                            }}
                            className="absolute right-2.5 top-3.5 flex h-6 w-6 items-center justify-center rounded-full bg-muted/80 opacity-0 shadow-xs backdrop-blur-sm transition-opacity hover:bg-muted group-hover:opacity-100"
                            aria-label="Mark as read"
                          >
                            <Check className="size-3 text-muted-foreground" />
                          </motion.button>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </div>

        {/* ── Footer ────────────────────────────────────────────────── */}
        {notifications.length > 0 && (
          <div className="border-t border-border/40 px-4 py-2.5">
            <Link
              href="/notifications"
              className="block text-center text-[11px] font-medium tracking-wide text-muted-foreground/60 uppercase transition-colors hover:text-foreground"
            >
              View all notifications
            </Link>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
