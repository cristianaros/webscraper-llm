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
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

const CATEGORIES = ["Academia", "Becas", "Cultura", "Deportes", "Destacados", "En los medios", "Género", "Infraestructura", "Investigación", "Opinión", "Tecnología"];
const EMPTY_CATEGORIES = new Set(["", "n/a", "none", "null", "no content available", "not available"]);

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" });
}

function displayCategory(value: string) {
  return EMPTY_CATEGORIES.has(value.trim().toLowerCase()) ? "General" : value;
}

function validSourceUrl(value: string | null) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}

// ─── News Card ────────────────────────────────────────────────

function NewsCard({ news, onClick, delay }: { news: News; onClick: () => void; delay: number }) {
  const category = displayCategory(news.category);

  return (
    <article
      className="group animate-fade-up flex flex-col overflow-hidden rounded-xl border border-border bg-card transition-all duration-200 hover:-translate-y-1 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 focus-within:border-primary/50 focus-within:ring-3 focus-within:ring-ring/30"
      style={{ animationDelay: `${delay}ms` }}
    >
      <button type="button" onClick={onClick} className="flex flex-1 cursor-pointer flex-col text-left outline-none">
        {/* Image */}
        <div className="relative aspect-[16/9] flex-shrink-0 overflow-hidden bg-muted">
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
          {news.is_featured ? (
            <Badge className="absolute left-3 top-3">
              <StarIcon data-icon="inline-start" />
              Destacada
            </Badge>
          ) : null}
        </div>

        {/* Body */}
        <div className="flex flex-1 flex-col gap-3 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{category}</Badge>
            <span className="ml-auto flex items-center gap-1 text-[11px] text-muted-foreground">
              <CalendarIcon className="size-3" />
              {formatDate(news.published_at ?? news.created_at)}
            </span>
          </div>

          <h3 className="line-clamp-2 font-display text-base font-normal leading-snug text-foreground transition-colors group-hover:text-primary">
            {news.title}
          </h3>

          {news.summary ? (
            <p className="line-clamp-2 text-sm leading-relaxed text-muted-foreground">
              {news.summary}
            </p>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center gap-2 border-t border-border/60 px-4 py-2.5">
          <BuildingIcon className="size-3.5 flex-shrink-0 text-muted-foreground" />
          <span className="flex-1 truncate text-xs text-muted-foreground">{news.university}</span>
          {news.author ? (
            <span className="flex flex-shrink-0 items-center gap-1 text-[11px] text-muted-foreground/70">
              <UserIcon className="size-3" />
              {news.author.split(" ").slice(0, 2).join(" ")}
            </span>
          ) : null}
        </div>
      </button>
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
  const category = displayCategory(news.category);
  const sourceUrl = validSourceUrl(news.source_url);
  const paragraphs = news.content.split(/\n{2,}/).map((paragraph) => paragraph.trim()).filter(Boolean);

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="h-[calc(100dvh-2rem)] max-h-[900px] max-w-6xl grid-rows-[minmax(0,1fr)] gap-0 overflow-hidden p-0 sm:max-w-6xl md:h-[min(88dvh,900px)]">
        <div className="grid h-full min-h-0 grid-rows-[minmax(13rem,34vh)_minmax(0,1fr)] md:grid-cols-[minmax(19rem,0.85fr)_minmax(0,1.15fr)] md:grid-rows-1">
          {/* Visual y procedencia */}
          <div className="relative min-h-0 overflow-hidden bg-muted">
            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-primary/5 to-primary/20">
              <NewspaperIcon className="size-16 text-primary/20" />
            </div>
            {news.image_url ? (
              <img
                src={news.image_url}
                alt={news.title}
                className="relative size-full object-cover"
                onError={(event) => { event.currentTarget.style.display = "none"; }}
              />
            ) : null}
            <div className="absolute inset-0 bg-gradient-to-t from-background/70 via-transparent to-transparent" />

            {news.is_featured ? (
              <Badge className="absolute left-4 top-4">
                <StarIcon data-icon="inline-start" />
                Destacada
              </Badge>
            ) : null}

            <div className="absolute inset-x-4 bottom-4 rounded-xl border border-border bg-background/90 p-4 shadow-lg backdrop-blur-md md:inset-x-6 md:bottom-6">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">
                Publicación institucional
              </p>
              <div className="flex items-start gap-3">
                <BuildingIcon className="mt-0.5 size-4 flex-shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-foreground">{news.university}</p>
                  <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                    <CalendarIcon className="size-3" />
                    {formatDate(news.published_at ?? news.created_at)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Lectura */}
          <div className="flex min-h-0 flex-col bg-popover">
            <ScrollArea className="min-h-0 flex-1">
              <article className="px-6 py-7 md:px-8 md:py-9 lg:px-10">
                <DialogHeader className="pr-8 text-left">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <Badge variant="outline">{category}</Badge>
                    <span className="text-xs text-muted-foreground">Noticia UPLA</span>
                  </div>
                  <DialogTitle className="font-display text-3xl font-normal leading-[1.05] text-foreground md:text-4xl">
                    {news.title}
                  </DialogTitle>
                  <DialogDescription className="sr-only">
                    Detalle completo de la noticia {news.title}
                  </DialogDescription>
                </DialogHeader>

                {news.summary ? (
                  <p className="mt-6 border-l-2 border-primary bg-primary/5 py-3 pl-5 pr-4 text-base font-medium leading-relaxed text-muted-foreground">
                    {news.summary}
                  </p>
                ) : null}

                <Separator className="my-7" />

                <section aria-labelledby="article-content-title">
                  <h2 id="article-content-title" className="mb-4 text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                    Artículo completo
                  </h2>
                  <div className="flex flex-col gap-4 pr-3 text-[15px] leading-7 text-foreground/85">
                    {paragraphs.map((paragraph, index) => (
                      <p key={`${news.id}-${index}`} className="whitespace-pre-line">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </section>
              </article>
            </ScrollArea>

            <div className="flex flex-col gap-3 border-t border-border bg-muted/30 p-4 sm:flex-row sm:items-center sm:justify-between md:px-8">
              <div className="min-w-0">
                {news.author ? (
                  <p className="flex items-center gap-1.5 truncate text-xs text-muted-foreground">
                    <UserIcon className="size-3.5" />
                    {news.author}
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground">Dirección General de Comunicaciones UPLA</p>
                )}
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                {sourceUrl ? (
                  <a
                    href={sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(buttonVariants({ variant: "outline", size: "default" }), "w-full sm:w-auto")}
                    aria-label={`Abrir fuente original de ${news.title}`}
                  >
                    <ExternalLinkIcon data-icon="inline-start" />
                    Ver fuente original
                  </a>
                ) : (
                  <Button variant="outline" disabled className="w-full sm:w-auto">
                    <ExternalLinkIcon data-icon="inline-start" />
                    Fuente no disponible
                  </Button>
                )}
                <a
                  href={`/chat?news=${news.id}`}
                  className={cn(buttonVariants({ size: "default" }), "w-full sm:w-auto")}
                  aria-label={`Preguntar a la IA sobre ${news.title}`}
                >
                  <SparklesIcon data-icon="inline-start" />
                  Preguntar sobre esta noticia
                </a>
              </div>
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
