import { dash } from "@better-auth/infra";
import { betterAuth } from "better-auth";
import { Pool } from "pg";

import { getAuthEnvironment } from "./env";

const authEnvironment = getAuthEnvironment();

export const auth = betterAuth({
  secret: authEnvironment.betterAuthSecret,
  baseURL: authEnvironment.betterAuthUrl,
  trustedOrigins: authEnvironment.trustedOrigins,
  database: new Pool({
    connectionString: authEnvironment.databaseUrl,
  }),
  emailAndPassword: {
    enabled: true,
  },
  plugins: [
    dash({
      apiKey: authEnvironment.betterAuthApiKey,
    }),
  ],
  advanced: {
    defaultCookieAttributes: {
      sameSite: "lax",
      secure: authEnvironment.isProduction,
      httpOnly: true,
    },
  },
});
