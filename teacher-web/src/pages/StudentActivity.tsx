import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { Card, ErrorBox, Loading } from "../components/ui";
import { api } from "../services/api";
import { pendingAttempts, type PendingAttempt } from "../services/pendingAttempts";
import { errMsg } from "../utils/format";
import { offlineVault } from "../services/offlineVault";

type Question = { id: string; type: "MULTIPLE_CHOICE" | "NUMERIC" | "SHORT_TEXT"; prompt: string; options: string[] | null };
type Task = { student_assignment_id: string; title: string; questions: Question[] };
type Status = { question_id: string; closed: boolean; device_attempt_number: number };

export function StudentActivity() {
  const { id } = useParams();
  const { user } = useAuth();
  if (user && offlineVault.isOpen(user.id)) return <Navigate to={`/estudiante/descargada/${id}`} replace />;
  return <OnlineStudentActivity />;
}

function OnlineStudentActivity() {
  const { id } = useParams();
  const { user } = useAuth();
  const key = user && id ? `${user.id}:${id}` : null;
  const device = localStorage.getItem("kawsay_web_device_id");
  const [task, setTask] = useState<Task | null>(null);
  const [statuses, setStatuses] = useState<Status[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<PendingAttempt | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!id || !device || !key) throw new Error("No se encontró la actividad o el dispositivo.");
      const saved = await pendingAttempts.get(key);
      if (!cancelled && saved) setPending(saved);
      let cursor = 0;
      while (true) {
        const page = await api.get<{ tasks: Task[]; cursor: number; has_more: boolean }>(`/sync/pull?cursor=${cursor}&limit=50`);
        const found = page.tasks.find(t => t.student_assignment_id === id);
        if (found) {
          const status = await api.get<{ questions: Status[] }>(`/sync/tasks/${id}/attempts?device_id=${device}`);
          if (!cancelled) { setTask(found); setStatuses(status.questions); }
          return;
        }
        if (!page.has_more || page.cursor <= cursor) throw new Error("No se encontró la actividad.");
        cursor = page.cursor;
      }
    }
    void load().catch(e => { if (!cancelled) setError(errMsg(e)); }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id, device, key]);

  const current = task?.questions.find(q => !statuses.find(s => s.question_id === q.id)?.closed);
  const send = async (record: PendingAttempt) => {
    if (!device || !id || busy) return;
    setBusy(true); setError(null);
    try {
      const event = record.event;
      const result = await api.post<{ results: { event_id: string; status: string; reason?: string }[] }>("/sync/push", { device_id: record.deviceId, events: [event] });
      const ack = result.results?.[0];
      if (result.results?.length !== 1 || ack?.event_id !== event.event_id || !["ACKED", "DUPLICATE"].includes(ack.status)) {
        throw new Error("No se confirmó la respuesta. Solicita ayuda al docente antes de volver a intentarlo.");
      }
      const state = await api.get<{ questions: Status[] }>(`/sync/tasks/${id}/attempts?device_id=${device}`);
      const removed = await pendingAttempts.removeConfirmed(record.key, event.event_id);
      if (!removed) throw new Error("La respuesta pendiente cambió en otra pestaña. Recarga la actividad para revisarla.");
      setStatuses(state.questions); setPending(null); setValue("");
      setMessage("Respuesta guardada en el servidor.");
    } catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!current || !id || !device || !key || pending || busy || !value.trim()) return;
    const answer = current.type === "MULTIPLE_CHOICE" ? { index: Number(value) } : current.type === "NUMERIC" ? { value: Number(value.replace(",", ".")) } : { text: value };
    if (current.type === "NUMERIC" && !Number.isFinite((answer as { value: number }).value)) { setError("Escribe un número válido."); return; }
    const n = (statuses.find(s => s.question_id === current.id)?.device_attempt_number ?? 0) + 1;
    const event = { event_id: crypto.randomUUID(), type: "attempt.created", payload: { student_assignment_id: id, question_id: current.id, attempt_number: n, answer, hints_used: 0, response_time_ms: 0, client_created_at: new Date().toISOString() } };
    const record = { key, deviceId: device, event };
    setBusy(true);
    try { await pendingAttempts.add(record); setPending(record); }
    catch (e) { setError(errMsg(e)); setBusy(false); return; }
    setBusy(false);
    // El envío se hace después de que IndexedDB confirme la escritura.
    void send(record);
  };
  return <div><Link to="/estudiante">← Volver a mi inicio</Link><ErrorBox message={error} />{loading ? <Loading /> : task && <Card title={task.title}>
    <p className="muted">Para abrir actividades necesitas conexión. Una respuesta pendiente se guarda en este navegador; no borres sus datos hasta sincronizarla.</p>
    {message && <p role="status">{message}</p>}
    {pending && <p role="status">Hay una respuesta pendiente de confirmar. Reintenta su envío.</p>}
    {current ? <form className="stack" onSubmit={e => void submit(e)}><h3>{current.prompt}</h3>
      {current.type === "MULTIPLE_CHOICE" ? current.options?.map((option, i) => <label className="inline" key={i}><input type="radio" name="answer" value={String(i)} checked={value === String(i)} onChange={e => setValue(e.target.value)} />{option}</label>) : <label>Tu respuesta<input value={value} onChange={e => setValue(e.target.value)} required /></label>}
      {pending ? <button type="button" disabled={busy} onClick={() => void send(pending)}>Reintentar envío</button> : <button disabled={busy}>Guardar respuesta</button>}
    </form> : pending ? <button type="button" disabled={busy} onClick={() => void send(pending)}>Reintentar envío pendiente</button> : <p>Terminaste los ejercicios disponibles.</p>}
  </Card>}</div>;
}
