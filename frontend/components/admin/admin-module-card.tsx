import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { ArrowUpRight, Clock3 } from "lucide-react";

import { cn } from "@/lib/utils";

export type AdminModuleCardProps = {
  compact?: boolean;
  description: string;
  href?: string;
  icon: LucideIcon;
  status: "live" | "planned";
  title: string;
};

/* ── Per-module accent system ── */
const moduleAccents: Record<
  string,
  { gradient: string; iconBg: string; badge: string; glow: string }
> = {
  "Blog posts": {
    gradient: "from-emerald-500/8 to-emerald-500/0",
    iconBg: "from-emerald-500 to-emerald-600",
    badge:
      "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 ring-emerald-500/20",
    glow: "shadow-emerald-500/5",
  },
  Compose: {
    gradient: "from-blue-500/8 to-blue-500/0",
    iconBg: "from-blue-500 to-blue-600",
    badge: "bg-blue-500/10 text-blue-600 dark:text-blue-400 ring-blue-500/20",
    glow: "shadow-blue-500/5",
  },
  "Blog ideas": {
    gradient: "from-amber-500/8 to-amber-500/0",
    iconBg: "from-amber-500 to-amber-600",
    badge:
      "bg-amber-500/10 text-amber-600 dark:text-amber-400 ring-amber-500/20",
    glow: "shadow-amber-500/5",
  },
  Projects: {
    gradient: "from-violet-500/8 to-violet-500/0",
    iconBg: "from-violet-500 to-violet-600",
    badge:
      "bg-violet-500/10 text-violet-600 dark:text-violet-400 ring-violet-500/20",
    glow: "shadow-violet-500/5",
  },
  Showcases: {
    gradient: "from-rose-500/8 to-rose-500/0",
    iconBg: "from-rose-500 to-rose-600",
    badge:
      "bg-rose-500/10 text-rose-600 dark:text-rose-400 ring-rose-500/20",
    glow: "shadow-rose-500/5",
  },
  "AI News review": {
    gradient: "from-sky-500/8 to-sky-500/0",
    iconBg: "from-sky-500 to-sky-600",
    badge: "bg-sky-500/10 text-sky-600 dark:text-sky-400 ring-sky-500/20",
    glow: "shadow-sky-500/5",
  },
  "AI News sources": {
    gradient: "from-cyan-500/8 to-cyan-500/0",
    iconBg: "from-cyan-500 to-cyan-600",
    badge:
      "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 ring-cyan-500/20",
    glow: "shadow-cyan-500/5",
  },
};

function getAccent(title: string, isLive: boolean) {
  if (!isLive)
    return {
      gradient: "from-muted/5 to-transparent",
      iconBg: "from-muted-foreground/30 to-muted-foreground/20",
      badge: "bg-muted/30 text-muted-foreground/60 ring-border/30",
      glow: "shadow-transparent",
    };
  return (
    moduleAccents[title] ?? {
      gradient: "from-brand/8 to-transparent",
      iconBg: "from-brand to-brand/90",
      badge: "bg-brand/10 text-brand ring-brand/20",
      glow: "shadow-brand/5",
    }
  );
}

/* ── Shared render args ── */
type RenderArgs = {
  description: string;
  href?: string;
  Icon: LucideIcon;
  isLive: boolean;
  title: string;
  accent: ReturnType<typeof getAccent>;
};

/* ══════════════════════════════════════════
   Default (spacious) card
   ══════════════════════════════════════════ */

