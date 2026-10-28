import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { Card, ErrorBox, Loading } from "../components/ui";
import { api } from "../services/api";
import { pendingAttempts, type PendingAttempt } from "../services/pendingAttempts";
import { offlineTasks } from "../services/offlineTasks";
import { errMsg } from "../utils/format";
import "./student-activity-exercises.css";

type Question = { id: string; type: "MULTIPLE_CHOICE" | "NUMERIC" | "SHORT_TEXT"; prompt: string; options: string[] | null };
type Task = { student_assignment_id: string; title: string; instructions?: string; questions: Question[] };
type Status = { question_id: string; closed: boolean; device_attempt_number: number };

export function StudentActivity() {
  const { id } = useParams();
  const { user } = useAuth();
  const key = user && id ? `${user.id}:${id}` : null;
  const device = (() => {
    // La sesión restaurada puede no tener un identificador de dispositivo inicializado.
    let id = localStorage.getItem("kawsay_web_device_id");
    if (!id) { id = crypto.randomUUID(); localStorage.setItem("kawsay_web_device_id", id); }
    return id;
  })();
  const [task, setTask] = useState<Task | null>(null);
  const [statuses, setStatuses] = useState<Status[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<PendingAttempt[]>([]);
  const attempted = useRef(new Set<string>());
  const sending = useRef(false);
  const [message, setMessage] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);
  const [online, setOnline] = useState(typeof navigator !== "undefined" ? navigator.onLine : true);
  useEffect(() => { const onNetwork = () => setOnline(navigator.onLine); window.addEventListener("online", onNetwork); window.addEventListener("offline", onNetwork); return () => { window.removeEventListener("online", onNetwork); window.removeEventListener("offline", onNetwork); }; }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!id || !device || !key) throw new Error("No se encontró la actividad o el dispositivo.");
      const saved = await pendingAttempts.list(key);
      if (!cancelled) setPending(saved);
      // Cargar primero el contenido descargado para poder trabajar sin conexión.
      const local = await offlineTasks.list(user!.id);
      const cached = local.find(t => t.student_assignment_id === id);
      if (cached?.questions?.length && !cancelled) setTask(cached as Task);
      try {
        let cursor = 0;
        while (true) {
          const page = await api.get<{ tasks: Task[]; cursor: number; has_more: boolean }>(`/sync/pull?cursor=${cursor}&limit=50`);
          const found = page.tasks.find(t => t.student_assignment_id === id);
          if (found) {
            await offlineTasks.save(user!.id, [found]);
            const status = await api.get<{ questions: Status[] }>(`/sync/tasks/${id}/attempts?device_id=${device}`);
            if (!cancelled) { setTask(found); setStatuses(status.questions); setOffline(false); }
            return;
          }
          if (!page.has_more || page.cursor <= cursor) throw new Error("No se encontró la actividad.");
          cursor = page.cursor;
        }
      } catch (networkError) {
        if (cached?.questions?.length) { if (!cancelled) setOffline(true); return; }
        throw networkError;
      }
    }
    void load().catch(e => { if (!cancelled) setError(errMsg(e)); }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id, device, key]);

  const current = task?.questions.find(q => !statuses.find(s => s.question_id === q.id)?.closed && !pending.some(p => p.event.payload.question_id === q.id));
  const completedCount = task ? task.questions.filter(q => statuses.some(s => s.question_id === q.id && s.closed) || pending.some(p => p.event.payload.question_id === q.id)).length : 0;
  const send = async (record: PendingAttempt) => {
    if (!device || !id || sending.current) return;
    sending.current = true;
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
      setStatuses(state.questions); setPending(old => old.filter(p => p.event.event_id !== event.event_id)); setValue("");
      setOffline(false); setMessage("Respuesta guardada en el servidor.");
    } catch (e) { setOffline(true); setMessage("Respuesta conservada en este dispositivo. Reintenta cuando recuperes la conexión."); setError(errMsg(e)); } finally { sending.current = false; setBusy(false); }
  };
  // Procesa secuencialmente la cola; cada evento mantiene su ID durante reintentos.
  useEffect(() => {
    if (!pending.length || !online || busy || loading) return;
    const next = pending.find(p => !attempted.current.has(p.event.event_id));
    if (next) { attempted.current.add(next.event.event_id); void send(next); }
  }, [online, pending, loading, busy]);
  useEffect(() => { if (!online) attempted.current.clear(); }, [online]);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!current || !id || !device || !key || busy || !value.trim()) return;
    const answer = current.type === "MULTIPLE_CHOICE" ? { index: Number(value) } : current.type === "NUMERIC" ? { value: Number(value.replace(",", ".")) } : { text: value };
    if (current.type === "NUMERIC" && !Number.isFinite((answer as { value: number }).value)) { setError("Escribe un número válido."); return; }
    const n = (statuses.find(s => s.question_id === current.id)?.device_attempt_number ?? 0) + pending.filter(p => p.event.payload.question_id === current.id).length + 1;
    const event = { event_id: crypto.randomUUID(), type: "attempt.created", payload: { student_assignment_id: id, question_id: current.id, attempt_number: n, answer, hints_used: 0, response_time_ms: 0, client_created_at: new Date().toISOString() } };
    const record = { key, deviceId: device, event };
    setBusy(true);
    try { await pendingAttempts.add(record); setPending(old => [...old, record]); setValue(""); }
    catch (e) { setError(errMsg(e)); setBusy(false); return; }
    setBusy(false);
    // El envío se hace después de que IndexedDB confirme la escritura.
    // El efecto de cola inicia el envío tras confirmar la escritura. No duplica peticiones.
  };
  return <div><Link to="/estudiante">← Volver a mi inicio</Link><ErrorBox message={error} />{loading ? <Loading /> : task && <Card title={task.title}>
    <p role="status" className={`connection-status ${online && !offline ? "connected" : "disconnected"}`}>{offline || !online ? "Sin conexión con el servidor. Tus respuestas se guardan en este dispositivo." : "Conectado: tus entregas se confirmarán en el servidor."}</p>
    {task.instructions?.trim() && <section className="student-activity-instructions" aria-label="Indicaciones de la actividad"><h3>Indicaciones del docente</h3><p>{task.instructions}</p></section>}
    {message && <p role="status">{message}</p>}
    {pending.length > 0 && <><p role="status">{pending.length} respuesta(s) pendientes. Puedes seguir resolviendo otras preguntas.</p><button type="button" disabled={!online || busy} onClick={() => { const next = pending[0]; if (!next) return; attempted.current.clear(); void send(next); }}>Reintentar sincronización</button></>}
    {current ? <form className="stack" onSubmit={e => void submit(e)}><div className="question-progress">Pregunta {task.questions.findIndex(q => q.id === current.id) + 1} de {task.questions.length}</div><div className="activity-progress-track" role="progressbar" aria-label="Preguntas confirmadas" aria-valuemin={0} aria-valuemax={task.questions.length} aria-valuenow={completedCount}><span style={{width:`${Math.round(completedCount / task.questions.length * 100)}%`}} /></div><h3>{current.prompt}</h3>
      {current.type === "MULTIPLE_CHOICE" ? current.options?.map((option, i) => <label className="inline" key={i}><input type="radio" name="answer" value={String(i)} checked={value === String(i)} onChange={e => setValue(e.target.value)} />{option}</label>) : <label>Tu respuesta<input value={value} onChange={e => setValue(e.target.value)} required /></label>}
      <button disabled={busy}>Guardar respuesta localmente</button>
    </form> : pending.length > 0 ? <p>Tus respuestas están guardadas en este dispositivo. Se enviarán cuando vuelva la conexión.</p> : <p>Terminaste los ejercicios disponibles.</p>}
  </Card>}</div>;
}
