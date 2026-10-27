import { useEffect, useState } from "react";
import { FlagCard } from "../components/FlagCard";
import { Card, ErrorBox, Loading } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import type { Classroom, CompetencyProgress, Forecast, Strength, Summary, SupportFlag } from "../types/api";
import { percent } from "../utils/format";
import { Link } from "react-router-dom";
import { Icon, type IconName } from "../components/Icon";

export function Dashboard() {
  const rooms = useAsync(() => api.get<Classroom[]>("/classrooms"), []);
  const [roomId, setRoomId] = useState<string>("");
  useEffect(() => { if (!roomId && rooms.data?.[0]) setRoomId(rooms.data[0].id); }, [rooms.data, roomId]);

  return (
    <div>
      <div className="page-heading"><div><p className="eyebrow">UNA MIRADA A TU AULA</p><h2>Dashboard</h2><p className="muted">Reconoce los avances. Encuentra dónde acompañar.</p></div><div className="teacher-dashboard-actions"><Link className="button teacher-register-action" to="/estudiantes"><Icon name="students" /> Registrar estudiante</Link><Link className="button" to="/actividades/nueva"><Icon name="tasks" /> Crear actividad</Link></div></div>
      <div className="welcome-banner"><span className="welcome-icon"><Icon name="leaf" /></span><div><h3>Pequeños avances, grandes oportunidades.</h3><p>Tu mirada hace la diferencia. Aquí encontrarás evidencia para acompañar a cada estudiante.</p></div><span className="banner-tag">El docente decide</span></div>
      <ErrorBox message={rooms.error} />
      <div className="room-selector">
      {rooms.loading ? <Loading /> : rooms.data?.length === 0 ? <p>Aún no tienes aulas. Crea una en «Mis aulas».</p> : (
        <label>Aula<select value={roomId} onChange={(e) => setRoomId(e.target.value)}>
          {rooms.data?.map((r) => <option key={r.id} value={r.id}>{r.name} ({r.academic_year})</option>)}
        </select></label>
      )}
      <span className="muted selector-note">La información corresponde al aula seleccionada.</span>
      </div>
      {roomId && <RoomPanel key={roomId} roomId={roomId} />}
    </div>
  );
}

