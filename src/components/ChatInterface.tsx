"use client";

import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import {
  sendChatMessage,
  fetchNewsById,
  fetchRagStatus,
  type ChatResponse,
  type News,
} from "@/lib/api";
import {
  SparklesIcon, SendIcon, UserIcon, BotIcon, InfoIcon, NewspaperIcon, RefreshCwIcon,
} from "@/lib/icons";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: ChatResponse["sources"];
  timestamp: Date;
}

const SUGGESTIONS = [
  "¿Cuáles son las últimas becas publicadas?",
  "Resume los avances en investigación científica",
  "¿Qué noticias hay de infraestructura universitaria?",
  "Dime qué actividades culturales se realizarán pronto",
];

const SCOPED_SUGGESTIONS = [
  "Dame un resumen breve de esta noticia",
  "¿Cuáles son los datos y personas más importantes?",
  "¿Qué impacto tiene esta noticia para la comunidad UPLA?",
];

function requestedNewsId() {
  if (typeof window === "undefined") return undefined;

  const newsId = Number(new URLSearchParams(window.location.search).get("news"));
  return Number.isInteger(newsId) && newsId > 0 ? newsId : undefined;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "¡Hola! Soy tu asistente de Inteligencia Artificial de UniNews. Puedo responder tus dudas sobre noticias universitarias basándome en los artículos indexados en nuestro sistema RAG. ¿En qué te puedo ayudar hoy?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [ragStatus, setRagStatus] = useState<{ status: string; count: number } | null>(null);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [scopedNews, setScopedNews] = useState<News | null>(null);
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
    const timer = window.setTimeout(checkStatus, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const newsId = requestedNewsId();
    if (!newsId) return;

    fetchNewsById(newsId)
      .then(setScopedNews)
      .catch(() => toast.error("No se pudo cargar la noticia seleccionada."));
  }, []);

  useEffect(() => {
    // Scroll to bottom of chat area when messages change
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector("[data-slot='scroll-area-viewport']");
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages, loading]);

  const handleSubmit = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMessage: Message = {
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendChatMessage(text, scopedNews?.id ?? requestedNewsId());
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
          content: "Disculpa, hubo un problema al conectar con el servidor de inteligencia artificial. Asegúrate de tener el backend activo y las variables de OpenRouter configuradas.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const clearNewsScope = () => {
    window.history.replaceState({}, "", window.location.pathname);
    setScopedNews(null);
    setMessages([
      {
        role: "assistant",
        content: "Ahora puedes preguntarme sobre cualquiera de las noticias indexadas en UniNews.",
        timestamp: new Date(),
      },
    ]);
  };

  const suggestions = scopedNews ? SCOPED_SUGGESTIONS : SUGGESTIONS;

  return (
    <div className="mx-auto max-w-screen-md px-4 py-6">
      <div className="flex flex-col rounded-xl border border-border bg-card overflow-hidden h-[calc(100vh-12rem)] min-h-[500px]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border bg-muted/20 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <SparklesIcon className="size-5" />
            </div>
            <div>
              <h2 className="font-display text-lg font-normal">Asistente UniNews IA</h2>
              <p className="text-xs text-muted-foreground">
                {scopedNews ? "Consulta enfocada en una noticia" : "MiniMax M3 vía OpenRouter + RAG"}
              </p>
            </div>
          </div>

          {/* RAG Status info */}
          <div className="flex items-center gap-2">
            {ragStatus && (
              <span className={cn(
                "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border",
                ragStatus.status === "ok"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-destructive/10 text-destructive border-destructive/20"
              )}>
                <span className={cn(
                  "size-1.5 rounded-full",
                  ragStatus.status === "ok" ? "bg-emerald-400" : "bg-destructive"
                )} />
                {ragStatus.status === "ok" ? `${ragStatus.count} noticias indexadas` : "Desconectado"}
              </span>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={checkStatus}
              disabled={checkingStatus}
            >
              <RefreshCwIcon data-icon="inline-start" className={cn(checkingStatus && "animate-spin")} />
            </Button>
          </div>
        </div>

        {scopedNews ? (
          <div className="flex items-center gap-3 border-b border-border bg-primary/5 px-4 py-3 sm:px-6">
            {scopedNews.image_url ? (
              <img
                src={scopedNews.image_url}
                alt=""
                className="size-11 flex-shrink-0 rounded-lg object-cover"
              />
            ) : (
              <div className="flex size-11 flex-shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <NewspaperIcon className="size-5" />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-primary">Preguntando sobre</p>
              <p className="truncate text-sm font-medium text-foreground" title={scopedNews.title}>
                {scopedNews.title}
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={clearNewsScope} className="flex-shrink-0">
              Consultar todas
            </Button>
          </div>
        ) : null}

        {/* Messages */}
        <ScrollArea ref={scrollAreaRef} className="flex-1 p-6">
          <div className="flex flex-col gap-6">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  "flex gap-4 max-w-[85%] animate-fade-in",
                  msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
                )}
              >
                {/* Avatar */}
                <div className={cn(
                  "flex size-8 shrink-0 select-none items-center justify-center rounded-lg border text-sm font-medium shadow-sm",
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-muted text-muted-foreground border-border"
                )}>
                  {msg.role === "user" ? <UserIcon className="size-4" /> : <BotIcon className="size-4" />}
                </div>

                {/* Content Bubble */}
                <div className="flex flex-col gap-2">
                  <div className={cn(
                    "rounded-xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap shadow-sm",
                    msg.role === "user"
                      ? "bg-primary/10 text-primary border border-primary/20"
                      : "bg-muted/40 text-foreground border border-border/50"
                  )}>
                    {msg.content}
                  </div>

                  {/* Sources if assistant response */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-1 flex flex-col gap-1.5 pl-1">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                        <NewspaperIcon className="size-3" />
                        Fuentes consultadas:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.sources.map((src, idx) =>
                          src.source_url ? (
                            <a
                              key={`${src.news_id}-${idx}`}
                              href={src.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="max-w-xs"
                              title={`${src.title} (${src.university})`}
                            >
                              <Badge variant="secondary" className="max-w-full truncate font-normal">
                                {src.title}
                              </Badge>
                            </a>
                          ) : (
                            <Badge
                              key={`${src.news_id}-${idx}`}
                              variant="secondary"
                              className="max-w-xs truncate font-normal"
                              title={`${src.title} (${src.university})`}
                            >
                              {src.title}
                            </Badge>
                          )
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-4 max-w-[85%] mr-auto animate-pulse">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-border bg-muted text-muted-foreground">
                  <BotIcon className="size-4" />
                </div>
                <div className="flex flex-col gap-2">
                  <div className="rounded-xl px-4 py-2.5 bg-muted/40 border border-border/50 flex items-center gap-1">
                    <span className="size-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="size-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="size-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Footer input area */}
        <div className="border-t border-border bg-muted/10 p-4">
          {messages.length === 1 && (
            <div className="mb-4">
              <span className="text-xs font-semibold text-muted-foreground block mb-2">Preguntas recomendadas:</span>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((sug, i) => (
                  <button
                    key={i}
                    onClick={() => handleSubmit(sug)}
                    className="text-xs bg-muted hover:bg-muted/80 border border-border/60 hover:border-primary/40 hover:text-primary transition-all duration-200 rounded-lg px-3 py-1.5 text-left text-muted-foreground"
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
                placeholder={scopedNews ? "Pregunta sobre esta noticia..." : "Pregunta sobre las noticias indexadas..."}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(input);
                  }
                }}
                rows={1}
                className="resize-none min-h-[44px] max-h-32 py-3 pr-4 pl-4"
              />
            </div>
            <Button type="submit" size="icon" disabled={!input.trim() || loading} className="shrink-0 h-[44px] w-[44px]">
              <SendIcon data-icon="inline-start" />
            </Button>
          </form>
          <div className="mt-2 text-center text-[10px] text-muted-foreground flex items-center justify-center gap-1">
            <InfoIcon className="size-3" />
            Respuestas generadas por IA utilizando la base de datos de noticias.
          </div>
        </div>
      </div>
    </div>
  );
}
