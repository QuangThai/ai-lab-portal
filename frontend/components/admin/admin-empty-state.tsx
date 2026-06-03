import type { ReactNode } from "react";
import { Plus } from "lucide-react";

import { adminEmptyStateClass } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";

type AdminEmptyStateProps = {
  ctaHref?: string;
  ctaLabel?: string;
  description: string;
  icon: ReactNode;
  title: string;
};

export function AdminEmptyState({ ctaHref, ctaLabel, description, icon, title }: AdminEmptyStateProps) {
  return (
    <div className={adminEmptyStateClass}>
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md bg-accent text-brand">
        {icon}
      </div>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <p className="mt-2 max-w-sm text-sm leading-6 text-muted-foreground">{description}</p>
      {ctaHref && ctaLabel && (
        <ButtonLink className="mt-6" href={ctaHref}>
          <Plus className="size-4" aria-hidden />
          {ctaLabel}
        </ButtonLink>
      )}
    </div>
  );
}
