import { expect, test, type Page } from "@playwright/test";

test("la cola IndexedDB conserva el evento tras recargar", async ({ page }) => {
  await page.goto("/login");
  await page.evaluate(async () => {
    const modulePath = "/src/services/pendingAttempts.ts";
    const { pendingAttempts } = await import(/* @vite-ignore */ modulePath);
    await pendingAttempts.add({ key: "test-user:test-task", deviceId: "test-device", event: { event_id: "test-event", type: "attempt.created", payload: { answer: { index: 1 } } } });
  });
  await page.reload();
  const eventId = await page.evaluate(async () => {
    const modulePath = "/src/services/pendingAttempts.ts";
    const { pendingAttempts } = await import(/* @vite-ignore */ modulePath);
    const saved = await pendingAttempts.get("test-user:test-task");
    await pendingAttempts.removeConfirmed("test-user:test-task", "test-event");
    return saved?.event.event_id;
  });
  expect(eventId).toBe("test-event");
});

test("una confirmación antigua no borra otra respuesta pendiente", async ({ page }) => {
  await page.goto("/login");
  const result = await page.evaluate(async () => {
    const modulePath = "/src/services/pendingAttempts.ts";
    const { pendingAttempts } = await import(/* @vite-ignore */ modulePath);
    const key = "user:task";
    await pendingAttempts.add({ key, deviceId: "device", event: { event_id: "new-event", type: "attempt.created", payload: {} } });
    const removed = await pendingAttempts.removeConfirmed(key, "old-event");
    const saved = await pendingAttempts.get(key);
    await pendingAttempts.removeConfirmed(key, "new-event");
    return { removed, eventId: saved?.event.event_id };
  });
  expect(result).toEqual({ removed: false, eventId: "new-event" });
});

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Correo").fill("maestra@demo.pe");
  await page.getByLabel("Contraseña", { exact: true }).fill("Aula-Multigrado-2026!");
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
}

test("login, evidencia calculada, progreso, restauración de sesión y logout", async ({ page }) => {
  await page.goto("/alertas");
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel("Correo").fill("maestra@demo.pe");
  await page.getByLabel("Contraseña", { exact: true }).fill("Clave-Incorrecta-2026!");
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);

  await login(page);
  const flag = page.getByRole("article", { name: "Alerta educativa de Juan" });
  await expect(flag.getByText("4 de los últimos 5 ejercicios presentan dificultad.", { exact: true })).toBeVisible();
  await expect(flag.getByRole("listitem").filter({ hasText: "6 pistas utilizadas" })).toBeVisible();
  await expect(flag.getByRole("row")).toHaveCount(6);
  await expect(page.getByText(/Las alertas por reglas siguen funcionando/)).toBeVisible();
  await page.getByRole("button", { name: "VER PROGRESO" }).click();
  await expect(page.getByRole("heading", { name: "Progreso por competencia" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "5 ejercicios", exact: true })).toBeVisible();

  const refreshed = page.waitForResponse((r) => r.url().endsWith("/auth/refresh") && r.status() === 200);
  await page.reload();
  await refreshed;
  await expect(flag).toBeVisible();
  await page.goto("/admin");
  await expect(page.getByRole("alert")).toHaveText("No tienes permiso para ver esta sección.");
  await page.getByRole("button", { name: "Salir", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect(await page.evaluate(() => sessionStorage.getItem("kawsay_rt"))).toBeNull();
  await page.goto("/estudiantes");
  await expect(page).toHaveURL(/\/login$/);
});

test("intervención docente persistida y alerta resuelta con filtros", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Alertas educativas", exact: true }).click();
  await page.getByRole("button", { name: "En seguimiento", exact: true }).click();
  const flag = page.getByRole("article", { name: "Alerta educativa de Juan" });
  await expect(flag).toBeVisible();
  await flag.getByRole("button", { name: "REGISTRAR INTERVENCIÓN" }).click();
  await flag.getByLabel("Estrategia", { exact: true }).fill("Acompañamiento con fichas DEMO desde el navegador");
  await flag.getByLabel("Notas (opcional)").fill("Registro E2E DEMO; sin datos de estudiantes reales.");
  const saved = page.waitForResponse((r) => r.url().endsWith("/interventions") && r.request().method() === "POST");
  await flag.getByRole("button", { name: "Guardar intervención" }).click();
  expect((await saved).status()).toBe(201);
  await expect(flag.getByLabel("Estrategia", { exact: true })).toHaveCount(0);
  // Consultar a través del cliente real autenticado; no se simula ninguna respuesta.
  const interventions = await page.evaluate(async () => {
    const modulePath = "/src/services/api.ts";
    const { api } = await import(modulePath) as typeof import("../src/services/api");
    const flags = await api.get<Array<{ student: { id: string } }>>("/support-flags");
    return api.get<Array<{ strategy: string }>>(`/interventions?student_id=${flags[0]!.student.id}`);
  });
  expect(interventions.some((i) => i.strategy === "Acompañamiento con fichas DEMO desde el navegador")).toBe(true);
  const resolved = page.waitForResponse((r) => r.url().includes("/support-flags/") && r.request().method() === "PATCH");
  await flag.getByRole("button", { name: "Resuelta", exact: true }).click();
  expect((await resolved).status()).toBe(200);
  await expect(page.getByText("No hay alertas con este filtro.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Resueltas", exact: true }).click();
  await expect(flag).toBeVisible();
  await expect(flag.locator("header").getByText("Resuelta", { exact: true })).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "Resueltas", exact: true }).click();
  await expect(flag).toBeVisible();
});

