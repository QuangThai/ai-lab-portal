import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { ShowcaseEditor } from "@/components/admin/showcase-editor";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { publishAction, saveDraftAction } from "../../editor/actions";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type AdminShowcaseDetail = {
  id: string;
  slug: string;
  title: string;
  status: "draft" | "published";
  hero_summary: string;
  industry: string | null;
  use_case: string | null;
  content_markdown: string;
  image_url?: string | null;
};

async function getAdminShowcase(id: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/showcases/${id}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (response.status === 404) return undefined;
  if (!response.ok)
    throw new Error(`Failed to fetch admin showcase: ${response.status}`);
  return (await response.json()) as AdminShowcaseDetail;
}

export default async function AdminShowcaseEditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const item = await getAdminShowcase(id);
  if (!item) notFound();

  return (
    <AdminCmsShell active="showcases">
      <div className={adminPageStackClass}>
        <AdminPageHeader
          actions={<AdminBackLink href="/admin/showcases">Back to showcases</AdminBackLink>}
          description={`Editing “${item.title}”.`}
          eyebrow="Content workspace"
          metaText={`/${item.slug}`}
          status={item.status}
          title="Edit showcase"
        />

        <ShowcaseEditor
          initialContentMarkdown={item.content_markdown}
          initialHeroSummary={item.hero_summary}
          initialImageUrl={item.image_url ?? undefined}
          initialIndustry={item.industry ?? ""}
          initialShowcaseId={item.id}
          initialSlug={item.slug}
          initialTitle={item.title}
          initialUseCase={item.use_case ?? ""}
          publishAction={publishAction}
          saveDraftAction={saveDraftAction}
        />
      </div>
    </AdminCmsShell>
  );
}
