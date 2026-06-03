const nodeEnv = process.env.NODE_ENV ?? "development";
const allowSeed = process.env.ALLOW_ADMIN_SEED === "1" || nodeEnv === "test";

if (nodeEnv === "production" || !allowSeed) {
  throw new Error("Admin seed is allowed only in test mode or with ALLOW_ADMIN_SEED=1 outside production.");
}

const baseUrl = process.env.BETTER_AUTH_URL ?? "http://127.0.0.1:13100";
const email = process.env.E2E_ADMIN_EMAIL ?? "admin@example.com";
const password = process.env.E2E_ADMIN_PASSWORD ?? "test-admin-password-123456";
const name = process.env.E2E_ADMIN_NAME ?? "AI Lab Admin";

const response = await fetch(`${baseUrl}/api/auth/sign-up/email`, {
  method: "POST",
  headers: {
    "content-type": "application/json",
    origin: baseUrl,
  },
  body: JSON.stringify({
    email,
    password,
    name,
  }),
});

if (response.ok) {
  console.log(`Seeded admin user ${email}`);
  process.exit(0);
}

const text = await response.text();

if (response.status === 422 || response.status === 400 || text.toLowerCase().includes("already")) {
  console.log(`Admin user ${email} already exists or could not be recreated: ${response.status}`);
  process.exit(0);
}

throw new Error(`Admin seed failed: ${response.status} ${text}`);
