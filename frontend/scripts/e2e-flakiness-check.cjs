/**
 * Cross-platform E2E flakiness check.
 * Called by npm run quality:e2e-flakiness via run-e2e-flakiness-check.cjs.
 * Checks for known flaky patterns in Playwright test files.
 * Replaces both e2e-flakiness-check.bat and e2e-flakiness-check.sh.
 */
const fs = require("fs");
const path = require("path");

const e2eDir = path.resolve(__dirname, "..", "tests", "e2e");
let exitCode = 0;

if (!fs.existsSync(e2eDir)) {
  console.log("✅ No E2E tests directory found - skipping flakiness check");
  process.exit(0);
}

// Collect all .ts and .js files in the e2e directory
const files = fs.readdirSync(e2eDir, { recursive: true }).filter(
  (f) => typeof f === "string" && (f.endsWith(".ts") || f.endsWith(".js"))
);

let foundWaitForTimeout = [];
let foundNumericWaitFor = [];
let foundShortTimeout = [];

for (const file of files) {
  const absPath = path.join(e2eDir, file);
  const content = fs.readFileSync(absPath, "utf-8");
  const lines = content.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const lineNum = i + 1;
    const line = lines[i];

    // Pattern 1: waitForTimeout calls
    if (line.includes("waitForTimeout")) {
      foundWaitForTimeout.push(`${absPath}:${lineNum}:${line.trim()}`);
    }

    // Pattern 2: page.waitFor with numeric timeout
    const waitForMatch = line.match(/page\.waitFor\(\s*\d/);
    if (waitForMatch) {
      foundNumericWaitFor.push(`${absPath}:${lineNum}:${line.trim()}`);
    }

    // Pattern 3: Very short timeouts (< 1000ms)
    const timeoutMatch = line.match(/timeout:\s*([1-9]\d{0,2})(?:\}|,|\s)/);
    if (timeoutMatch && parseInt(timeoutMatch[1]) < 1000 && parseInt(timeoutMatch[1]) > 0) {
      foundShortTimeout.push(`${absPath}:${lineNum}:${line.trim()}`);
    }
  }
}

// Report Pattern 1
console.log("  Checking for waitForTimeout() calls...");
if (foundWaitForTimeout.length > 0) {
  console.log("❌ Found waitForTimeout() calls (use waitForSelector instead):");
  foundWaitForTimeout.forEach((entry) => console.log(`  ${entry}`));
  exitCode = 1;
}

// Report Pattern 2
console.log("  Checking for numeric waitFor patterns...");
if (foundNumericWaitFor.length > 0) {
  console.log("❌ Found numeric waitFor() calls (use waitForSelector instead):");
  foundNumericWaitFor.forEach((entry) => console.log(`  ${entry}`));
  exitCode = 1;
}

// Report Pattern 3
console.log("  Checking for overly short timeouts...");
if (foundShortTimeout.length > 0) {
  console.log("⚠️ Found potentially too-short timeouts (< 1000ms):");
  foundShortTimeout.forEach((entry) => console.log(`  ${entry}`));
  exitCode = 1;
}

// Report Pattern 4: sleep/delay (informational)
console.log("  Checking for sleep/delay patterns...");
let foundSleepDelay = [];
for (const file of files) {
  const absPath = path.join(e2eDir, file);
  const content = fs.readFileSync(absPath, "utf-8");
  const lines = content.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.includes("sleep") || line.includes("delay")) {
      foundSleepDelay.push(`${absPath}:${i + 1}:${line.trim()}`);
    }
  }
}
if (foundSleepDelay.length > 0) {
  console.log("ℹ️ Found sleep/delay patterns (verify context - retry helpers are OK):");
  foundSleepDelay.slice(0, 5).forEach((entry) => console.log(`  ${entry}`));
  if (foundSleepDelay.length > 5) {
    console.log(`  ... and ${foundSleepDelay.length - 5} more`);
  }
}

if (exitCode === 0) {
  console.log("✅ No E2E flakiness patterns detected");
} else {
  console.log("\n💡 Common fixes:");
  console.log("  - Replace waitForTimeout() with waitForSelector() or waitForLoadState()");
  console.log("  - Increase short timeouts to at least 5000ms for CI environments");
}

process.exit(exitCode);
