import { test, expect } from "@playwright/test";

const token = "admin-session-token";
const revision = {
  id: 7, news_id: null, source_id: 2, document: { url: "https://university.example/news" },
  fields: { title: "Hallazgo científico", category: "Investigación", published_on: "2026-10-30", content: "Texto candidato", summary: "Resumen" },
  issues: ["Revisar fecha"], review_status: "pending",
};

test("el panel envía Bearer al iniciar y publica una revisión editada", async ({ page }) => {
  const writes: Array<{ url: string; authorization: string | undefined; body: Record<string, unknown> }> = [];
  const reads: Array<{ url: string; authorization: string | undefined }> = [];
  let pending = true;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const authorization = request.headers().authorization;
    if (request.method() === "GET") reads.push({ url: url.pathname, authorization });
    else writes.push({ url: url.pathname, authorization, body: request.postDataJSON() ?? {} });
    if (url.pathname === "/api/admin/universities") return route.fulfill({ json: [{ id: 1, name: "Universidad Austral" }] });
    if (url.pathname === "/api/news/stats") return route.fulfill({ json: { total_news: 0, categories: {}, universities: [], featured_count: 0 } });
    if (url.pathname === "/api/news/") return route.fulfill({ json: [] });
    if (url.pathname === "/api/admin/revisions") return route.fulfill({ json: { items: pending ? [revision] : [], total: pending ? 1 : 0 } });
    if (url.pathname.endsWith("/publish")) { pending = false; return route.fulfill({ json: { id: 10, title: "Hallazgo científico" } }); }
    if (url.pathname === "/api/admin/sources") return route.fulfill({ json: [] });
    if (url.pathname === "/api/admin/runs") return route.fulfill({ json: { items: [], total: 0 } });
    if (url.pathname === "/api/admin/collector/status") return route.fulfill({ json: { stale: true } });
    return route.fulfill({ status: 404, json: { detail: "not found" } });
  });

  await page.goto("/admin");
  await page.getByLabel("Clave de administración").fill(token);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect.poll(() => reads.some((read) => read.url.includes("/api/admin/universities") && read.authorization === `Bearer ${token}`)).toBe(true);
  await page.getByRole("button", { name: "Nueva noticia" }).click();
  await page.getByRole("combobox").first().click();
  await expect(page.getByRole("option", { name: "Admisión" })).toBeVisible();
  await expect(page.getByRole("option", { name: "Destacados" })).toHaveCount(0);
  await expect(page.locator("datalist#universities-list option[value='Universidad Austral']")).toHaveCount(1);
  await page.getByRole("button", { name: "Cancelar" }).click();
  await page.getByRole("tab", { name: "Revisión" }).click();
  const title = page.getByLabel("Título revisión 7");
  await expect(title).toHaveValue("Hallazgo científico");
  await title.fill("Título corregido por edición");
  await page.getByRole("button", { name: "Aprobar y publicar" }).click();
  await expect.poll(() => writes.find((write) => write.url.endsWith("/publish"))).toBeTruthy();
  const request = writes.find((write) => write.url.endsWith("/publish"));
  expect(request?.authorization).toBe(`Bearer ${token}`);
  expect((request?.body.fields as Record<string, unknown>).title).toBe("Título corregido por edición");
  expect((request?.body.fields as Record<string, unknown>).published_at).toBe("2026-10-30T00:00:00Z");
  await expect(page.getByText("No hay revisiones pendientes.")).toBeVisible();
});

test("la clave inválida no abre el panel de administración", async ({ page }) => {
  await page.route("**/api/admin/universities", (route) => route.fulfill({ status: 401, json: { detail: "unauthorized" } }));
  await page.goto("/admin");
  await page.getByLabel("Clave de administración").fill("incorrecta");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("alert")).toHaveText("Clave inválida o API no disponible.");
  await expect(page.getByRole("tab", { name: "Fuentes" })).toHaveCount(0);
});

test("aprobar sin editar conserva la hora y precisión de una fecha instantánea", async ({ page }) => {
  const writes: Array<{ url: string; authorization: string | undefined; body: Record<string, unknown> }> = [];
  const instantRevision = {
    ...revision,
    fields: {
      ...revision.fields,
      published_on: "2026-10-30",
      published_at: "2026-10-30T14:37:00Z",
      date_precision: "instant",
      original_date_text: "30 de octubre de 2026, 11:37",
    },
  };
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (request.method() !== "GET") writes.push({ url: url.pathname, authorization: request.headers().authorization, body: request.postDataJSON() ?? {} });
    if (url.pathname === "/api/admin/universities") return route.fulfill({ json: [{ id: 1, name: "Universidad Austral" }] });
    if (url.pathname === "/api/news/stats") return route.fulfill({ json: { total_news: 0, categories: {}, universities: [], featured_count: 0 } });
    if (url.pathname === "/api/news/") return route.fulfill({ json: [] });
    if (url.pathname === "/api/admin/revisions") return route.fulfill({ json: { items: [instantRevision], total: 1 } });
    if (url.pathname.endsWith("/publish")) return route.fulfill({ json: { id: 10, title: "Hallazgo científico" } });
    return route.fulfill({ status: 404, json: { detail: "not found" } });
  });

  await page.goto("/admin");
  await page.getByLabel("Clave de administración").fill(token);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("tab", { name: "Revisión" }).click();
  await page.getByRole("button", { name: "Aprobar y publicar" }).click();
  await expect.poll(() => writes.find((write) => write.url.endsWith("/publish"))).toBeTruthy();
  const request = writes.find((write) => write.url.endsWith("/publish"));
  const submittedFields = request?.body.fields as Record<string, unknown>;
  expect(submittedFields.published_at).toBe("2026-10-30T14:37:00Z");
  expect(submittedFields.date_precision).toBe("instant");
  expect(submittedFields.original_date_text).toBe("30 de octubre de 2026, 11:37");
});
