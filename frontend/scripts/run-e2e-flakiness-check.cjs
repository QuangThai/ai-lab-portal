/**
 * Cross-platform E2E flakiness check runner.
 * Called by npm run quality:e2e-flakiness from frontend/package.json.
 * Delegates to the unified Node.js check script.
 */
require("./e2e-flakiness-check.cjs");
