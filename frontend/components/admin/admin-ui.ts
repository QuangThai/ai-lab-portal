import { cn } from "@/lib/utils";

/**
 * Admin layout tokens only — interactive controls use shadcn Button, Input, Textarea, Badge, Label.
 */

export const adminPageStackClass = "flex flex-col gap-5";

/** Blog / showcase editor: main column + fixed sidebar */
export const adminEditorGridClass =
  "grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_17.5rem] xl:grid-cols-[minmax(0,1fr)_19rem] xl:gap-6";

/** Two-column metadata fields inside editor card */
export const adminEditorFieldsClass = "grid gap-4 md:grid-cols-2 md:items-start [&_input]:min-w-0";

export const adminCardResetClass = "gap-0 py-0 ring-0 shadow-none";

export const adminCardClass = cn(
  adminCardResetClass,
  "overflow-hidden rounded-lg border border-border bg-card text-card-foreground"
);

export const adminCardHoverClass = cn(
  adminCardClass,
  "transition-colors hover:border-foreground/20 hover:bg-muted/20"
);

export const adminPanelClass = "rounded-lg border border-border bg-card p-4 sm:p-5";

export const adminSectionPanelClass = cn(adminCardClass, "overflow-hidden");

export const adminListPanelClass = adminSectionPanelClass;

export const adminListRowClass =
  "border-b border-border px-4 py-3.5 transition-colors last:border-b-0 hover:bg-muted/30 sm:px-5";

export function adminIdeaStatusClass(status: "pending" | "approved" | "rejected") {
  if (status === "approved") return "bg-accent text-brand";
  if (status === "rejected") return "bg-destructive/10 text-destructive";
  return "border border-border bg-muted/40 text-muted-foreground";
}

export function adminIdeaPhaseClass(kind: "neutral" | "ready" | "pending") {
  if (kind === "ready") return "bg-accent text-brand";
  if (kind === "pending") return "bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200";
  return "bg-muted/40 text-muted-foreground";
}

export const adminEyebrowClass = "text-xs font-medium text-muted-foreground";

export const adminDisplayTitleClass =
  "font-(family-name:--font-gt-super) text-2xl font-normal tracking-[-0.03em] text-foreground sm:text-[1.75rem] sm:leading-tight";

export const adminPageTitleClass = adminDisplayTitleClass;

export const adminSectionTitleClass = "text-sm font-semibold text-foreground";

export const adminEmptyStateClass =
  "flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 px-6 py-12 text-center";

export const adminEditorSectionClass = "border-b border-border px-4 py-4 sm:px-5";

export const adminEditorBodyClass = "px-4 py-4 sm:px-5";

export const adminEditorDividerClass = "h-px bg-border";

export const adminPageHeaderSurfaceClass = "border-b border-border pb-4";

export const adminWorkflowStatusClass =
  "flex min-h-9 w-full items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium";

export type AdminActionStatus = "idle" | "draft" | "published" | "error";

export function adminStatusPanelClass(status: AdminActionStatus) {
  if (status === "published") return "border-brand/30 bg-accent/70 text-foreground";
  if (status === "error") return "border-destructive/30 bg-destructive/10 text-foreground";
  if (status === "draft") return "border-border bg-muted/40 text-foreground";
  return "border-border bg-muted/25 text-muted-foreground";
}

export const adminTiptapShellClass =
  "w-full overflow-hidden rounded-lg border border-input bg-background focus-within:border-ring focus-within:ring-[3px] focus-within:ring-ring/50";

export const adminEditorialCardClass = adminCardClass;
export const adminStatCardClass = adminCardHoverClass;
export const adminModuleCardClass = adminCardHoverClass;

export const adminLoginFieldClass = "admin-login-field";
