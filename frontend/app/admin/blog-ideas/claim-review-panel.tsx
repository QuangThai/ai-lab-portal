"use client";

import { useMemo, useState } from "react";
import { useFormStatus } from "react-dom";
import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  Gavel,
  Search,
  ShieldOff,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button-variants";
import { cn } from "@/lib/utils";

import type { BlogClaimItem } from "./idea-detail-view";
import { summarizeClaims } from "./lib/claim-publish-gate";

const CLAIM_STATUS_STYLES: Record<BlogClaimItem["status"], string> = {
  pending:
    "text-amber-700 bg-amber-50 border-amber-200 dark:text-amber-300 dark:bg-amber-950/30 dark:border-amber-900",
  supported:
    "text-emerald-700 bg-emerald-50 border-emerald-200 dark:text-emerald-300 dark:bg-emerald-950/30 dark:border-emerald-900",
  waived:
    "text-sky-700 bg-sky-50 border-sky-200 dark:text-sky-300 dark:bg-sky-950/30 dark:border-sky-900",
  unsupported:
    "text-red-700 bg-red-50 border-red-200 dark:text-red-300 dark:bg-red-950/30 dark:border-red-900",
};

const EVIDENCE_SOURCES = [
  { value: "measurement", label: "Measurement / benchmark" },
  { value: "documentation", label: "Documentation" },
  { value: "expert", label: "Expert review" },
  { value: "customer", label: "Customer reference" },
  { value: "other", label: "Other" },
] as const;

const selectClassName =
  "flex h-9 w-full rounded-[var(--radius-admin-sm)] border border-input bg-background px-3 py-1.5 text-sm";

type ClaimActions = {
  extractClaims: (formData: FormData) => Promise<void>;
  updateClaim: (formData: FormData) => Promise<void>;
  waiveAllClaims: (formData: FormData) => Promise<void>;
};

type Props = {
  ideaId: string;
  claims: BlogClaimItem[];
  actions: ClaimActions;
};

function SubmitButton({
  label,
  variant = "default",
  icon: Icon,
}: {
  label: string;
  variant?: "default" | "outline" | "secondary";
  icon?: typeof CheckCircle2;
}) {
  const { pending } = useFormStatus();
  return (
    <Button disabled={pending} size="sm" type="submit" variant={variant}>
      {Icon ? <Icon className="size-3.5" aria-hidden /> : null}
      {pending ? "Saving…" : label}
    </Button>
  );
}

function ClaimStatusBadge({ status }: { status: BlogClaimItem["status"] }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-md border px-2 py-0.5 text-xs font-medium capitalize",
        CLAIM_STATUS_STYLES[status],
      )}
    >
      {status}
    </span>
  );
}

const CLAIM_TYPE_CONFIG: Record<string, { icon: typeof FileText; label: string; color: string }> = {
  quantified: {
    icon: Gavel,
    label: "Quantified claim",
    color: "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/30",
  },
  comparative: {
    icon: Gavel,
    label: "Comparative",
    color: "text-violet-600 bg-violet-50 dark:text-violet-400 dark:bg-violet-950/30",
  },
  best_practice: {
    icon: FileText,
    label: "Best practice",
    color: "text-sky-600 bg-sky-50 dark:text-sky-400 dark:bg-sky-950/30",
  },
};

