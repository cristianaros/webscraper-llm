"use client";

import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import {
  fetchNews, fetchStats, createNews, updateNews, deleteNews,
  type News, type NewsCreate, type StatsResponse,
} from "@/lib/api";
import {
  PlusIcon, EditIcon, TrashIcon, SearchIcon, RefreshIcon,
  LayoutDashboardIcon, ListIcon, NewspaperIcon, StarIcon,
  BuildingIcon, TagIcon, DatabaseIcon, CalendarIcon,
} from "@/lib/icons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";

const CATEGORIES = ["Becas", "Investigación", "Infraestructura", "Cultura", "Logros", "Empleo", "Bienestar", "Tecnología", "General"];
const UNIVERSITIES = ["Universidad Central", "Universidad Politécnica", "Universidad de las Artes", "Otra"];

const DEFAULT_FORM: NewsCreate = {
  title: "",
  summary: "",
  content: "",
  category: "General",
  university: "",
  author: "",
  image_url: "",
  source_url: "",
  is_featured: false,
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" });
}

// ─── Stat Card ────────────────────────────────────────────────

function StatCard({ label, value, icon: Icon, accent = false }: {
  label: string; value: number | string; icon: React.ComponentType<{ className?: string }>; accent?: boolean;
}) {
  return (
    <div className={cn(
      "flex items-center gap-4 rounded-xl border border-border bg-card p-5",
      accent && "border-primary/30 bg-primary/5"
    )}>
      <div className={cn("flex size-11 items-center justify-center rounded-lg", accent ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground")}>
        <Icon className="size-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-foreground tabular-nums">{value}</p>
        <p className="text-xs uppercase tracking-wider text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}

// ─── News Form ────────────────────────────────────────────────

function NewsForm({
  initial, onSave, onCancel, loading: saving,
}: {
  initial?: Partial<NewsCreate>;
  onSave: (data: NewsCreate) => void;
  onCancel: () => void;
  loading?: boolean;
}) {
  const [form, setForm] = useState<NewsCreate>({ ...DEFAULT_FORM, ...initial });

  function set<K extends keyof NewsCreate>(key: K, value: NewsCreate[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title.trim()) { toast.error("El título es requerido."); return; }
    if (!form.content.trim()) { toast.error("El contenido es requerido."); return; }
    if (!form.university.trim()) { toast.error("La universidad es requerida."); return; }
    onSave(form);
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      {/* Título */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-foreground">Título *</label>
        <Input
          value={form.title}
          onChange={(e) => set("title", e.target.value)}
          placeholder="Título de la noticia..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Categoría */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-foreground">Categoría *</label>
          <Select value={form.category} onValueChange={(v) => set("category", v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CATEGORIES.map((c) => (
                <SelectItem key={c} value={c}>{c}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Universidad */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-foreground">Universidad *</label>
          <Input
            value={form.university}
            onChange={(e) => set("university", e.target.value)}
            placeholder="Nombre de la universidad"
            list="universities-list"
          />
          <datalist id="universities-list">
            {UNIVERSITIES.map((u) => <option key={u} value={u} />)}
          </datalist>
        </div>
      </div>

      {/* Resumen */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-foreground">Resumen</label>
        <Textarea
          value={form.summary ?? ""}
          onChange={(e) => set("summary", e.target.value)}
          placeholder="Resumen breve de la noticia..."
          className="resize-none"
          rows={2}
        />
      </div>

      {/* Contenido */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-foreground">Contenido *</label>
        <Textarea
          value={form.content}
          onChange={(e) => set("content", e.target.value)}
          placeholder="Escribe el contenido completo de la noticia..."
          className="resize-none"
          rows={5}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-foreground">Autor</label>
          <Input value={form.author ?? ""} onChange={(e) => set("author", e.target.value)} placeholder="Nombre del autor" />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-foreground">URL de imagen</label>
          <Input value={form.image_url ?? ""} onChange={(e) => set("image_url", e.target.value)} placeholder="https://..." />
        </div>
      </div>

      {/* Destacada toggle */}
      <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-border p-3 transition-colors hover:bg-muted/40">
        <div
          role="switch"
          aria-checked={form.is_featured}
          onClick={() => set("is_featured", !form.is_featured)}
          className={cn(
            "relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors",
            form.is_featured ? "bg-[oklch(var(--gold)/1)]" : "bg-muted"
          )}
        >
          <span className={cn(
            "inline-block h-4 w-4 rounded-full bg-white shadow transition-transform",
            form.is_featured ? "translate-x-4" : "translate-x-0"
          )} />
        </div>
        <div>
          <p className="text-sm font-medium text-foreground">Marcar como destacada</p>
          <p className="text-xs text-muted-foreground">Aparecerá con el distintivo dorado</p>
        </div>
      </label>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={saving}>Cancelar</Button>
        <Button type="submit" disabled={saving}>
          {saving ? "Guardando..." : "Guardar noticia"}
        </Button>
      </div>
    </form>
  );
}

// ─── Admin Panel ──────────────────────────────────────────────

export default function AdminPanel() {
  const [news, setNews] = useState<News[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [editNews, setEditNews] = useState<News | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      fetchNews({ limit: 100 }),
      fetchStats(),
    ])
      .then(([n, s]) => { setNews(n); setStats(s); })
      .catch(() => toast.error("Error al cargar datos. Verifica que el backend esté corriendo."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = search
    ? news.filter((n) => n.title.toLowerCase().includes(search.toLowerCase()) || n.university.toLowerCase().includes(search.toLowerCase()))
    : news;

  async function handleSave(data: NewsCreate) {
    setSaving(true);
    try {
      if (editNews) {
        await updateNews(editNews.id, data);
        toast.success("Noticia actualizada correctamente.");
      } else {
        await createNews(data);
        toast.success("Noticia creada y añadida al índice IA.");
      }
      setDialogOpen(false);
      setEditNews(null);
      setIsCreating(false);
      load();
    } catch (err: any) {
      toast.error(err.message || "Error al guardar la noticia.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!deleteId) return;
    try {
      await deleteNews(deleteId);
      toast.success("Noticia eliminada.");
      setDeleteId(null);
      load();
    } catch {
      toast.error("Error al eliminar la noticia.");
    }
  }

  function openEdit(n: News) {
    setEditNews(n);
    setIsCreating(false);
    setDialogOpen(true);
  }

  function openCreate() {
    setEditNews(null);
    setIsCreating(true);
    setDialogOpen(true);
  }

  return (
    <div className="mx-auto max-w-screen-xl px-6 py-8">
      {/* Page header */}
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-normal text-foreground">Panel de Administración</h1>
          <p className="mt-1 text-sm text-muted-foreground">Gestiona el contenido del portal de noticias universitarias.</p>
        </div>
        <Button onClick={openCreate}>
          <PlusIcon data-icon="inline-start" className="size-4" />
          Nueva noticia
        </Button>
      </div>

      <Tabs defaultValue="dashboard">
        <TabsList className="mb-6">
          <TabsTrigger value="dashboard">
            <LayoutDashboardIcon data-icon="inline-start" className="size-4" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="news">
            <ListIcon data-icon="inline-start" className="size-4" />
            Noticias ({news.length})
          </TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard">
          {loading || !stats ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {Array(4).fill(null).map((_, i) => (
                <Skeleton key={i} className="h-24 rounded-xl" />
              ))}
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Total noticias" value={stats.total_news} icon={NewspaperIcon} accent />
              <StatCard label="Categorías" value={Object.keys(stats.categories).length} icon={TagIcon} />
              <StatCard label="Universidades" value={stats.universities.length} icon={BuildingIcon} />
              <StatCard label="Destacadas" value={stats.featured_count} icon={StarIcon} />
            </div>
          )}

          {stats && (
            <div className="mt-8 grid gap-6 sm:grid-cols-2">
              {/* Categories breakdown */}
              <div className="rounded-xl border border-border bg-card p-5">
                <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                  <TagIcon className="size-4" />
                  Por categoría
                </h3>
                <div className="flex flex-col gap-2">
                  {Object.entries(stats.categories)
                    .sort(([, a], [, b]) => b - a)
                    .map(([cat, count]) => (
                      <div key={cat} className="flex items-center gap-3">
                        <span className="min-w-[120px] text-sm text-foreground truncate">{cat}</span>
                        <div className="flex-1 overflow-hidden rounded-full bg-muted h-1.5">
                          <div
                            className="h-full rounded-full bg-primary transition-all"
                            style={{ width: `${(count / stats.total_news) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-muted-foreground tabular-nums w-6 text-right">{count}</span>
                      </div>
                    ))}
                </div>
              </div>

              {/* Universities */}
              <div className="rounded-xl border border-border bg-card p-5">
                <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                  <BuildingIcon className="size-4" />
                  Universidades
                </h3>
                <div className="flex flex-col gap-1.5">
                  {stats.universities.map((u) => (
                    <div key={u} className="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted/40 transition-colors">
                      <div className="size-2 rounded-full bg-primary flex-shrink-0" />
                      <span className="text-sm text-foreground">{u}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </TabsContent>

        {/* News Table Tab */}
        <TabsContent value="news">
          <div className="mb-4 flex items-center gap-3">
            <div className="relative flex-1 max-w-sm">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
              <Input
                placeholder="Buscar en noticias..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Button variant="outline" size="icon" onClick={load} title="Actualizar">
              <RefreshIcon className="size-4" />
            </Button>
          </div>

          {loading ? (
            <div className="flex flex-col gap-2">
              {Array(5).fill(null).map((_, i) => <Skeleton key={i} className="h-14 rounded-lg" />)}
            </div>
          ) : (
            <div className="rounded-xl border border-border overflow-hidden">
              <ScrollArea className="max-h-[60vh]">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/40">
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Título</th>
                      <th className="hidden px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground sm:table-cell">Categoría</th>
                      <th className="hidden px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground md:table-cell">Universidad</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Fecha</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filtered.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-12 text-center text-sm text-muted-foreground">
                          {search ? "No se encontraron noticias." : "No hay noticias aún."}
                        </td>
                      </tr>
                    ) : (
                      filtered.map((n) => (
                        <tr key={n.id} className="group transition-colors hover:bg-muted/30">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              {n.is_featured && <StarIcon className="size-3 text-[oklch(var(--gold)/1)] flex-shrink-0" />}
                              <span className="font-medium text-foreground line-clamp-1 max-w-[200px] lg:max-w-[320px]">{n.title}</span>
                            </div>
                          </td>
                          <td className="hidden px-4 py-3 sm:table-cell">
                            <span className="inline-flex rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">{n.category}</span>
                          </td>
                          <td className="hidden px-4 py-3 text-muted-foreground md:table-cell truncate max-w-[160px]">{n.university}</td>
                          <td className="px-4 py-3 text-muted-foreground text-xs whitespace-nowrap">
                            {formatDate(n.created_at)}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center justify-end gap-1">
                              <Button variant="ghost" size="icon" className="size-8 opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => openEdit(n)} title="Editar">
                                <EditIcon className="size-3.5" />
                              </Button>
                              <Button variant="ghost" size="icon" className="size-8 opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive" onClick={() => setDeleteId(n.id)} title="Eliminar">
                                <TrashIcon className="size-3.5" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </ScrollArea>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(o) => { if (!o) { setDialogOpen(false); setEditNews(null); } }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden p-0">
          <DialogHeader className="px-6 pt-6 pb-4 border-b border-border">
            <DialogTitle className="font-display text-xl font-normal">
              {editNews ? "Editar noticia" : "Nueva noticia"}
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[70vh]">
            <div className="p-6">
              <NewsForm
                initial={editNews ? {
                  title: editNews.title,
                  summary: editNews.summary ?? "",
                  content: editNews.content,
                  category: editNews.category,
                  university: editNews.university,
                  author: editNews.author ?? "",
                  image_url: editNews.image_url ?? "",
                  source_url: editNews.source_url ?? "",
                  is_featured: editNews.is_featured,
                } : undefined}
                onSave={handleSave}
                onCancel={() => { setDialogOpen(false); setEditNews(null); }}
                loading={saving}
              />
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteId !== null} onOpenChange={(o) => !o && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar noticia</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción no se puede deshacer. La noticia será eliminada permanentemente y removida del índice de IA.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
