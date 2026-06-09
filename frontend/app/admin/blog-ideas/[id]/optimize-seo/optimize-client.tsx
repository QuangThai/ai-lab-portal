"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check, X } from "lucide-react";

type SeoChange = {
  section: string;
  before: string;
  after: string;
  rationale: string;
};

type SeoOptimizationResult = {
  id: string;
  blog_idea_id: string;
  changes: SeoChange[];
  overall_summary: string;
  created_at: string;
};

const sectionLabels: Record<string, string> = {
  title: "Title",
  meta_description: "Meta Description",
  headings: "Heading Structure",
  internal_links: "Internal Links",
  keywords: "Keyword Placement",
};

const sectionIcons: Record<string, string> = {
  title: "🔤",
  meta_description: "📝",
  headings: "📑",
  internal_links: "🔗",
  keywords: "🎯",
};

export function SeoOptimizeClient({
  ideaId,
  result,
}: {
  ideaId: string;
  result: SeoOptimizationResult;
}) {
  const router = useRouter();
  const [accepted, setAccepted] = useState<Set<string>>(new Set());
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleAccept = useCallback((section: string) => {
    setAccepted((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  }, []);

  const handleApply = useCallback(async () => {
    if (accepted.size === 0) return;
    setApplying(true);
    setError(null);

    try {
      const res = await fetch(
        `/api/admin/blog-ideas/${ideaId}/apply-seo-changes`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            accepted_sections: Array.from(accepted),
            changes: result.changes,
          }),
        },
      );

      if (!res.ok) {
        const body = await res.text();
        throw new Error(body || `HTTP ${res.status}`);
      }

      setApplied(true);
      // Refresh the parent page so data is up to date
      setTimeout(() => router.refresh(), 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply changes");
    } finally {
      setApplying(false);
    }
  }, [accepted, result.changes, ideaId, router]);

  const handleBackToIdea = () => {
    router.push(`/admin/blog-ideas/${ideaId}`);
  };

  if (applied) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border bg-card px-6 py-16 text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
          <Check className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
        </div>
        <h2 className="mb-2 text-lg font-semibold">Changes Applied</h2>
        <p className="mb-6 text-sm text-muted-foreground">
          {accepted.size} SEO change(s) have been applied to this blog idea.
        </p>
        <button
          type="button"
          onClick={handleBackToIdea}
          className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand/90"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to idea
        </button>
      </div>
    );
  }

  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {accepted.size} of {result.changes.length} sections selected
        </p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleBackToIdea}
            className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted/50 hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back
          </button>
          <button
            type="button"
            onClick={handleApply}
            disabled={accepted.size === 0 || applying}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-4 py-1.5 text-xs font-medium text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {applying ? (
              <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <Check className="h-3.5 w-3.5" />
            )}
            {applying ? "Applying..." : `Apply Selected (${accepted.size})`}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/30 dark:bg-red-950/10 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {result.changes.map((change, i) => {
          const isAccepted = accepted.has(change.section);
          return (
            <div
              key={i}
              className={`rounded-lg border bg-card text-card-foreground shadow-sm transition-colors ${
                isAccepted
                  ? "border-emerald-300 ring-1 ring-emerald-200 dark:border-emerald-700 dark:ring-emerald-800"
                  : ""
              }`}
            >
              {/* Section header with accept/reject toggle */}
              <div className="flex items-center justify-between border-b border-border/50 px-6 py-3">
                <div className="flex items-center gap-2">
                  <span className="text-base">{sectionIcons[change.section] || "📌"}</span>
                  <h3 className="text-sm font-semibold">
                    {sectionLabels[change.section] || change.section}
                  </h3>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => toggleAccept(change.section)}
                    className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors ${
                      isAccepted
                        ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400"
                        : "border-border/60 text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                    }`}
                  >
                    {isAccepted ? (
                      <>
                        <Check className="h-3 w-3" />
                        Accepted
                      </>
                    ) : (
                      <>
                        <X className="h-3 w-3" />
                        Reject
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Diff display */}
              <div className="p-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-red-200 bg-red-50/50 p-4 dark:border-red-900/30 dark:bg-red-950/10">
                    <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-red-600 dark:text-red-400">
                      Before
                    </p>
                    <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                      {change.before || (
                        <span className="italic opacity-50">(empty)</span>
                      )}
                    </p>
                  </div>
                  <div
                    className={`rounded-lg border p-4 ${
                      isAccepted
                        ? "border-emerald-200 bg-emerald-50/50 dark:border-emerald-900/30 dark:bg-emerald-950/10"
                        : "border-border/60 bg-muted/20"
                    }`}
                  >
                    <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                      After
                    </p>
                    <p className="whitespace-pre-wrap text-sm text-foreground">
                      {change.after}
                    </p>
                  </div>
                </div>

                <p className="mt-3 text-xs italic text-muted-foreground">
                  {change.rationale}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
