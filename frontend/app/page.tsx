import type { Metadata } from "next";

import { PublicHomeCta } from "@/components/public/public-home-cta";
import { PublicHomeEntries } from "@/components/public/public-home-entries";
import { PublicHomeHero } from "@/components/public/public-home-hero";
import { PublicHomePrinciples } from "@/components/public/public-home-principles";
import { PublicHomeStandards } from "@/components/public/public-home-standards";
import { PublicLandingShell } from "@/components/public/public-landing-shell";
import { createPublicMetadata } from "@/lib/seo/metadata";

export const metadata: Metadata = createPublicMetadata({
  title: "AI Lab Portal",
  description:
    "Human-reviewed AI engineering notes, client-ready showcases, and a calm publishing surface for the AI Lab.",
  path: "/",
});

export default function PublicHomePage() {
  return (
    <PublicLandingShell>
      <PublicHomeHero />
      <PublicHomePrinciples />
      <PublicHomeEntries />
      <PublicHomeStandards />
      <PublicHomeCta />
    </PublicLandingShell>
  );
}
