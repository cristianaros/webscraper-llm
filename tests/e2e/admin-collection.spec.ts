import { test, expect } from "@playwright/test";

test("registrar una fuente no la publica antes de revisar la muestra", async ({ page }) => {
  await page.goto("/admin");
  const adminKey = page.getByLabel("Clave de administración");
  if (await adminKey.isVisible()) {
    await adminKey.fill("admin-test");
    await page.getByRole("button", { name: "Entrar", exact: true }).click();
  }
  const fuentesTab = page.getByRole("tab", { name: "Fuentes" });
  if (await fuentesTab.isVisible()) {
    await fuentesTab.click();
    await expect(page.getByRole("button", { name: "Agregar fuente" })).toBeVisible();
  }
});
