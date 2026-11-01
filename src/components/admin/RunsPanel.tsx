import { useCallback, useEffect, useState } from "react";
import { collectorStatus, listRuns, listSources, validateSource, type CollectorStatusView, type RunReport } from "@/lib/admin-api";
import { Button } from "@/components/ui/button";

export function RunsPanel({ token, active }: { token: string; active: boolean }) {
  const [runs, setRuns] = useState<RunReport[]>([]);
  const [status, setStatus] = useState<CollectorStatusView | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const load = useCallback(async () => {
    try {
      const [runData, statusData] = await Promise.all([listRuns(token), collectorStatus(token)]);
      setRuns(runData.items); setStatus(statusData); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudieron cargar las ejecuciones"); }
  }, [token]);
  useEffect(() => {
    if (!active) return;
    const initial = window.setTimeout(() => void load(), 0);
    const timer = window.setInterval(() => void load(), 15000);
    return () => { window.clearTimeout(initial); window.clearInterval(timer); };
  }, [load, active]);
  async function validate(run: RunReport) {
    setBusy(run.run_id); setError("");
    try {
      const sources = await listSources(token);
      const source = sources.find((item) => item.id === run.source_id);
      if (!source) throw new Error("La fuente asociada ya no existe.");
      await validateSource(source.id, run.run_id, source.revision, token);
      await load();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo validar la fuente"); }
    finally { setBusy(""); }
  }
  return <section>
    <h2 className="font-display text-xl font-bold">Ejecuciones</h2>
    <p className="mt-2 text-sm">Recolector: {status ? status.stale ? "sin contacto reciente" : "activo" : "estado desconocido"} · Pendientes: {status?.queue_size ?? "—"}</p>
    {error ? <p role="alert" className="mt-3 rounded bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
    {runs.length === 0 ? <p className="mt-4 text-sm text-muted-foreground">No hay ejecuciones registradas.</p> :
      <ul className="mt-4 space-y-2">{runs.map((run) => <li key={run.run_id} className="flex flex-wrap items-center justify-between gap-3 rounded border border-border p-3 text-sm">
        <div className="min-w-0"><p className="font-medium">{run.run_id} · fuente {run.source_id} · {run.status}{run.error_code ? ` · ${run.error_code}` : ""}</p>
          <p className="mt-1 text-muted-foreground">Descubiertos {run.counts?.discovered ?? 0} · Descargados {run.counts?.downloaded ?? 0} · Entregados {run.counts?.delivered ?? 0} · Publicados {run.counts?.published ?? 0} · Pendientes {run.counts?.pending ?? 0}</p>
        </div>
        {run.trigger === "preview" && run.status === "success" ? <Button size="sm" variant="outline" disabled={busy !== ""} onClick={() => void validate(run)}>{busy === run.run_id ? "Validando…" : "Validar fuente"}</Button> : null}
      </li>)}</ul>}
    <p className="mt-3 text-xs text-muted-foreground">El estado se actualiza automáticamente cada 15 segundos.</p>
  </section>;
}
