import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export default function LabLoading() {
  return (
    <PublicPageShell currentPath="/lab">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-14 sm:gap-16 lg:gap-20")}>
        <div className="flex flex-col gap-3">
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-5 w-1/2" />
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-3 rounded-lg border border-border p-5">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/5" />
            </div>
          ))}
        </div>
      </section>
    </PublicPageShell>
  );
}
