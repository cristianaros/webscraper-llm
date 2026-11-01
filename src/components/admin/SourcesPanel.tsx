import { useCallback, useEffect, useState } from "react";
import {
  createSource,
  createUniversity,
  listSources,
  listUniversities,
  patchSource,
  requestRun,
  type SourceConfig,
  type University,
} from "@/lib/admin-api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function SourcesPanel({ token }: { token: string }) {
  const [sources, setSources] = useState<SourceConfig[]>([]);
  const [universities, setUniversities] = useState<University[]>([]);
  const [open, setOpen] = useState(false);
  const [openUni, setOpenUni] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const refresh = useCallback(async () => {
    const [rows, unis] = await Promise.all([
      listSources(token),
      listUniversities(token),
    ]);
    setSources(rows);
    setUniversities(unis);
  }, [token]);

  useEffect(() => {
    const timer = window.setTimeout(() => void refresh(), 0);
    return () => window.clearTimeout(timer);
  }, [refresh]);

  return (
    <section>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-xl font-bold">Fuentes Universitarias</h2>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setOpenUni(!openUni)}>
            {openUni ? "Cancelar" : "+ Nueva Universidad"}
          </Button>
          <Button onClick={() => setOpen(!open)}>
            {open ? "Cerrar" : "+ Agregar Fuente"}
          </Button>
        </div>
      </div>

      {msg ? <p className="mb-4 rounded bg-primary/10 p-2 text-sm text-primary">{msg}</p> : null}

      {openUni ? (
        <UniForm
          token={token}
          onSaved={() => {
            setOpenUni(false);
            void refresh();
          }}
        />
      ) : null}

      {open ? (
        <SourceForm
          token={token}
          universities={universities}
          onSaved={() => {
            setOpen(false);
            void refresh();
          }}
        />
      ) : null}

      <div className="space-y-3">
        {sources.length === 0 ? (
          <p className="rounded border border-dashed border-border p-6 text-center text-muted-foreground">
            No hay fuentes registradas aún. Haz clic en <strong>+ Nueva Universidad</strong> y luego <strong>+ Agregar Fuente</strong> para comenzar.
          </p>
        ) : null}
        {sources.map((source) => (
          <article key={source.id} className="rounded border border-border p-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-semibold text-lg">{source.university_name}</p>
                <p className="text-sm text-muted-foreground">{source.start_url}</p>
                <span className="mt-1 inline-block text-xs text-muted-foreground">
                  Revisión: {source.revision} · Intervalo: {source.interval_minutes} min
                </span>
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  <span className="rounded-full bg-muted px-2 py-1">{source.enabled ? "Activa" : "Inactiva"}</span>
                  <span className="rounded-full bg-muted px-2 py-1">{source.auto_publish ? "Auto-publicación" : "Revisión editorial"}</span>
                  <span className="rounded-full bg-muted px-2 py-1">{source.validated_revision === source.revision ? `Validada rev. ${source.revision}` : "Sin validar"}</span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" disabled={busy || ( !source.enabled && source.validated_revision !== source.revision)} onClick={async () => {
                  setBusy(true); setMsg("");
                  try {
                    await patchSource(source.id, { ...source, enabled: !source.enabled, expected_revision: source.revision }, token);
                    await refresh();
                    setMsg(source.enabled ? "Fuente pausada." : "Fuente activada.");
                  } catch (err) { setMsg(err instanceof Error ? err.message : "No se pudo cambiar el estado"); }
                  finally { setBusy(false); }
                }}>{source.enabled ? "Pausar" : "Activar"}</Button>
                <Button size="sm" variant="outline" disabled={busy} onClick={async () => {
                  setBusy(true); setMsg("");
                  try {
                    await patchSource(source.id, { ...source, auto_publish: !source.auto_publish, expected_revision: source.revision }, token);
                    await refresh();
                  } catch (err) { setMsg(err instanceof Error ? err.message : "No se pudo cambiar la auto-publicación"); }
                  finally { setBusy(false); }
                }}>{source.auto_publish ? "Desactivar auto-publicación" : "Activar auto-publicación"}</Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={async () => {
                    setBusy(true);
                    setMsg("");
                    try {
                      await requestRun(source.id, "preview", token);
                      setMsg(`Vista previa solicitada para ${source.university_name}. Ve a la pestaña Ejecuciones.`);
                    } catch (err) {
                      setMsg(err instanceof Error ? err.message : "Error al solicitar prueba");
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Probar extracción (Preview)
                </Button>
                <Button
                  size="sm"
                  variant="default"
                  disabled={busy}
                  onClick={async () => {
                    setBusy(true);
                    setMsg("");
                    try {
                      await requestRun(source.id, "manual", token);
                      setMsg(`Ejecución encolada para ${source.university_name}. El recolector la procesará.`);
                    } catch (err) {
                      setMsg(err instanceof Error ? err.message : "Error al solicitar ejecución");
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Ejecutar ahora
                </Button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function UniForm({ token, onSaved }: { token: string; onSaved: () => void }) {
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  return (
    <form
      className="mb-5 grid gap-3 rounded border border-border bg-card p-4"
      onSubmit={async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        try {
          await createUniversity(name.trim(), token);
          setName("");
          onSaved();
        } catch (err) {
          setError(err instanceof Error ? err.message : "No se pudo registrar la universidad");
        } finally {
          setSaving(false);
        }
      }}
    >
      <h3 className="font-semibold text-sm">Registrar Nombre Institucional</h3>
      <label className="text-sm">
        Nombre de la Universidad
        <Input
          placeholder="ej. Universidad de Playa Ancha"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </label>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <Button type="submit" disabled={saving}>
        {saving ? "Guardando..." : "Guardar Universidad"}
      </Button>
    </form>
  );
}

function SourceForm({
  token,
  universities,
  onSaved,
}: {
  token: string;
  universities: University[];
  onSaved: () => void;
}) {
  const [university, setUniversity] = useState(String(universities[0]?.id ?? ""));
  const [startUrl, setStartUrl] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  return (
    <form
      className="mb-5 grid gap-3 rounded border border-border bg-card p-4"
      onSubmit={async (event) => {
        event.preventDefault();
        setSaving(true);
        setError("");
        try {
          const parsed = new URL(startUrl);
          const host = parsed.hostname;
          await createSource(
            {
              university_id: Number(university),
              start_url: startUrl.trim(),
              allowed_hosts: [host],
              allowed_image_hosts: [host],
              interval_minutes: 360,
              link_selector: "article a[href]",
              title_selector: "h1",
              date_selector: "time",
              render_mode: "http",
              enabled: false,
              auto_publish: false,
            },
            token
          );
          onSaved();
        } catch (cause) {
          setError(cause instanceof Error ? cause.message : "No se pudo guardar la fuente");
        } finally {
          setSaving(false);
        }
      }}
    >
      <h3 className="font-semibold text-sm">Nueva Fuente de Noticias</h3>
      {universities.length === 0 ? (
        <p className="text-sm text-amber-500">
          Primero debes registrar una universidad con el botón "+ Nueva Universidad" de arriba.
        </p>
      ) : (
        <label className="text-sm">
          Universidad asignada
          <select
            aria-label="Universidad"
            value={university}
            onChange={(e) => setUniversity(e.target.value)}
            className="mt-1 block w-full rounded border border-input bg-background p-2 text-sm"
          >
            {universities.map((row) => (
              <option key={row.id} value={row.id}>
                {row.name}
              </option>
            ))}
          </select>
        </label>
      )}

      <label className="text-sm">
        Enlace de noticias o portada
        <Input
          placeholder="https://www.upla.cl/noticias/ o https://uchile.cl/noticias"
          value={startUrl}
          onChange={(event) => setStartUrl(event.target.value)}
          required
        />
      </label>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <Button type="submit" disabled={saving || universities.length === 0}>
        {saving ? "Guardando..." : "Guardar fuente"}
      </Button>
      <p className="text-xs text-muted-foreground">
        La fuente se guarda inicialmente inactiva. Podrás solicitar una prueba de extracción (Preview) para verificar los campos antes de activarla.
      </p>
    </form>
  );
}
