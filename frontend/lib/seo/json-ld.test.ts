import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  webSiteSchema,
  organizationSchema,
  blogPostingSchema,
  breadcrumbListSchema,
  itemListSchema,
} from "./json-ld";

describe("webSiteSchema", () => {
  it("returns WebSite schema with search action", () => {
    const schema = webSiteSchema();
    assert.equal(schema["@type"], "WebSite");
    assert.equal(schema.name, "AI Lab Portal");
    assert.ok(schema.potentialAction);
    assert.equal(schema.potentialAction["@type"], "SearchAction");
  });
});

describe("organizationSchema", () => {
  it("returns Organization schema", () => {
    const schema = organizationSchema();
    assert.equal(schema["@type"], "Organization");
    assert.equal(schema.name, "AI Lab Portal");
  });
});

describe("blogPostingSchema", () => {
  const base = {
    headline: "Test Post",
    description: "A test post description",
    url: "/blog/test-post",
    datePublished: "2026-06-01",
  };

  it("returns BlogPosting schema with required fields", () => {
    const schema = blogPostingSchema(base);
    assert.equal(schema["@type"], "BlogPosting");
    assert.equal(schema.headline, "Test Post");
    assert.equal(schema.datePublished, "2026-06-01");
    assert.equal(schema.dateModified, "2026-06-01");
  });

  it("uses dateModified when provided", () => {
    const schema = blogPostingSchema({ ...base, dateModified: "2026-06-05" });
    assert.equal(schema.dateModified, "2026-06-05");
  });

  it("resolves relative URL to absolute", () => {
    const schema = blogPostingSchema(base);
    assert.match(schema.url, /^https?:\/\//);
    assert.ok(schema.url.endsWith("/blog/test-post"));
  });

  it("includes author when provided", () => {
    const schema = blogPostingSchema({ ...base, authorName: "Alice", authorUrl: "/author/alice" });
    assert.ok(schema.author);
    assert.equal((schema.author as { name: string }).name, "Alice");
  });

  it("includes image when provided", () => {
    const schema = blogPostingSchema({ ...base, imageUrl: "/images/test.png" });
    assert.ok(schema.image);
  });

  it("includes publisher organization", () => {
    const schema = blogPostingSchema(base);
    assert.equal(schema.publisher["@type"], "Organization");
  });
});

describe("breadcrumbListSchema", () => {
  it("generates breadcrumb items with correct positions", () => {
    const items = [
      { name: "Home", url: "/" },
      { name: "Blog", url: "/blog" },
      { name: "Post", url: "/blog/my-post" },
    ];
    const schema = breadcrumbListSchema(items);
    assert.equal(schema["@type"], "BreadcrumbList");
    assert.equal(schema.itemListElement.length, 3);
    assert.equal(schema.itemListElement[0].position, 1);
    assert.equal(schema.itemListElement[0].name, "Home");
    assert.equal(schema.itemListElement[1].position, 2);
    assert.equal(schema.itemListElement[2].position, 3);
  });

  it("handles single item", () => {
    const schema = breadcrumbListSchema([{ name: "Home", url: "/" }]);
    assert.equal(schema.itemListElement.length, 1);
  });
});

describe("itemListSchema", () => {
  const items = [{ slug: "post-1" }, { slug: "post-2" }];

  it("creates ItemList with correct structure", () => {
    const schema = itemListSchema({
      items,
      itemUrl: (i) => `/blog/${i.slug}`,
      itemName: () => "Post",
      numberOfItems: 2,
    });
    assert.equal(schema["@type"], "ItemList");
    assert.equal(schema.numberOfItems, 2);
    assert.equal(schema.itemListElement.length, 2);
    assert.equal(schema.itemListElement[0].position, 1);
  });

  it("assigns sequential positions", () => {
    const schema = itemListSchema({
      items,
      itemUrl: (i) => `/blog/${i.slug}`,
      itemName: () => "Post",
      numberOfItems: 2,
    });
    assert.equal(schema.itemListElement[1].position, 2);
  });
});
