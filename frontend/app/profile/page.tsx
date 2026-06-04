import { headers } from "next/headers";
import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Briefcase, Code, Globe, Pencil } from "lucide-react";

import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { buttonVariants } from "@/components/ui/button-variants";
import { auth } from "@/lib/auth/server";
import { getMyProfile } from "@/lib/user/profile";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function ProfilePage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");
  const profile = await getMyProfile(session);

  return (
    <PublicPageShell currentPath="/profile">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-8 py-10 sm:py-14")}>
        <div className="flex items-start justify-between gap-4">
          <PublicBackLink href="/blog">Blog</PublicBackLink>
          <Link className={buttonVariants({ variant: "outline", size: "sm" })} href="/profile/edit">
            <Pencil className="size-3.5" />
            Edit profile
          </Link>
        </div>

        <div className="rounded-2xl border bg-card p-6 sm:p-8">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
            <div className="relative flex size-24 shrink-0 items-center justify-center overflow-hidden rounded-full border bg-muted text-3xl font-semibold text-muted-foreground">
              {profile.avatarUrl ? (
                <Image src={profile.avatarUrl} alt="" fill className="object-cover" unoptimized />
              ) : (
                profile.displayName[0]?.toUpperCase()
              )}
            </div>
            <div className="min-w-0 flex-1 space-y-4">
              <div>
                <h1 className="text-3xl font-semibold tracking-tight">{profile.displayName}</h1>
                <p className="mt-1 text-sm text-muted-foreground">Member profile</p>
              </div>
              {profile.bio && <p className="max-w-2xl whitespace-pre-wrap text-sm leading-7 text-foreground/85">{profile.bio}</p>}
              <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                {profile.websiteUrl && <a className="inline-flex items-center gap-1.5 hover:text-foreground" href={profile.websiteUrl}><Globe className="size-4" />Website</a>}
                {profile.githubUrl && <a className="inline-flex items-center gap-1.5 hover:text-foreground" href={profile.githubUrl}><Code className="size-4" />GitHub</a>}
                {profile.linkedinUrl && <a className="inline-flex items-center gap-1.5 hover:text-foreground" href={profile.linkedinUrl}><Briefcase className="size-4" />LinkedIn</a>}
              </div>
            </div>
          </div>
        </div>
      </section>
    </PublicPageShell>
  );
}
