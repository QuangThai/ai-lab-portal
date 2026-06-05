import { AdminQuickActionPanel } from "@/components/admin/admin-dashboard-stat-grid";
import { adminDisplayTitleClass, adminEyebrowClass } from "@/components/admin/admin-ui";
import { cn } from "@/lib/utils";

type Props = { description: string; email: string; title: string };

export function AdminDashboardHeader({ description, email, title }: Props) {
  const initial = email.charAt(0).toUpperCase();

  return (
    <header className="pb-6">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        {/* Left: title area */}
        <div className="min-w-0 max-w-2xl">
          <div className="flex items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-[var(--radius-admin-sm)] bg-primary text-primary-foreground shadow-[0_2px_6px_rgba(0,0,0,0.1)]">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            </span>
            <div>
              <p className={adminEyebrowClass}>Admin control room</p>
              <h1 className={cn(adminDisplayTitleClass, "mt-0.5")}>{title}</h1>
            </div>
          </div>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground">{description}</p>
        </div>

        {/* Right: user + quick actions */}
        <div className="flex shrink-0 flex-col gap-3">
          {/* User badge */}
          <div className="flex min-w-0 items-center gap-3 rounded-[var(--radius-admin-sm)] border border-border/60 bg-card px-3.5 py-2.5 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
            <span className="flex size-9 items-center justify-center rounded-[var(--radius-admin-sm)] bg-primary text-sm font-semibold text-primary-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]">
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
