"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import {
  sendChatMessage,
  fetchNewsById,
  fetchNews,
  fetchRagStatus,
  type ChatResponse,
  type News,
  resolveExternalUrl,
  resolveMediaUrl,
} from "@/lib/api";
import { formatPublicationDate } from "@/lib/date";
import {
  SparklesIcon,
  SendIcon,
  UserIcon,
  BotIcon,
  InfoIcon,
  NewspaperIcon,
  RefreshCwIcon,
  SearchIcon,
  XIcon,
} from "@/lib/icons";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import MarkdownMessage from "@/components/MarkdownMessage";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: ChatResponse["sources"];
  timestamp: Date;
}

const GLOBAL_SUGGESTIONS = [
  "Hazme un resumen de lo que dicen las noticias publicadas en este blog",
  "¿Cuáles son las últimas noticias de investigación científica?",
  "¿Qué actividades o proyectos universitarios se destacan recientemente?",
  "Dame un panorama general de las publicaciones",
];

function scopedSuggestions(university?: string) {
  return [
    "Dame un resumen detallado de esta noticia",
    "¿Cuáles son los datos, personas y fechas más importantes?",
    `¿Qué impacto o relevancia tiene este anuncio para ${university || "la universidad"}?`,
    "¿Hay antecedentes o noticias relacionadas en el archivo?",
  ];
}

