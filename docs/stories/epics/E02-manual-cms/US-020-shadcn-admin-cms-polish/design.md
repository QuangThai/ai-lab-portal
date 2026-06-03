# Design

## Theme

Map AI Lab editorial tokens (`docs/product/style-guide.md`, `frontend/app/theme.css`) to shadcn CSS variables in `frontend/app/globals.css`:

- vellum background → `--background`
- parchment cards → `--card`
- charcoal primary actions → `--primary`
- story green accent → `--brand`, `--ring`, success badges

## Components

Install and use:

- `cn` via `frontend/lib/utils.ts`
- shadcn: `button`, `input`, `textarea`, `label`, `badge`, `card`, `separator`, `alert`
- shared admin helpers in `frontend/components/admin/admin-ui.ts`

## Surfaces

- `/admin/login` — Card + Input + brand pill submit
- `/admin` — `AdminCmsShell` dashboard with section cards
- `/admin/blog`, editor routes — existing shell/header/list/editor on shadcn primitives

Preserve E2E selectors: `Open editor` link, `New draft`, `role=status`, publish/unpublish button labels.
