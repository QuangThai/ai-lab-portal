import type { ReactNode } from "react";

import { PublicEditorialShell } from "@/components/public/public-editorial-shell";

type PublicPageShellProps = {
  children: ReactNode;
  currentPath?: string;
};

/** Editorial shell for /lab, /blog, /showcases and detail routes */
export function PublicPageShell({ children, currentPath }: PublicPageShellProps) {
  return (
    <PublicEditorialShell currentPath={currentPath} variant="page">
      {children}
    </PublicEditorialShell>
  );
}
