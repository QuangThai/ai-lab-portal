"use client";

import { useFormStatus } from "react-dom";
import type { ReactNode } from "react";
import type { VariantProps } from "class-variance-authority";

import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button-variants";
import { cn } from "@/lib/utils";

type PendingSubmitButtonProps = {
  children: ReactNode;
  className?: string;
  formAction?: (formData: FormData) => void | Promise<void>;
  pendingLabel: string;
  size?: VariantProps<typeof buttonVariants>["size"];
  variant?: VariantProps<typeof buttonVariants>["variant"];
};

/** Full-width workflow actions — same height and alignment as shadcn Button */
export function PendingSubmitButton({
  children,
  className,
  formAction,
  pendingLabel,
  size = "default",
  variant = "default",
}: PendingSubmitButtonProps) {
  const { pending } = useFormStatus();

  return (
    <Button
      aria-busy={pending}
      className={cn("w-full justify-center", className)}
      disabled={pending}
      formAction={formAction}
      size={size}
      type="submit"
      variant={variant}
    >
      {pending ? pendingLabel : children}
    </Button>
  );
}
