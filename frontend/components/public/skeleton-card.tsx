import { Skeleton } from "@/components/ui/skeleton";

/** Skeleton placeholder matching PublicIndexEntry card dimensions. */
export function SkeletonCard() {
  return (
    <div className="flex flex-col gap-1.5 border-b border-border pb-5">
      <Skeleton className="h-3 w-1/3" />
      <Skeleton className="mt-2 h-6 w-2/3" />
      <Skeleton className="mt-1 h-4 w-full" />
      <Skeleton className="mt-0.5 h-4 w-5/6" />
    </div>
  );
}

/** Grid of skeleton cards for list pages. */
export function SkeletonCardGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="flex flex-col gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
