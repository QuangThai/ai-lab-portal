import { PublicIndexEntry } from "@/components/public/public-index-entry";
import { PublicIndexList } from "@/components/public/public-index-list";
import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { listPublishedAiNews } from "@/lib/ai-news/posts";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const metadata = createPublicMetadata({
  title: "AI News | AI Lab Portal",
  description: "Human-reviewed AI news curated from official sources.",
  path: "/ai-news",
});

export const dynamic = "force-dynamic";

export default async function AiNewsIndexPage() {
  const items = await listPublishedAiNews();

  return (
    <PublicPageShell currentPath="/ai-news">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-14 sm:gap-16 lg:gap-20")}>
        <PublicPageHero
          description="Curated AI news from official sources. Items are extracted, deduplicated, scored, and reviewed before publish."
          eyebrow="AI News"
          title="Human-reviewed AI intelligence."
        />

        <PublicIndexList
          emptyDescription="Published AI news will appear here after an editor approves and publishes a candidate."
          emptyTitle="No published AI news yet"
          isEmpty={items.length === 0}
        >
          {items.map((item) => (
            <PublicIndexEntry
              key={item.slug}
              excerpt={item.summary}
              href={`/ai-news/${item.slug}`}
              meta={
                <>
                  {item.sourceName} · {new Date(item.publishedAt).toLocaleDateString("en-US")}
                </>
              }
              title={item.title}
            />
          ))}
        </PublicIndexList>
      </section>
    </PublicPageShell>
  );
}
