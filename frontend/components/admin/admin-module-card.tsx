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

/* ── Per-module accent ── */
const moduleAccents: Record<string, { color: string; badge: string }> = {
  "Blog posts": {
    color: "text-emerald-600 dark:text-emerald-400",
    badge: "bg-emerald-50 text-emerald-700 ring-emerald-200/50 dark:bg-emerald-950/30 dark:text-emerald-300 dark:ring-emerald-800/30",
  },
  Compose: {
    color: "text-blue-600 dark:text-blue-400",
    badge: "bg-blue-50 text-blue-700 ring-blue-200/50 dark:bg-blue-950/30 dark:text-blue-300 dark:ring-blue-800/30",
  },
  "Blog ideas": {
    color: "text-amber-600 dark:text-amber-400",
    badge: "bg-amber-50 text-amber-700 ring-amber-200/50 dark:bg-amber-950/30 dark:text-amber-300 dark:ring-amber-800/30",
  },
  Projects: {
    color: "text-violet-600 dark:text-violet-400",
    badge: "bg-violet-50 text-violet-700 ring-violet-200/50 dark:bg-violet-950/30 dark:text-violet-300 dark:ring-violet-800/30",
  },
  Showcases: {
    color: "text-rose-600 dark:text-rose-400",
    badge: "bg-rose-50 text-rose-700 ring-rose-200/50 dark:bg-rose-950/30 dark:text-rose-300 dark:ring-rose-800/30",
  },
  "AI News review": {
    color: "text-sky-600 dark:text-sky-400",
    badge: "bg-sky-50 text-sky-700 ring-sky-200/50 dark:bg-sky-950/30 dark:text-sky-300 dark:ring-sky-800/30",
  },
  "AI News sources": {
    color: "text-cyan-600 dark:text-cyan-400",
    badge: "bg-cyan-50 text-cyan-700 ring-cyan-200/50 dark:bg-cyan-950/30 dark:text-cyan-300 dark:ring-cyan-800/30",
  },
};

function getAccent(title: string, isLive: boolean) {
  if (!isLive) return { color: "text-muted-foreground", badge: "bg-muted text-muted-foreground ring-border/30" };
  return moduleAccents[title] ?? { color: "text-brand", badge: "bg-accent/80 text-foreground ring-brand/10" };
}

export function AdminModuleCard({ compact = false, description, href, icon: Icon, status, title }: AdminModuleCardProps) {
  const isLive = status === "live";
  const accent = getAccent(title, isLive);

  if (compact) {
    return renderCompact({ description, href, Icon, isLive, title, accent });
  }

  return renderDefault({ description, href, Icon, isLive, title, accent });
}

/* ── Spacious (default) card ── */
function renderDefault({ description, href, Icon, isLive, title, accent }: RenderArgs) {
  const body = (
    <article
      className={cn(
        "group relative flex h-full min-h-[9.5rem] flex-col rounded-[var(--radius-admin-md)] border p-5 transition-all duration-200",
        isLive
          ? "border-border/60 bg-card shadow-[0_1px_3px_rgba(0,0,0,0.03)] hover:-translate-y-[1px] hover:border-border/80 hover:shadow-[0_6px_20px_rgba(0,0,0,0.07)]"
          : "border-dashed border-border/50 bg-muted/10 opacity-80"
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <span
          className={cn(
            "flex size-9 shrink-0 items-center justify-center rounded-[var(--radius-admin-sm)] ring-1 transition-all",
            isLive
              ? "bg-white dark:bg-card text-foreground ring-border/30 shadow-[0_1px_2px_rgba(0,0,0,0.04)] group-hover:ring-border/50"
              : "bg-muted text-muted-foreground ring-border/20"
          )}
        >
          <Icon className={cn("size-[18px]", accent.color)} aria-hidden />
        </span>
        <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-medium leading-relaxed ring-1", accent.badge)}>
          {isLive ? "Live" : "Planned"}
        </span>
      </div>
      <div className="mt-3 flex-1">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{description}</p>
      </div>
      <div className="mt-3">
        {href ? (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors group-hover:text-foreground">
            Open <ArrowUpRight className="size-3 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" aria-hidden />
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground/60">
            <Clock3 className="size-3" aria-hidden /> Reserved
          </span>
        )}
      </div>
    </article>
  );

  if (href) {
    return <Link className="block h-full focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2" href={href}>{body}</Link>;
  }
  return <div className="h-full">{body}</div>;
}

/* ── Compact card (horizontal, dense) ── */
function renderCompact({ description, href, Icon, isLive, title, accent }: RenderArgs) {
  const body = (
    <article
      className={cn(
        "group relative flex items-center gap-3 rounded-[var(--radius-admin-sm)] border px-3.5 py-3 transition-all duration-200",
        isLive
          ? "border-border/50 bg-card shadow-[0_1px_2px_rgba(0,0,0,0.02)] hover:-translate-y-[0.5px] hover:border-border/70 hover:shadow-[0_3px_10px_rgba(0,0,0,0.05)]"
          : "border-dashed border-border/40 bg-muted/10 opacity-70"
      )}
    >
      {/* Icon */}
      <span
        className={cn(
          "flex size-7 shrink-0 items-center justify-center rounded-[var(--radius-admin-sm)] ring-1",
          isLive ? "bg-white dark:bg-card text-foreground ring-border/25" : "bg-muted text-muted-foreground ring-border/20"
        )}
      >
        <Icon className={cn("size-3.5", accent.color)} aria-hidden />
      </span>

      {/* Text */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h3 className="truncate text-sm font-medium text-foreground">{title}</h3>
        </div>
        <p className="mt-0.5 truncate text-xs text-muted-foreground/70">{description}</p>
      </div>

      {/* Status + arrow */}
      <div className="flex shrink-0 items-center gap-2">
        <span className={cn("inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-medium leading-relaxed ring-1", accent.badge)}>
          {isLive ? "Live" : "Planned"}
        </span>
        {href ? (
          <ArrowUpRight className="size-3 text-muted-foreground/30 transition-colors group-hover:text-muted-foreground/60" aria-hidden />
        ) : (
          <Clock3 className="size-3 text-muted-foreground/30" aria-hidden />
        )}
      </div>
    </article>
  );

  if (href) {
    return <Link className="block h-full focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2" href={href}>{body}</Link>;
  }
  return <div className="h-full">{body}</div>;
}

/* ── Shared type ── */
type RenderArgs = {
  description: string;
  href?: string;
  Icon: LucideIcon;
  isLive: boolean;
  title: string;
  accent: { color: string; badge: string };
};
