import { readFileSync } from "node:fs";
import { join } from "node:path";

import { expect, test } from "@playwright/test";
import pg from "pg";

const { Client } = pg;
const e2eDatabaseUrl = process.env.AUTH_DATABASE_URL ?? "postgresql://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal";

function readTestPostContent() {
  return readFileSync(join(process.cwd(), "..", "test-post.md"), "utf8");
}

async function cleanupE2eData(email: string, slug: string) {
  const client = new Client({ connectionString: e2eDatabaseUrl });
  await client.connect();
  try {
    await client.query('delete from audit_events where entity_id in (select id from blog_posts where slug = $1)', [slug]);
    await client.query("delete from blog_posts where slug = $1", [slug]);
    await client.query('delete from session where "userId" in (select id from "user" where email = $1)', [email]);
    await client.query('delete from account where "userId" in (select id from "user" where email = $1)', [email]);
    await client.query('delete from "user" where email = $1', [email]);
  } finally {
    await client.end();
  }
}

test("public home renders MVP1 navigation and entry points", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle(/AI Lab Portal/);
  await expect(page.getByRole("heading", { name: /credible AI Lab presence/i })).toBeVisible();

  const nav = page.getByRole("navigation", { name: "Public navigation" });
  await expect(nav.getByRole("link", { name: "AI Lab" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Showcases" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Blog" })).toBeVisible();

  await expect(page.getByRole("link", { name: "Explore AI Lab" }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "View showcases" }).first()).toBeVisible();
});

test("public showcase and lab pages render published content", async ({ page }) => {
  await page.goto("/showcases");

  await expect(page.getByRole("heading", { name: "Practical AI delivery stories." })).toBeVisible();
  await expect(page.getByRole("link", { name: "Scopelytics" })).toBeVisible();

  await page.getByRole("link", { name: "Scopelytics" }).click();
  await expect(page).toHaveURL(/\/showcases\/scopelytics$/);
  await expect(page.getByRole("heading", { name: "Scopelytics" })).toBeVisible();

  await page.goto("/lab");
  await expect(page.getByRole("heading", { name: /Human-reviewed AI engineering/i })).toBeVisible();
  await expect(page.getByRole("link", { name: "Scopelytics" })).toBeVisible();
});

test("public blog pages render published content", async ({ page }) => {
  await page.goto("/blog");

  await expect(page.getByRole("heading", { name: "Practical AI engineering notes." })).toBeVisible();
  await expect(page.getByRole("link", { name: "Building an AI Lab with Human Review at the Center" })).toBeVisible();

  await page.getByRole("link", { name: "Building an AI Lab with Human Review at the Center" }).click();
  await expect(page).toHaveURL(/\/blog\/building-an-ai-lab-with-human-review$/);
  await expect(page.getByRole("heading", { name: "Building an AI Lab with Human Review at the Center" })).toBeVisible();
  await expect(page.getByText(/publishing remains a deliberate act/i)).toBeVisible();
});

test("admin shell redirects unauthenticated users to login", async ({ page }) => {
  await page.goto("/admin");

  await expect(page).toHaveURL(/\/admin\/login$/);
  await expect(page.getByRole("heading", { name: /Publish with\s+intention/i })).toBeVisible();
});

test("admin blog editor redirects unauthenticated users to login", async ({ page }) => {
  await page.goto("/admin/blog/editor");

  await expect(page).toHaveURL(/\/admin\/login$/);
  await expect(page.getByRole("heading", { name: /Publish with\s+intention/i })).toBeVisible();
});

test("authenticated admin can publish test-post content and clean up", async ({ context, page }, testInfo) => {
  test.setTimeout(90_000);
  const uniqueId = `${testInfo.workerIndex}-${Date.now()}`;
  const adminEmail = `admin-${uniqueId}@example.com`;
  const adminPassword = "test-admin-password-123456";
  const slug = `e2e-agent-tips-${uniqueId}`;
  const testPostContent = readTestPostContent();

  try {
    const signUpResponse = await context.request.post("/api/auth/sign-up/email", {
      headers: { Origin: "http://127.0.0.1:13100" },
      data: { email: adminEmail, password: adminPassword, name: "AI Lab Admin" },
    });
    const signInResponse = await context.request.post("/api/auth/sign-in/email", {
      headers: { Origin: "http://127.0.0.1:13100" },
      data: { email: adminEmail, password: adminPassword },
    });

    expect(signUpResponse.ok(), await signUpResponse.text()).toBeTruthy();
    expect(signInResponse.ok(), await signInResponse.text()).toBeTruthy();

    await page.goto("/admin/blog");
    await expect(page.getByRole("heading", { name: "Blog posts" })).toBeVisible();

    const openEditor = page.getByRole("link", { name: "Open editor" }).first();
    if (await openEditor.isVisible()) {
      await openEditor.click();
      await page.waitForURL(/\/admin\/blog\/[^/]+\/edit$/);
      await expect(page.getByRole("heading", { name: "Edit blog post" })).toBeVisible({ timeout: 45_000 });
      await expect(page.getByLabel("Title")).toBeVisible();
      await page.goto("/admin/blog");
    }
    await expect(page.getByRole("link", { name: "New draft" })).toBeVisible();
    await page.getByRole("link", { name: "New draft" }).click();

    await expect(page.getByRole("heading", { name: "Blog editor" })).toBeVisible();
    await page.getByLabel("Title").fill("Pi and Codex Agent Workflow Tips");
    await page.getByLabel("Slug").fill(slug);
    await page.getByLabel("Excerpt").fill("Practical tips for Pi coding agent packages and Codex coding agent workflows.");
    await page.locator(".tiptap").fill(testPostContent);

    await page.getByRole("button", { name: "Publish saved post" }).click();
    await expect(page.getByRole("status")).toContainText("Published");

    await page.goto("/blog");
    await expect(page.getByRole("link", { name: "Pi and Codex Agent Workflow Tips" })).toBeVisible();
    await page.getByRole("link", { name: "Pi and Codex Agent Workflow Tips" }).click();
    await expect(page.getByText("pi-subagents")).toBeVisible();
    await expect(page.getByText("codex feature list")).toBeVisible();

  } finally {
    await cleanupE2eData(adminEmail, slug);
  }
});

test("admin login page renders credential form", async ({ page }) => {
  await page.goto("/admin/login");

  await expect(page.getByRole("heading", { name: /Publish with\s+intention/i })).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Password" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});