export function ClaimReviewPanel({ ideaId, claims, actions }: Props) {
  const summary = summarizeClaims(claims);
  const pendingClaims = claims.filter((c) => c.status === "pending");
  const [statusFilter, setStatusFilter] = useState<BlogClaimItem["status"] | "all">("all");
  const [searchText, setSearchText] = useState("");

  const filteredClaims = useMemo(() => {
    return claims.filter((c) => {
      if (statusFilter !== "all" && c.status !== statusFilter) return false;
      if (searchText && !c.claim_text.toLowerCase().includes(searchText.toLowerCase())) return false;
      return true;
    });
  }, [claims, statusFilter, searchText]);

  const filterTabs: { key: typeof statusFilter; label: string; count: number }[] = [
    { key: "all", label: "All", count: claims.length },
    { key: "pending", label: "Pending", count: summary.pending },
    { key: "supported", label: "Supported", count: summary.supported },
    { key: "waived", label: "Waived", count: summary.waived },
    { key: "unsupported", label: "Unsupported", count: summary.unsupported },
  ];

  return (
    <div className="grid gap-4">
      {/* Summary bar */}
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">{summary.total} total</span>
        <span>·</span>
        <span className={summary.pending > 0 ? "text-amber-600 font-medium" : ""}>
          {summary.pending} pending
        </span>
        <span>·</span>
        <span>{summary.supported} supported</span>
        <span>·</span>
        <span>{summary.waived} waived</span>
        {summary.unsupported > 0 ? (
          <>
            <span>·</span>
            <span className="text-red-600">{summary.unsupported} unsupported</span>
          </>
        ) : null}
      </div>

      {/* Blocking / clear banner */}
      {summary.blocking > 0 ? (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/20 dark:text-amber-200">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
          <p>
            <strong>{summary.blocking}</strong> claim
            {summary.blocking === 1 ? "" : "s"} block{summary.blocking === 1 ? "s" : ""} publishing.
            Attach evidence, waive, or mark unsupported before publish.
          </p>
        </div>
      ) : claims.length > 0 ? (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50/70 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/20 dark:text-emerald-300">
          <CheckCircle2 className="size-4 shrink-0" aria-hidden />
          All claims cleared for publish.
        </div>
      ) : null}

      {/* Empty state: extract claims */}
      {claims.length === 0 ? (
        <>
          <form action={actions.extractClaims}>
            <input name="ideaId" type="hidden" value={ideaId} />
            <Button size="sm" type="submit" variant="secondary">
              <Search className="size-4" aria-hidden />
              Extract claims from draft
            </Button>
          </form>
          <p className="text-sm text-muted-foreground">
            No claims in the ledger yet. Extract claims before publishing quantified statements.
          </p>
        </>
      ) : (
        <>
          {/* Filter + bulk actions bar */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-1">
              {filterTabs.map((tab) =>
                tab.count > 0 || tab.key === "all" ? (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setStatusFilter(tab.key)}
                    className={cn(
                      "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
                      statusFilter === tab.key
                        ? "bg-brand/10 text-brand"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    {tab.label}
                    <span className="ml-1 text-[10px] opacity-60">{tab.count}</span>
                  </button>
                ) : null,
              )}
            </div>

            <div className="flex items-center gap-2">
              <input
                className="h-7 w-36 rounded-md border border-border bg-background px-2 text-xs placeholder:text-muted-foreground/60"
                placeholder="Search claims…"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
              />
              {pendingClaims.length > 1 ? (
                <form action={actions.waiveAllClaims}>
                  <input name="ideaId" type="hidden" value={ideaId} />
                  <SubmitButton label="Waive all" variant="outline" icon={ShieldOff} />
                </form>
              ) : null}
            </div>
          </div>

          {/* Claim cards */}
          {filteredClaims.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              No {statusFilter !== "all" ? statusFilter : "matching"} claims.
            </p>
          ) : (
            <ul className="grid gap-3">
              {filteredClaims.map((claim) => {
                const typeConfig = CLAIM_TYPE_CONFIG[claim.claim_type] || {
                  icon: FileText,
                  label: claim.claim_type.replace(/_/g, " "),
                  color: "text-muted-foreground bg-muted/40",
                };
                const TypeIcon = typeConfig.icon;

                return (
                  <li
                    key={claim.id}
                    className="rounded-lg border border-border bg-card p-4 shadow-sm transition-shadow hover:shadow-md"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="text-sm font-medium leading-snug text-foreground">
                        {claim.claim_text}
                      </p>
                      <ClaimStatusBadge status={claim.status} />
                    </div>

                    {/* Claim type badge */}
                    <span
                      className={cn(
                        "mt-2 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
                        typeConfig.color,
                      )}
                    >
                      <TypeIcon className="size-3" aria-hidden />
                      {typeConfig.label}
                    </span>

                    {/* Existing evidence */}
                    {claim.evidence_source_type || claim.evidence_reference ? (
                      <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50/40 px-3 py-2 text-xs dark:border-emerald-900 dark:bg-emerald-950/15">
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                          Evidence attached
                        </p>
                        {claim.evidence_source_type ? (
                          <p className="mt-1 text-muted-foreground">
                            <span className="font-medium text-foreground">Source:</span>{" "}
                            {claim.evidence_source_type}
                          </p>
                        ) : null}
                        {claim.evidence_reference ? (
                          <p className="mt-0.5 break-all text-muted-foreground">
                            <span className="font-medium text-foreground">Reference:</span>{" "}
                            {claim.evidence_reference}
                          </p>
                        ) : null}
                      </div>
                    ) : null}

                    {/* Pending claim: evidence form */}
                    {claim.status === "pending" ? (
                      <form action={actions.updateClaim} className="mt-4 grid gap-3 rounded-lg border border-dashed border-border/70 bg-muted/20 p-4">
                        <input name="claimId" type="hidden" value={claim.id} />
                        <input name="ideaId" type="hidden" value={ideaId} />

                        <p className="text-xs font-semibold text-foreground">
                          Provide evidence or resolve
                        </p>

                        <div className="grid gap-3 sm:grid-cols-2">
                          <label className="grid gap-1.5 text-xs font-medium text-foreground">
                            Evidence source
                            <select
                              className={selectClassName}
                              defaultValue=""
                              name="evidenceSource"
                              required
                            >
                              <option disabled value="">
                                Select source type
                              </option>
                              {EVIDENCE_SOURCES.map((source) => (
                                <option key={source.value} value={source.value}>
                                  {source.label}
                                </option>
                              ))}
                            </select>
                          </label>
                          <label className="grid gap-1.5 text-xs font-medium text-foreground">
                            Evidence reference
                            <input
                              className="rounded-md border border-border bg-background px-2 py-1.5 text-sm"
                              name="evidenceReference"
                              placeholder="Link, doc section, or measurement note"
                              required
                            />
                          </label>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <SubmitButton label="Mark supported" icon={CheckCircle2} />
                          <button
                            className={cn(
                              buttonVariants({ size: "sm", variant: "outline" }),
                              "gap-1.5",
                            )}
                            name="waive"
                            type="submit"
                            value="on"
                          >
                            <ShieldOff className="size-3.5" aria-hidden />
                            Waive for publish
                          </button>
                          <button
                            className={cn(
                              buttonVariants({ size: "sm", variant: "outline" }),
                              "gap-1.5",
                            )}
                            name="unsupported"
                            type="submit"
                            value="on"
                          >
                            <XCircle className="size-3.5" aria-hidden />
                            Mark unsupported
                          </button>
                        </div>
                      </form>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
