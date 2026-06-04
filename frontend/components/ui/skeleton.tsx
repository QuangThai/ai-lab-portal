import { cn } from "@/lib/utils";

type SkeletonProps = {
  className?: string;
};

/** Simple CSS shimmer skeleton — matches shadcn/ui Skeleton API. */
export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      aria-hidden
      className={cn("animate-pulse rounded-md bg-muted", className)}
    />
  );
}
