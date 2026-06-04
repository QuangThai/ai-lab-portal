import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { auth } from "@/lib/auth/server";
import { getMyProfile } from "@/lib/user/profile";
import { cn } from "@/lib/utils";
import { updateProfileAction } from "./actions";

export const dynamic = "force-dynamic";

export default async function EditProfilePage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");
  const profile = await getMyProfile(session);

  return (
    <PublicPageShell currentPath="/profile">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-8 py-10 sm:py-14")}>
        <PublicBackLink href="/profile">Profile</PublicBackLink>
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Edit profile</h1>
          <p className="text-sm text-muted-foreground">Update your public display name, bio, avatar, and links.</p>
        </div>

        <form action={updateProfileAction} className="grid gap-5 rounded-2xl border bg-card p-6 sm:p-8">
          <label className="grid gap-2 text-sm font-medium">
            Display name
            <Input name="displayName" required defaultValue={profile.displayName} maxLength={120} />
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Bio
            <textarea
              name="bio"
              defaultValue={profile.bio ?? ""}
              maxLength={2000}
              rows={5}
              className="min-h-28 rounded-md border bg-background px-3 py-2 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
            />
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Avatar URL
            <Input name="avatarUrl" type="url" defaultValue={profile.avatarUrl ?? ""} placeholder="https://example.com/avatar.png" />
          </label>
          <div className="grid gap-5 md:grid-cols-3">
            <label className="grid gap-2 text-sm font-medium">
              Website
              <Input name="websiteUrl" type="url" defaultValue={profile.websiteUrl ?? ""} />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              GitHub
              <Input name="githubUrl" type="url" defaultValue={profile.githubUrl ?? ""} />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              LinkedIn
              <Input name="linkedinUrl" type="url" defaultValue={profile.linkedinUrl ?? ""} />
            </label>
          </div>
          <Button className="w-fit" type="submit">Save profile</Button>
        </form>
      </section>
    </PublicPageShell>
  );
}
