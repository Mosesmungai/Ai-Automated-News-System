import { MetadataRoute } from "next";
import { getStories } from "@/lib/api";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://kenya-news.vercel.app";

const CATEGORIES = ["kenya", "africa", "world", "business", "sports", "technology", "health", "politics"];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const stories = await getStories(1, 100).then((r) => r.stories).catch(() => []);

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: BASE_URL, lastModified: new Date(), changeFrequency: "always", priority: 1 },
    { url: `${BASE_URL}/search`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
    ...CATEGORIES.map((cat) => ({
      url: `${BASE_URL}/category/${cat}`,
      lastModified: new Date(),
      changeFrequency: "always" as const,
      priority: 0.8,
    })),
  ];

  const storyRoutes: MetadataRoute.Sitemap = stories.map((s) => ({
    url: `${BASE_URL}/story/${s.id}`,
    lastModified: new Date(s.timestamp.replace(" ", "T") + "Z"),
    changeFrequency: "weekly" as const,
    priority: 0.7,
  }));

  return [...staticRoutes, ...storyRoutes];
}
