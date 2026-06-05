"use client";

import { cn } from "@/lib/utils";

type BrandMarkSize = "sm" | "md" | "lg";

type BrandMarkProps = {
  size?: BrandMarkSize;
  className?: string;
};

const sizes: Record<
  BrandMarkSize,
  { fontSize: string; dot: string; dotPos: string }
> = {
  sm: {
    fontSize: "18px",
    dot: "size-[4px]",
    dotPos: "-right-[1px] -top-[1px]",
  },
  md: {
    fontSize: "22px",
    dot: "size-[5px]",
    dotPos: "-right-[1px] -top-[2px]",
  },
  lg: {
    fontSize: "26px",
    dot: "size-[6px]",
    dotPos: "-right-[1px] -top-[2px]",
  },
};

/**
 * Typographic brand mark for AI Lab Portal.
 *
 * "ai" in GT Super — the brand's editorial serif.
 * "a" is brand green, "i" is charcoal, and the dot of the "i" is a
 * floating green circle accent. Pure typography, no container.
 * Reads as "Ai" → editorial AI.
 */
export function BrandMark({ size = "md", className }: BrandMarkProps) {
  const s = sizes[size];

  return (
    <span
      className={cn(
        "inline-flex items-baseline leading-none tracking-[-0.03em]",
        className
      )}
      aria-label="AI Lab Portal"
      role="img"
    >
      <span
        className={cn(
          "font-(family-name:--font-gt-super) font-semibold text-brand",
          "tracking-[-0.02em]"
        )}
        style={{ fontSize: s.fontSize }}
      >
        a
      </span>
      <span
        className={cn(
          "relative font-(family-name:--font-gt-super) font-medium text-foreground",
          "tracking-[-0.02em]"
        )}
        style={{ fontSize: s.fontSize }}
      >
        i
        <span
          className={cn(
            "absolute rounded-full bg-brand ring-[0.5px] ring-white/20",
            s.dot,
            s.dotPos
          )}
          aria-hidden
        />
      </span>
    </span>
  );
}
