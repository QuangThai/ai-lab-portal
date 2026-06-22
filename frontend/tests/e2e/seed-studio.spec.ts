import { expect, test } from "@playwright/test";
import { signInAdmin } from "./helpers";

const testEmail = `seed-studio-test-${Date.now()}@example.com`;
const testPassword = "TestPassword123!";

test.describe("Admin Seed Studio", () => {
  test("renders content type cards and seeds content successfully", async ({ context, page }) => {
    test.setTimeout(45_000);

    // Sign in and navigate to seed studio
    await signInAdmin(context, testEmail, testPassword);
    await page.goto("/admin/seed-studio");
    await page.waitForLoadState("networkidle");

    // Verify page header
    await expect(page.getByText("Seed Studio")).toBeVisible();
    await expect(page.getByText("Populate the platform with demo content")).toBeVisible();

    // Verify 3 content type cards are rendered
    const cardLabels = ["Blog Posts", "Showcases", "Projects"];
    for (const label of cardLabels) {
      await expect(page.getByText(label).first()).toBeVisible();
    }

    // Verify descriptions
    await expect(page.getByText("6 editorial posts about AI agents").first()).toBeVisible();
    await expect(page.getByText("5 client case studies").first()).toBeVisible();
    await expect(page.getByText("4 published projects for AI pipeline").first()).toBeVisible();

    // Click "Seed all content"
    const seedButton = page.getByRole("button", { name: /seed all content/i });
    await expect(seedButton).toBeVisible();
    await seedButton.click();

    // Wait for success state
    await expect(page.getByText(/seeded/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/blog posts? added|all content already exists/i)).toBeVisible();

    // Verify button text changed
    await expect(page.getByRole("button", { name: /seed again/i })).toBeVisible();
  });

  test("dashboard shows Seed Studio module card", async ({ context, page }) => {
    test.setTimeout(30_000);

    await signInAdmin(context, testEmail, testPassword);
    await page.goto("/admin");
    await page.waitForLoadState("networkidle");

    // Verify Seed Studio card exists on dashboard
    const seedCard = page.locator("a[href='/admin/seed-studio']").first();
    await expect(seedCard).toBeVisible({ timeout: 10_000 });

    // Click through to verify it works
    await seedCard.click();
    await expect(page).toHaveURL(/\/admin\/seed-studio/);
    await expect(page.getByText("Seed Studio")).toBeVisible();
  });
});
