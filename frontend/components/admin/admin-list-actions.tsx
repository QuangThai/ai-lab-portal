import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";
import type { VariantProps } from "class-variance-authority";

import { buttonVariants } from "@/components/ui/button-variants";
import { cn } from "@/lib/utils";

const adminListActionSize = "sm" as const;

type AdminListActionVariant = NonNullable<VariantProps<typeof buttonVariants>["variant"]>;

type AdminListActionsProps = {
  children: ReactNode;
};

type AdminListActionFormProps = {
  action: (formData: FormData) => void | Promise<void>;
  children: ReactNode;
  className?: string;
};

type AdminListActionLinkProps = ComponentProps<typeof Link> & {
  variant?: AdminListActionVariant;
};

type AdminListSubmitButtonProps = ComponentProps<"button"> & {
  variant?: AdminListActionVariant;
};

function adminListActionClassName(variant?: AdminListActionVariant, className?: string) {
  return cn(buttonVariants({ size: adminListActionSize, variant }), className);
}

/** Row action cluster — only use AdminListActionLink / AdminListActionForm + AdminListSubmitButton. */
export function AdminListActions({ children }: AdminListActionsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">{children}</div>
  );
}

/** Next.js link styled with the same sm button tokens as list submit actions. */
export function AdminListActionLink({
  className,
  variant,
  ...props
}: AdminListActionLinkProps) {
  return <Link className={adminListActionClassName(variant, className)} {...props} />;
}

/**
 * Server-action form with `display: contents` so the submit button participates
 * directly in the AdminListActions flex row (avoids block-form height mismatch).
 */
export function AdminListActionForm({ action, children, className }: AdminListActionFormProps) {
  return (
    <form action={action} className={cn("contents", className)}>
      {children}
    </form>
  );
}

/** Native submit button — matches AdminListActionLink height (both use buttonVariants sm). */
export function AdminListSubmitButton({
  className,
  type = "submit",
  variant,
  ...props
}: AdminListSubmitButtonProps) {
  return <button className={adminListActionClassName(variant, className)} type={type} {...props} />;
}
