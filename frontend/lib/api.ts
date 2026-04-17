// frontend/lib/api.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Story {
  id: string;
  headline: string;
  summary: string;
  bullets: string[];
  source_links: string[];
  media: string[];
  category: string;
  source: string;
  verified_by: string[];
  confidence: number;
  social_mentions: number;
  social_platforms: string[];
  timestamp: string;
}

export interface PaginatedStories {
  stories: Story[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface Stats {
  total_stories: number;
  by_category: Record<string, number>;
  latest_update: string | null;
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${path}`);
  return res.json();
}

export async function getStories(
  page = 1,
  size = 20,
  category?: string
): Promise<PaginatedStories> {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  if (category) params.set("category", category);
  return apiFetch<PaginatedStories>(`/api/stories?${params}`);
}

export async function getStory(id: string): Promise<Story> {
  return apiFetch<Story>(`/api/stories/${id}`);
}

export async function searchStories(
  q: string,
  page = 1
): Promise<{ query: string; stories: Story[]; total: number; page: number }> {
  const params = new URLSearchParams({ q, page: String(page) });
  return apiFetch(`/api/search?${params}`);
}

export async function getStats(): Promise<Stats> {
  return apiFetch<Stats>("/api/stats");
}

export async function getByCategory(
  category: string,
  limit = 20
): Promise<{ category: string; stories: Story[]; count: number }> {
  return apiFetch(`/api/stories/category/${category}?limit=${limit}`);
}

export async function subscribe(email: string, name?: string) {
  const res = await fetch(`${API_URL}/api/subscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, name }),
  });
  return res.json();
}

// Helper: relative time
export function relativeTime(ts: string): string {
  const date = new Date(ts.replace(" ", "T") + ":00Z");
  const diff = Date.now() - date.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return "Just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)  return `${hrs} hours ago`;
  return `${Math.floor(hrs / 24)} days ago`;
}
