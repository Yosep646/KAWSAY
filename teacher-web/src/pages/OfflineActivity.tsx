import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { Card, ErrorBox, Loading } from "../components/ui";
import { offlineVault, type VaultData } from "../services/offlineVault";
import { errMsg } from "../utils/format";

export function OfflineActivity() {
  const { id } = useParams();
  const { user } = useAuth();
  const [data, setData] = useState<VaultData | null>(null);
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    if (!offlineVault.isOpen(user?.id)) { setError("Vuelve a tu inicio y desbloquea las actividades descargadas."); return; }
    void offlineVault.snapshot().then(local => { if (!cancelled) setData(local); }).catch(e => { if (!cancelled) setError(errMsg(e)); });
    return () => { cancelled = true; };
  }, [id, user?.id]);
  const task = data?.tasks.find(t => t.student_assignment_id === id);
  const current = task?.questions.find(q => !data?.statuses[id!]?.find(s => s.question_id === q.id)?.closed
    && !data?.pending.some(p => p.event.payload.student_assignment_id === id && p.event.payload.question_id === q.id));
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!id || !current || busy || !value.trim()) return;
    setBusy(true); setError(null);
    try {
      const answer = current.type === "MULTIPLE_CHOICE" ? { index: Number(value) }
        : current.type === "NUMERIC" ? { value: Number(value.replace(",", ".")) } : { text: value.trim() };
      if (current.type === "NUMERIC" && !Number.isFinite((answer as { value: number }).value)) throw new Error("Escribe un número válido.");
      setData(await offlineVault.enqueue(id, current.id, answer)); setValue("");
    } catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  }
  return <div><Link to="/estudiante">← Volver a mi inicio</Link><ErrorBox message={error} />
    {!data && !error ? <Loading /> : task ? <Card title={task.title}>
      <p>{task.instructions}</p><p role="status">{data?.pending.filter(p => p.event.payload.student_assignment_id === id).length} respuestas guardadas en este equipo, pendientes de confirmación.</p>
      {current ? <form className="stack" onSubmit={e => void submit(e)}><h3>{current.prompt}</h3>
        {current.type === "MULTIPLE_CHOICE" ? current.options?.map((option, index) => <label className="inline" key={index}>
          <input type="radio" name="answer" required value={index} checked={value === String(index)} onChange={e => setValue(e.target.value)} />{option}</label>)
          : <label>Tu respuesta<input required value={value} onChange={e => setValue(e.target.value)} /></label>}
        <button disabled={busy}>{busy ? "Guardando…" : "Guardar en este equipo"}</button>
      </form> : <p>No quedan preguntas por responder en este equipo. Sincroniza para consultar el resultado oficial.</p>}
    </Card> : !error && <p>Esta actividad no está descargada para tu cuenta.</p>}
  </div>;
}
