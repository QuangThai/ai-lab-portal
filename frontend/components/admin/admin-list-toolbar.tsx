import type { ReactNode } from "react";
import { Plus } from "lucide-react";

import {
  adminDisplayTitleClass,
  adminEyebrowClass,
  adminPageHeaderSurfaceClass,
} from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { cn } from "@/lib/utils";

export type AdminMetric = {
  dotClassName: string;
  label: string;
};

type Props = {
  ctaHref?: string;
  ctaLabel?: string;
  description: string;
  eyebrow: string;
  metrics?: AdminMetric[];
  secondaryAction?: ReactNode;
  title: string;
};

export function AdminListToolbar({ ctaHref, ctaLabel, description, eyebrow, metrics, secondaryAction, title }: Props) {
  return (
    <header className={cn(adminPageHeaderSurfaceClass)}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className={adminEyebrowClass}>{eyebrow}</p>
          <h1 className={cn(adminDisplayTitleClass, "mt-1")}>{title}</h1>
          <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground">{description}</p>
          {metrics && metrics.length > 0 && (
            <ul className="mt-3 flex flex-wrap items-center gap-1.5 text-sm tabular-nums text-muted-foreground">
              {metrics.map((m) => (
                <li key={m.label} className="rounded-md border border-border bg-muted/30 px-2 py-0.5 text-xs">
                  {m.label}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {secondaryAction}
          {ctaHref && ctaLabel && (
            <ButtonLink href={ctaHref}>
              <Plus className="size-4" aria-hidden />
              {ctaLabel}
            </ButtonLink>
          )}
        </div>
      </div>
    </header>
  );
}
