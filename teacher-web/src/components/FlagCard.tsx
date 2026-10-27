import { useState } from "react";
import { api } from "../services/api";
import type { SupportFlag } from "../types/api";
import { errMsg } from "../utils/format";
import { Badge, ErrorBox } from "./ui";

interface Props { flag: SupportFlag; onChanged: () => void }

export function FlagCard({ flag, onChanged }: Props) {
  const [showForm, setShowForm] = useState(false);
  const [strategy, setStrategy] = useState("");
  const [notes, setNotes] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const e = flag.evidence;
  const statusLabel = { OPEN: "Nueva", ACKNOWLEDGED: "En seguimiento", RESOLVED: "Resuelta", DISMISSED: "Descartada" }[flag.status];

  const act = async (fn: () => Promise<unknown>) => { try { setErr(null); await fn(); onChanged(); } catch (x) { setErr(errMsg(x)); } };
  const intervene = () => act(async () => {
    await api.post("/interventions", { student_id: flag.student.id, competency_id: flag.competency.id, strategy, notes: notes || null, support_flag_id: flag.id });
    setShowForm(false); setStrategy(""); setNotes("");
  });

  return (
    <article className="flag" aria-label={`Alerta educativa de ${flag.student.display_name}`}>
      <header>
        <strong>ATENCIÓN RECOMENDADA</strong>{" "}
        <Badge tone={flag.status === "OPEN" ? "warn" : flag.status === "RESOLVED" ? "ok" : "info"}>{statusLabel}</Badge>
      </header>
      <dl className="kv">
        <dt>Estudiante</dt><dd>{flag.student.display_name}</dd>
        <dt>Grado</dt><dd>{flag.student.grade ?? "—"}</dd>
        <dt>Competencia</dt><dd>{flag.competency.name}</dd>
        <dt>Temas</dt><dd>{e.topics.join(", ") || "—"}</dd>
      </dl>
      <p>{flag.message}</p>
      <h4>Evidencia</h4>
      <ul>
        <li>{e.difficult} de los últimos {e.window} ejercicios presentan dificultad.</li>
        <li>{e.hints_total} pistas utilizadas · {e.wrong_attempts_total} intentos incorrectos.</li>
        <li>Patrón observado en {e.distinct_days} día(s). Regla {flag.rule_id} v{flag.rule_version}.</li>
      </ul>
      <div className="table-wrap" tabIndex={0} role="region" aria-label="Detalle de la evidencia"><table className="evidence">
        <thead><tr><th>Ejercicio (tema)</th><th>Intentos</th><th>Pistas</th><th>Resultado</th></tr></thead>
        <tbody>
          {e.results.map((r) => (
            <tr key={r.question_id}><td>{r.topic ?? "—"}</td><td>{r.attempts}</td><td>{r.hints}</td><td>{r.correct ? (r.score <= 0.4 ? "Correcto con mucha ayuda" : "Correcto") : "Sin acierto"}</td></tr>
          ))}
        </tbody>
      </table></div>
      <p className="muted">Recomendación: {flag.recommendation ?? "—"} El docente decide qué hacer. Esto no es un diagnóstico.</p>
      <ErrorBox message={err} />
      <div className="row">
        <button onClick={() => setShowForm((s) => !s)}>REGISTRAR INTERVENCIÓN</button>
        {flag.status === "OPEN" && <button className="ghost" onClick={() => act(() => api.patch(`/support-flags/${flag.id}`, { status: "ACKNOWLEDGED" }))}>Marcar como vista</button>}
        <button className="ghost" onClick={() => act(() => api.patch(`/support-flags/${flag.id}`, { status: "RESOLVED" }))}>Resuelta</button>
        <button className="ghost" onClick={() => act(() => api.patch(`/support-flags/${flag.id}`, { status: "DISMISSED" }))}>Descartar</button>
      </div>
      {showForm && (
        <form className="stack" onSubmit={(ev) => { ev.preventDefault(); void intervene(); }}>
          <label>Estrategia<input value={strategy} onChange={(x) => setStrategy(x.target.value)} minLength={3} maxLength={300} required /></label>
          <label>Notas (opcional)<textarea value={notes} onChange={(x) => setNotes(x.target.value)} maxLength={3000} /></label>
          <button type="submit">Guardar intervención</button>
        </form>
      )}
    </article>
  );
}
