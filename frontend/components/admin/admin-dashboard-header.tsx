import { AdminQuickActionPanel } from "@/components/admin/admin-dashboard-stat-grid";
import { adminDisplayTitleClass, adminEyebrowClass, adminPageHeaderSurfaceClass } from "@/components/admin/admin-ui";
import { cn } from "@/lib/utils";

type Props = { description: string; email: string; title: string };

export function AdminDashboardHeader({ description, email, title }: Props) {
  const initial = email.charAt(0).toUpperCase();

  return (
    <header className={cn(adminPageHeaderSurfaceClass)}>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_16rem] lg:items-end">
        <div className="min-w-0">
          <p className={adminEyebrowClass}>Admin control room</p>
          <h1 className={cn(adminDisplayTitleClass, "mt-1 max-w-3xl")}>{title}</h1>
          <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground">{description}</p>
        </div>

        <div className="grid gap-2">
          <div className="flex min-w-0 items-center gap-2.5 rounded-lg border border-border bg-muted/25 px-2.5 py-2">
            <span className="flex size-8 items-center justify-center rounded-md bg-primary text-xs font-semibold text-primary-foreground">
              {initial}
            </span>
            <div className="min-w-0">
              <p className="text-[10px] font-medium text-muted-foreground">Signed in</p>
              <p className="truncate text-sm font-medium">{email}</p>
            </div>
          </div>
          <AdminQuickActionPanel />
        </div>
      </div>
    </header>
  );
}
