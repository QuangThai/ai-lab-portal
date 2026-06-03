import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { PublicArticleHeader } from "@/components/public/public-article-header";
import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { PublicProse } from "@/components/public/public-prose";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { getPublishedAiNewsItem } from "@/lib/ai-news/posts";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const item = await getPublishedAiNewsItem(slug);

  if (!item) {
    return createPublicMetadata({
      title: "AI News | AI Lab Portal",
      description: "Human-reviewed AI news.",
      path: `/ai-news/${slug}`,
    });
  }

  return createPublicMetadata({
    title: `${item.title} | AI Lab Portal`,
    description: item.summary,
    path: `/ai-news/${slug}`,
  });
}

export default async function AiNewsDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const item = await getPublishedAiNewsItem(slug);

  if (!item) {
    notFound();
  }

  return (
    <PublicPageShell currentPath="/ai-news">
      <article className={cn(publicMainWidthClass, "flex flex-col gap-10 sm:gap-12")}>
        <PublicBackLink href="/ai-news">AI News</PublicBackLink>

        <PublicArticleHeader
          dateLabel={new Date(item.publishedAt).toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric",
          })}
          eyebrow={item.sourceName}
          excerpt={item.whyItMatters}
          title={item.title}
        />

        <p className="text-sm text-muted-foreground">{item.summary}</p>

        <PublicProse contentMarkdown={item.contentMarkdown} />

        <p className="text-sm">
          <Link className="underline underline-offset-4" href={item.sourceUrl} rel="noopener noreferrer" target="_blank">
            Read original source
          </Link>
        </p>
      </article>
    </PublicPageShell>
  );
}
