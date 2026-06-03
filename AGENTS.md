# Agent Instructions

Add project-specific agent instructions here.

<!-- HARNESS:BEGIN -->
## Harness

This repo uses Harness. Before work, read:

- `README.md`
- `docs/HARNESS.md`
- `docs/FEATURE_INTAKE.md`
- `docs/ARCHITECTURE.md`
- `docs/CONTEXT_RULES.md`
- `scripts/bin/harness-cli query matrix` on macOS/Linux, or `.\scripts\bin\harness-cli.exe query matrix` on Windows

Use the Rust Harness CLI at `scripts/bin/harness-cli` on macOS/Linux or
`scripts/bin/harness-cli.exe` on Windows as the main operational tool.

After work, record a trace with `scripts/bin/harness-cli trace`. For
`harness_friction`, name only **new** pain. If the issue is already in
`scripts/bin/harness-cli query backlog`, reference that backlog id in `notes`
and use `harness_friction: none` unless something changed. See
`docs/TRACE_SPEC.md` (recurring friction deduplication).
<!-- HARNESS:END -->