function RoomPanel({ roomId }: { roomId: string }) {
  const summary = useAsync(() => api.get<Summary>(`/analytics/classrooms/${roomId}/summary`), [roomId]);
  const flags = useAsync(() => api.get<SupportFlag[]>(`/support-flags?classroom_id=${roomId}`), [roomId]);
  const strengths = useAsync(() => api.get<Strength[]>(`/analytics/classrooms/${roomId}/strengths`), [roomId]);
  const forecast = useAsync(() => api.get<Forecast>(`/analytics/classrooms/${roomId}/forecast`), [roomId]);
  const [progressFor, setProgressFor] = useState<string | null>(null);
  const active = flags.data?.filter((f) => f.status === "OPEN" || f.status === "ACKNOWLEDGED") ?? [];
  const reloadAll = () => { void flags.reload(); void summary.reload(); void strengths.reload(); void forecast.reload(); };

  return (
    <>
      <div className="room-selector"><p className="muted">Datos consultados al servidor del aula.</p><button className="ghost" onClick={reloadAll} disabled={summary.loading || flags.loading || strengths.loading || forecast.loading}>Actualizar datos</button></div>
      <ErrorBox message={summary.error} />
      {summary.loading && <Loading />}
      {summary.data && (
        <div className="stats-grid">
          <Stat label="Estudiantes" value={summary.data.students_total} icon="students" />
          <Stat label="Con actividad" value={summary.data.students_with_activity} icon="activity" />
          <Stat label="Intentos registrados" value={summary.data.attempts_total} icon="book" />
          <Stat label="Tareas publicadas" value={summary.data.published_assignments} icon="tasks" />
          <Stat label="Alertas activas" value={summary.data.open_support_flags} icon="alert" warn />
        </div>
      )}
      {summary.data && Object.keys(summary.data.students_by_grade).length > 0 && (
        <div className="grade-distribution"><span className="muted">Distribución por grado</span>{Object.entries(summary.data.students_by_grade).map(([g, n]) => <span className="grade-chip" key={g}>{g}<strong>{n}</strong></span>)}</div>
      )}
      <div className="dashboard-columns"><div>
      <Card title="Alertas educativas" actions={<Link className="text-link" to="/alertas">Ver todas <Icon name="arrow" /></Link>}>
        <p className="section-description">Señales para acompañar, con evidencia que puedes revisar.</p>
        <ErrorBox message={flags.error} />
        {flags.loading ? <Loading /> : flags.error ? null : active.length === 0 ? <p className="muted">No hay alertas activas. Aparecerán solo cuando exista evidencia suficiente.</p> :
          active.map((f) => (
            <div key={f.id}>
              <FlagCard flag={f} onChanged={reloadAll} />
              <button className="ghost progress-action" onClick={() => setProgressFor(f.student.id)}><Icon name="activity" />VER PROGRESO</button>
            </div>
          ))}
      </Card>
      {progressFor && <ProgressPanel roomId={roomId} studentId={progressFor} onClose={() => setProgressFor(null)} />}
      </div><div className="dashboard-aside">
      <Card title="Fortalezas observadas">
        <div className="aside-illustration"><Icon name="spark" /></div>
        <p className="section-description">También importa reconocer lo que va bien.</p>
        <ErrorBox message={strengths.error} />
        {strengths.loading ? <Loading /> : strengths.error ? null : (strengths.data?.length ?? 0) === 0 ? <p className="muted">Aún no hay evidencia suficiente de fortalezas.</p> : (
          <ul className="strengths-list">{strengths.data?.map((s, i) => <li key={i}><span className="strength-dot"><Icon name="check" /></span><div><strong>{s.student.display_name}</strong><small>{s.student.grade} · {s.competency.name}</small><p>{s.strengths.map((x) => x.name.replace(/_/g, " ")).join(", ")}</p></div></li>)}</ul>
        )}
      </Card>
      <Card title="Pronóstico de apoyo (ML, opcional)">
        <span className="badge muted">Herramienta complementaria</span>
        <ErrorBox message={forecast.error} />
        {forecast.loading ? <Loading /> : forecast.error ? <p className="muted">Las alertas por reglas siguen funcionando.</p> : !forecast.data?.available ? <p className="muted">{forecast.data?.reason ?? "No disponible."} Las alertas por reglas siguen funcionando.</p> : forecast.data.items.length === 0
          ? <p className="muted">Aún no hay suficientes ejercicios para estimar.</p> : (
            <>
              {forecast.data.experimental && <p role="alert" className="notice warn">Modelo EXPERIMENTAL no aprobado: solo demostración, no usar para decidir.</p>}
              <ul>{forecast.data.items.map((f) => <li key={f.student.id + f.competency.id}><strong>{f.student.display_name}</strong> · {f.competency.name}: probabilidad estimada de dificultad {Math.round(f.probability * 100)} %{f.above_threshold ? " (revisar)" : ""}<small className="muted"> · Modelo {f.model_id} · {f.model_status}</small></li>)}</ul>
              <p className="muted">{forecast.data.items[0]?.advisory}</p>
            </>)}
      </Card>
      </div></div>
    </>
  );
}

const Stat = ({ label, value, icon, warn = false }: { label: string; value: number; icon: IconName; warn?: boolean }) => <div className={`stat${warn ? " stat-warn" : ""}`}><span className="stat-icon"><Icon name={icon} /></span><div className="stat-n">{value}</div><div className="muted">{label}</div></div>;

function ProgressPanel({ roomId, studentId, onClose }: { roomId: string; studentId: string; onClose: () => void }) {
  const p = useAsync(() => api.get<{ competencies: CompetencyProgress[] }>(`/analytics/classrooms/${roomId}/students/${studentId}/progress`), [roomId, studentId]);
  return (
    <Card title="Progreso por competencia" actions={<button className="ghost" onClick={onClose}>Cerrar</button>}>
      <ErrorBox message={p.error} />
      {p.loading ? <Loading /> : (
        <div className="table-wrap"><table><thead><tr><th>Competencia</th><th>Progreso</th><th>Evidencia</th><th>Sugerencia para el docente</th></tr></thead>
          <tbody>{p.data?.competencies.map((c) => (
            <tr key={c.competency_id}><td>{c.name}</td>
              <td>{c.score === null ? percent(null) : <><meter min={0} max={1} value={c.score} /> {percent(c.score)}</>}</td>
              <td>{c.evidence_count} ejercicios</td><td>{c.difficulty_recommendation ? <>{c.difficulty_recommendation.reason}{c.difficulty_recommendation.suggested_difficulty !== null && <> Nivel sugerido: {c.difficulty_recommendation.suggested_difficulty} de 3.</>} <small>Recomendación por reglas; el docente decide.</small></> : 'No disponible'}</td></tr>))}
           </tbody></table></div>
      )}
    </Card>
  );
}
