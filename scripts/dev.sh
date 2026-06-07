#!/usr/bin/env bash
# Auto-detect port for Next.js dev server. Sets BETTER_AUTH_URL dynamically.
# Falls back: 3000 → 3001 → 3002 → ... up to 10 tries.
# Usage: bash scripts/dev.sh
# Or from npm: npm run dev (configured in package.json)

set -euo pipefail

PORT=3000
MAX_TRIES=10

# Check which ports are in use and pick the first free one
for ((i = 0; i < MAX_TRIES; i++)); do
    candidate=$((PORT + i))
    if ! netstat -ano 2>/dev/null | grep -q ":$candidate "; then
        PORT=$candidate
        break
    fi
done

echo "→ Starting Next.js on port ${PORT}"
export BETTER_AUTH_URL="http://localhost:${PORT}"
cd "$(dirname "$0")/../frontend"

npx next dev --port "$PORT" --hostname 127.0.0.1
