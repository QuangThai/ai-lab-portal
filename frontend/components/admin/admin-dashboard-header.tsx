import { AdminQuickActionPanel } from "@/components/admin/admin-dashboard-stat-grid";
import { adminEyebrowClass } from "@/components/admin/admin-ui";

type Props = { description: string; email: string; title: string };

export function AdminDashboardHeader({ description, email, title }: Props) {
  const initial = email.charAt(0).toUpperCase();

  return (
    <header className="relative overflow-hidden rounded-2xl border border-border/40 bg-card shadow-[0_1px_4px_rgba(0,0,0,0.03)]">
      {/* Subtle decorative gradient in top-right */}
      <div
        className="pointer-events-none absolute -right-24 -top-24 size-80 rounded-full opacity-[0.04]"
        style={{
          background:
            "radial-gradient(circle, var(--color-story-green, #50b33a) 0%, transparent 70%)",
        }}
        aria-hidden
      />

      <div className="relative flex flex-col gap-8 px-8 py-7 lg:flex-row lg:items-start lg:justify-between lg:px-10 lg:py-8">
        {/* Left: title area */}
        <div className="min-w-0 max-w-2xl">
          <div className="flex items-center gap-4">
            {/* Dashboard icon in a premium container */}
            <span className="flex size-11 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-green-600 text-white shadow-[0_3px_10px_rgba(80,179,58,0.25)] ring-1 ring-green-400/20">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden
              >
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            </span>
            <div>
              <p className={adminEyebrowClass}>Operations</p>
              <h1 className="font-(family-name:--font-gt-super) mt-0.5 text-2xl font-normal tracking-[-0.03em] text-foreground sm:text-[1.85rem] sm:leading-tight">
                {title}
              </h1>
            </div>
          </div>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground">
            {description}
          </p>
        </div>

        {/* Right: user + quick actions */}
        <div className="flex shrink-0 flex-col gap-3">
          {/* User badge — cleaner pill */}
          <div className="flex min-w-0 items-center gap-3 rounded-xl border border-border/40 bg-card px-4 py-2.5 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
            <span className="flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-green-500 to-green-600 text-sm font-semibold text-white shadow-[0_2px_4px_rgba(80,179,58,0.2)]">
              {initial}
            </span>
            <div className="min-w-0">
              <p className="text-[10px] font-medium text-muted-foreground/60">
                Signed in
              </p>
              <p className="truncate text-sm font-medium text-foreground">
                {email}
              </p>
            </div>
          </div>

          <AdminQuickActionPanel />
        </div>
      </div>
    </header>
  );
}
