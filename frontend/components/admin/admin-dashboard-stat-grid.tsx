import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import {
  ArrowUpRight,
  Lightbulb,
  PencilLine,
  TrendingUp,
} from "lucide-react";

import { cn } from "@/lib/utils";

export type AdminDashboardStat = {
  href: string;
  hint: string;
  icon: LucideIcon;
  label: string;
  value: number;
};

/* ── Per-stat accent palette ── */
const statAccents: Record<
  string,
  {
    gradient: string;
    iconBg: string;
    dot: string;
    glow: string;
  }
> = {
  "Blog posts": {
    gradient: "from-emerald-500/10 via-emerald-500/5 to-transparent",
    iconBg: "bg-gradient-to-br from-emerald-500 to-emerald-600",
    dot: "bg-emerald-500",
    glow: "shadow-emerald-500/10",
  },
  Comments: {
    gradient: "from-sky-500/10 via-sky-500/5 to-transparent",
    iconBg: "bg-gradient-to-br from-sky-500 to-sky-600",
    dot: "bg-sky-500",
    glow: "shadow-sky-500/10",
  },
  "Blog ideas": {
    gradient: "from-amber-500/10 via-amber-500/5 to-transparent",
    iconBg: "bg-gradient-to-br from-amber-500 to-amber-600",
    dot: "bg-amber-500",
    glow: "shadow-amber-500/10",
  },
  Showcases: {
    gradient: "from-violet-500/10 via-violet-500/5 to-transparent",
    iconBg: "bg-gradient-to-br from-violet-500 to-violet-600",
    dot: "bg-violet-500",
    glow: "shadow-violet-500/10",
  },
  "AI News": {
    gradient: "from-rose-500/10 via-rose-500/5 to-transparent",
    iconBg: "bg-gradient-to-br from-rose-500 to-rose-600",
    dot: "bg-rose-500",
    glow: "shadow-rose-500/10",
  },
};

/* ── Stat card ── */

function StatCard({ stat }: { stat: AdminDashboardStat }) {
  const Icon = stat.icon;
  const accent = statAccents[stat.label] ?? {
    gradient: "from-muted/20 to-transparent",
    iconBg: "bg-gradient-to-br from-muted-foreground to-muted-foreground/80",
    dot: "bg-muted-foreground",
    glow: "shadow-black/5",
  };

  return (
    <Link
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-border/50 bg-card p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300",
        "hover:-translate-y-0.5 hover:shadow-[0_8px_24px_rgba(0,0,0,0.06)]",
        "focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2",
        "active:translate-y-0 active:shadow-[0_1px_2px_rgba(0,0,0,0.04)]",
      )}
      href={stat.href}
    >
      {/* Colored gradient overlay on hover */}
      <div
        className={cn(
          "pointer-events-none absolute inset-0 bg-gradient-to-br opacity-0 transition-opacity duration-300 group-hover:opacity-100",
          accent.gradient,
        )}
        aria-hidden
      />

      {/* Glow dot - top right */}
      <span
        className={cn(
          "absolute right-4 top-4 size-1.5 rounded-full opacity-60 transition-all duration-300 group-hover:opacity-100 group-hover:shadow-[0_0_6px]",
          accent.dot,
          accent.glow,
        )}
        aria-hidden
      />

      {/* Icon row */}
      <div className="relative flex items-start justify-between">
        <span
          className={cn(
            "flex size-10 items-center justify-center rounded-xl text-white shadow-[0_2px_6px_rgba(0,0,0,0.12)] ring-1 ring-white/20 transition-transform duration-300 group-hover:scale-105",
            accent.iconBg,
          )}
        >
          <Icon className="size-[18px]" aria-hidden />
        </span>
        <ArrowUpRight
          className="size-3.5 text-muted-foreground/20 transition-all duration-300 group-hover:text-muted-foreground/50 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
          aria-hidden
        />
      </div>

      {/* Value + label */}
      <div className="relative mt-4">
        <p className="text-xs font-medium text-muted-foreground/80">
          {stat.label}
        </p>
        <p className="mt-1 font-(family-name:--font-sohne) text-[2.25rem] font-semibold leading-none tracking-tight text-foreground tabular-nums">
          {stat.value}
        </p>
        <p className="mt-2 text-xs text-muted-foreground/70">{stat.hint}</p>
      </div>
    </Link>
  );
}

/* ══════════════════════════════════════════
   AdminDashboardStatGrid
   ══════════════════════════════════════════ */

type Props = { stats: AdminDashboardStat[] };

export function AdminDashboardStatGrid({ stats }: Props) {
  return (
    <section aria-labelledby="stats-heading">
      {/* Section header with label and decorative line */}
      <div className="mb-4 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="size-4 text-muted-foreground/60" aria-hidden />
          <h2
            id="stats-heading"
            className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground/70"
          >
            At a glance
          </h2>
        </div>
        <div className="h-px flex-1 bg-border/60" aria-hidden />
        <p className="text-[11px] text-muted-foreground/50">
          Publishing inventory
        </p>
      </div>

      {/* Stat cards — 5-column responsive grid */}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {stats.map((stat) => (
          <StatCard key={stat.label} stat={stat} />
        ))}
      </div>
    </section>
  );
}

/* ══════════════════════════════════════════
   AdminQuickActionPanel
   ══════════════════════════════════════════ */

export function AdminQuickActionPanel() {
  return (
    <div className="flex gap-2.5">
      <Link
        className="group flex flex-1 items-center justify-center gap-2 rounded-xl border border-green-500/20 bg-green-500/5 px-3 py-2.5 text-sm font-medium text-green-700 dark:text-green-400 shadow-[0_1px_2px_rgba(0,0,0,0.02)] transition-all duration-200 hover:border-green-500/30 hover:bg-green-500/10 hover:shadow-[0_2px_6px_rgba(80,179,58,0.08)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-500/30 focus-visible:ring-offset-2 active:scale-[0.98]"
        href="/admin/blog/editor"
      >
        <span className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-green-500/15 text-green-600 dark:text-green-400 transition-transform duration-200 group-hover:scale-105">
          <PencilLine className="size-3.5" aria-hidden />
        </span>
        <span className="whitespace-nowrap">New draft</span>
      </Link>
      <Link
        className="group flex flex-1 items-center justify-center gap-2 rounded-xl border border-amber-500/15 bg-amber-500/5 px-3 py-2.5 text-sm font-medium text-amber-700 dark:text-amber-400 shadow-[0_1px_2px_rgba(0,0,0,0.02)] transition-all duration-200 hover:border-amber-500/25 hover:bg-amber-500/10 hover:shadow-[0_2px_6px_rgba(251,191,36,0.08)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500/30 focus-visible:ring-offset-2 active:scale-[0.98]"
        href="/admin/blog-ideas/new"
      >
        <span className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-amber-500/15 text-amber-600 dark:text-amber-400 transition-transform duration-200 group-hover:scale-105">
          <Lightbulb className="size-3.5" aria-hidden />
        </span>
        <span className="whitespace-nowrap">New idea</span>
      </Link>
    </div>
  );
}
