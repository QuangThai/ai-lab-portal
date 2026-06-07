"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Cpu,
  Database,
  HardDrive,
  RefreshCw,
  Server,
} from "lucide-react";
import { cn } from "@/lib/utils";

type HealthData = {
  service: string;
  status: string;
  environment: string;
  database?: string;
  redis?: string;
  celery_workers?: string[];
  celery_worker_count?: number;
  celery_status?: string;
  celery_queues?: Record<string, number>;
};

const statusConfig = {
  ok: {
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    ring: "ring-emerald-500/20",
    border: "border-emerald-500/20",
    label: "Healthy",
    dot: "bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.4)]",
  },
  degraded: {
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    ring: "ring-amber-500/20",
    border: "border-amber-500/20",
    label: "Degraded",
    dot: "bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.4)]",
  },
  error: {
    color: "text-red-500",
    bg: "bg-red-500/10",
    ring: "ring-red-500/20",
    border: "border-red-500/20",
    label: "Error",
    dot: "bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.4)]",
  },
  unreachable: {
    color: "text-red-600",
    bg: "bg-red-500/10",
    ring: "ring-red-500/20",
    border: "border-red-500/20",
    label: "Unreachable",
    dot: "bg-red-500/50 shadow-[0_0_6px_rgba(239,68,68,0.2)]",
  },
} as const;

function getStatusInfo(status: string) {
  return statusConfig[status as keyof typeof statusConfig] ?? statusConfig.error;
}

function StatusDot({ status }: { status: string }) {
  const info = getStatusInfo(status);
  return (
    <span
      className={cn("inline-block size-2 rounded-full", info.dot)}
    />
  );
}

function StatusPulse({ status }: { status: string }) {
  const info = getStatusInfo(status);
  return (
    <span className="relative inline-flex">
      <span
        className={cn(
          "absolute inline-flex h-full w-full animate-ping rounded-full opacity-30",
          info.dot.replace("shadow-[^_]+", "").replace("bg-", "bg-").split(" ")[0] ||
            "bg-emerald-500",
        )}
      />
      <StatusDot status={status} />
    </span>
  );
}

/* ══════════════════════════════════════════
   AdminHealthWidget
   ══════════════════════════════════════════ */

export function AdminHealthWidget() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function fetchHealth() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/health");
      if (!res.ok) {
        setHealth(null);
        setError(`HTTP ${res.status}`);
        return;
      }
      const data: HealthData = await res.json();
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch");
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30_000);
    return () => clearInterval(interval);
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  const overallStatus = health?.status ?? (error ? "unreachable" : "error");
  const statusInfo = getStatusInfo(overallStatus);

  return (
    <section
      className={cn(
        "overflow-hidden rounded-2xl border bg-card shadow-[0_1px_3px_rgba(0,0,0,0.03)]",
        statusInfo.border,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/40 px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <span className="flex size-7 items-center justify-center rounded-lg bg-muted/30">
            <Activity className="size-3.5 text-muted-foreground" aria-hidden />
          </span>
          <h2 className="text-sm font-semibold text-foreground">
            System health
          </h2>
        </div>
        <button
          type="button"
          onClick={fetchHealth}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border/40 px-2.5 py-1.5 text-xs font-medium text-muted-foreground/70 transition-all duration-200 hover:border-border/60 hover:bg-muted/20 hover:text-foreground disabled:opacity-50"
        >
          <RefreshCw
            className={cn("size-3", loading && "animate-spin")}
          />
          Refresh
        </button>
      </div>

      {/* Body */}
      {loading && !health ? (
        <div className="flex items-center justify-center px-5 py-10">
          <div className="flex items-center gap-2.5 text-sm text-muted-foreground/60">
            <div className="size-4 animate-spin rounded-full border-2 border-muted-foreground/20 border-t-muted-foreground/60" />
            Checking services&hellip;
          </div>
        </div>
      ) : (
        <div className="px-5 py-4">
          {/* Overall status — hero row */}
          <div className="mb-4 flex items-center justify-between rounded-xl border border-border/30 bg-muted/10 px-4 py-3">
            <div className="flex items-center gap-3">
              <Server className="size-4 text-muted-foreground/60" aria-hidden />
              <span className="text-sm font-medium text-foreground">Overall</span>
            </div>
            <span
              className={cn(
                "flex items-center gap-2 text-sm font-semibold",
                statusInfo.color,
              )}
            >
              <StatusPulse status={overallStatus} />
              {statusInfo.label}
            </span>
          </div>

          {/* Component details */}
          {health && (
            <div className="space-y-1">
              <HealthRow
                label="API"
                ok
                icon={<Cpu className="size-3.5" />}
              />
              <HealthRow
                label="Database"
                ok={health.database === "connected"}
                detail={health.database}
                icon={<Database className="size-3.5" />}
              />
              <HealthRow
                label="Redis"
                ok={health.redis === "connected"}
                detail={health.redis}
                icon={<HardDrive className="size-3.5" />}
              />
              <HealthRow
                label="Celery"
                ok={(health.celery_worker_count ?? 0) > 0}
                detail={
                  health.celery_worker_count != null
                    ? `${health.celery_worker_count} worker${health.celery_worker_count !== 1 ? "s" : ""}`
                    : health.celery_status
                }
                icon={<Cpu className="size-3.5" />}
              />
            </div>
          )}

          {/* Error state */}
          {error && !health && (
            <div className="rounded-xl border border-red-500/15 bg-red-500/5 px-4 py-3">
              <p className="text-xs font-medium text-red-500/80">
                Backend unreachable: {error}
              </p>
            </div>
          )}

          {/* Queue depths */}
          {health?.celery_queues &&
            Object.keys(health.celery_queues).length > 0 && (
              <div className="mt-4 border-t border-border/30 pt-3.5">
                <p className="mb-2 text-xs font-medium text-muted-foreground/60">
                  Queue depths
                </p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(health.celery_queues).map(
                    ([queue, depth]) => (
                      <span
                        key={queue}
                        className={cn(
                          "inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs",
                          "border-border/40 bg-muted/10",
                        )}
                      >
                        <span className="text-muted-foreground/70">
                          {queue}
                        </span>
                        <span
                          className={cn(
                            "inline-flex items-center gap-1 font-mono text-xs font-medium tabular-nums",
                            (depth as number) > 0
                              ? "text-amber-500"
                              : "text-emerald-500",
                          )}
                        >
                          <span
                            className={cn(
                              "size-1.5 rounded-full",
                              (depth as number) > 0
                                ? "bg-amber-500"
                                : "bg-emerald-500",
                            )}
                          />
                          {(depth as number) > 0
                            ? `${depth} pending`
                            : "clear"}
                        </span>
                      </span>
                    ),
                  )}
                </div>
              </div>
            )}
        </div>
      )}
    </section>
  );
}

/* ══════════════════════════════════════════
   HealthRow
   ══════════════════════════════════════════ */

function HealthRow({
  label,
  ok,
  detail,
  icon,
}: {
  label: string;
  ok: boolean;
  detail?: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors hover:bg-muted/10">
      <div className="flex items-center gap-2.5">
        <span className="text-muted-foreground/60 [&>svg]:size-3.5">
          {icon}
        </span>
        <span className="text-foreground/80">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {detail &&
          detail !== "connected" &&
          detail !== "not_available" &&
          !ok && (
            <span className="text-xs text-muted-foreground/50">{detail}</span>
          )}
        <StatusDot status={ok ? "ok" : "error"} />
      </div>
    </div>
  );
}
