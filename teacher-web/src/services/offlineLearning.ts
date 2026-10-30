import { api } from "./api";
import { offlineVault, type LocalTask, type QuestionStatus, type VaultData } from "./offlineVault";

export async function downloadStudentTasks(deviceId: string): Promise<Pick<VaultData, "tasks" | "statuses">> {
  const tasks: LocalTask[] = [];
  const statuses: Record<string, QuestionStatus[]> = {};
  let cursor = 0;
  for (;;) {
    const page = await api.get<{ tasks: LocalTask[]; cursor: number; has_more: boolean }>(`/sync/pull?cursor=${cursor}&limit=50`);
    // Store the presentation contract only, excluding answer keys and translations
    // that the current interface cannot render or verify.
    for (const task of page.tasks) {
      tasks.push({ student_assignment_id: task.student_assignment_id, title: task.title, subject: task.subject,
        instructions: task.instructions, questions: task.questions.map(q => ({ id: q.id, type: q.type, prompt: q.prompt, options: q.options })) });
      statuses[task.student_assignment_id] = (await api.get<{ questions: QuestionStatus[] }>(
        `/sync/tasks/${task.student_assignment_id}/attempts?device_id=${deviceId}`)).questions;
    }
    if (!page.has_more) break;
    if (page.cursor <= cursor) throw new Error("El servidor no permite continuar la descarga.");
    cursor = page.cursor;
  }
  return { tasks, statuses };
}

export async function synchronizeOffline(studentId: string): Promise<number> {
  if (!offlineVault.isOpen(studentId)) throw new Error("Desbloquea las actividades de esta cuenta antes de sincronizar.");
  // Always verify the actual server identity, including after reconnecting.
  const me = await api.get<{ id: string; role: string }>("/auth/me");
  if (me.id !== studentId || me.role !== "STUDENT") throw new Error("Inicia sesión con la cuenta que descargó estas actividades.");
  const snapshot = await offlineVault.snapshot();
  const pending = snapshot.pending;
  let confirmed = 0;
  for (let offset = 0; offset < pending.length; offset += 100) {
    const batch = pending.slice(offset, offset + 100);
    const response = await api.post<{ results: { event_id: string; status: string; reason?: string }[] }>("/sync/push",
      { device_id: snapshot.deviceId, events: batch.map(p => p.event) });
    const ids = new Set(batch.map(p => p.event.event_id));
    if (!Array.isArray(response.results) || response.results.length !== batch.length
        || new Set(response.results.map(r => r.event_id)).size !== batch.length
        || response.results.some(r => !ids.has(r.event_id) || !["ACKED", "DUPLICATE", "REJECTED"].includes(r.status))) {
      throw new Error("Confirmación inválida del servidor. Se conservan las respuestas para reintentar.");
    }
    const accepted = new Set(response.results.filter(r => ["ACKED", "DUPLICATE"].includes(r.status)).map(r => r.event_id));
    // Status fetch happens before removal: interruption leaves the events retryable.
    const states: Record<string, QuestionStatus[]> = {};
    for (const taskId of new Set(batch.map(p => String(p.event.payload.student_assignment_id)))) {
      states[taskId] = (await api.get<{ questions: QuestionStatus[] }>(`/sync/tasks/${taskId}/attempts?device_id=${snapshot.deviceId}`)).questions;
    }
    await offlineVault.update(data => {
      data.pending = data.pending.filter(p => !accepted.has(p.event.event_id));
      Object.assign(data.statuses, states);
      data.verifiedAt = Date.now();
    });
    confirmed += accepted.size;
    if (response.results.some(r => r.status === "REJECTED")) {
      throw new Error("Algunas respuestas requieren revisión docente. Se conservan localmente y no se cuentan como confirmadas.");
    }
  }
  return confirmed;
}
