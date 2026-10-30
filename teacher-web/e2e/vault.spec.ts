import { expect, test } from "@playwright/test";

test("el almacén cifra identidad y respuestas, rechaza otra frase y detecta manipulación", async ({ page }) => {
  await page.goto("/login");
  const result = await page.evaluate(async () => {
    const path = "/src/services/offlineVault.ts";
    const { offlineVault: vault } = await import(/* @vite-ignore */ path);
    await vault.create({ user: { id: "student-a", role: "STUDENT", display_name: "Nombre sintético privado" }, deviceId: "device",
      verifiedAt: Date.now(), tasks: [{ student_assignment_id: "task", title: "Actividad privada", questions: [{ id: "q", type: "NUMERIC", prompt: "2+3", options: null }] }], statuses: {}, pending: [] }, "frase privada de prueba");
    await vault.enqueue("task", "q", { value: 5 });
    vault.lock();
    let locked = false, wrongPhrase = false, wrongOwner = false, protectedPending = false;
    try { await vault.snapshot(); } catch { locked = true; }
    try { await vault.unlock("otra frase equivocada"); } catch { wrongPhrase = true; }
    try { await vault.unlock("frase privada de prueba", "other-user"); } catch { wrongOwner = true; }
    const restored = await vault.unlock("frase privada de prueba");
    try { await vault.removeDownloaded(); } catch { protectedPending = true; }
    const db = await new Promise<IDBDatabase>(resolve => { const req = indexedDB.open("kawsay-encrypted-offline"); req.onsuccess = () => resolve(req.result); });
    const record = await new Promise<Record<string, unknown>>(resolve => { const req = db.transaction("vault").objectStore("vault").get("student"); req.onsuccess = () => resolve(req.result); });
    const raw = JSON.stringify(record);
    const bytes = record.ciphertext as number[]; bytes[0] = (bytes[0] ?? 0) ^ 1;
    await new Promise<void>(resolve => { const tx = db.transaction("vault", "readwrite"); tx.objectStore("vault").put(record); tx.oncomplete = () => resolve(); });
    db.close(); vault.lock();
    let tampered = false;
    try { await vault.unlock("frase privada de prueba"); } catch { tampered = true; }
    return { locked, wrongPhrase, wrongOwner, tampered, protectedPending, pending: restored.pending.length, raw };
  });
  expect(result).toMatchObject({ locked: true, wrongPhrase: true, wrongOwner: true, tampered: true, protectedPending: true, pending: 1 });
  for (const secret of ["Nombre sintético privado", "Actividad privada", "attempt.created", "frase privada de prueba"]) expect(result.raw).not.toContain(secret);
});

test("dos pestañas conservan ambas respuestas sin sobrescribir la cola", async ({ page, context }) => {
  await page.goto("/login");
  await page.evaluate(async () => {
    const path = "/src/services/offlineVault.ts";
    const { offlineVault: vault } = await import(/* @vite-ignore */ path);
    await vault.create({ user: { id: "student", role: "STUDENT", display_name: "Ficticio" }, deviceId: "device", verifiedAt: Date.now(),
      tasks: [{ student_assignment_id: "task", title: "Prueba", questions: ["q1", "q2"].map(id => ({ id, type: "NUMERIC", prompt: id, options: null })) }], statuses: {}, pending: [] }, "frase local de prueba");
  });
  const second = await context.newPage(); await second.goto("/login");
  await second.evaluate(async () => { const path = "/src/services/offlineVault.ts"; const { offlineVault } = await import(/* @vite-ignore */ path); await offlineVault.unlock("frase local de prueba"); });
  await Promise.all([page, second].map((tab, index) => tab.evaluate(async question => {
    const path = "/src/services/offlineVault.ts"; const { offlineVault } = await import(/* @vite-ignore */ path); await offlineVault.enqueue("task", question, { value: 5 });
  }, `q${index + 1}`)));
  const questions = await page.evaluate(async () => {
    const path = "/src/services/offlineVault.ts"; const { offlineVault } = await import(/* @vite-ignore */ path);
    return (await offlineVault.snapshot()).pending.map((p: { event: { payload: { question_id: string } } }) => p.event.payload.question_id).sort();
  });
  expect(questions).toEqual(["q1", "q2"]);
});

test("el acceso local vencido conserva la cola y exige renovación con la misma cuenta", async ({ page }) => {
  await page.goto("/login");
  const result = await page.evaluate(async () => {
    const path = "/src/services/offlineVault.ts"; const { offlineVault: vault } = await import(/* @vite-ignore */ path);
    await vault.create({ user: { id: "student", role: "STUDENT", display_name: "Ficticio" }, deviceId: "device", verifiedAt: Date.now() - 8 * 86400000,
      tasks: [], statuses: {}, pending: [{ key: "student:task", deviceId: "device", event: { event_id: "saved", type: "attempt.created", payload: {} } }] }, "frase local de prueba");
    vault.lock();
    let expired = false;
    try { await vault.unlock("frase local de prueba"); } catch { expired = true; }
    const renewed = await vault.unlock("frase local de prueba", "student");
    return { expired, pending: renewed.pending.length, renewed: Date.now() - renewed.verifiedAt < 5000 };
  });
  expect(result).toEqual({ expired: true, pending: 1, renewed: true });
});
