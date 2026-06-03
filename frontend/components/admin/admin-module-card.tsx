import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { ArrowUpRight, Clock3 } from "lucide-react";

import { cn } from "@/lib/utils";

export type AdminModuleCardProps = {
  description: string;
  href?: string;
  icon: LucideIcon;
  status: "live" | "planned";
  title: string;
};

export function AdminModuleCard({ description, href, icon: Icon, status, title }: AdminModuleCardProps) {
  const isLive = status === "live";

  const body = (
    <article
      className={cn(
        "relative flex h-full min-h-36 flex-col gap-3 rounded-lg border p-4 transition-colors",
        isLive
          ? "border-border bg-card hover:border-foreground/20 hover:bg-muted/15"
          : "border-dashed border-border/80 bg-muted/15 opacity-90"
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <span
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-md",
            isLive ? "bg-accent text-brand" : "bg-muted text-muted-foreground"
          )}
        >
          <Icon className="size-4" aria-hidden />
        </span>
        <span
          className={cn(
            "rounded-md px-1.5 py-0.5 text-[10px] font-medium",
            isLive ? "bg-accent/80 text-foreground" : "bg-muted text-muted-foreground"
          )}
        >
          {isLive ? "Live" : "Planned"}
        </span>
      </div>
      <div className="min-w-0 flex-1">
        <h3 className="text-sm font-semibold">{title}</h3>
        <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{description}</p>
      </div>
      <div>
        {href ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-brand">
            Open <ArrowUpRight className="size-3" aria-hidden />
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
            <Clock3 className="size-3" aria-hidden /> Reserved
          </span>
        )}
      </div>
    </article>
  );

  if (href) {
    return (
      <Link
        className="block h-full focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2"
        href={href}
      >
        {body}
      </Link>
    );
  }
  return <div className="h-full">{body}</div>;
}
