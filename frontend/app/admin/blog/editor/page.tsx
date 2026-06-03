import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { BlogEditor } from "@/components/admin/blog-editor";
import { publishAction, saveDraftAction } from "./actions";
import { auth } from "@/lib/auth/server";

export default async function AdminBlogEditorPage() {
  const session = await auth.api.getSession({
    headers: await headers(),
  });

  if (!session) {
    redirect("/admin/login");
  }

  return (
    <AdminCmsShell active="editor">
      <div className={adminPageStackClass}>
        <AdminPageHeader
          description="A clean Tiptap editor for human-approved AI Lab content."
          eyebrow="Content workspace"
          title="Blog editor"
        />

        <BlogEditor publishAction={publishAction} saveDraftAction={saveDraftAction} />
      </div>
    </AdminCmsShell>
  );
}
