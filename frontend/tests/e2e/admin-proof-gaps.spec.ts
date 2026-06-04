import { expect, test, type BrowserContext } from "@playwright/test";
import pg from "pg";

const { Client } = pg;
const e2eDatabaseUrl =
  process.env.AUTH_DATABASE_URL ??
  "postgresql://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal";

function uniqueId(prefix: string, workerIndex: number) {
  return `${prefix}-${workerIndex}-${Date.now()}`;
}

async function dbQuery(query: string, values: unknown[] = []) {
  const client = new Client({ connectionString: e2eDatabaseUrl });
  await client.connect();
  try {
    return await client.query(query, values);
  } finally {
    await client.end();
  }
}

async function signInAdmin(context: BrowserContext, email: string, password: string) {
  const signUpResponse = await context.request.post("/api/auth/sign-up/email", {
    headers: { Origin: "http://127.0.0.1:13100" },
    data: { email, password, name: "AI Lab Admin" },
  });
  const signInResponse = await context.request.post("/api/auth/sign-in/email", {
    headers: { Origin: "http://127.0.0.1:13100" },
    data: { email, password },
  });

  expect(signUpResponse.ok(), await signUpResponse.text()).toBeTruthy();
  expect(signInResponse.ok(), await signInResponse.text()).toBeTruthy();
}

async function cleanupAdmin(email: string) {
  await dbQuery('delete from session where "userId" in (select id from "user" where email = $1)', [email]);
  await dbQuery('delete from account where "userId" in (select id from "user" where email = $1)', [email]);
  await dbQuery('delete from "user" where email = $1', [email]);
}

test("admin blog idea detail shows queued generation job status", async ({ context, page }, testInfo) => {
  const id = uniqueId("idea-job", testInfo.workerIndex);
  const email = `${id}@example.com`;
  const password = "test-admin-password-123456";
  const ideaId = `idea_${id}`;
  const taskId = `task_${id}`;

  await signInAdmin(context, email, password);
  await dbQuery(
    `
    insert into blog_ideas (
      id, title, angle, target_reader, article_goal, positioning_notes,
      source, source_project_context, status, outline_sections,
      created_at, updated_at
    )
    values ($1, $2, $3, $4, $5, $6, 'manual', null, 'approved', '[]', now(), now())
    `,
    [
      ideaId,
      "Queued Generation E2E Proof",
      "AI operations",
      "Engineering leaders",
      "Show generation job polling",
      "[]",
    ],
  );
  await dbQuery(
    `
    insert into blog_generation_jobs (
      id, blog_idea_id, stage, celery_task_id, status, created_at, updated_at
    )
    values ($1, $2, 'outline', $3, 'queued', now(), now())
    `,
    [`genjob_${id}`, ideaId, taskId],
  );

  try {
    await page.goto(
      `/admin/blog-ideas/${ideaId}?opStage=outline&opStatus=queued&taskId=${taskId}&message=Outline%20generation%20started`,
    );

    await expect(page.getByRole("heading", { name: "Queued Generation E2E Proof" })).toBeVisible();
    await expect(page.getByRole("status")).toContainText("Generation queued");
    await expect(page.getByRole("status")).toContainText(`Task: ${taskId}`);
  } finally {
    await dbQuery("delete from blog_generation_jobs where blog_idea_id = $1", [ideaId]);
    await dbQuery("delete from blog_ideas where id = $1", [ideaId]);
    await cleanupAdmin(email);
  }
});

test("admin blog idea detail can extract claim evidence ledger items", async ({ context, page }, testInfo) => {
  const id = uniqueId("idea-claims", testInfo.workerIndex);
  const email = `${id}@example.com`;
  const password = "test-admin-password-123456";
  const ideaId = `idea_${id}`;

  await signInAdmin(context, email, password);
  await dbQuery(
    `
    insert into blog_ideas (
      id, title, angle, target_reader, article_goal, positioning_notes,
      source, source_project_context, status, outline_sections,
      draft_markdown, draft_status, created_at, updated_at
    )
    values ($1, $2, $3, $4, $5, $6, 'manual', null, 'approved', '[]', $7, 'approved', now(), now())
    `,
    [
      ideaId,
      "Claim Ledger E2E Proof",
      "AI quality",
      "Technical buyers",
      "Prove claim evidence workflow",
      "[]",
      "The review workflow reduces manual QA time by 40% for 12 users.",
    ],
  );

  try {
    await page.goto(`/admin/blog-ideas/${ideaId}`);
    await expect(page.getByRole("heading", { name: "Claim Ledger E2E Proof" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Extract claims from draft" })).toBeVisible();

    await page.getByRole("button", { name: "Extract claims from draft" }).click();
    await expect(page.getByText("reduces manual QA time by 40%")).toBeVisible();
    await expect(page.getByRole("button", { name: "Attach evidence" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Waive for publish" })).toBeVisible();
  } finally {
    await dbQuery("delete from blog_claims where blog_idea_id = $1", [ideaId]);
    await dbQuery("delete from blog_ideas where id = $1", [ideaId]);
    await cleanupAdmin(email);
  }
});

test("admin can create and view a news source", async ({ context, page }, testInfo) => {
  const id = uniqueId("news-source", testInfo.workerIndex);
  const email = `${id}@example.com`;
  const password = "test-admin-password-123456";
  const sourceName = `E2E News Source ${id}`;
  const sourceUrl = `https://example.com/${id}.xml`;

  await signInAdmin(context, email, password);

  try {
    await page.goto("/admin/news-sources/new");
    await expect(page.getByRole("heading", { name: "Add news source" })).toBeVisible();
    await page.getByLabel("Name").fill(sourceName);
    await page.getByLabel("URL or identifier").fill(sourceUrl);
    await page.getByLabel("Priority").selectOption("high");
    await page.getByRole("button", { name: "Save source" }).click();

    await expect(page).toHaveURL(/\/admin\/news-sources$/);
    await expect(page.getByRole("heading", { name: "News sources" })).toBeVisible();
    await expect(page.getByText(sourceName)).toBeVisible();
    await expect(page.getByText(sourceUrl)).toBeVisible();
  } finally {
    await dbQuery("delete from news_sources where name = $1", [sourceName]);
    await cleanupAdmin(email);
  }
});
