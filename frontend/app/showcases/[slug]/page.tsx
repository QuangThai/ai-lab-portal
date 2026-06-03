import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { PublicArticleHeader } from "@/components/public/public-article-header";
import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { PublicProse } from "@/components/public/public-prose";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { getPublishedShowcase } from "@/lib/showcases/items";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const showcase = await getPublishedShowcase(slug);

  if (!showcase) {
    return createPublicMetadata({
      title: "Showcase | AI Lab Portal",
      description: "AI Lab showcase.",
      path: `/showcases/${slug}`,
    });
  }

  return createPublicMetadata({
    title: `${showcase.title} | AI Lab Portal`,
    description: showcase.heroSummary,
    path: `/showcases/${slug}`,
  });
}

export default async function ShowcaseDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const showcase = await getPublishedShowcase(slug);

  if (!showcase) {
    notFound();
  }

  return (
    <PublicPageShell currentPath="/showcases">
      <article className={cn(publicMainWidthClass, "flex flex-col gap-10 sm:gap-12")}>
        <PublicBackLink href="/showcases">Showcases</PublicBackLink>

        <PublicArticleHeader
          dateLabel={new Date(showcase.publishedAt).toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric",
          })}
          eyebrow={[showcase.industry, showcase.useCase].filter(Boolean).join(" · ") || "AI Lab showcase"}
          excerpt={showcase.heroSummary}
          title={showcase.title}
        />

        <PublicProse contentMarkdown={showcase.contentMarkdown} />
      </article>
    </PublicPageShell>
  );
}
