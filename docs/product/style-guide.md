# AI Lab Portal Style Guide

Source: `styles/` Medium-inspired style reference.

## Design Read

AI Lab Portal should use a light editorial foundation: warm vellum canvas,
ink-black typography, minimal chrome, pill-shaped actions, and a restrained
single green accent. This supports public credibility and publishing workflows
without making the foundation shell look like a generic dark AI dashboard.

## Core Tokens

- Page background: `#f7f4ed` / `--color-vellum-background`
- Secondary surface: `#ffffff` / `--color-parchment-white`
- Primary text and button fill: `#191919` / `--color-charcoal-black`
- Body text: `#242424` / `--color-inkwell-black`
- Borders and general text accents: `#333333` / `--color-book-text-gray`
- Muted text: `#6b6b6b` / `--color-muted-text-gray`
- Reserved accent: `#50b33a` / `--color-story-green`

## Typography

- Display/editorial headlines: `--font-gt-super` with serif fallback.
- Body, navigation, and UI labels: `--font-sohne` with system sans fallback.
- Reading/body content can use `--font-medium-content-sans-serif-font`.
- Use regular weight first; avoid heavy font weight as the default visual crutch.

## Spacing and Shape

- Base spacing unit: `8px`.
- Common gaps: `16px`, `24px`, `48px`, `64px`.
- Section gap: `64px`.
- Buttons should use pill radii (`--radius-buttons`, `--radius-pillbuttons`).

## Do

- Keep the interface light, flat, and content-forward.
- Use warm off-white as the default app canvas.
- Use black/ink text for primary hierarchy.
- Reserve green for rare brand accents or illustrative emphasis.
- Prefer simple borders and whitespace over shadows and glass effects.

## Don't

- Do not introduce purple AI gradients or generic dark mesh backgrounds.
- Do not add heavy shadows, glossy cards, or dense dashboards for public shells.
- Do not use many accent colors.
- Do not implement real admin/domain behavior until its story exists.

## Implementation

Runtime tokens live in `frontend/app/theme.css` and are imported by
`frontend/app/globals.css`. Tailwind v4 theme variables are declared there so
future components can use token-backed utility names.
