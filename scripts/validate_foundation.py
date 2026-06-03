from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NPM = shutil.which("npm") or shutil.which("npm.cmd") or "npm"
DOCKER = shutil.which("docker") or shutil.which("docker.exe") or "docker"

COMMANDS: list[tuple[str, list[str], Path]] = [
    ("docker compose config", [DOCKER, "compose", "config", "--quiet"], ROOT),
    ("backend tests", [sys.executable, "-m", "pytest", "backend/tests"], ROOT),
    (
        "alembic offline SQL",
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head", "--sql"],
        ROOT,
    ),
    ("frontend unit tests", [NPM, "run", "test"], ROOT / "frontend"),
    ("frontend typecheck", [NPM, "run", "typecheck"], ROOT / "frontend"),
    ("frontend lint", [NPM, "run", "lint"], ROOT / "frontend"),
    ("frontend build", [NPM, "run", "build"], ROOT / "frontend"),
    ("frontend e2e", [NPM, "run", "test:e2e"], ROOT / "frontend"),
]


def run_step(name: str, command: list[str], cwd: Path) -> None:
    print(f"\n==> {name}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    for name, command, cwd in COMMANDS:
        run_step(name, command, cwd)
    print("\nFoundation validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
