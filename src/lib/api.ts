// API client tipado para el backend FastAPI de UniNews

// En producción configura PUBLIC_API_URL en el dashboard de Vercel
export const API_BASE = import.meta.env.PUBLIC_API_URL ?? "http://localhost:8000";

export interface News {
  id: number;
  title: string;
  summary: string | null;
  content: string;
  category: string;
  university: string;
  author: string | null;
  image_url: string | null;
  source_url: string | null;
  is_featured: boolean;
  published_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface NewsCreate {
  title: string;
  summary?: string;
  content: string;
  category: string;
  university: string;
  author?: string;
  image_url?: string;
  source_url?: string;
  is_featured: boolean;
  published_at?: string;
}

export interface StatsResponse {
  total_news: number;
  categories: Record<string, number>;
  universities: string[];
  featured_count: number;
}

export interface ChatResponse {
  answer: string;
  sources: Array<{
    news_id: number;
    title: string;
    category: string;
    university: string;
    source_url?: string | null;
  }>;
}

export interface ScrapeUplaResponse {
  requested: number;
  found: number;
  created: number;
  skipped: number;
  failed: number;
  model: string;
  items: Array<{
    title: string;
    source_url: string;
    status: "created" | "skipped" | "failed";
    news_id: number | null;
    error: string | null;
  }>;
}

// ─── News endpoints ───────────────────────────────────────────

export async function fetchNews(params?: {
  skip?: number;
  limit?: number;
  category?: string;
  search?: string;
  featured?: boolean;
}): Promise<News[]> {
  const url = new URL(`${API_BASE}/api/news/`);
  if (params?.skip !== undefined) url.searchParams.set("skip", String(params.skip));
  if (params?.limit !== undefined) url.searchParams.set("limit", String(params.limit));
  if (params?.category) url.searchParams.set("category", params.category);
  if (params?.search) url.searchParams.set("search", params.search);
  if (params?.featured !== undefined) url.searchParams.set("featured", String(params.featured));

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Failed to fetch news: ${res.status}`);
  return res.json();
}

export async function fetchNewsById(id: number): Promise<News> {
  const res = await fetch(`${API_BASE}/api/news/${id}`);
  if (!res.ok) throw new Error(`News ${id} not found`);
  return res.json();
}

export async function fetchStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_BASE}/api/news/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function createNews(data: NewsCreate): Promise<News> {
  const res = await fetch(`${API_BASE}/api/news/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Create failed: ${res.status}`);
  }
  return res.json();
}

export async function updateNews(id: number, data: Partial<NewsCreate>): Promise<News> {
  const res = await fetch(`${API_BASE}/api/news/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Update failed: ${res.status}`);
  }
  return res.json();
}

export async function deleteNews(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/news/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
}

// ─── Scraping endpoint ────────────────────────────────────────

export async function scrapeUplaNews(limit: number): Promise<ScrapeUplaResponse> {
  const res = await fetch(`${API_BASE}/api/scrape/upla`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ limit }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Scraping failed: ${res.status}`);
  }
  return res.json();
}

// ─── Chat endpoint ────────────────────────────────────────────

export async function sendChatMessage(question: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}

export async function fetchRagStatus(): Promise<{ status: string; indexed_documents: number; model?: string }> {
  const res = await fetch(`${API_BASE}/api/chat/status`);
  if (!res.ok) throw new Error("RAG status check failed");
  return res.json();
}
