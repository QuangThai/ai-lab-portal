import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type AdminStatusBadgeProps = {
  status: "draft" | "published";
};

export function AdminStatusBadge({ status }: AdminStatusBadgeProps) {
  return (
    <Badge
      className={cn(
        "rounded-[var(--radius-admin-sm)] font-normal transition-colors",
        status === "draft" && "text-muted-foreground"
      )}
      variant={status === "published" ? "success" : "outline"}
    >
      {status}
    </Badge>
  );
}
