import { useCallback, useEffect, useState } from "react";
import { listRevisions, publishRevision, rejectRevision, type ArticleFieldsInput, type RevisionView } from "@/lib/admin-api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

type Draft = { title: string; category: string; published_on: string; summary: string; content: string };
function fields(row: RevisionView): Draft {
  const source = row.fields ?? {};
  const date = typeof source.published_on === "string" ? source.published_on.slice(0, 10) :
    typeof source.published_at === "string" ? source.published_at.slice(0, 10) : "";
  return {
    title: typeof source.title === "string" ? source.title : "",
    category: typeof source.category === "string" ? source.category : "General",
    published_on: date,
    summary: typeof source.summary === "string" ? source.summary : "",
    content: typeof source.content === "string" ? source.content : "",
  };
}

export function ReviewPanel({ token }: { token: string }) {
  const [rows, setRows] = useState<RevisionView[]>([]);
  const [drafts, setDrafts] = useState<Record<number, Draft>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const refresh = useCallback(async () => {
    try {
      const value = await listRevisions(token);
      setRows(value.items);
      setDrafts(Object.fromEntries(value.items.map((row) => [row.id, fields(row)])));
      setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudieron cargar las revisiones"); }
  }, [token]);
  useEffect(() => {
    const timer = window.setTimeout(() => void refresh(), 0);
    return () => window.clearTimeout(timer);
  }, [refresh]);

  function change(id: number, key: keyof Draft, value: string) {
    setDrafts((current) => ({ ...current, [id]: { ...current[id], [key]: value } }));
  }
  async function approve(row: RevisionView) {
    const draft = drafts[row.id];
    if (!draft) return;
    setBusy(row.id); setError("");
    try {
      const originalDate = fields(row).published_on;
      const dateChanged = draft.published_on !== originalDate;
      const originalPublishedAt = typeof row.fields?.published_at === "string" ? row.fields.published_at : null;
      const originalPrecision = row.fields?.date_precision === "instant" || row.fields?.date_precision === "day"
        ? row.fields.date_precision
        : null;
      const article: ArticleFieldsInput = {
        ...draft, summary: draft.summary || null, published_on: draft.published_on || null,
        published_at: !dateChanged && originalPublishedAt ? originalPublishedAt : draft.published_on ? `${draft.published_on}T00:00:00Z` : null,
        date_precision: !dateChanged && originalPublishedAt ? originalPrecision : draft.published_on ? "day" : null,
        original_date_text: typeof row.fields?.original_date_text === "string" ? row.fields.original_date_text : null,
      };
      await publishRevision(row.id, article, token);
      await refresh();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo publicar la revisión"); }
    finally { setBusy(null); }
  }
  async function reject(row: RevisionView) {
    setBusy(row.id); setError("");
    try { await rejectRevision(row.id, "descartada en panel", token); await refresh(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo rechazar la revisión"); }
    finally { setBusy(null); }
  }

  return <section>
    <h2 className="font-display text-xl font-bold">Revisión</h2>
    {error ? <p role="alert" className="mt-3 rounded bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
    {rows.length === 0 ? <p className="mt-3 text-sm text-muted-foreground">No hay revisiones pendientes.</p> :
      <ul className="mt-3 space-y-3">{rows.map((row) => {
        const draft = drafts[row.id] ?? fields(row);
        const doc = row.document && typeof row.document === "object" ? row.document as Record<string, unknown> : {};
        return <li key={row.id} className="space-y-3 rounded-lg border border-border bg-card p-4">
          <div className="flex flex-wrap justify-between gap-2 text-sm"><strong>Revisión {row.id} · fuente {row.source_id}</strong><span className="text-muted-foreground">{typeof doc.url === "string" ? doc.url : "Origen no informado"}</span></div>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="text-sm">Título<Input aria-label={`Título revisión ${row.id}`} value={draft.title} onChange={(e) => change(row.id, "title", e.target.value)} /></label>
            <label className="text-sm">Categoría<Input aria-label={`Categoría revisión ${row.id}`} value={draft.category} onChange={(e) => change(row.id, "category", e.target.value)} /></label>
            <label className="text-sm">Fecha detectada<Input type="date" aria-label={`Fecha revisión ${row.id}`} value={draft.published_on} onChange={(e) => change(row.id, "published_on", e.target.value)} /></label>
            <label className="text-sm">Resumen<Input aria-label={`Resumen revisión ${row.id}`} value={draft.summary} onChange={(e) => change(row.id, "summary", e.target.value)} /></label>
          </div>
          <label className="block text-sm">Contenido candidato<Textarea aria-label={`Contenido revisión ${row.id}`} rows={6} value={draft.content} onChange={(e) => change(row.id, "content", e.target.value)} /></label>
          {row.issues.length ? <div><h3 className="text-sm font-semibold">Observaciones</h3><ul className="mt-1 list-disc pl-5 text-sm text-muted-foreground">{row.issues.map((issue, index) => <li key={`${issue}-${index}`}>{issue}</li>)}</ul></div> : null}
          <div className="flex flex-wrap gap-2"><Button disabled={busy !== null} onClick={() => void approve(row)}>{busy === row.id ? "Procesando…" : "Aprobar y publicar"}</Button><Button variant="outline" disabled={busy !== null} onClick={() => void reject(row)}>Rechazar</Button></div>
        </li>;
      })}</ul>}
  </section>;
}
