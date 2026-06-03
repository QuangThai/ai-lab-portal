import { PublicIndexEntry } from "@/components/public/public-index-entry";
import { PublicIndexList } from "@/components/public/public-index-list";
import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { listPublishedBlogPosts } from "@/lib/blog/posts";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const metadata = createPublicMetadata({
  title: "AI Lab Blog | AI Lab Portal",
  description:
    "Practical AI engineering notes and human-reviewed AI Lab articles.",
  path: "/blog",
});

export const dynamic = "force-dynamic";

export default async function BlogIndexPage() {
  const posts = await listPublishedBlogPosts();

  return (
    <PublicPageShell currentPath="/blog">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-14 sm:gap-16 lg:gap-20")}>
        <PublicPageHero
          description="Published posts from the AI Lab. Drafts and internal review material stay private."
          eyebrow="AI Lab Blog"
          title="Practical AI engineering notes."
        />

        <PublicIndexList
          emptyDescription="Published articles will appear here after an admin approves them."
          emptyTitle="No published articles yet"
          isEmpty={posts.length === 0}
        >
          {posts.map((post) => (
            <PublicIndexEntry
              key={post.slug}
              excerpt={post.excerpt}
              href={`/blog/${post.slug}`}
              meta={
                <>
                  {post.authorName} · {new Date(post.publishedAt).toLocaleDateString("en-US")}
                </>
              }
              title={post.title}
            />
          ))}
        </PublicIndexList>
      </section>
    </PublicPageShell>
  );
}
