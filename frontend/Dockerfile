# syntax=docker/dockerfile:1

# Frontend images for local Compose (development) and server deploy (production).
#
# Environment contract:
# - Never COPY .env / .env.local into the image (.dockerignore blocks them).
# - Server/runtime secrets (BETTER_AUTH_SECRET, DATABASE_URL, ADMIN_BOUNDARY_SECRET,
#   BACKEND_INTERNAL_URL, etc.) are injected at container start by Compose or the
#   deployment platform — see compose.yaml `environment:` and docs/docker-deployment.md.
# - NEXT_PUBLIC_* values are inlined at `next build` time. For production images,
#   pass them as build-args on the `build` stage (see docs/docker-deployment.md).

FROM node:24-slim AS base

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY frontend/package.json frontend/package-lock.json ./
COPY frontend/scripts/ ./scripts/
# Use npm install instead of npm ci because the lock file generated on Windows
# does not resolve wasm32-wasi platform-specific dependencies (emnapi runtime/core).
# npm install re-resolves these on the build platform (linux/amd64).
# --ignore-scripts prevents prepare hook from failing (../scripts reference).
# Run the postinstall hook manually after install.
RUN npm install --legacy-peer-deps --ignore-scripts && \
    node scripts/ensure-better-auth-sso-stub.mjs

# --- development: used by compose.yaml full Docker stack ---
FROM base AS development

# Copy root-level scripts (dev.cjs references ../scripts/)
COPY scripts/ /scripts/

COPY frontend ./

# Make entrypoint script executable (Compose overrides CMD, but keep for standalone runs)
RUN chmod +x scripts/docker-entrypoint.sh

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]

# --- build + production: server deploy (`docker build --target production`) ---
FROM base AS build

COPY frontend ./

ARG NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL}

RUN npm run build

FROM node:24-slim AS production

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=build /app/package.json /app/package-lock.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/.next ./.next
COPY --from=build /app/next.config.ts ./next.config.ts
COPY --from=build /app/public ./public

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
