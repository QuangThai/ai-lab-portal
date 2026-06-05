import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { ProjectEditor } from "@/components/admin/project-editor";
import { auth } from "@/lib/auth/server";
import { publishAction, saveDraftAction } from "./actions";

export default async function AdminProjectEditorPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  return (
      <div className={adminPageStackClass}>
        <AdminPageHeader
          description="Create a new project or company initiative to showcase on the public site."
          eyebrow="Content workspace"
          title="Project editor"
        />

        <ProjectEditor publishAction={publishAction} saveDraftAction={saveDraftAction} />
      </div>
  );
}
