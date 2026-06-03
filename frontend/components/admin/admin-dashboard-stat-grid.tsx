import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { ArrowUpRight, Lightbulb, PencilLine } from "lucide-react";

import { adminCardHoverClass, adminSectionTitleClass } from "@/components/admin/admin-ui";
import { cn } from "@/lib/utils";

export type AdminDashboardStat = {
  href: string;
  hint: string;
  icon: LucideIcon;
  label: string;
  value: number;
};

type Props = { stats: AdminDashboardStat[] };

export function AdminDashboardStatGrid({ stats }: Props) {
  return (
    <section aria-labelledby="stats-heading" className="grid gap-3 lg:grid-cols-[10rem_minmax(0,1fr)]">
      <div className={cn(adminCardHoverClass, "p-4")}>
        <h2 id="stats-heading" className={adminSectionTitleClass}>
          At a glance
        </h2>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">Publishing inventory by surface.</p>
      </div>

      <div className="grid gap-2 sm:grid-cols-3">
        {stats.map((stat) => {
          const Icon = stat.icon;

          return (
            <Link
              key={stat.label}
              className={cn(
                adminCardHoverClass,
                "group block p-4 focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2"
              )}
              href={stat.href}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="flex size-8 items-center justify-center rounded-md bg-accent text-brand">
                  <Icon className="size-4" aria-hidden />
                </span>
                <ArrowUpRight
                  className="size-3.5 text-muted-foreground/40 transition-colors group-hover:text-muted-foreground"
                  aria-hidden
                />
              </div>

              <div className="mt-3">
                <p className="text-sm font-medium">{stat.label}</p>
                <p className="mt-1 font-(family-name:--font-gt-super) text-3xl tabular-nums tracking-tight">{stat.value}</p>
                <p className="mt-1 text-xs text-muted-foreground">{stat.hint}</p>
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}

export function AdminQuickActionPanel() {
  return (
    <div className="grid grid-cols-2 gap-2">
      <Link
        className="flex min-h-16 flex-col justify-between rounded-md bg-primary p-3 text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2"
        href="/admin/blog/editor"
      >
        <PencilLine className="size-4" aria-hidden />
        <span className="text-sm font-medium leading-tight">New draft</span>
      </Link>
      <Link
        className="flex min-h-16 flex-col justify-between rounded-md border border-border bg-card p-3 transition-colors hover:bg-muted/40 focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2"
        href="/admin/blog-ideas/new"
      >
        <Lightbulb className="size-4 text-brand" aria-hidden />
        <span className="text-sm font-medium leading-tight">New idea</span>
      </Link>
    </div>
  );
}
