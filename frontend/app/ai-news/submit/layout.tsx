import type { Metadata } from "next";

import { createPublicMetadata } from "@/lib/seo/metadata";

export const metadata: Metadata = createPublicMetadata({
  title: "Submit AI News | AI Lab Portal",
  description: "Suggest an AI-related link for human review before it appears on the public feed.",
  path: "/ai-news/submit",
});

export default function AiNewsSubmitLayout({ children }: { children: React.ReactNode }) {
  return children;
}
