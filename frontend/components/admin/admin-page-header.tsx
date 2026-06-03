import type { ReactNode } from "react";
import {
  adminDisplayTitleClass,
  adminEyebrowClass,
  adminPageHeaderSurfaceClass,
} from "@/components/admin/admin-ui";
import { AdminStatusBadge } from "@/components/admin/admin-status-badge";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type Props = {
  actions?: ReactNode;
  description: string;
  eyebrow?: string;
  metaText?: string;
  stats?: { label: string; variant?: "outline" | "secondary" | "success" }[];
  status?: "draft" | "published";
  title: string;
};

export function AdminPageHeader({ actions, description, eyebrow = "Admin CMS", metaText, stats, status, title }: Props) {
  return (
    <header className={cn(adminPageHeaderSurfaceClass)}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          {eyebrow && <p className={adminEyebrowClass}>{eyebrow}</p>}
          <h1 className={cn(adminDisplayTitleClass, eyebrow && "mt-1")}>{title}</h1>
          <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground">{description}</p>
          {(status || metaText || stats) && (
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {status && <AdminStatusBadge status={status} />}
              {metaText && <span className="text-sm text-muted-foreground">{metaText}</span>}
              {stats?.map((s) => (
                <Badge key={s.label} className="rounded-md font-normal" variant={s.variant ?? "outline"}>
                  {s.label}
                </Badge>
              ))}
            </div>
          )}
        </div>
        {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
      </div>
    </header>
  );
}
