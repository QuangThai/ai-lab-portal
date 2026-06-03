import type { ReactNode } from "react";

import { PublicEditorialShell } from "@/components/public/public-editorial-shell";

type PublicLandingShellProps = {
  children: ReactNode;
};

export function PublicLandingShell({ children }: PublicLandingShellProps) {
  return <PublicEditorialShell variant="landing">{children}</PublicEditorialShell>;
}
