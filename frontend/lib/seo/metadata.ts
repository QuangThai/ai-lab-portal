import type { Metadata } from "next";

const siteName = "AI Lab Portal";

export function createPublicMetadata({
  title,
  description,
  path,
}: {
  title: string;
  description: string;
  path: string;
}): Metadata {
  const canonicalPath = path.startsWith("/") ? path : `/${path}`;

  return {
    title,
    description,
    alternates: {
      canonical: canonicalPath,
    },
    openGraph: {
      title,
      description,
      siteName,
      type: "website",
      url: canonicalPath,
    },
  };
}
