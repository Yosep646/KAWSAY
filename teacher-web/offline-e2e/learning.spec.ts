import { chromium, expect, test, type BrowserContext, type Page } from "@playwright/test";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

const URL = "http://127.0.0.1:15173";
const API = "http://127.0.0.1:18000/api/v1";
const PHRASE = "cuatro montanas de prueba";

async function loginTeacher(page: Page) {
  await page.goto(`${URL}/login`);
  await page.getByLabel("Correo", { exact: true }).fill("maestra@demo.pe");
  await page.getByLabel("Contraseña", { exact: true }).fill("Aula-Multigrado-2026!");
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
}

async function unlock(page: Page, phrase = PHRASE) {
  await page.getByText("Abrir actividades descargadas sin conexión", { exact: true }).click();
  await page.getByLabel("Frase local", { exact: true }).fill(phrase);
  await page.getByRole("button", { name: "Desbloquear actividades", exact: true }).click();
}

test("diez respuestas cifradas sobreviven al cierre total y se sincronizan una sola vez", async ({ request, browser }, testInfo) => {
  // A fresh synthetic student; the teacher creates, approves and publishes through
  // existing API contracts. Student download, answers and teacher view use UI.
  const response = await request.post(`${API}/auth/login`, { data: { email: "maestra@demo.pe", password: "Aula-Multigrado-2026!" } });
  expect(response.ok()).toBe(true);
  const tokens = await response.json();
  const headers = { Authorization: `Bearer ${tokens.access_token}` };
  const rooms = await (await request.get(`${API}/classrooms`, { headers })).json();
  const room = rooms[0];
  const assignments = await (await request.get(`${API}/assignments`, { headers })).json();
  const original = await (await request.get(`${API}/assignments/${assignments[0].id}`, { headers })).json();
  const source = original.variants[0];
  const studentResponse = await request.post(`${API}/students`, { headers, data: { classroom_id: room.id,
    grade_id: source.grade_id, display_name: "Estudiante offline ficticio" } });
  expect(studentResponse.status()).toBe(201);
  const student = await studentResponse.json();
  const created = await request.post(`${API}/assignments`, { headers, data: { classroom_id: room.id,
    title: "Diez sumas sin conexión DEMO", instructions: "Responde diez sumas de prueba.",
    grade_topics: [{ grade_id: source.grade_id, topic_id: source.topic_id }] } });
  expect(created.status()).toBe(201);
  const activity = await created.json();
  const variant = activity.variants[0];
  const path = `${API}/assignments/${activity.id}/variants/${variant.id}`;
  expect((await request.put(`${path}/questions`, { headers, data: { questions: Array.from({ length: 10 }, (_, i) => ({
    type: "NUMERIC", prompt: `Suma offline ${i + 1}: ${i + 1} + 1`, correct_answer: { value: i + 2 }, hints: [], difficulty: 1,
  })) } })).ok()).toBe(true);
  expect((await request.post(`${path}/approve`, { headers })).ok()).toBe(true);
  expect((await request.post(`${API}/assignments/${activity.id}/publish`, { headers })).ok()).toBe(true);
  const profile = mkdtempSync(join(process.env.TEMP ?? tmpdir(), "kw-"));
  let context: BrowserContext | undefined;
  const evidence: Record<string, unknown> = {};
  try {
    context = await chromium.launchPersistentContext(profile, { headless: true });
    let page = await context.newPage();
    await page.goto(`${URL}/login`);
    await page.getByRole("button", { name: "Soy estudiante", exact: true }).click();
    await page.getByLabel("Código de estudiante", { exact: true }).fill(student.login_code);
    await page.getByLabel("PIN", { exact: true }).fill(student.pin);
    await page.getByRole("button", { name: "Ingresar", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Aprender sin conexión", exact: true })).toBeVisible();
    await page.getByLabel("Frase para actividades descargadas", { exact: true }).fill(PHRASE);
    await page.getByLabel("Repetir frase local", { exact: true }).fill(PHRASE);
    await page.getByRole("button", { name: "Descargar y proteger actividades", exact: true }).click();
    await expect(page.getByText(/Actividades protegidas\. Guarda tu frase/)).toBeVisible();
    await page.evaluate(async () => {
      await navigator.serviceWorker.ready;
      if (!navigator.serviceWorker.controller) await new Promise<void>(resolve => navigator.serviceWorker.addEventListener("controllerchange", () => resolve(), { once: true }));
    });
    const link = page.getByRole("listitem").filter({ hasText: "Diez sumas sin conexión DEMO" }).getByRole("link", { name: "Resolver actividad descargada" });
    await link.click();
    const activityUrl = page.url();
    await context.setOffline(true);
    for (let i = 0; i < 10; i++) {
      await expect(page.getByRole("heading", { name: `Suma offline ${i + 1}: ${i + 1} + 1`, exact: true })).toBeVisible();
      await page.getByLabel("Tu respuesta", { exact: true }).fill(String(i + 2));
      await page.getByRole("button", { name: "Guardar en este equipo", exact: true }).click();
    }
    await expect(page.getByText("10 respuestas guardadas en este equipo, pendientes de confirmación.", { exact: true })).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath("diez-respuestas-offline.png"), fullPage: true });
    const plaintext = await page.evaluate(async () => {
      const db = await new Promise<IDBDatabase>((resolve, reject) => {
        const req = indexedDB.open("kawsay-encrypted-offline", 1); req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error);
      });
      const record = await new Promise<unknown>(resolve => { const req = db.transaction("vault").objectStore("vault").get("student"); req.onsuccess = () => resolve(req.result); });
      db.close(); return JSON.stringify(record);
    });
    expect(plaintext).not.toContain("Suma offline");
    expect(plaintext).not.toContain("Estudiante offline ficticio");
    expect(plaintext).not.toContain("attempt.created");
    expect(plaintext).not.toContain(PHRASE);
    await context.close(); context = undefined;
    // A new Chromium process, same disk profile, fully offline from launch.
    context = await chromium.launchPersistentContext(profile, { headless: true, offline: true });
    page = await context.newPage();
    await page.goto(activityUrl);
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByText("Estudiante offline ficticio", { exact: true })).toHaveCount(0);
    await unlock(page, "frase local incorrecta");
    await expect(page.getByRole("alert")).toContainText("no es correcta");
    await page.getByLabel("Frase local", { exact: true }).fill(PHRASE);
    await page.getByRole("button", { name: "Desbloquear actividades", exact: true }).click();
    await expect(page.getByText(/10 respuestas pendientes de confirmación/)).toBeVisible();
    await expect(page.getByRole("link", { name: "Mis aulas", exact: true })).toHaveCount(0);
    await context.setOffline(false);
    await page.getByLabel("Código para sincronizar", { exact: true }).fill(student.login_code);
    await page.getByLabel("PIN para sincronizar", { exact: true }).fill(student.pin);
    await page.getByRole("button", { name: "Verificar sesión para sincronizar", exact: true }).click();
    const sync = page.getByRole("button", { name: "Sincronizar respuestas y actualizar", exact: true });
    await expect(sync).toBeVisible();
    await sync.click();
    await expect(page.getByText("10 respuestas confirmadas. Actividades actualizadas.", { exact: true })).toBeVisible();
    await expect(page.getByText(/0 respuestas pendientes de confirmación/)).toBeVisible();
    await sync.click();
    await expect(page.getByText("0 respuestas confirmadas. Actividades actualizadas.", { exact: true })).toBeVisible();
    const dbResult = execFileSync(process.env.KAWSAY_E2E_PYTHON!, ["-c", `import json,sqlite3,sys; c=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True); r=c.execute('SELECT count(*),count(DISTINCT id),sum(is_correct) FROM learning_attempts WHERE student_user_id=?',(sys.argv[2],)).fetchone(); print(json.dumps(r)); c.close()`, process.env.KAWSAY_E2E_DB!, student.id.replaceAll("-", "")], { encoding: "utf8" }).trim();
    expect(JSON.parse(dbResult)).toEqual([10, 10, 10]);
    evidence.sqlite = JSON.parse(dbResult);
    const teacherContext = await browser.newContext();
    try {
      const teacherPage = await teacherContext.newPage();
      await loginTeacher(teacherPage);
      await expect(teacherPage.getByText("Intentos registrados", { exact: true })).toBeVisible();
      const summary = await (await request.get(`${API}/analytics/classrooms/${room.id}/summary`, { headers })).json();
      const countCard = teacherPage.locator(".stat").filter({ hasText: "Intentos registrados" });
      await expect(countCard).toContainText(String(summary.attempts_total));
      const progress = await (await request.get(`${API}/analytics/classrooms/${room.id}/students/${student.id}/progress`, { headers })).json();
      expect(progress.competencies.some((c: { evidence_count: number; score: number }) => c.evidence_count === 10 && c.score === 1)).toBe(true);
      await teacherPage.screenshot({ path: testInfo.outputPath("docente-resultados.png"), fullPage: true });
      evidence.teacherAttempts = summary.attempts_total;
    } finally { await teacherContext.close(); }
    evidence.offlineAnswers = 10; evidence.fullBrowserRestart = true; evidence.wrongPhraseRejected = true;
    await testInfo.attach("evidencia-offline.json", { body: JSON.stringify(evidence, null, 2), contentType: "application/json" });
  } finally {
    await context?.close();
    rmSync(profile, { recursive: true, force: true });
  }
});
