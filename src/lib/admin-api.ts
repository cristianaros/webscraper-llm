import { API_BASE, type News, type NewsCreate } from "./api";

export type University = { id: number; name: string };
export type SourceInput = {
  university_id: number; start_url: string; allowed_hosts: string[]; allowed_image_hosts: string[];
  interval_minutes: number; link_selector: string; title_selector: string; date_selector: string;
  render_mode: "http" | "browser"; enabled: boolean; auto_publish: boolean;
};
export type SourceConfig = SourceInput & { id: number; university_name: string; revision: number; validated_revision: number | null };
export type RunReport = {
  run_id: string; source_id: number; status: string; trigger?: string;
  counts?: Partial<Record<"discovered" | "downloaded" | "delivered" | "published" | "pending", number>>;
  error_code?: string | null;
};
export type RevisionView = {
  id: number; news_id: number | null; source_id: number; document: unknown;
  fields: Record<string, unknown> | null; issues: string[]; review_status: string;
};
export type CollectorStatusView = { stale: boolean; last_seen_at?: string; llm_status?: string; queue_size?: number; oldest_pending_at?: string | null };
export type ArticleFieldsInput = {
  title: string; content: string; category: string; summary: string | null;
  published_at: string | null; published_on: string | null;
  date_precision: "day" | "instant" | null; original_date_text: string | null;
};

function url(path: string) { return API_BASE ? `${API_BASE}${path}` : path; }

export async function adminRequest<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(url(path), {
    ...init,
    headers: { "Content-Type": "application/json", ...init.headers, Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Error de conexión" }));
    throw new Error(typeof error.detail === "string" ? error.detail : "Revisa los datos ingresados");
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}

export const listUniversities = (token: string) => adminRequest<University[]>("/api/admin/universities", token);
export const listSources = (token: string) => adminRequest<SourceConfig[]>("/api/admin/sources", token);
export const createUniversity = (name: string, token: string) => adminRequest<University>("/api/admin/universities", token, { method: "POST", body: JSON.stringify({ name }) });
export const createSource = (input: SourceInput, token: string) => adminRequest<SourceConfig>("/api/admin/sources", token, { method: "POST", body: JSON.stringify(input) });
export const requestRun = (id: number, kind: "manual" | "preview", token: string) => adminRequest<{ run_id: string; status: string }>(`/api/admin/sources/${id}/runs`, token, { method: "POST", body: JSON.stringify({ kind }) });
export const listRuns = (token: string) => adminRequest<{ items: RunReport[]; total: number }>("/api/admin/runs", token);
export const collectorStatus = (token: string) => adminRequest<CollectorStatusView>("/api/admin/collector/status", token);
export const listRevisions = (token: string) => adminRequest<{ items: RevisionView[]; total: number }>("/api/admin/revisions?status=pending", token);

export const createAdminNews = (data: NewsCreate, token: string) => adminRequest<News>("/api/news/", token, { method: "POST", body: JSON.stringify(data) });
export const updateAdminNews = (id: number, data: Partial<NewsCreate>, token: string) => adminRequest<News>(`/api/news/${id}`, token, { method: "PUT", body: JSON.stringify(data) });
export const deleteAdminNews = (id: number, token: string) => adminRequest<void>(`/api/news/${id}`, token, { method: "DELETE" });
export const publishRevision = (id: number, fields: ArticleFieldsInput, token: string, editorialLock = true) =>
  adminRequest<News>(`/api/admin/revisions/${id}/publish`, token, { method: "POST", body: JSON.stringify({ fields, editorial_lock: editorialLock }) });
export const rejectRevision = (id: number, reason: string, token: string) =>
  adminRequest<void>(`/api/admin/revisions/${id}/reject`, token, { method: "POST", body: JSON.stringify({ reason }) });
export const patchSource = (id: number, patch: Partial<SourceInput> & { expected_revision: number }, token: string) =>
  adminRequest<SourceConfig>(`/api/admin/sources/${id}`, token, { method: "PATCH", body: JSON.stringify(patch) });
export const validateSource = (id: number, runId: string, expectedRevision: number, token: string) =>
  adminRequest<SourceConfig>(`/api/admin/sources/${id}/validate`, token, { method: "POST", body: JSON.stringify({ run_id: runId, expected_revision: expectedRevision }) });
