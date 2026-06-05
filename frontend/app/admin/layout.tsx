import type { ReactNode } from "react";

import { AdminLayoutShell } from "./admin-layout-shell";

/**
 * Shared admin layout.
 *
 * Renders the persistent sidebar shell around every admin page.
 * Only the page content (children) changes between navigations —
 * the sidebar, theme toggle, and brand mark are never remounted.
 *
 * The login page is excluded from the shell by AdminLayoutShell
 * (it checks usePathname and renders standalone).
 */
export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminLayoutShell>{children}</AdminLayoutShell>;
}
