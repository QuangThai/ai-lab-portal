/** Decorative page atmosphere (grid, glow, grain). Always aria-hidden. */
export function PublicAtmosphere() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_90%_55%_at_15%_-5%,color-mix(in_srgb,var(--brand)_16%,transparent),transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_45%_at_95%_15%,color-mix(in_srgb,var(--brand)_10%,transparent),transparent_45%)]" />
      <div className="absolute inset-0 opacity-[0.4] bg-[linear-gradient(color-mix(in_srgb,var(--border)_70%,transparent)_1px,transparent_1px),linear-gradient(90deg,color-mix(in_srgb,var(--border)_70%,transparent)_1px,transparent_1px)] bg-size-[56px_56px] mask-[linear-gradient(to_bottom,black_0%,black_45%,transparent_92%)]" />
      <div
        className="absolute inset-0 opacity-[0.045] mix-blend-multiply"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        }}
      />
    </div>
  );
}
