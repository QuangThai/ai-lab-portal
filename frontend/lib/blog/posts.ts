export type BlogPostSummary = {
  slug: string;
  title: string;
  excerpt: string;
  authorName: string;
  publishedAt: string;
};

export type BlogPostDetail = BlogPostSummary & {
  contentMarkdown: string;
};

type ApiBlogPostSummary = {
  slug: string;
  title: string;
  excerpt: string;
  author_name: string;
  published_at: string;
};

type ApiBlogPostDetail = ApiBlogPostSummary & {
  content_markdown: string;
};

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

function toSummary(post: ApiBlogPostSummary): BlogPostSummary {
  return {
    slug: post.slug,
    title: post.title,
    excerpt: post.excerpt,
    authorName: post.author_name,
    publishedAt: post.published_at,
  };
}

function toDetail(post: ApiBlogPostDetail): BlogPostDetail {
  return {
    ...toSummary(post),
    contentMarkdown: post.content_markdown,
  };
}

export async function listPublishedBlogPosts(): Promise<BlogPostSummary[]> {
  const response = await fetch(`${backendBaseUrl}/public/blog-posts`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Failed to fetch published blog posts: ${response.status}`);
  }

  const posts = (await response.json()) as ApiBlogPostSummary[];
  return posts.map(toSummary);
}

export async function getPublishedBlogPost(slug: string): Promise<BlogPostDetail | undefined> {
  const response = await fetch(`${backendBaseUrl}/public/blog-posts/${slug}`, { cache: "no-store" });

  if (response.status === 404) {
    return undefined;
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch published blog post: ${response.status}`);
  }

  return toDetail((await response.json()) as ApiBlogPostDetail);
}