test("idioma declarado guardado y recuperado tras recargar", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Estudiantes", exact: true }).click();
  const rooms = page.getByLabel("Aula", { exact: true });
  await expect(rooms.getByRole("option")).toHaveCount(2);
  await rooms.selectOption({ index: 1 });
  const juan = page.getByRole("row").filter({ has: page.getByRole("cell", { name: "Juan", exact: true }) });
  await juan.getByRole("button", { name: "Configurar idioma" }).click();
  await page.getByLabel("Lengua materna", { exact: true }).selectOption("qu");
  await page.getByLabel("Idioma preferido para aprender", { exact: true }).selectOption("es");
  await page.getByRole("button", { name: "Guardar idioma", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Preferencias guardadas" })).toBeVisible();
  await expect(juan.getByRole("cell", { name: "ES", exact: true })).toBeVisible();
  await page.reload();
  await expect(rooms.getByRole("option")).toHaveCount(2);
  await rooms.selectOption({ index: 1 });
  await juan.getByRole("button", { name: "Configurar idioma" }).click();
  await expect(page.getByLabel("Lengua materna", { exact: true })).toHaveValue("qu");
  await expect(page.getByLabel("Idioma preferido para aprender", { exact: true })).toHaveValue("es");
});

for (const viewport of [{ name: "escritorio", width: 1440, height: 1000 }, { name: "móvil", width: 390, height: 844 }]) {
  test(`diseño adaptable en ${viewport.name}: acceso y navegación sin desbordamiento`, async ({ page }, testInfo) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto("/login");
    const password = page.getByLabel("Contraseña", { exact: true });
    await password.fill("Clave-DEMO-visible");
    await page.getByRole("button", { name: "Mostrar contraseña", exact: true }).click();
    await expect(password).toHaveAttribute("type", "text");
    await page.getByRole("button", { name: "Ocultar contraseña", exact: true }).click();
    await expect(password).toHaveAttribute("type", "password");
    await password.clear();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath("acceso.png"), fullPage: true });
    await login(page);
    await expect(page.getByText("Intentos registrados", { exact: true })).toBeVisible();
    const nav = page.getByRole("navigation", { name: "Principal" });
    await expect(nav.getByRole("link", { name: "Dashboard", exact: true })).toHaveAttribute("aria-current", "page");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath("dashboard.png"), fullPage: true });
    await nav.getByRole("link", { name: "Alertas educativas", exact: true }).click();
    const flag = page.getByRole("article", { name: "Alerta educativa de Juan" });
    await expect(flag.getByRole("heading", { name: "Evidencia", exact: true })).toBeVisible();
    await expect(flag.getByRole("row")).toHaveCount(6);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath("alertas.png"), fullPage: true });
    await nav.getByRole("link", { name: "Mis aulas", exact: true }).click();
    await expect(page).toHaveURL(/\/aulas$/);
    await expect(nav.getByRole("link", { name: "Mis aulas", exact: true })).toHaveAttribute("aria-current", "page");
    await expect(nav.getByRole("link", { name: "Dashboard", exact: true })).not.toHaveAttribute("aria-current", "page");
    if (viewport.name === "móvil") {
      await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
      await nav.getByRole("link", { name: "Dashboard", exact: true }).click();
      await expect(page.getByText("Intentos registrados", { exact: true })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await page.screenshot({ path: testInfo.outputPath("dashboard-oscuro.png"), fullPage: true });
    }
    expect(errors).toEqual([]);
  });
}
