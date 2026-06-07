import assert from "node:assert/strict";
import { describe, it } from "node:test";

// Set env before any imports run (imports are hoisted in ESM, but tsx compiles
// to CJS where assignment order matters. Using process.env before the import
// in the same module ensures it's set when the module evaluates.)
process.env.NEXT_PUBLIC_SITE_URL = "https://test-ailab.com";

import { createPublicMetadata } from "./metadata";

describe("createPublicMetadata", () => {
  it("returns basic metadata with title and description", () => {
    const meta = createPublicMetadata({
      title: "Test Article",
      description: "A test article",
      path: "/blog/test",
    });

    assert.equal(meta.title, "Test Article");
    assert.equal(meta.description, "A test article");
    assert.equal((meta.openGraph as Record<string, unknown>).title, "Test Article");
    assert.equal((meta.twitter as Record<string, unknown>).title, "Test Article");
  });

  it("creates canonical URL from path", () => {
    const meta = createPublicMetadata({
      title: "Test",
      description: "Desc",
      path: "/blog/my-post",
    });

    assert.equal(meta.alternates?.canonical, "/blog/my-post");
    assert.equal((meta.openGraph as Record<string, unknown>).url, "/blog/my-post");
  });

  it("prepends slash to bare path", () => {
    const meta = createPublicMetadata({
      title: "Test",
      description: "Desc",
      path: "blog/no-slash",
    });

    assert.equal(meta.alternates?.canonical, "/blog/no-slash");
  });

  it("uses article type when specified", () => {
    const meta = createPublicMetadata({
      title: "Test",
      description: "Desc",
      path: "/blog/article",
      type: "article",
    });

    assert.equal((meta.openGraph as Record<string, unknown>).type, "article");
  });

  it("includes OG image when provided", () => {
    const meta = createPublicMetadata({
      title: "Test",
      description: "Desc",
      path: "/blog/test",
      ogImageUrl: "https://cdn.example.com/image.png",
    });

    const ogImages = (meta.openGraph as Record<string, unknown>).images as Array<{ url: string }>;
    assert.equal(ogImages[0].url, "https://cdn.example.com/image.png");
    const twImages = (meta.twitter as Record<string, unknown>).images as string[];
    assert.equal(twImages[0], "https://cdn.example.com/image.png");
  });

  it("uses default OG image from env base URL when not provided", () => {
    const meta = createPublicMetadata({
      title: "My Title",
      description: "My Desc",
      path: "/blog/default-og",
      ogAuthor: "Alice",
      ogReadingTime: 5,
    });

    const ogImages = (meta.openGraph as Record<string, unknown>).images as Array<{ url: string }>;
    const url = ogImages[0].url;
    // baseUrl is process.env.NEXT_PUBLIC_SITE_URL at module load time
    assert.ok(url.startsWith("https://"), `Expected absolute URL, got: ${url}`);
    assert.ok(url.includes("/api/og?"), `Expected /api/og? in URL, got: ${url}`);
    assert.ok(url.includes("author=Alice"), url);
    assert.ok(url.includes("readingTime=5"), url);
  });

  it("includes twitter card fields", () => {
    const meta = createPublicMetadata({
      title: "Test",
      description: "Desc",
      path: "/blog/twitter",
    });

    assert.equal((meta.twitter as Record<string, unknown>).card, "summary_large_image");
  });
});
