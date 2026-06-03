"use client";

import { useActionState, useState } from "react";
import { Save, Globe, FileText } from "lucide-react";

import type { ShowcaseEditorActionState } from "@/app/admin/showcases/editor/actions";
import { AdminCard, AdminCardBody, AdminCardSection, AdminWorkflowCard } from "@/components/admin/admin-card";
import { AdminFormField, AdminInput, AdminTextarea } from "@/components/admin/admin-form";
import { AdminMinimalTiptap } from "@/components/admin/admin-minimal-tiptap";
import { AdminEditorDivider } from "@/components/admin/admin-editor-divider";
import {
  adminEditorFieldsClass,
  adminEditorGridClass,
  adminStatusPanelClass,
  adminWorkflowStatusClass,
} from "@/components/admin/admin-ui";
import { PendingSubmitButton } from "@/components/admin/pending-submit-button";
import { cn } from "@/lib/utils";

type ShowcaseEditorProps = {
  initialContentMarkdown?: string;
  initialHeroSummary?: string;
  initialIndustry?: string;
  initialShowcaseId?: string;
  initialSlug?: string;
  initialTitle?: string;
  initialUseCase?: string;
  publishAction: (
    previous: ShowcaseEditorActionState,
    formData: FormData
  ) => Promise<ShowcaseEditorActionState>;
  saveDraftAction: (
    previous: ShowcaseEditorActionState,
    formData: FormData
  ) => Promise<ShowcaseEditorActionState>;
};

const initialActionState: ShowcaseEditorActionState = {
  message: "Ready",
  showcaseId: "",
  status: "idle",
};

export function ShowcaseEditor({
  initialContentMarkdown = "",
  initialHeroSummary = "A client-ready AI Lab delivery story with human review at the center.",
  initialIndustry = "Engineering",
  initialShowcaseId = "",
  initialSlug,
  initialTitle = "New AI Lab Showcase",
  initialUseCase = "Workflow design",
  saveDraftAction,
  publishAction,
}: ShowcaseEditorProps) {
  const [saveState, saveFormAction] = useActionState(saveDraftAction, {
    ...initialActionState,
    showcaseId: initialShowcaseId,
  });
  const [publishState, publishFormAction] = useActionState(publishAction, {
    ...initialActionState,
    showcaseId: initialShowcaseId,
  });
  const visibleState = publishState.status !== "idle" ? publishState : saveState;
  const [slug] = useState(() => initialSlug ?? `new-ai-lab-showcase-${Date.now()}`);
  const [contentMarkdown, setContentMarkdown] = useState(initialContentMarkdown);

  return (
    <form action={saveFormAction} className={adminEditorGridClass}>
      <input name="showcaseId" type="hidden" value={visibleState.showcaseId} />
      <input name="contentMarkdown" type="hidden" value={contentMarkdown} />

      <AdminCard>
        <AdminCardSection title="Metadata" />
        <AdminCardBody className={adminEditorFieldsClass}>
          <AdminFormField htmlFor="showcase-title" label="Title">
            <AdminInput id="showcase-title" name="title" defaultValue={initialTitle} />
          </AdminFormField>
          <AdminFormField htmlFor="showcase-slug" label="Slug">
            <AdminInput id="showcase-slug" name="slug" defaultValue={slug} />
          </AdminFormField>
          <AdminFormField className="md:col-span-2" htmlFor="showcase-hero-summary" label="Hero summary">
            <AdminTextarea
              id="showcase-hero-summary"
              name="heroSummary"
              defaultValue={initialHeroSummary}
              rows={4}
            />
          </AdminFormField>
          <AdminFormField htmlFor="showcase-industry" label="Industry">
            <AdminInput id="showcase-industry" name="industry" defaultValue={initialIndustry} />
          </AdminFormField>
          <AdminFormField htmlFor="showcase-use-case" label="Use case">
            <AdminInput id="showcase-use-case" name="useCase" defaultValue={initialUseCase} />
          </AdminFormField>
        </AdminCardBody>

        <AdminCardSection
          description="Rich text is saved as Markdown so formatting persists on publish."
          title="Showcase story"
        />
        <AdminCardBody>
          <AdminMinimalTiptap
            onChange={setContentMarkdown}
            placeholder="Describe the delivery story, workflow, and review gates…"
            value={contentMarkdown}
          />
        </AdminCardBody>
      </AdminCard>

      <AdminWorkflowCard
        description="Signed server actions keep the admin boundary secret off the browser."
        title="Publish controls"
      >
        <div
          className={cn(adminWorkflowStatusClass, adminStatusPanelClass(visibleState.status))}
          role="status"
        >
          {visibleState.status === "published" ? (
            <Globe className="size-4 shrink-0 text-brand" />
          ) : visibleState.status === "error" ? (
            <span className="h-2 w-2 shrink-0 rounded-full bg-destructive" aria-hidden />
          ) : (
            <FileText className="size-4 shrink-0 text-muted-foreground" />
          )}
          <span className="truncate">{visibleState.status === "published" ? "Published" : visibleState.message}</span>
        </div>

        <AdminEditorDivider />

        <p className="text-xs leading-relaxed text-muted-foreground">Keep this tab open until the status updates.</p>

        <PendingSubmitButton pendingLabel="Saving draft...">
          <Save className="size-4 shrink-0" />
          Save draft
        </PendingSubmitButton>

        <PendingSubmitButton formAction={publishFormAction} pendingLabel="Publishing..." variant="outline">
          <Globe className="size-4 shrink-0" />
          Publish showcase
        </PendingSubmitButton>
      </AdminWorkflowCard>
    </form>
  );
}
