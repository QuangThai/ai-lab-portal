#!/usr/bin/env node
// Auto-detect port for Next.js dev server (cross-platform).
// Sets BETTER_AUTH_URL dynamically so Better Auth works regardless of port.
// Falls back: 3000 -> 3001 -> 3002 -> 3003 (up to 4 tries)
//
// Usage: node scripts/dev.cjs

const { spawn } = require("child_process");
const net = require("net");
const path = require("path");

const START_PORT = 3000;
const MAX_TRIES = 4;

function isPortInUse(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once("error", () => resolve(true));
    server.once("listening", () => {
      server.close();
      resolve(false);
    });
    server.listen(port);
  });
}

async function findFreePort() {
  for (let i = 0; i < MAX_TRIES; i++) {
    const candidate = START_PORT + i;
    const inUse = await isPortInUse(candidate);
    if (!inUse) return candidate;
    console.log(`  Port ${candidate} in use, trying ${candidate + 1}...`);
  }
  console.error(
    `  Ports ${START_PORT}-${START_PORT + MAX_TRIES - 1} all in use. ` +
      `Use E2E_PORT=13100 npm run test:e2e or free a port.`
  );
  process.exit(1);
}

function cleanEnv() {
  // Yarn leaks internal config vars that confuse npx/npm.
  // Strip anything that starts with npm_config_ or npm_lifecycle_
  const cleaned = { ...process.env };
  for (const key of Object.keys(cleaned)) {
    if (
      key.startsWith("npm_config_") ||
      key === "npm_lifecycle_event" ||
      key === "npm_lifecycle_script" ||
      key === "npm_execpath" ||
      key === "npm_node_execpath" ||
      key === "npm_package_json" ||
      key === "npm_package_name" ||
      key === "yarn_" ||
      key === "init_module"
    ) {
      delete cleaned[key];
    }
  }
  return cleaned;
}

async function main() {
  // Check if --port was passed (e.g., from Playwright: npm run dev -- --port 13100)
  const portArgIndex = process.argv.indexOf("--port");
  const explicitPort = portArgIndex > -1 ? parseInt(process.argv[portArgIndex + 1], 10) : NaN;
  const port = Number.isFinite(explicitPort) ? explicitPort : await findFreePort();
  const baseUrl = `http://localhost:${port}`;
  const frontendDir = path.resolve(__dirname, "..", "frontend");
  const isWin = process.platform === "win32";

  console.log(`\n  -> Starting Next.js on port ${port}`);
  console.log(`  -> BETTER_AUTH_URL=${baseUrl}\n`);

  // Build command line properly to avoid DEP0190 warning
  const args = [
    "next", "dev",
    "--port", String(port),
    "--hostname", "127.0.0.1",
  ];

  const env = {
    ...cleanEnv(),
    BETTER_AUTH_URL: baseUrl,
  };

  let child;
  if (isWin) {
    // Windows: use cmd.exe /c with quoted args to avoid shell:true + args warning
    const cmdLine = `npx ${args.map((a) => (a.includes(" ") ? `"${a}"` : a)).join(" ")}`;
    child = spawn("cmd.exe", ["/c", cmdLine], {
      cwd: frontendDir,
      stdio: "inherit",
      env,
    });
  } else {
    child = spawn("npx", args, {
      cwd: frontendDir,
      stdio: "inherit",
      env,
    });
  }

  child.on("exit", (code) => process.exit(code ?? 0));
}

main().catch((err) => {
  console.error("dev.cjs failed:", err);
  process.exit(1);
});
