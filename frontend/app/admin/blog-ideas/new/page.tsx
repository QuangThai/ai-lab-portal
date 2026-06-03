import { AdminBackLink } from "@/components/admin/admin-back-link";
import { AdminCard, AdminCardBody } from "@/components/admin/admin-card";
import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { AdminFormField, AdminInput, AdminTextarea } from "@/components/admin/admin-form";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { createIdeaAction } from "./actions";

export default function NewBlogIdeaPage() {
  return (
    <AdminCmsShell active="ideas">
      <div className={adminPageStackClass}>
        <AdminPageHeader
          description="Create a blog idea manually."
          title="New idea"
          actions={<AdminBackLink href="/admin/blog-ideas">Back to ideas</AdminBackLink>}
        />

        <AdminCard>
          <AdminCardBody>
            <form action={createIdeaAction} className="grid max-w-2xl gap-5">
              <AdminFormField htmlFor="title" label="Title">
                <AdminInput
                  id="title"
                  name="title"
                  placeholder="e.g. How We Built an AI Evaluation Pipeline"
                  required
                />
              </AdminFormField>

              <AdminFormField htmlFor="angle" label="Angle">
                <AdminInput
                  id="angle"
                  name="angle"
                  placeholder="e.g. AI Engineering, Case Study, Evaluation"
                  required
                />
              </AdminFormField>

              <AdminFormField htmlFor="targetReader" label="Target reader">
                <AdminInput
                  id="targetReader"
                  name="targetReader"
                  placeholder="e.g. CTO, product manager, developer"
                  required
                />
              </AdminFormField>

              <AdminFormField htmlFor="articleGoal" label="Article goal">
                <AdminTextarea
                  id="articleGoal"
                  name="articleGoal"
                  placeholder="What should this article accomplish?"
                  rows={4}
                  required
                />
              </AdminFormField>

              <div className="flex flex-wrap gap-3 pt-2">
                <Button type="submit" variant="brand">
                  Create idea
                </Button>
                <ButtonLink href="/admin/blog-ideas" variant="outline">
                  Cancel
                </ButtonLink>
              </div>
            </form>
          </AdminCardBody>
        </AdminCard>
      </div>
    </AdminCmsShell>
  );
}
