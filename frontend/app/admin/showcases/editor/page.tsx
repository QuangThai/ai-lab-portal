import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { ShowcaseEditor } from "@/components/admin/showcase-editor";
import { auth } from "@/lib/auth/server";
import { publishAction, saveDraftAction } from "./actions";

export default async function AdminShowcaseEditorPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  return (
      <div className={adminPageStackClass}>
        <AdminPageHeader
          description="Compose a client-ready showcase with human-reviewed delivery narrative."
          eyebrow="Content workspace"
          title="Showcase editor"
        />

        <ShowcaseEditor publishAction={publishAction} saveDraftAction={saveDraftAction} />
      </div>
  );
}
