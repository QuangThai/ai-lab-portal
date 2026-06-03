import { Rss } from "lucide-react";

import { AdminListActionForm, AdminListSubmitButton } from "@/components/admin/admin-list-actions";
import { adminPanelClass } from "@/components/admin/admin-ui";
import { cn } from "@/lib/utils";
import type { AdminNewsSource } from "./page";

type Props = {
  items: AdminNewsSource[];
  toggleAction: (formData: FormData) => Promise<void>;
};

export function NewsSourceCardList({ items, toggleAction }: Props) {
  if (items.length === 0) {
    return (
      <div className={cn(adminPanelClass, "p-8 text-center text-sm text-muted-foreground")}>
        No sources configured yet.
      </div>
    );
  }

  return (
    <ul className="grid gap-3">
      {items.map((item) => (
        <li key={item.id} className={cn(adminPanelClass, "flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between")}>
          <div className="flex gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-muted">
              <Rss className="size-4 text-muted-foreground" aria-hidden />
            </div>
            <div>
              <p className="font-medium text-foreground">{item.name}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {item.source_type} · {item.priority} · {item.is_enabled ? "enabled" : "disabled"}
              </p>
              <p className="mt-1 max-w-xl truncate text-xs text-muted-foreground">{item.url_or_identifier}</p>
            </div>
          </div>
          <AdminListActionForm action={toggleAction}>
            <input name="sourceId" type="hidden" value={item.id} />
            <input name="enabled" type="hidden" value={item.is_enabled ? "false" : "true"} />
            <AdminListSubmitButton variant="outline">
              {item.is_enabled ? "Disable" : "Enable"}
            </AdminListSubmitButton>
          </AdminListActionForm>
        </li>
      ))}
    </ul>
  );
}
