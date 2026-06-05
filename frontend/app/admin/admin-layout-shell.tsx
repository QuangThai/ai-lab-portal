"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";

/**
 * Client boundary that decides whether to wrap children in AdminCmsShell.
 * The login page renders standalone; all other admin routes get the shell.
 */
export function AdminLayoutShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  // Login has its own full-screen UI — no sidebar needed.
  if (pathname.startsWith("/admin/login")) {
    return <>{children}</>;
  }

  return <AdminCmsShell>{children}</AdminCmsShell>;
}
