import { createHmac } from "node:crypto";

import { getAuthEnvironment } from "../auth/env";

export const ADMIN_IDENTITY_HEADER = "x-ai-lab-admin-identity";
export const ADMIN_SIGNATURE_HEADER = "x-ai-lab-admin-signature";

type BetterAuthSessionUser = {
  id: string;
  email: string;
};

type BetterAuthSession = {
  user: BetterAuthSessionUser;
};

export type AdminBoundaryHeaders = {
  [ADMIN_IDENTITY_HEADER]: string;
  [ADMIN_SIGNATURE_HEADER]: string;
};

export function signAdminIdentity(identityPayload: string, secret = getAuthEnvironment().adminBoundarySecret): string {
  return createHmac("sha256", secret).update(identityPayload).digest("hex");
}

export function createAdminBoundaryHeaders(session: BetterAuthSession, issuedAt = Math.floor(Date.now() / 1000)): AdminBoundaryHeaders {
  const identityPayload = JSON.stringify(
    {
      email: session.user.email,
      issued_at: issuedAt,
      role: "admin",
      user_id: session.user.id,
    },
    Object.keys({ email: true, issued_at: true, role: true, user_id: true }).sort(),
  );

  return {
    [ADMIN_IDENTITY_HEADER]: identityPayload,
    [ADMIN_SIGNATURE_HEADER]: signAdminIdentity(identityPayload),
  };
}
