"use client";

import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { fetchNews, fetchStats, type News, type StatsResponse } from "@/lib/api";
import {
  SearchIcon, FilterIcon, SparklesIcon, StarIcon,
  BuildingIcon, CalendarIcon, UserIcon, ExternalLinkIcon, NewspaperIcon,
} from "@/lib/icons";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

// Mapa categoría → color semántico en shadcn
const CATEGORY_COLORS: Record<string, string> = {
  Becas: "bg-primary/10 text-primary border-primary/20",
  Investigación: "bg-teal-500/10 text-teal-400 border-teal-500/20",
  Infraestructura: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  Cultura: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  Logros: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  Empleo: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  Bienestar: "bg-pink-500/10 text-pink-400 border-pink-500/20",
  Tecnología: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  General: "bg-muted text-muted-foreground border-border",
};

const CATEGORIES = ["Academia", "Becas", "Cultura", "Deportes", "Destacados", "En los medios", "Género", "Infraestructura", "Investigación", "Opinión", "Tecnología"];

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" });
}

// ─── News Card ────────────────────────────────────────────────

function NewsCard({ news, onClick, delay }: { news: News; onClick: () => void; delay: number }) {
  const catColor = CATEGORY_COLORS[news.category] ?? CATEGORY_COLORS.General;

  return (
    <article
      className="group animate-fade-up flex flex-col rounded-xl border border-border bg-card overflow-hidden cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5"
      style={{ animationDelay: `${delay}ms` }}
      onClick={onClick}
    >
      {/* Image */}
      <div className="relative overflow-hidden aspect-[16/9] bg-muted flex-shrink-0">
        {news.image_url ? (
          <img
            src={news.image_url}
            alt={news.title}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
          />
        ) : (
          <div className="flex size-full items-center justify-center bg-gradient-to-br from-primary/5 to-primary/20">
            <NewspaperIcon className="size-10 text-primary/30" />
          </div>
        )}
        {news.is_featured && (
          <span className="absolute left-3 top-3 flex items-center gap-1 rounded-full bg-[oklch(var(--gold)/1)] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[oklch(var(--gold-foreground)/1)] shadow">
            <StarIcon className="size-2.5" />
            Destacada
          </span>
        )}
      </div>

      {/* Body */}
      <div className="flex flex-col gap-3 p-4 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide", catColor)}>
            {news.category}
          </span>
          <span className="ml-auto flex items-center gap-1 text-[11px] text-muted-foreground">
            <CalendarIcon className="size-3" />
            {formatDate(news.published_at ?? news.created_at)}
          </span>
        </div>

        <h3 className="font-display text-base font-normal leading-snug text-foreground line-clamp-2 group-hover:text-primary transition-colors">
          {news.title}
        </h3>

        {news.summary && (
          <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">
            {news.summary}
          </p>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center gap-2 border-t border-border/60 px-4 py-2.5">
        <BuildingIcon className="size-3.5 text-muted-foreground flex-shrink-0" />
        <span className="text-xs text-muted-foreground truncate flex-1">{news.university}</span>
        {news.author && (
          <span className="text-[11px] text-muted-foreground/70 flex items-center gap-1 flex-shrink-0">
            <UserIcon className="size-3" />
            {news.author.split(" ").slice(0, 2).join(" ")}
          </span>
        )}
      </div>
    </article>
  );
}

// ─── Stats Bar ────────────────────────────────────────────────

