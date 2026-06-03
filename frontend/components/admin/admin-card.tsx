import type { ReactNode } from "react";

import {
  adminCardClass,
  adminEditorBodyClass,
  adminEditorSectionClass,
  adminEyebrowClass,
  adminSectionTitleClass,
} from "@/components/admin/admin-ui";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type AdminCardProps = {
  children: ReactNode;
  className?: string;
};

export function AdminCard({ children, className }: AdminCardProps) {
  return <Card className={cn(adminCardClass, className)}>{children}</Card>;
}

type AdminCardSectionProps = {
  children?: ReactNode;
  className?: string;
  description?: string;
  eyebrow?: string;
  title: string;
};

export function AdminCardSection({ children, className, description, eyebrow, title }: AdminCardSectionProps) {
  return (
    <div className={cn(adminEditorSectionClass, className)}>
      {eyebrow ? <p className={adminEyebrowClass}>{eyebrow}</p> : null}
      <h2 className={cn(adminSectionTitleClass, eyebrow && "mt-1")}>{title}</h2>
      {description ? <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{description}</p> : null}
      {children}
    </div>
  );
}

export function AdminCardBody({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn(adminEditorBodyClass, className)}>{children}</div>;
}

type AdminWorkflowCardProps = {
  children: ReactNode;
  className?: string;
  description: string;
  title: string;
};

export function AdminWorkflowCard({ children, className, description, title }: AdminWorkflowCardProps) {
  return (
    <Card className={cn(adminCardClass, "lg:sticky lg:top-4", className)}>
      <div className={adminEditorSectionClass}>
        <h2 className={adminSectionTitleClass}>{title}</h2>
        <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{description}</p>
      </div>
      <div className="flex flex-col gap-3 p-4 sm:p-5">{children}</div>
    </Card>
  );
}
