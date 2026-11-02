"use client";

import { useState } from "react";
import { resolveExternalUrl, sendChatMessage, type ChatResponse, type News } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import MarkdownMessage from "@/components/MarkdownMessage";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: ChatResponse["sources"];
}

const suggestions = [
  "¿Cuál es el contexto y los puntos clave de esta noticia?",
  "¿Cómo se relaciona esta noticia con otras publicaciones universitarias?",
];

export default function NewsContextAssistant({ news }: { news: News }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitQuestion(text: string) {
    const prompt = text.trim();
    if (!prompt || loading) return;
    setMessages((current) => [...current, { role: "user", content: prompt }]);
    setQuestion("");
    setError(null);
    setLoading(true);
    try {
      const response = await sendChatMessage(prompt, news.id);
      setMessages((current) => [...current, { role: "assistant", content: response.answer, sources: response.sources }]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo consultar el asistente.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: { preventDefault: () => void }) {
    event.preventDefault();
    void submitQuestion(question);
  }

  return (
    <section aria-label="Contexto IA de esta noticia" className="mt-8 border-t-2 border-foreground/15 pt-6">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#D8232A]">Archivo universitario · IA</p>
          <h3 className="mt-1 font-display text-2xl font-bold">Explora el contexto</h3>
          <p className="mt-1 text-sm text-muted-foreground">Pregunta por esta noticia y sus antecedentes en el archivo.</p>
        </div>
        <a className="shrink-0 pt-1 text-xs font-medium underline underline-offset-4" href={`/chat?news=${news.id}`}>Asistente completo →</a>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {[...suggestions, `¿Qué relevancia tiene este anuncio para ${news.university}?`].map((suggestion) => (
          <button key={suggestion} type="button" onClick={() => void submitQuestion(suggestion)} disabled={loading} className="border border-border bg-muted/30 px-3 py-2 text-left text-xs leading-relaxed transition-colors hover:border-primary/50 hover:text-primary disabled:opacity-50">
            {suggestion}
          </button>
        ))}
      </div>

      {messages.length > 0 && <div aria-live="polite" className="mb-4 space-y-3">
        {messages.map((message, index) => <div key={`${index}-${message.role}`} className={message.role === "user" ? "ml-6 border-l-2 border-primary/40 pl-3" : "border-l-2 border-foreground/10 pl-3"}>
          <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{message.role === "user" ? "Tu pregunta" : "Respuesta"}</p>
          {message.role === "assistant" ? (
            <MarkdownMessage content={message.content} />
          ) : (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
          )}
          {message.sources && message.sources.length > 0 && <div className="mt-3 space-y-2">
            {message.sources.map((source, sourceIndex) => {
              const current = source.news_id === news.id;
              const sourceUrl = resolveExternalUrl(source.source_url);
              return <div key={`${source.news_id}-${sourceIndex}`} className="flex flex-wrap items-baseline gap-x-2 text-xs">
                <span className="font-semibold text-[#D8232A]">{current ? "Noticia en foco" : "Antecedente relacionado"}</span>
                {sourceUrl ? <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">{source.title}</a> : <span>{source.title}</span>}
                <span className="text-muted-foreground">{source.university}</span>
              </div>;
            })}
          </div>}
        </div>)}
      </div>}

      {loading && <p role="status" aria-live="polite" className="mb-3 text-sm text-muted-foreground">Consultando el archivo…</p>}
      {error && <p role="alert" className="mb-3 border border-destructive/30 bg-destructive/5 p-3 text-sm">{error}</p>}
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        <label className="sr-only" htmlFor={`news-question-${news.id}`}>Pregunta sobre esta noticia</label>
        <Textarea id={`news-question-${news.id}`} value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Escribe una pregunta sobre esta noticia…" rows={2} disabled={loading} className="min-h-11 resize-y rounded-none text-sm" />
        <Button type="submit" disabled={loading || !question.trim()} className="h-11 shrink-0 rounded-none">Preguntar</Button>
      </form>
    </section>
  );
}
