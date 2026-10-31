import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FlagCard } from "../components/FlagCard";
import { ErrorBox, Loading } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import type { SupportFlag } from "../types/api";

interface TutorSupportRequest {
  id: string; student: string; assignment_title: string;
  reason: string; requested_at: string; requires_teacher_decision: boolean;
}

const FILTERS = [["", "Todas"], ["OPEN", "Nuevas"], ["ACKNOWLEDGED", "En seguimiento"], ["RESOLVED", "Resueltas"], ["DISMISSED", "Descartadas"]] as const;

export function Alerts() {
  const [status, setStatus] = useState("");
  const tutor = useAsync(() => api.get<TutorSupportRequest[]>("/tutor/help-requests"), []);
  const flags = useAsync(() => api.get<SupportFlag[]>(`/support-flags${status ? `?status=${status}` : ""}`), [status]);
  // Las solicitudes reales del Tutor IA se actualizan automáticamente mientras
  // el panel está abierto; no se consulta si la pestaña está oculta.
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (!document.hidden) void tutor.reload();
    }, 30000);
    return () => window.clearInterval(timer);
  }, [tutor.reload]);
  return (
    <div>
      <h2>Alertas educativas</h2>
      <p className="muted">KAWSAY muestra la evidencia que hay detrás de cada alerta. No son diagnósticos: tú decides cómo acompañar.</p>
      <section aria-labelledby="tutor-help-heading" className="card">
        <div className="card-h">
          <h3 id="tutor-help-heading">Solicitudes de apoyo del Tutor KAWSAY</h3>
          <button type="button" className="ghost" disabled={tutor.loading} onClick={() => void tutor.reload()}>Actualizar</button>
        </div>
        <p className="muted">Aparecen cuando un estudiante pide al menos dos niveles de ayuda. El panel se actualiza automáticamente cada 30 segundos mientras está abierto. Es una señal para acompañar, no un diagnóstico automático de ML.</p>
        <ErrorBox message={tutor.error} />
        {tutor.loading ? <Loading /> : !tutor.data?.length
          ? <p className="muted">Todavía no hay solicitudes de apoyo registradas.</p>
          : <ul className="tutor-request-list">{tutor.data.map(item => <li key={item.id}>
              <strong>{item.student}</strong> · {item.assignment_title}
              <p>{item.reason}</p>
              <Link to="/estudiantes">Consultar estudiantes y planificar apoyo</Link>
            </li>)}</ul>}
      </section>
      <div className="row">{FILTERS.map(([v, l]) => <button key={v} className={status === v ? "" : "ghost"} onClick={() => setStatus(v)}>{l}</button>)}</div>
      <ErrorBox message={flags.error} />
      {flags.loading ? <Loading /> : (flags.data?.length ?? 0) === 0 ? <p className="muted">No hay alertas con este filtro.</p> : flags.data?.map((f) => <FlagCard key={f.id} flag={f} onChanged={() => void flags.reload()} />)}
    </div>
  );
}
