export function formatPublicationDate(news: { published_on: string | null; published_at: string | null; date_precision: string | null }): string {
  if (news.published_on) { const [year, month, day] = news.published_on.slice(0, 10).split("-"); return year && month && day ? `${day}/${month}/${year}` : "Fecha de publicación no disponible"; }
  if (news.published_at) return new Intl.DateTimeFormat("es-CL", { timeZone: "America/Santiago" }).format(new Date(news.published_at));
  return "Fecha de publicación no disponible";
}
