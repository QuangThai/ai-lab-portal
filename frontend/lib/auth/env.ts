export type AuthEnvironment = {
  betterAuthSecret: string;
  betterAuthUrl: string;
  databaseUrl: string;
  trustedOrigins: string[];
  betterAuthApiKey: string | undefined;
  adminBoundarySecret: string;
  isProduction: boolean;
};

export function getAuthEnvironment(): AuthEnvironment {
  const rawTrustedOrigins = process.env.BETTER_AUTH_TRUSTED_ORIGINS ?? "";
  const trustedOrigins = rawTrustedOrigins
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  return {
    betterAuthSecret:
      process.env.BETTER_AUTH_SECRET || "development-better-auth-secret-at-least-32-chars",
    betterAuthUrl: process.env.BETTER_AUTH_URL || "http://127.0.0.1:13000",
    databaseUrl:
      process.env.DATABASE_URL ||
      process.env.AUTH_DATABASE_URL ||
      "postgresql://ai_lab:ai_lab_dev_password@127.0.0.1:15432/ai_lab_portal",
    trustedOrigins: trustedOrigins.length > 0 ? trustedOrigins : ["http://127.0.0.1:13000"],
    betterAuthApiKey: process.env.BETTER_AUTH_API_KEY || undefined,
    adminBoundarySecret:
      process.env.ADMIN_BOUNDARY_SECRET || "development-admin-boundary-secret-at-least-32-chars",
    isProduction: process.env.NODE_ENV === "production",
  };
}
