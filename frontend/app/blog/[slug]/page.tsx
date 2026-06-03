import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { PublicArticleHeader } from "@/components/public/public-article-header";
import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { PublicProse } from "@/components/public/public-prose";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { getPublishedBlogPost } from "@/lib/blog/posts";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPublishedBlogPost(slug);

  if (!post) {
    return createPublicMetadata({
      title: "Blog post | AI Lab Portal",
      description: "AI Lab blog post.",
      path: `/blog/${slug}`,
    });
  }

  return createPublicMetadata({
    title: `${post.title} | AI Lab Portal`,
    description: post.excerpt,
    path: `/blog/${slug}`,
  });
}

export default async function BlogDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPublishedBlogPost(slug);

  if (!post) {
    notFound();
  }

  return (
    <PublicPageShell currentPath="/blog">
      <article className={cn(publicMainWidthClass, "flex flex-col gap-10 sm:gap-12")}>
        <PublicBackLink href="/blog">Blog</PublicBackLink>

        <PublicArticleHeader
          dateLabel={new Date(post.publishedAt).toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric",
          })}
          eyebrow={post.authorName}
          excerpt={post.excerpt}
          title={post.title}
        />

        <PublicProse contentMarkdown={post.contentMarkdown} />
      </article>
    </PublicPageShell>
  );
}
