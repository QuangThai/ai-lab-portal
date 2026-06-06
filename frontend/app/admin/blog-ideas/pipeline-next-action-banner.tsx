"use client";

import Link from "next/link";
import {
  ArrowDown,
  CheckCircle2,
  Loader2,
  PauseCircle,
  Sparkles,
} from "lucide-react";

import { buttonVariants } from "@/components/ui/button-variants";
import { cn } from "@/lib/utils";

import type { PipelineNextAction } from "./lib/pipeline-next-action";

type Props = {
  action: PipelineNextAction;
};

export function PipelineNextActionBanner({ action }: Props) {
  const icon =
    action.kind === "processing" ? (
      <Loader2 className="size-4 animate-spin" aria-hidden />
    ) : action.kind === "done" ? (
      <CheckCircle2 className="size-4" aria-hidden />
    ) : action.kind === "blocked" ? (
      <PauseCircle className="size-4" aria-hidden />
    ) : (
      <Sparkles className="size-4" aria-hidden />
    );

  const tone =
    action.kind === "processing"
      ? "border-sky-200 bg-sky-50/80 dark:border-sky-900 dark:bg-sky-950/20"
      : action.kind === "blocked"
        ? "border-red-200 bg-red-50/70 dark:border-red-900 dark:bg-red-950/15"
        : action.kind === "done"
          ? "border-emerald-200 bg-emerald-50/70 dark:border-emerald-900 dark:bg-emerald-950/15"
          : "border-brand/30 bg-brand/5";

  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-xl border px-4 py-3 sm:flex-row sm:items-center sm:justify-between",
        tone,
      )}
    >
      <div className="flex items-start gap-3">
        <span className="mt-0.5 text-brand">{icon}</span>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
            {action.kind === "processing" ? "Running" : "Next action"}
          </p>
          <p className="text-sm font-semibold text-foreground">{action.title}</p>
          <p className="mt-0.5 text-sm text-muted-foreground">{action.description}</p>
        </div>
      </div>
      {action.kind !== "done" && action.kind !== "processing" ? (
        <Link
          href={`#${action.sectionAnchor}`}
          className={cn(
            buttonVariants({ variant: "secondary", size: "sm" }),
            "shrink-0 gap-1.5 self-start sm:self-center",
          )}
        >
          Go to step
          <ArrowDown className="size-3.5" aria-hidden />
        </Link>
      ) : null}
    </div>
  );
}
