/**
 * Tailwind size utilities for step `8` resolve to `--spacing-8` (8px) from theme.css,
 * not the usual 2rem scale step. Use these helpers for h-8 / size-8 / min-w-8 intent.
 */
export const twScale8 = {
  h: "h-[calc(var(--spacing)*8)]",
  size: "size-[calc(var(--spacing)*8)]",
  minW: "min-w-[calc(var(--spacing)*8)]",
} as const;
