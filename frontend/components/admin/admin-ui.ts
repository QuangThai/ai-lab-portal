import { cn } from "@/lib/utils";

/**
 * Admin design tokens.
 *
 * Design language: Premium Operations Cockpit.
 * Dark sidebar, elevated glass-morphism cards, luminous green accent (#50b33a).
 * Moves away from flat Medium editorial toward a modern SaaS command center
 * with refined depth, texture, and intentional hierarchy.
 *
 * Interactive controls use shadcn Button, Input, Textarea, Badge, Label.
 */

/* ── Page layout ── */

/** Vertical stack for a full admin page — use once per page route. */
export const adminPageStackClass = "flex flex-col gap-6";

/** Blog / showcase editor: main column + fixed sidebar */
export const adminEditorGridClass =
  "grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_17.5rem] xl:grid-cols-[minmax(0,1fr)_19rem] xl:gap-7";

/** Two-column metadata fields inside editor card */
export const adminEditorFieldsClass =
  "grid gap-4 md:grid-cols-2 md:items-start [&_input]:min-w-0";

/* ── Card system ── */

/** Base card reset — removes shadcn Card interference. */
const adminCardResetClass = "gap-0 py-0 ring-0 shadow-none";

/**
 * Tier 1 — Primary card surface.
 * Uses admin-specific rounded-2xl with subtle elevation and border.
 */
export const adminCardClass = cn(
  adminCardResetClass,
  "overflow-hidden rounded-2xl border border-border/50 bg-card text-card-foreground shadow-[0_1px_3px_0_rgba(0,0,0,0.04),0_1px_2px_-1px_rgba(0,0,0,0.03)]"
);

/**
 * Tier 2 — Hover-reveal card (list items, stat blocks).
 * Elevates subtly on hover with a tinted shadow.
 */
export const adminCardHoverClass = cn(
  adminCardClass,
  "transition-all duration-200 ease-out hover:-translate-y-[1px] hover:border-border/70 hover:shadow-[0_4px_14px_0_rgba(0,0,0,0.07),0_1px_3px_0_rgba(0,0,0,0.04)]"
);

/**
 * Tier 3 — Nested / inner card.
 * Recedes behind Tier 1 — no shadow, lighter background.
 */
export const adminNestedCardClass =
  "overflow-hidden rounded-xl border border-border/40 bg-muted/20";

/* ── Section panels ── */

export const adminSectionPanelClass = adminCardClass;
export const adminListPanelClass = adminSectionPanelClass;

/** A plain panel (non-card, just border + bg). */
export const adminPanelClass =
  "rounded-2xl border border-border/50 bg-card p-5 shadow-[0_1px_3px_0_rgba(0,0,0,0.04)]";

/* ── List rows ── */

export const adminListRowClass =
  "border-b border-border/30 px-6 py-4 transition-colors last:border-b-0 hover:bg-muted/10";

/* ── Status / phase badges ── */

export function adminIdeaStatusClass(
  status: "pending" | "approved" | "rejected",
) {
  if (status === "approved")
    return "bg-brand/10 text-brand ring-1 ring-brand/20";
  if (status === "rejected")
    return "bg-destructive/10 text-destructive ring-1 ring-destructive/15";
  return "border border-border/50 bg-muted/30 text-muted-foreground";
}

export function adminIdeaPhaseClass(kind: "neutral" | "ready" | "pending") {
  if (kind === "ready")
    return "bg-brand/10 text-brand ring-1 ring-brand/20";
  if (kind === "pending")
    return "bg-amber-500/10 text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/20";
  return "bg-muted/30 text-muted-foreground ring-1 ring-border/40";
}

/* ── Typography ── */

/** Eyebrow label — micro, uppercase, muted. Used above page titles. */
export const adminEyebrowClass =
  "text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground/60";

/**
 * Display / page title — uses the Medium gt-super brand font.
 * Reserved for the top-level page title only (one per page).
 */
export const adminDisplayTitleClass =
  "font-(family-name:--font-gt-super) text-2xl font-normal tracking-[-0.03em] text-foreground sm:text-[1.85rem] sm:leading-tight";

/** Alias — same as display title. */
export const adminPageTitleClass = adminDisplayTitleClass;

/**
 * Section title — bold, compact, used inside panels to label a group.
 */
export const adminSectionTitleClass = "text-sm font-semibold text-foreground";

/**
 * Sub-section / card title — lighter weight, used for sub-groupings.
 */
export const adminSubTitleClass = "text-sm font-medium text-foreground/80";

/* ── Empty state ── */

export const adminEmptyStateClass =
  "flex flex-col items-center justify-center rounded-2xl border border-dashed border-border/40 bg-muted/10 px-6 py-14 text-center";

/* ── Editor layout ── */

export const adminEditorSectionClass = "border-b border-border/40 px-6 py-5";
export const adminEditorBodyClass = "px-6 py-5";
export const adminEditorDividerClass = "h-px bg-border/30";
export const adminPageHeaderSurfaceClass = "border-b border-border/30 pb-5";

/* ── Workflow / status panels ── */

export const adminWorkflowStatusClass =
  "flex min-h-9 w-full items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium";

export type AdminActionStatus = "idle" | "draft" | "published" | "error";

export function adminStatusPanelClass(status: AdminActionStatus) {
  if (status === "published")
    return "border-brand/20 bg-brand/8 text-foreground ring-1 ring-brand/10";
  if (status === "error")
    return "border-destructive/20 bg-destructive/8 text-foreground ring-1 ring-destructive/10";
  if (status === "draft")
    return "border-border/50 bg-muted/20 text-foreground";
  return "border-border/40 bg-muted/15 text-muted-foreground";
}

export const adminTiptapShellClass =
  "w-full overflow-hidden rounded-2xl border border-input bg-background focus-within:border-ring focus-within:ring-[3px] focus-within:ring-ring/50";

/* ── Specific card variants (aliases for clarity) ── */

export const adminEditorialCardClass = adminCardClass;
export const adminStatCardClass = adminCardHoverClass;
export const adminModuleCardClass = adminCardHoverClass;

/* ── Login field ── */

export const adminLoginFieldClass = "admin-login-field";
