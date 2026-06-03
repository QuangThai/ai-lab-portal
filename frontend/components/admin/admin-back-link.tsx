import Link from "next/link";

import { cn } from "@/lib/utils";

type AdminBackLinkProps = {
  children: string;
  href: string;
};

export function AdminBackLink({ children, href }: AdminBackLinkProps) {
  return (
    <Link
      className={cn(
        "inline-flex items-center gap-1.5 text-sm font-semibold text-foreground/70 underline decoration-border/50 underline-offset-4",
        "transition-colors hover:text-brand hover:decoration-brand/30"
      )}
      href={href}
    >
      {children}
    </Link>
  );
}
