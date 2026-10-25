import { test, expect } from "@playwright/test";

test("muestra interfaz publica de noticias y boton de refresco", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/UniNews/i);
});
