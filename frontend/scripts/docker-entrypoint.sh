#!/bin/sh
# Entrypoint for the frontend Docker container.
# Starts the Next.js dev server directly (bypassing dev.cjs wrapper which
# has path assumptions that don't hold in the Docker filesystem layout).
# Waits for it to be ready, then runs the admin seed script (if ALLOW_ADMIN_SEED=1).

set -e

npx next dev --port 3000 --hostname 0.0.0.0 &
DEV_PID=$!

# Poll until the dev server responds
echo "Waiting for Next.js dev server to be ready..."
until node -e "require('http').get('http://127.0.0.1:3000',r=>{process.exit(r.statusCode===200?0:1)}).on('error',()=>process.exit(1))" 2>/dev/null; do
  sleep 2
done
echo "Next.js dev server is ready."

# Seed admin user if enabled
if [ "${ALLOW_ADMIN_SEED}" = "1" ]; then
  echo "Running admin seed..."
  BETTER_AUTH_URL="http://127.0.0.1:3000" node scripts/seed-admin.mjs || echo "Admin seed completed (or already exists)."
else
  echo "Admin seed skipped (ALLOW_ADMIN_SEED=${ALLOW_ADMIN_SEED:-0})."
fi

# Keep running foreground so container stays up
wait $DEV_PID
