import { createHmac } from "node:crypto";

import { getAuthEnvironment } from "../auth/env";

export const ADMIN_IDENTITY_HEADER = "x-ai-lab-admin-identity";
export const ADMIN_SIGNATURE_HEADER = "x-ai-lab-admin-signature";

export const USER_IDENTITY_HEADER = "x-ai-lab-user-identity";
export const USER_SIGNATURE_HEADER = "x-ai-lab-user-signature";

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

export type UserBoundaryHeaders = {
  [USER_IDENTITY_HEADER]: string;
  [USER_SIGNATURE_HEADER]: string;
};

function sortedKeys<T extends Record<string, unknown>>(obj: T): (keyof T)[] {
  return Object.keys(obj).sort();
}

function signIdentity(identityPayload: string, secret: string): string {
  return createHmac("sha256", secret).update(identityPayload).digest("hex");
}

export function createAdminBoundaryHeaders(
  session: BetterAuthSession,
  issuedAt = Math.floor(Date.now() / 1000),
): AdminBoundaryHeaders {
  const payload = {
    email: session.user.email,
    issued_at: issuedAt,
    role: "admin" as const,
    user_id: session.user.id,
  };
  const identityPayload = JSON.stringify(payload, sortedKeys(payload));

  return {
    [ADMIN_IDENTITY_HEADER]: identityPayload,
    [ADMIN_SIGNATURE_HEADER]: signIdentity(identityPayload, getAuthEnvironment().adminBoundarySecret),
  };
}

export function createUserBoundaryHeaders(
  session: BetterAuthSession,
  issuedAt = Math.floor(Date.now() / 1000),
): UserBoundaryHeaders {
  const payload = {
    email: session.user.email,
    issued_at: issuedAt,
    role: "user" as const,
    user_id: session.user.id,
  };
  const identityPayload = JSON.stringify(payload, sortedKeys(payload));

  return {
    [USER_IDENTITY_HEADER]: identityPayload,
    [USER_SIGNATURE_HEADER]: signIdentity(identityPayload, getAuthEnvironment().adminBoundarySecret),
  };
}
