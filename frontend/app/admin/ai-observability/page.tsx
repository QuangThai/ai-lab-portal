import { headers } from "next/headers";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

// ── Types ───────────────────────────────────────────────────────

type StageStats = {
  count: number;
  avg_latency_ms: number;
  avg_total_tokens: number;
  total_tokens: number;
};

type Stats = {
  total_runs: number;
  completed: number;
  failed: number;
  success_rate: number;
  avg_latency_ms: number;
  avg_total_tokens: number;
  total_tokens: number;
  stages: Record<string, StageStats>;
};

type AiRun = {
  id: string;
  prompt_name: string;
  prompt_version: string;
  entity_type: string;
  entity_id: string;
  provider: string;
  model: string;
  status: "completed" | "failed";
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  latency_ms: number | null;
  error_message: string | null;
  trace_id: string | null;
  created_at: string;
};

async function adminFetch(path: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user?.id) {
    return { ok: false, json: () => null as never };
  }
  const response = await fetch(`${backendBaseUrl}${path}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });
  return response;
}

export default async function AiObservabilityPage() {
  const [statsRes, runsRes] = await Promise.all([
    adminFetch("/admin/ai-observability/stats"),
    adminFetch("/admin/ai-observability/runs?limit=30"),
  ]);

  const stats: Stats = statsRes.ok ? await statsRes.json() : emptyStats();
  const runs: AiRun[] = runsRes.ok ? await runsRes.json() : [];

  const stageNames = Object.keys(stats.stages).sort();
  const maxLatency = Math.max(
    ...stageNames.map((s) => stats.stages[s].avg_latency_ms),
    1,
  );
  const maxTokens = Math.max(
    ...stageNames.map((s) => stats.stages[s].avg_total_tokens),
    1,
  );

  return (
    <div className={adminPageStackClass}>
      <AdminPageHeader
        title="AI Observability"
        description="AI run metrics, latency, and token usage across all pipeline stages"
        actions={<AdminBackLink href="/admin">Back to dashboard</AdminBackLink>}
      />

      {/* ── Stat cards ── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total runs"
          value={stats.total_runs.toLocaleString()}
          color="text-foreground"
        />
        <StatCard
          label="Success rate"
          value={`${stats.success_rate}%`}
          color={
            stats.success_rate >= 90
              ? "text-emerald-600 dark:text-emerald-400"
              : stats.success_rate >= 70
                ? "text-amber-600 dark:text-amber-400"
                : "text-red-600 dark:text-red-400"
          }
        />
        <StatCard
          label="Avg latency"
          value={`${stats.avg_latency_ms.toFixed(0)}ms`}
          color="text-foreground"
        />
        <StatCard
          label="Total tokens"
          value={stats.total_tokens.toLocaleString()}
          color="text-foreground"
        />
      </div>

      {/* ── Stage breakdown ── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Latency by stage */}
        <div className="rounded-xl border border-border/70 bg-card p-5">
          <h3 className="mb-4 text-sm font-semibold text-foreground">
            Avg latency by stage
          </h3>
          <div className="space-y-3">
            {stageNames.length === 0 ? (
              <NoDataMessage />
            ) : (
              stageNames.map((name) => {
                const s = stats.stages[name];
                const pct = (s.avg_latency_ms / maxLatency) * 100;
                return (
                  <div key={name}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="font-medium text-foreground">
                        {stageLabel(name)}
                      </span>
                      <span className="text-muted-foreground">
                        {s.avg_latency_ms.toFixed(0)}ms
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-brand transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Tokens by stage */}
        <div className="rounded-xl border border-border/70 bg-card p-5">
          <h3 className="mb-4 text-sm font-semibold text-foreground">
            Avg tokens by stage
          </h3>
          <div className="space-y-3">
            {stageNames.length === 0 ? (
              <NoDataMessage />
            ) : (
              stageNames.map((name) => {
                const s = stats.stages[name];
                const pct = (s.avg_total_tokens / maxTokens) * 100;
                return (
                  <div key={name}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="font-medium text-foreground">
                        {stageLabel(name)}
                      </span>
                      <span className="text-muted-foreground">
                        {s.avg_total_tokens.toFixed(0)} tok
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-sky-500 transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* ── Stage summary table ── */}
      <div className="rounded-xl border border-border/70 bg-card">
        <div className="border-b border-border/50 px-5 py-4">
          <h3 className="text-sm font-semibold text-foreground">
            Stage summary
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border/30 text-xs text-muted-foreground">
                <th className="px-5 py-3 font-medium">Stage</th>
                <th className="px-5 py-3 font-medium">Runs</th>
                <th className="px-5 py-3 font-medium">Avg latency</th>
                <th className="px-5 py-3 font-medium">Avg tokens</th>
                <th className="px-5 py-3 font-medium">Total tokens</th>
              </tr>
            </thead>
            <tbody>
              {stageNames.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">
                    No runs recorded yet
                  </td>
                </tr>
              ) : (
                stageNames.map((name) => {
                  const s = stats.stages[name];
                  return (
                    <tr
                      key={name}
                      className="border-b border-border/20 transition-colors hover:bg-muted/30"
                    >
                      <td className="px-5 py-3 font-medium text-foreground">
                        {stageLabel(name)}
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">{s.count}</td>
                      <td className="px-5 py-3 text-muted-foreground">
                        {s.avg_latency_ms.toFixed(0)}ms
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">
                        {s.avg_total_tokens.toFixed(0)}
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">
                        {s.total_tokens.toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Recent runs ── */}
      <div className="rounded-xl border border-border/70 bg-card">
        <div className="border-b border-border/50 px-5 py-4">
          <h3 className="text-sm font-semibold text-foreground">
            Recent runs
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border/30 text-xs text-muted-foreground">
                <th className="px-5 py-3 font-medium">Time</th>
                <th className="px-5 py-3 font-medium">Stage</th>
                <th className="px-5 py-3 font-medium">Entity</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Latency</th>
                <th className="px-5 py-3 font-medium">Tokens</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-muted-foreground">
                    No runs recorded yet
                  </td>
                </tr>
              ) : (
                runs.map((run) => (
                  <tr
                    key={run.id}
                    className="border-b border-border/20 transition-colors hover:bg-muted/30"
                  >
                    <td className="whitespace-nowrap px-5 py-3 text-muted-foreground">
                      {formatTime(run.created_at)}
                    </td>
                    <td className="px-5 py-3">
                      <span className="font-medium text-foreground">
                        {stageLabel(run.prompt_name)}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      <span className="truncate max-w-[120px] inline-block align-bottom">
                        {run.entity_id}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {run.latency_ms != null ? `${run.latency_ms}ms` : "—"}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {run.total_tokens != null
                        ? run.total_tokens.toLocaleString()
                        : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-border/70 bg-card p-5">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn("mt-1 text-2xl font-semibold tracking-tight", color)}>
        {value}
      </p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
        status === "completed"
          ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400"
          : "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400",
      )}
    >
      <span
        className={cn(
          "inline-block size-1.5 rounded-full",
          status === "completed" ? "bg-emerald-500" : "bg-red-500",
        )}
      />
      {status}
    </span>
  );
}

function NoDataMessage() {
  return (
    <p className="py-4 text-center text-xs text-muted-foreground">
      No data yet
    </p>
  );
}

// ── Helpers ────────────────────────────────────────────────────

function emptyStats(): Stats {
  return {
    total_runs: 0,
    completed: 0,
    failed: 0,
    success_rate: 0,
    avg_latency_ms: 0,
    avg_total_tokens: 0,
    total_tokens: 0,
    stages: {},
  };
}

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function stageLabel(name: string): string {
  const labels: Record<string, string> = {
    blog_idea: "Idea",
    blog_outline: "Outline",
    draft_writer: "Draft",
    draft_section_writer: "Draft (section)",
    technical_review: "Review",
    marketing_metadata: "Marketing",
    claim_extraction: "Claims",
    ai_news_scoring: "News scoring",
  };
  return labels[name] ?? name;
}
