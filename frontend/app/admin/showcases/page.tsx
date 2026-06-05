import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminListToolbar } from "@/components/admin/admin-list-toolbar";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { ShowcaseCardList } from "./showcase-card-list";
import { publishFromListAction, unpublishFromListAction } from "./actions";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export type AdminShowcase = {
  id: string;
  slug: string;
  title: string;
  status: "draft" | "published";
  published_at: string | null;
};

async function listAdminShowcases() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/showcases`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch admin showcases: ${response.status}`);
  }

  return (await response.json()) as AdminShowcase[];
}

export default async function AdminShowcasesListPage() {
  const items = await listAdminShowcases();
  const publishedCount = items.filter((item) => item.status === "published").length;
  const draftCount = items.length - publishedCount;

  return (
      <div className={adminPageStackClass}>
        <AdminListToolbar
          ctaHref="/admin/showcases/editor"
          ctaLabel="New showcase"
          description="Manage client-ready showcases with the same publish workflow as blog posts."
          eyebrow="Client stories"
          metrics={[
            { dotClassName: "bg-brand", label: `${publishedCount} live` },
            { dotClassName: "bg-amber-500", label: `${draftCount} drafts` },
            { dotClassName: "bg-muted-foreground", label: `${items.length} total` },
          ]}
          title="Showcases"
        />

        <ShowcaseCardList
          items={items}
          publishAction={publishFromListAction}
          unpublishAction={unpublishFromListAction}
        />
      </div>
  );
}