function StatsBar({ stats }: { stats: StatsResponse | null }) {
  const items = stats
    ? [
        { label: "Noticias", value: stats.total_news },
        { label: "Categorías", value: Object.keys(stats.categories).length },
        { label: "Universidades", value: stats.universities.length },
        { label: "Destacadas", value: stats.featured_count },
      ]
    : Array(4).fill(null);

  return (
    <div className="grid grid-cols-2 gap-px border-b border-border bg-border sm:grid-cols-4">
      {items.map((item, i) => (
        <div key={i} className="flex flex-col items-center gap-0.5 bg-muted/30 py-4 px-3">
          {item ? (
            <>
              <span className="text-2xl font-bold text-primary tabular-nums">{item.value}</span>
              <span className="text-[11px] uppercase tracking-wider text-muted-foreground">{item.label}</span>
            </>
          ) : (
            <>
              <Skeleton className="h-7 w-10 rounded" />
              <Skeleton className="h-3 w-16 rounded mt-1" />
            </>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── News Detail Dialog ───────────────────────────────────────

function NewsDialog({ news, open, onClose }: { news: News | null; open: boolean; onClose: () => void }) {
  if (!news) return null;
  const catColor = CATEGORY_COLORS[news.category] ?? CATEGORY_COLORS.General;

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl p-0 overflow-hidden">
        {news.image_url && (
          <div className="relative h-52 overflow-hidden">
            <img src={news.image_url} alt={news.title} className="h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" />
            {news.is_featured && (
              <span className="absolute left-4 bottom-4 flex items-center gap-1 rounded-full bg-[oklch(var(--gold)/1)] px-3 py-1 text-xs font-bold uppercase text-[oklch(var(--gold-foreground)/1)]">
                <StarIcon className="size-3" /> Destacada
              </span>
            )}
          </div>
        )}

        <div className="p-6">
          <DialogHeader>
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <span className={cn("inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide", catColor)}>
                {news.category}
              </span>
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <BuildingIcon className="size-3.5" />
                {news.university}
              </span>
              <span className="ml-auto flex items-center gap-1 text-xs text-muted-foreground">
                <CalendarIcon className="size-3.5" />
                {formatDate(news.published_at ?? news.created_at)}
              </span>
            </div>
            <DialogTitle className="font-display text-xl font-normal leading-snug text-left">
              {news.title}
            </DialogTitle>
          </DialogHeader>

          {news.summary && (
            <p className="mt-3 text-sm font-medium text-muted-foreground border-l-2 border-primary pl-3 leading-relaxed">
              {news.summary}
            </p>
          )}

          <Separator className="my-4" />

          <ScrollArea className="max-h-64">
            <p className="text-sm text-foreground/80 leading-relaxed whitespace-pre-wrap pr-4">
              {news.content}
            </p>
          </ScrollArea>

          <div className="mt-5 flex items-center justify-between gap-3">
            {news.author && (
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <UserIcon className="size-3.5" />
                {news.author}
              </span>
            )}
            <div className="flex items-center gap-2 ml-auto">
              {news.source_url && (
                <a href={news.source_url} target="_blank" rel="noopener noreferrer" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
                  <ExternalLinkIcon data-icon="inline-start" className="size-3.5" />
                  Fuente
                </a>
              )}
              <a href="/chat" className={cn(buttonVariants({ size: "sm" }))}>
                <SparklesIcon data-icon="inline-start" className="size-3.5" />
                Preguntar a la IA
              </a>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Main NewsPage Component ──────────────────────────────────

export default function NewsPage() {
  const [news, setNews] = useState<News[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [selectedNews, setSelectedNews] = useState<News | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Load stats and inject ticker
  useEffect(() => {
    fetchStats()
      .then((s) => {
        setStats(s);
        // Will inject ticker after news loads
      })
      .catch(() => toast.error("No se pudieron cargar las estadísticas."));
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    fetchNews({ limit: 50, category: category || undefined, search: search || undefined })
      .then((data) => {
        setNews(data);
        // Update ticker with real headlines
        const track = document.getElementById("ticker-track");
        if (track && data.length > 0) {
          const items = [...data, ...data]; // duplicate for seamless loop
          track.innerHTML = items
            .map(
              (n) =>
                `<span class="whitespace-nowrap px-8 text-xs font-medium text-muted-foreground">
                  ${n.is_featured ? '<span class="text-[oklch(var(--gold)/1)] font-semibold">★</span> ' : ""}
                  ${n.title}
                  <span class="mx-4 text-border">·</span>
                </span>`
            )
            .join("");
        }
      })
      .catch(() => toast.error("No se pudo conectar con el servidor. Asegúrate de que el backend esté en ejecución."))
      .finally(() => setLoading(false));
  }, [category, search]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(load, 300);
    return () => clearTimeout(timer);
  }, [load]);

  function openNews(n: News) {
    setSelectedNews(n);
    setDialogOpen(true);
  }

  return (
    <>
      {/* Stats */}
      <StatsBar stats={stats} />

      <main className="mx-auto max-w-screen-xl px-6 py-8">
        {/* Filters */}
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
            <Input
              placeholder="Buscar noticias..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Category chips */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <FilterIcon className="size-3.5 text-muted-foreground flex-shrink-0" />
            <button
              onClick={() => setCategory("")}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                !category
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border bg-background text-muted-foreground hover:border-primary/40 hover:text-foreground"
              )}
            >
              Todas
            </button>
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategory(cat === category ? "" : cat)}
                className={cn(
                  "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                  category === cat
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border bg-background text-muted-foreground hover:border-primary/40 hover:text-foreground"
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Section header */}
        <div className="mb-5 flex items-center justify-between gap-4">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            {category || "Todas las noticias"}
            {!loading && <span className="ml-2 text-foreground">({news.length})</span>}
          </h2>
          <Button variant="ghost" size="sm" onClick={load} className="text-muted-foreground">
            Actualizar
          </Button>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array(6).fill(null).map((_, i) => (
              <div key={i} className="rounded-xl border border-border overflow-hidden">
                <Skeleton className="aspect-[16/9] w-full rounded-none" />
                <div className="p-4 flex flex-col gap-3">
                  <Skeleton className="h-4 w-24 rounded-full" />
                  <Skeleton className="h-5 w-full rounded" />
                  <Skeleton className="h-4 w-3/4 rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : news.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <NewspaperIcon className="size-12 text-muted-foreground/30 mb-4" />
            <h3 className="text-base font-medium text-foreground">Sin noticias</h3>
            <p className="text-sm text-muted-foreground mt-1">
              {search || category
                ? "No se encontraron noticias con los filtros actuales."
                : "Aún no hay noticias. Agrega una desde el panel de administración."}
            </p>
            <a href="/admin" className={cn(buttonVariants({ size: "sm" }), "mt-4")}>
              Agregar noticia
            </a>
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {news.map((n, i) => (
              <NewsCard key={n.id} news={n} onClick={() => openNews(n)} delay={i * 40} />
            ))}
          </div>
        )}
      </main>

      {/* Detail dialog */}
      <NewsDialog
        news={selectedNews}
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
    </>
  );
}