function requestedNewsId(): number | undefined {
  if (typeof window === "undefined") return undefined;
  const newsId = Number(new URLSearchParams(window.location.search).get("news"));
  return Number.isInteger(newsId) && newsId > 0 ? newsId : undefined;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "¡Hola! Soy tu asistente de UniNews. Puedo responder preguntas sobre las noticias universitarias publicadas, elaborar resúmenes o explicar detalles de cualquier artículo. ¿En qué te puedo ayudar hoy?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [ragStatus, setRagStatus] = useState<{ status: string; count: number } | null>(null);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [scopedNews, setScopedNews] = useState<News | null>(null);
  const [imageBroken, setImageBroken] = useState(false);

  // News picker state
  const [pickerOpen, setPickerOpen] = useState(false);
  const [allNews, setAllNews] = useState<News[]>([]);
  const [loadingNews, setLoadingNews] = useState(false);
  const [pickerSearch, setPickerSearch] = useState("");

  // Mobile tab state when scopedNews is active: "article" | "chat"
  const [mobileTab, setMobileTab] = useState<"article" | "chat">("chat");

  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const checkStatus = () => {
    setCheckingStatus(true);
    fetchRagStatus()
      .then((res) => {
        setRagStatus({
          status: res.status,
          count: res.indexed_documents || 0,
        });
      })
      .catch(() => {
        setRagStatus({ status: "error", count: 0 });
      })
      .finally(() => {
        setCheckingStatus(false);
      });
  };

  useEffect(() => {
    checkStatus();
  }, []);

  // Load requested news if present in URL
  useEffect(() => {
    const newsId = requestedNewsId();
    if (!newsId) return;

    fetchNewsById(newsId)
      .then((item) => {
        setScopedNews(item);
        setImageBroken(false);
      })
      .catch(() => toast.error("No se pudo cargar la noticia seleccionada."));
  }, []);

  // Fetch news list for the picker dialog
  const loadPickerNews = () => {
    if (allNews.length > 0) return;
    setLoadingNews(true);
    fetchNews({ limit: 60 })
      .then(setAllNews)
      .catch(() => toast.error("No se pudo cargar la lista de noticias."))
      .finally(() => setLoadingNews(false));
  };

  useEffect(() => {
    if (pickerOpen) {
      loadPickerNews();
    }
  }, [pickerOpen]);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({
        top: scrollAreaRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, loading]);

  const selectNews = (item: News) => {
    setScopedNews(item);
    setImageBroken(false);
    setPickerOpen(false);
    setPickerSearch("");
    const newUrl = `${window.location.pathname}?news=${item.id}`;
    window.history.pushState({}, "", newUrl);

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: `He enfocado la consulta en la noticia: **"${item.title}"** (${item.university}).\n\nPuedes preguntarme sobre los puntos clave, fechas, participantes o sus relaciones con otras publicaciones del archivo.`,
        timestamp: new Date(),
      },
    ]);
  };

  const clearNewsScope = () => {
    window.history.replaceState({}, "", window.location.pathname);
    setScopedNews(null);
    setImageBroken(false);
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: "Se ha quitado el foco. Ahora puedes consultarme sobre cualquiera de las noticias publicadas en el portal general.",
        timestamp: new Date(),
      },
    ]);
  };

  const handleSubmit = async (text: string) => {
    const cleanText = text.trim();
    if (!cleanText || loading) return;

    const userMessage: Message = {
      role: "user",
      content: cleanText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendChatMessage(cleanText, scopedNews?.id ?? requestedNewsId());
      const assistantMessage: Message = {
        role: "assistant",
        content: res.answer,
        sources: res.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      toast.error("Ocurrió un error al enviar el mensaje.");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Disculpa, hubo un problema al conectar con el servidor de inteligencia artificial. Asegúrate de tener el backend activo y las variables de OpenRouter configuradas.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = scopedNews ? scopedSuggestions(scopedNews.university) : GLOBAL_SUGGESTIONS;

  const filteredPickerNews = useMemo(() => {
    if (!pickerSearch.trim()) return allNews;
    const term = pickerSearch.toLowerCase();
    return allNews.filter(
      (n) =>
        n.title.toLowerCase().includes(term) ||
        n.university.toLowerCase().includes(term) ||
        n.category.toLowerCase().includes(term)
    );
  }, [allNews, pickerSearch]);

  const scopedImageUrl = scopedNews ? resolveMediaUrl(scopedNews.image_url) : null;
  const scopedSourceUrl = scopedNews ? resolveExternalUrl(scopedNews.source_url) : null;
  const scopedParagraphs = scopedNews?.content
    ? scopedNews.content
        .split(/\n{2,}/)
        .map((p) => p.trim())
        .filter(Boolean)
    : [];

  return (
    <div className="mx-auto max-w-7xl px-3 sm:px-6 py-4 sm:py-6">
      {/* Mobile Switcher Tab (Only visible on small screens when scopedNews is active) */}
      {scopedNews && (
        <div className="lg:hidden mb-3 flex items-center justify-between gap-2 rounded-lg border border-border bg-card p-1">
          <button
            type="button"
            onClick={() => setMobileTab("article")}
            className={cn(
              "flex-1 rounded-md py-1.5 text-xs font-semibold transition-all",
              mobileTab === "article"
                ? "bg-primary text-primary-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            Ver Noticia Completa
          </button>
          <button
            type="button"
            onClick={() => setMobileTab("chat")}
            className={cn(
              "flex-1 rounded-md py-1.5 text-xs font-semibold transition-all",
              mobileTab === "chat"
                ? "bg-primary text-primary-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            Chat Asistente IA
          </button>
        </div>
      )}

      {/* Main Container */}
      <div
        className={cn(
          "w-full h-[calc(100vh-11rem)] min-h-[620px] max-h-[920px]",
          scopedNews ? "grid grid-cols-1 lg:grid-cols-12 gap-5" : "max-w-5xl mx-auto flex flex-col"
        )}
      >
        {/* ================= LEFT PANEL: FULL NEWS ARTICLE (When scopedNews is active) ================= */}
        {scopedNews && (
          <aside
            aria-label="Artículo en foco"
            className={cn(
              "lg:col-span-5 flex flex-col rounded-xl border border-border bg-card overflow-hidden h-full shadow-xs",
              mobileTab !== "article" && "hidden lg:flex"
            )}
          >
            {/* News Header & Controls */}
            <div className="flex items-center justify-between border-b border-border bg-muted/20 px-4 py-3 sm:px-5">
              <div className="flex items-center gap-2">
                <span className="flex size-2 rounded-full bg-primary animate-pulse" />
                <span className="text-xs font-bold uppercase tracking-wider text-primary">
                  Noticia en Foco
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPickerOpen(true)}
                  className="h-7 text-xs px-2.5"
                >
                  Cambiar
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearNewsScope}
                  className="h-7 text-xs text-muted-foreground hover:text-foreground px-2"
                  title="Quitar foco y consultar todo el portal"
                >
                  <XIcon className="size-3.5 mr-1" />
                  Ver todas
                </Button>
              </div>
            </div>

            {/* Scrollable Article Body */}
            <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6 space-y-4">
              {/* Badges */}
              <div className="flex flex-wrap items-center gap-2 text-[11px]">
                <Badge variant="outline" className="font-semibold text-primary border-primary/30">
                  {scopedNews.university}
                </Badge>
                <Badge variant="secondary" className="font-normal text-muted-foreground">
                  {scopedNews.category}
                </Badge>
                <span className="text-muted-foreground ml-auto">
                  {formatPublicationDate(scopedNews)}
                </span>
              </div>

              {/* Title */}
              <h1 className="font-display text-xl sm:text-2xl font-bold leading-tight text-foreground">
                {scopedNews.title}
              </h1>

              {/* Full News Photo */}
              {scopedImageUrl && !imageBroken ? (
                <div className="relative overflow-hidden rounded-lg border border-border/50 bg-muted/30 shadow-xs">
                  <img
                    src={scopedImageUrl}
                    alt={scopedNews.title}
                    onError={() => setImageBroken(true)}
                    className="w-full max-h-72 object-cover object-center transition-transform duration-300 hover:scale-[1.01]"
                  />
                  <div className="absolute bottom-2 right-2 rounded bg-black/60 px-2 py-0.5 text-[10px] text-white backdrop-blur-xs">
                    Fotografía oficial
                  </div>
                </div>
              ) : (
                <div className="flex aspect-[16/9] w-full flex-col items-center justify-center rounded-lg border border-dashed border-border/70 bg-muted/20 text-muted-foreground">
                  <NewspaperIcon className="size-8 text-muted-foreground/60 mb-1" />
                  <span className="text-xs font-medium text-foreground/80">{scopedNews.university}</span>
                  <span className="text-[11px] text-muted-foreground">Registro oficial sin imagen adjunta</span>
                </div>
              )}

              {/* Summary */}
              {scopedNews.summary && (
                <div className="rounded-r-lg border-l-3 border-primary/70 bg-primary/5 p-3.5 text-sm italic font-serif text-foreground/90 leading-relaxed">
                  {scopedNews.summary}
                </div>
              )}

              {/* Full Article Content */}
              <div className="space-y-3.5 font-serif text-sm leading-relaxed text-foreground/90 pt-1">
                {scopedParagraphs.map((paragraph, idx) => (
                  <p key={idx} className="leading-7">
                    {paragraph}
                  </p>
                ))}
              </div>

              {/* Source Link */}
              {scopedSourceUrl && (
                <div className="pt-4 border-t border-border/60">
                  <a
                    href={scopedSourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline underline-offset-4"
                  >
                    Abrir fuente institucional original en {scopedNews.university} ↗
                  </a>
                </div>
              )}
            </div>
          </aside>
        )}

        {/* ================= RIGHT PANEL: CHAT ASSISTANT ================= */}
        <main
          aria-label="Asistente de inteligencia artificial"
          className={cn(
            "flex flex-col rounded-xl border border-border bg-card overflow-hidden h-full shadow-xs",
            scopedNews ? "lg:col-span-7" : "w-full flex-1",
            scopedNews && mobileTab !== "chat" && "hidden lg:flex"
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border bg-muted/20 px-4 py-3 sm:px-6">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex size-9 sm:size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <SparklesIcon className="size-5" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h2 className="font-display text-base sm:text-lg font-bold leading-none text-foreground truncate">
                    Asistente UniNews IA
                  </h2>
                  {scopedNews && (
                    <Badge variant="secondary" className="hidden sm:inline-flex text-[10px] py-0 px-1.5">
                      Foco activo
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground truncate mt-0.5">
                  {scopedNews
                    ? `Consultando: ${scopedNews.title}`
                    : "Noticias publicadas + Modelo OpenRouter"}
                </p>
              </div>
            </div>

            {/* Actions & Status info */}
            <div className="flex items-center gap-2 shrink-0">
              {!scopedNews && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPickerOpen(true)}
                  className="hidden sm:inline-flex items-center gap-1.5 text-xs h-8"
                >
                  <NewspaperIcon className="size-3.5 text-primary" />
                  <span>Enfocar noticia</span>
                </Button>
              )}

              {ragStatus && (
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border",
                    ragStatus.status === "ok"
                      ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                      : "bg-destructive/10 text-destructive border-destructive/20"
                  )}
                >
                  <span
                    className={cn(
                      "size-1.5 rounded-full",
                      ragStatus.status === "ok" ? "bg-emerald-500" : "bg-destructive"
                    )}
                  />
                  <span className="hidden sm:inline">
                    {ragStatus.status === "ok"
                      ? `${ragStatus.count} ${ragStatus.count === 1 ? "noticia" : "noticias"}`
                      : "Desconectado"}
                  </span>
                </span>
              )}

              <Button
                variant="ghost"
                size="icon"
                className="size-8 text-muted-foreground hover:text-foreground"
                onClick={checkStatus}
                disabled={checkingStatus}
                title="Actualizar estado del asistente"
              >
                <RefreshCwIcon
                  data-icon="inline-start"
                  className={cn("size-3.5", checkingStatus && "animate-spin")}
                />
              </Button>
            </div>
          </div>

          {/* Subheader when no news is selected: shortcut to select news on mobile */}
          {!scopedNews && (
            <div className="sm:hidden flex items-center justify-between border-b border-border bg-muted/10 px-4 py-2 text-xs">
              <span className="text-muted-foreground">¿Deseas consultar sobre una noticia específica?</span>
              <Button
                variant="link"
                size="sm"
                onClick={() => setPickerOpen(true)}
                className="h-auto p-0 text-primary font-semibold text-xs"
              >
                Seleccionar →
              </Button>
            </div>
          )}

          {/* Messages Scroll Area */}
          <div
            ref={scrollAreaRef}
            className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6 space-y-5"
          >
            {messages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  "flex gap-3 sm:gap-4 max-w-[95%] sm:max-w-[88%] animate-fade-in",
                  msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
                )}
              >
                {/* Avatar */}
                <div
                  className={cn(
                    "flex size-8 shrink-0 select-none items-center justify-center rounded-lg border text-sm font-medium shadow-2xs mt-0.5",
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-muted text-muted-foreground border-border"
                  )}
                >
                  {msg.role === "user" ? <UserIcon className="size-4" /> : <BotIcon className="size-4" />}
                </div>

                {/* Content Bubble */}
                <div className="flex flex-col gap-2 min-w-0 max-w-full">
                  <div
                    className={cn(
                      "rounded-xl px-4 py-3 shadow-2xs",
                      msg.role === "user"
                        ? "bg-primary/10 text-foreground border border-primary/20 text-sm whitespace-pre-wrap font-sans"
                        : "bg-muted/40 text-foreground border border-border/60"
                    )}
                  >
                    {msg.role === "assistant" ? (
                      <MarkdownMessage content={msg.content} />
                    ) : (
                      <span>{msg.content}</span>
                    )}
                  </div>

                  {/* Sources if assistant response */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-1 flex flex-col gap-1.5 pl-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                        <NewspaperIcon className="size-3 text-primary" />
                        Fuentes consultadas del portal:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.sources.map((src, idx) => {
                          const sourceUrl = resolveExternalUrl(src.source_url);
                          return sourceUrl ? (
                            <a
                              key={`${src.news_id}-${idx}`}
                              href={sourceUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="max-w-xs transition-opacity hover:opacity-80"
                              title={`${src.title} (${src.university})`}
                            >
                              <Badge
                                variant="secondary"
                                className="max-w-full truncate font-normal text-xs py-0.5 border border-border/60 hover:border-primary/50"
                              >
                                {src.title}
                              </Badge>
                            </a>
                          ) : (
                            <Badge
                              key={`${src.news_id}-${idx}`}
                              variant="secondary"
                              className="max-w-xs truncate font-normal text-xs py-0.5 border border-border/60"
                              title={`${src.title} (${src.university})`}
                            >
                              {src.title}
                            </Badge>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-3 sm:gap-4 max-w-[85%] mr-auto animate-pulse">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-border bg-muted text-muted-foreground">
                  <BotIcon className="size-4" />
                </div>
                <div className="flex flex-col gap-2">
                  <div className="rounded-xl px-4 py-3 bg-muted/40 border border-border/50 flex items-center gap-1.5">
                    <span
                      className="size-2 bg-primary rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    />
                    <span
                      className="size-2 bg-primary rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    />
                    <span
                      className="size-2 bg-primary rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    />
                    <span className="text-xs text-muted-foreground ml-2 font-medium">
                      Analizando archivo...
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer input area */}
          <div className="border-t border-border bg-muted/10 p-3 sm:p-4 shrink-0">
            {/* Suggestions */}
            {messages.length <= 2 && (
              <div className="mb-3">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
                  Preguntas recomendadas:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {suggestions.map((sug, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleSubmit(sug)}
                      disabled={loading}
                      className="text-xs bg-card hover:bg-muted/80 border border-border/80 hover:border-primary/50 hover:text-primary transition-all duration-150 rounded-lg px-2.5 py-1 text-left text-muted-foreground shadow-2xs disabled:opacity-50"
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSubmit(input);
              }}
              className="flex items-end gap-2"
            >
              <div className="relative flex-1">
                <Textarea
                  placeholder={
                    scopedNews
                      ? `Pregunta sobre "${scopedNews.title.slice(0, 35)}..."`
                      : "Escribe tu pregunta sobre las noticias universitarias..."
                  }
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(input);
                    }
                  }}
                  rows={1}
                  className="resize-none min-h-[44px] max-h-32 py-2.5 pr-4 pl-4 text-sm"
                />
              </div>
              <Button
                type="submit"
                size="icon"
                disabled={!input.trim() || loading}
                className="shrink-0 h-[44px] w-[44px]"
                title="Enviar mensaje"
              >
                <SendIcon data-icon="inline-start" className="size-4" />
              </Button>
            </form>

            <div className="mt-2 text-center text-[10px] text-muted-foreground flex items-center justify-center gap-1">
              <InfoIcon className="size-3 text-muted-foreground/80" />
              <span>Respuestas generadas por IA utilizando la base de datos de noticias universitarias.</span>
            </div>
          </div>
        </main>
      </div>

      {/* ================= NEWS PICKER MODAL ================= */}
      <Dialog open={pickerOpen} onOpenChange={setPickerOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col p-0 overflow-hidden">
          <DialogHeader className="p-5 border-b border-border bg-muted/20">
            <DialogTitle className="font-display text-2xl font-bold">
              Seleccionar noticia para el Asistente
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Elige un artículo para enfocar las respuestas, preguntas y resúmenes en su contenido oficial.
            </DialogDescription>
            <div className="relative mt-3">
              <SearchIcon className="pointer-events-none absolute left-3 top-2.5 size-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por título, universidad o categoría..."
                value={pickerSearch}
                onChange={(e) => setPickerSearch(e.target.value)}
                className="pl-9 text-sm"
              />
            </div>
          </DialogHeader>

          <div className="flex-1 min-h-0 overflow-y-auto p-4 divide-y divide-border/60">
            {loadingNews ? (
              <div className="py-12 text-center text-sm text-muted-foreground">
                Cargando noticias disponibles...
              </div>
            ) : filteredPickerNews.length === 0 ? (
              <div className="py-12 text-center text-sm text-muted-foreground">
                No se encontraron noticias para la búsqueda.
              </div>
            ) : (
              filteredPickerNews.map((item) => {
                const itemImg = resolveMediaUrl(item.image_url);
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => selectNews(item)}
                    className="w-full text-left py-3 px-2 flex items-start gap-3 rounded-lg hover:bg-muted/50 transition-colors group"
                  >
                    {itemImg ? (
                      <img
                        src={itemImg}
                        alt=""
                        className="size-14 shrink-0 rounded-md object-cover border border-border/40"
                      />
                    ) : (
                      <div className="flex size-14 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground border border-border/40">
                        <NewspaperIcon className="size-6 text-muted-foreground/60" />
                      </div>
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-primary">
                          {item.university}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {formatPublicationDate(item)}
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-foreground leading-snug line-clamp-2 group-hover:text-primary transition-colors">
                        {item.title}
                      </h4>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
