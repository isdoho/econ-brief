import type { MetadataRoute } from "next";
import { SITE_URL, loadBriefings } from "@/lib/briefings";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const { briefings, updated_at } = loadBriefings();
  const lastModified = updated_at ? new Date(updated_at) : undefined;

  return [
    { url: SITE_URL, lastModified, changeFrequency: "daily", priority: 1 },
    { url: `${SITE_URL}/about`, changeFrequency: "monthly", priority: 0.3 },
    ...briefings.map((b) => ({
      url: `${SITE_URL}/b/${b.date}`,
      lastModified: new Date(b.created_at),
      changeFrequency: "monthly" as const,
      priority: 0.7,
    })),
  ];
}
