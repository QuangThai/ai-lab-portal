#!/bin/sh
# Entrypoint for the frontend Docker container.
# Starts the Next.js dev server, waits for it to be ready,
# then runs the admin seed script (if ALLOW_ADMIN_SEED=1).

set -e

npm run dev -- --hostname 0.0.0.0 --port 3000 &
DEV_PID=$!

# Poll until the dev server responds
echo "Waiting for Next.js dev server to be ready..."
until node -e "require('http').get('http://127.0.0.1:3000',r=>{process.exit(r.statusCode===200?0:1)}).on('error',()=>process.exit(1))" 2>/dev/null; do
  sleep 1
done
echo "Next.js dev server is ready."

# Seed admin user if enabled
# The seed script calls the auth API internally, so BETTER_AUTH_URL must point to the
# container's internal port (3000), not the host-mapped port (13000).
if [ "${ALLOW_ADMIN_SEED}" = "1" ]; then
  echo "Running admin seed..."
  BETTER_AUTH_URL="http://127.0.0.1:3000" node scripts/seed-admin.mjs || echo "Admin seed completed (or already exists)."
else
  echo "Admin seed skipped (ALLOW_ADMIN_SEED=${ALLOW_ADMIN_SEED:-0})."
fi

# Keep running foreground so container stays up
wait $DEV_PID
