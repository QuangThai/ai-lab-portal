import { cn } from "@/lib/utils";

/**
 * Admin layout tokens only — interactive controls use shadcn Button, Input, Textarea, Badge, Label.
 *
 * Design language: refined editorial-product hybrid.
 * Keeps the Medium brand warmth (vellum, story green) but adds admin-grade
 * clarity through subtle elevation, cleaner borders, and better rhythm.
 */

/* ── Page layout ── */

/** Vertical stack for a full admin page — use once per page route. */
export const adminPageStackClass = "flex flex-col gap-6";

/** Blog / showcase editor: main column + fixed sidebar */
export const adminEditorGridClass =
  "grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_17.5rem] xl:grid-cols-[minmax(0,1fr)_19rem] xl:gap-7";

/** Two-column metadata fields inside editor card */
export const adminEditorFieldsClass = "grid gap-4 md:grid-cols-2 md:items-start [&_input]:min-w-0";

/* ── Card system (3 tiers) ── */

/** Flat reset for cards used inside other cards (no double border/ring). */
export const adminCardResetClass = "gap-0 py-0 ring-0 shadow-none";

/**
 * Tier 1 — Primary card surface.
 * Subtle border + a whisper of elevation for visual depth without breaking
 * the flat Medium ethos.
 */
export const adminCardClass = cn(
  adminCardResetClass,
  "overflow-hidden rounded-[var(--radius-admin-md)] border border-border/70 bg-card text-card-foreground shadow-[0_1px_3px_0_rgba(0,0,0,0.04),0_1px_2px_-1px_rgba(0,0,0,0.03)]"
);

/**
 * Tier 2 — Hover-reveal card (list items, stat blocks).
 * Elevates subtly on hover for a tactile feel.
 */
export const adminCardHoverClass = cn(
  adminCardClass,
  "transition-all duration-200 ease-out hover:-translate-y-[1px] hover:border-border hover:shadow-[0_4px_12px_0_rgba(0,0,0,0.06),0_1px_3px_0_rgba(0,0,0,0.04)]"
);

/**
 * Tier 3 — Nested / inner card (cards inside a section panel).
 * No shadow, lighter background — visually recedes behind Tier 1.
 */
export const adminNestedCardClass =
  "overflow-hidden rounded-[var(--radius-admin-sm)] border border-border/50 bg-muted/20";

/* ── Section panels ── */

/**
 * A section panel is a Tier-1 card whose header is visually distinct
 * from its body (header has bottom border, body uses flush padding).
 */
export const adminSectionPanelClass = adminCardClass;

/** Alias used by list pages that render rows inside a card shell. */
export const adminListPanelClass = adminSectionPanelClass;

/** A plain panel (non-card, just border + bg). */
export const adminPanelClass =
  "rounded-[var(--radius-admin-md)] border border-border/70 bg-card p-5 shadow-[0_1px_3px_0_rgba(0,0,0,0.04)]";

/* ── List rows ── */

/**
 * Row inside a list panel. Last child gets no border.
 * Uses a subtle `hover:bg-muted/20` to keep rows clean but interactive.
 */
export const adminListRowClass =
  "border-b border-border/50 px-5 py-4 transition-colors last:border-b-0 hover:bg-muted/20";

/* ── Status / phase badges ── */

export function adminIdeaStatusClass(status: "pending" | "approved" | "rejected") {
  if (status === "approved") return "bg-accent text-brand ring-1 ring-brand/15";
  if (status === "rejected") return "bg-destructive/10 text-destructive ring-1 ring-destructive/15";
  return "border border-border bg-muted/40 text-muted-foreground";
}

export function adminIdeaPhaseClass(kind: "neutral" | "ready" | "pending") {
  if (kind === "ready") return "bg-accent text-brand ring-1 ring-brand/15";
  if (kind === "pending") return "bg-amber-50 text-amber-800 ring-1 ring-amber-200/50 dark:bg-amber-950/30 dark:text-amber-200 dark:ring-amber-800/30";
  return "bg-muted/40 text-muted-foreground ring-1 ring-border/50";
}

/* ── Typography ── */

/** Eyebrow label — micro, uppercase, muted. Used above page titles. */
export const adminEyebrowClass = "text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground";

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
  "flex flex-col items-center justify-center rounded-[var(--radius-admin-md)] border border-dashed border-border/60 bg-muted/15 px-6 py-14 text-center";

/* ── Editor layout ── */

export const adminEditorSectionClass = "border-b border-border/70 px-5 py-5";
export const adminEditorBodyClass = "px-5 py-5";
export const adminEditorDividerClass = "h-px bg-border/60";
export const adminPageHeaderSurfaceClass = "border-b border-border/50 pb-5";

/* ── Workflow / status panels ── */

export const adminWorkflowStatusClass =
  "flex min-h-9 w-full items-center gap-2 rounded-[var(--radius-admin-sm)] border px-3 py-2 text-sm font-medium";

export type AdminActionStatus = "idle" | "draft" | "published" | "error";

export function adminStatusPanelClass(status: AdminActionStatus) {
  if (status === "published") return "border-brand/25 bg-accent/60 text-foreground ring-1 ring-brand/10";
  if (status === "error") return "border-destructive/25 bg-destructive/8 text-foreground ring-1 ring-destructive/10";
  if (status === "draft") return "border-border/70 bg-muted/30 text-foreground";
  return "border-border/50 bg-muted/20 text-muted-foreground";
}

export const adminTiptapShellClass =
  "w-full overflow-hidden rounded-[var(--radius-admin-md)] border border-input bg-background focus-within:border-ring focus-within:ring-[3px] focus-within:ring-ring/50";

/* ── Specific card variants (aliases for clarity) ── */

export const adminEditorialCardClass = adminCardClass;
export const adminStatCardClass = adminCardHoverClass;
export const adminModuleCardClass = adminCardHoverClass;

/* ── Login field ── */

export const adminLoginFieldClass = "admin-login-field";
