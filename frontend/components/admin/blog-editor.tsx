"use client";

import { useActionState, useState } from "react";
import { Save, Globe, FileText } from "lucide-react";

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

import type { EditorActionState } from "../../app/admin/blog/editor/actions";

type BlogEditorProps = {
  initialAuthorName?: string;
  initialContentMarkdown?: string;
  initialExcerpt?: string;
  initialPostId?: string;
  initialSlug?: string;
  initialTitle?: string;
  saveDraftAction: (previous: EditorActionState, formData: FormData) => Promise<EditorActionState>;
  publishAction: (previous: EditorActionState, formData: FormData) => Promise<EditorActionState>;
};

const initialActionState: EditorActionState = {
  message: "Ready",
  postId: "",
  status: "idle",
};

export function BlogEditor({
  initialAuthorName = "AI Lab Team",
  initialContentMarkdown = "",
  initialExcerpt = "A practical draft about pairing AI assistance with human approval, evidence, and measurable workflow design.",
  initialPostId = "",
  initialSlug,
  initialTitle = "Building useful AI agents without losing review control",
  saveDraftAction,
  publishAction,
}: BlogEditorProps) {
  const [saveState, saveFormAction] = useActionState(saveDraftAction, {
    ...initialActionState,
    postId: initialPostId,
  });
  const [publishState, publishFormAction] = useActionState(publishAction, {
    ...initialActionState,
    postId: initialPostId,
  });
  const visibleState = publishState.status !== "idle" ? publishState : saveState;
  const [slug] = useState(() => initialSlug ?? `building-useful-ai-agents-review-control-${Date.now()}`);
  const [contentMarkdown, setContentMarkdown] = useState(initialContentMarkdown);

  return (
    <form action={saveFormAction} className={adminEditorGridClass}>
      <input name="postId" type="hidden" value={visibleState.postId} />
      <input name="authorName" type="hidden" value={initialAuthorName} />
      <input name="contentMarkdown" type="hidden" value={contentMarkdown} />

      <AdminCard>
        <AdminCardSection title="Metadata" />
        <AdminCardBody className={adminEditorFieldsClass}>
          <AdminFormField htmlFor="blog-title" label="Title">
            <AdminInput id="blog-title" name="title" defaultValue={initialTitle} />
          </AdminFormField>
          <AdminFormField htmlFor="blog-slug" label="Slug">
            <AdminInput id="blog-slug" name="slug" defaultValue={slug} />
          </AdminFormField>
          <AdminFormField className="md:col-span-2" htmlFor="blog-excerpt" label="Excerpt">
            <AdminTextarea id="blog-excerpt" name="excerpt" defaultValue={initialExcerpt} rows={4} />
          </AdminFormField>
        </AdminCardBody>

        <AdminCardSection
          description="Rich text is saved as Markdown so formatting persists on publish."
          title="Article content"
        />
        <AdminCardBody>
          <AdminMinimalTiptap
            onChange={setContentMarkdown}
            placeholder="Draft your article… Use the toolbar for headings, lists, links, and more."
            value={contentMarkdown}
          />
        </AdminCardBody>
      </AdminCard>

      <AdminWorkflowCard
        description="Save and publish use a server action so the admin boundary secret never reaches the browser."
        title="Draft controls"
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
          Publish saved post
        </PendingSubmitButton>
      </AdminWorkflowCard>
    </form>
  );
}
