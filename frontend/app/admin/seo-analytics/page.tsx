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

type Stats = {
  total_posts: number;
  published_posts: number;
  draft_posts: number;
  ideas_with_seo: number;
  avg_seo_score: number;
  total_seo_issues: number;
  posts_needing_attention: number;
  publish_trend: Record<string, number>;
  tags: number;
};

type PostAnalysis = {
  post_id: string;
  title: string;
  slug: string;
  status: string;
  published_at: string | null;
  seo_score: number;
  issues: string[];
  seo_details: {
    seo_title_length: number;
    meta_description_length: number;
    keyword_count: number;
  };
  has_marketing_metadata: boolean;
};

const emptyStats = (): Stats => ({
  total_posts: 0,
  published_posts: 0,
  draft_posts: 0,
  ideas_with_seo: 0,
  avg_seo_score: 0,
  total_seo_issues: 0,
  posts_needing_attention: 0,
  publish_trend: {},
  tags: 0,
});

async function adminFetch(path: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user?.id) {
    return { ok: false, json: () => null as never };
  }
  return fetch(`${backendBaseUrl}${path}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });
}

// ── Components ─────────────────────────────────────────────────

function StatCard({
  label,
  value,
  sub,
  color = "text-foreground",
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <p className="text-xs font-medium text-muted-foreground mb-1">{label}</p>
      <p className={cn("text-2xl font-bold tracking-tight", color)}>
        {value}
      </p>
      {sub ? (
        <p className="text-[11px] text-muted-foreground mt-0.5">{sub}</p>
      ) : null}
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-emerald-500"
      : score >= 50
        ? "bg-amber-500"
        : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 flex-1 rounded-full bg-muted overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-xs font-medium tabular-nums w-8 text-right">
        {score}
      </span>
    </div>
  );
}

function MonthBar({ label, count, max }: { label: string; count: number; max: number }) {
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-right text-muted-foreground shrink-0">{label}</span>
      <div className="h-5 flex-1 rounded bg-muted overflow-hidden">
        <div
          className="h-full rounded bg-brand/70"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-6 text-right font-medium tabular-nums">{count}</span>
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────

export default async function SeoAnalyticsPage() {
  const [statsRes, postsRes] = await Promise.all([
    adminFetch("/admin/seo-analytics/stats"),
    adminFetch("/admin/seo-analytics/posts?limit=30"),
  ]);

  const stats: Stats = statsRes.ok ? await statsRes.json() : emptyStats();
  const posts: PostAnalysis[] = postsRes.ok ? await postsRes.json() : [];

  const trendEntries = Object.entries(stats.publish_trend).sort();
  const maxTrend = Math.max(...trendEntries.map(([, c]) => c), 1);

  return (
    <div className={adminPageStackClass}>
      <AdminPageHeader
        title="SEO & Analytics"
        description="Blog post performance, SEO quality scores, and keyword analysis"
        actions={<AdminBackLink href="/admin">Back to dashboard</AdminBackLink>}
      />

      {/* Stat cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Published posts"
          value={stats.published_posts}
          sub={`${stats.draft_posts} drafts, ${stats.total_posts} total`}
        />
        <StatCard
          label="Avg SEO score"
          value={`${stats.avg_seo_score}%`}
          color={
            stats.avg_seo_score >= 80
              ? "text-emerald-600 dark:text-emerald-400"
              : stats.avg_seo_score >= 50
                ? "text-amber-600 dark:text-amber-400"
                : "text-red-600 dark:text-red-400"
          }
          sub={`${stats.ideas_with_seo} ideas with metadata`}
        />
        <StatCard
          label="SEO issues found"
          value={stats.total_seo_issues}
          color={
            stats.total_seo_issues === 0
              ? "text-emerald-600 dark:text-emerald-400"
              : "text-amber-600 dark:text-amber-400"
          }
        />
        <StatCard
          label="Need attention"
          value={stats.posts_needing_attention}
          color={
            stats.posts_needing_attention === 0
              ? "text-emerald-600 dark:text-emerald-400"
              : "text-red-600 dark:text-red-400"
          }
          sub="Posts with SEO score &lt; 70"
        />
      </div>

      {/* Two-column layout */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Publish trend */}
        <div className="rounded-xl border border-border/60 bg-card p-4">
          <h2 className="text-sm font-semibold mb-3">Publish trend</h2>
          {trendEntries.length === 0 ? (
            <p className="text-xs text-muted-foreground">No published posts yet</p>
          ) : (
            <div className="space-y-1">
              {trendEntries.slice(-12).map(([month, count]) => (
                <MonthBar
                  key={month}
                  label={month}
                  count={count}
                  max={maxTrend}
                />
              ))}
            </div>
          )}
        </div>

        {/* Tags & Keywords */}
        <div className="rounded-xl border border-border/60 bg-card p-4">
          <h2 className="text-sm font-semibold mb-3">Tags</h2>
          <StatCard label="Total tags" value={stats.tags} />
        </div>
      </div>

      {/* SEO scores table */}
      <div className="rounded-xl border border-border/60 bg-card p-4">
        <h2 className="text-sm font-semibold mb-3">
          Post SEO scores
          <span className="font-normal text-muted-foreground ml-2">
            (worst first)
          </span>
        </h2>
        {posts.length === 0 ? (
          <p className="text-xs text-muted-foreground">No posts with SEO data</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border/60 text-muted-foreground">
                  <th className="text-left py-2 pr-3 font-medium">Title</th>
                  <th className="text-left py-2 pr-3 font-medium">Status</th>
                  <th className="text-right py-2 pr-3 font-medium">SEO score</th>
                  <th className="text-right py-2 pr-3 font-medium">Title len</th>
                  <th className="text-right py-2 pr-3 font-medium">Desc len</th>
                  <th className="text-left py-2 font-medium">Issues</th>
                </tr>
              </thead>
              <tbody>
                {posts.map((post) => (
                  <tr key={post.post_id} className="border-b border-border/30">
                    <td className="py-2 pr-3 max-w-48 truncate font-medium">
                      {post.title}
                    </td>
                    <td className="py-2 pr-3">
                      <span
                        className={cn(
                          "inline-block rounded px-1.5 py-0.5 text-[10px] font-medium",
                          post.status === "published"
                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                            : "bg-muted text-muted-foreground",
                        )}
                      >
                        {post.status}
                      </span>
                    </td>
                    <td className="py-2 pr-3">
                      <ScoreBar score={post.seo_score} />
                    </td>
                    <td className="py-2 pr-3 text-right tabular-nums">
                      {post.seo_details.seo_title_length}
                    </td>
                    <td className="py-2 pr-3 text-right tabular-nums">
                      {post.seo_details.meta_description_length}
                    </td>
                    <td className="py-2 max-w-48 truncate text-muted-foreground">
                      {post.issues.length > 0
                        ? post.issues.slice(0, 2).join("; ")
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