function renderDefault({
  description,
  href,
  Icon,
  isLive,
  title,
  accent,
}: RenderArgs) {
  const body = (
    <article
      className={cn(
        "group relative flex h-full min-h-[10rem] flex-col rounded-2xl border p-5 transition-all duration-300",
        isLive
          ? "border-border/50 bg-card shadow-[0_1px_3px_rgba(0,0,0,0.04)] hover:-translate-y-0.5 hover:border-border/80 hover:shadow-[0_8px_24px_rgba(0,0,0,0.06)]"
          : "border-dashed border-border/40 bg-muted/10 opacity-80",
      )}
    >
      {/* Accent gradient overlay — reveals on hover */}
      <div
        className={cn(
          "pointer-events-none absolute inset-0 rounded-2xl bg-gradient-to-br opacity-0 transition-opacity duration-300 group-hover:opacity-100",
          accent.gradient,
        )}
        aria-hidden
      />

      {/* Top: icon + badge */}
      <div className="relative flex items-start justify-between gap-2">
        <span
          className={cn(
            "flex size-10 shrink-0 items-center justify-center rounded-xl text-white shadow-[0_2px_6px_rgba(0,0,0,0.10)] ring-1 ring-white/15 transition-transform duration-300 group-hover:scale-105",
            "bg-gradient-to-br",
            accent.iconBg,
          )}
        >
          <Icon className="size-[18px]" aria-hidden />
        </span>
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-medium leading-relaxed ring-1 backdrop-blur-sm",
            accent.badge,
          )}
        >
          {isLive ? "Live" : "Planned"}
        </span>
      </div>

      {/* Text */}
      <div className="relative mt-3 min-w-0 flex-1">
        <h3 className="text-sm font-semibold text-foreground break-words">{title}</h3>
        <p className="mt-1 text-sm leading-relaxed text-muted-foreground break-words">
          {description}
        </p>
      </div>

      {/* Footer */}
      <div className="relative mt-3">
        {href ? (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground/60 transition-colors group-hover:text-foreground/80">
            Open
            <ArrowUpRight
              className="size-3 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
              aria-hidden
            />
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground/40">
            <Clock3 className="size-3" aria-hidden />
            Reserved
          </span>
        )}
      </div>
    </article>
  );

  if (href) {
    return (
      <Link
        className="block min-w-0 h-full focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2"
        href={href}
      >
        {body}
      </Link>
    );
  }
  return <div className="min-w-0 h-full overflow-hidden">{body}</div>;
}

/* ══════════════════════════════════════════
   Compact card (flat, horizontal)
   ══════════════════════════════════════════ */

function renderCompact({
  description,
  href,
  Icon,
  isLive,
  title,
  accent,
}: RenderArgs) {
  const body = (
    <article
      className={cn(
        "group relative flex min-w-0 items-start gap-3 rounded-xl border px-4 py-3 transition-all duration-200",
        isLive
          ? "border-border/40 bg-card shadow-[0_1px_2px_rgba(0,0,0,0.02)] hover:-translate-y-[0.5px] hover:border-border/60 hover:shadow-[0_4px_12px_rgba(0,0,0,0.04)]"
          : "border-dashed border-border/30 bg-muted/10 opacity-70",
      )}
    >
      {/* Accent dot */}
      <span
        className={cn(
          "absolute left-0 top-3 h-8 w-0.5 rounded-full opacity-0 transition-opacity duration-200 group-hover:opacity-60",
          isLive ? "bg-gradient-to-b from-green-500 to-green-400" : "bg-muted-foreground/20",
        )}
        aria-hidden
      />

      {/* Icon */}
      <span
        className={cn(
          "mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg text-white shadow-[0_1px_3px_rgba(0,0,0,0.08)] ring-1 ring-white/10",
          "bg-gradient-to-br",
          accent.iconBg,
        )}
      >
        <Icon className="size-3.5" aria-hidden />
      </span>

      {/* Text */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-foreground break-words">
            {title}
          </h3>
        </div>
        <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground/70 break-words">
          {description}
        </p>
      </div>

      {/* Status + arrow */}
      <div className="flex shrink-0 items-start gap-2 pt-0.5">
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-[9px] font-medium leading-relaxed ring-1",
            accent.badge,
          )}
        >
          {isLive ? "Live" : "Planned"}
        </span>
        {href ? (
          <ArrowUpRight
            className="mt-0.5 size-3 text-muted-foreground/20 transition-colors group-hover:text-muted-foreground/50"
            aria-hidden
          />
        ) : (
          <Clock3 className="mt-0.5 size-3 text-muted-foreground/20" aria-hidden />
        )}
      </div>
    </article>
  );

  if (href) {
    return (
      <Link
        className="block min-w-0 h-full focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2"
        href={href}
      >
        {body}
      </Link>
    );
  }
  return <div className="min-w-0 h-full overflow-hidden">{body}</div>;
}

/* ══════════════════════════════════════════
   AdminModuleCard — public entry
   ══════════════════════════════════════════ */

export function AdminModuleCard({
  compact = false,
  description,
  href,
  icon: Icon,
  status,
  title,
}: AdminModuleCardProps) {
  const isLive = status === "live";
  const accent = getAccent(title, isLive);

  if (compact) {
    return renderCompact({ description, href, Icon, isLive, title, accent });
  }

  return renderDefault({ description, href, Icon, isLive, title, accent });
}
