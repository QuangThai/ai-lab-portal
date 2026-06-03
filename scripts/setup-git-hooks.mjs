#!/usr/bin/env node
/**
 * Point this git worktree at the repo-root Husky hooks in `.husky/`.
 * Safe to run repeatedly; no-op outside a git checkout.
 */
import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");

try {
  execFileSync("git", ["rev-parse", "--git-dir"], { cwd: repoRoot, stdio: "ignore" });
  execFileSync("git", ["config", "core.hooksPath", ".husky"], { cwd: repoRoot, stdio: "inherit" });
} catch {
  // Not a git checkout (e.g. export-only tree); skip quietly.
}
