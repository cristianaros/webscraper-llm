import { test, expect } from "@playwright/test";

const article = {
  id: 42,
  title: "Nueva iniciativa de investigación",
  summary: "Una iniciativa de prueba para el portal.",
  content: "La universidad anunció una nueva iniciativa.\n\nEl proyecto comenzará este año.",
  category: "Investigación",
  university: "Universidad Austral de Chile",
  university_id: 2,
  author: null,
  image_url: "https://images.example.test/iniciativa.jpg",
  image_status: "not_found",
  image_sha256: null,
  source_url: "https://uach.cl/noticias/iniciativa",
  is_featured: false,
  published_at: "2026-10-31T12:00:00Z",
  published_on: "2026-10-31",
  date_precision: "day",
  publication_status: "published",
  created_at: "2026-10-31T12:00:00Z",
  updated_at: null,
};

test("filtra por universidad y ofrece contexto IA dentro del lector", async ({ page }) => {
  const requestedUrls: URL[] = [];
  await page.route("https://images.example.test/**", (route) => route.abort());
  await page.route("**/api/news/**", async (route) => {
    const url = new URL(route.request().url());
    requestedUrls.push(url);
    if (url.pathname.endsWith("/stats")) {
      await route.fulfill({ json: { total_news: 1, categories: { Investigación: 1 }, universities: [article.university], featured_count: 0 } });
      return;
    }
    await route.fulfill({ json: [article] });
  });

  await page.goto("/");
  await expect(page).toHaveTitle(/UniNews/i);
  const universityFilter = page.getByRole("combobox", { name: "Universidad" });
  await expect(universityFilter).toBeVisible();
  await expect(page.locator('img[src*="iniciativa.jpg"]')).toHaveCount(0);
  await expect(page.locator("span.sr-only", { hasText: "Sin imagen disponible" })).toHaveCount(1);
  await universityFilter.selectOption({ label: article.university });
  await expect.poll(() => requestedUrls.some((url) => url.searchParams.get("university") === article.university)).toBe(true);

  await page.getByRole("button", { name: /Nueva iniciativa de investigación/ }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByRole("region", { name: "Contexto IA de esta noticia" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Asistente completo →" })).toHaveAttribute("href", "/chat?news=42");
});
