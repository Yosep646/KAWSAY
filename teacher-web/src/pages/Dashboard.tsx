import { useEffect, useState } from "react";
import { FlagCard } from "../components/FlagCard";
import { Card, ErrorBox, Loading } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import type { AssignmentBrief, Classroom, CompetencyProgress, Forecast, Strength, Summary, SupportFlag } from "../types/api";
import { percent } from "../utils/format";
import { Link } from "react-router-dom";
import { Icon, type IconName } from "../components/Icon";
import "./teacher-dashboard-v2.css";

export function Dashboard() {
  const rooms = useAsync(() => api.get<Classroom[]>("/classrooms"), []);
  const assignments = useAsync(() => api.get<AssignmentBrief[]>("/assignments"), []);
  const [roomId, setRoomId] = useState<string>("");
  useEffect(() => {
    if (!rooms.data?.length) { if (roomId) setRoomId(""); return; }
    if (!rooms.data.some(room => room.id === roomId)) setRoomId(rooms.data[0]!.id);
  }, [rooms.data, roomId]);
  const hasRooms = (rooms.data?.length ?? 0) > 0;
  const items = assignments.data ?? [];
  const published = items.filter(a => a.status === "PUBLISHED");
  const draftCount = items.filter(a => a.status !== "PUBLISHED").length;
  const currentRoom = rooms.data?.find(r => r.id === roomId);
  const visibleAssignments = items.filter(a => !roomId || a.classroom_id === roomId).slice(0, 4);
  const statCards: { label: string; desc: string; icon: IconName; value: number | undefined; loading: boolean; color: string; to: string }[] = [
    {label:"Aulas registradas",desc:"Mis espacios educativos",icon:"classroom",value:rooms.data?.length,loading:rooms.loading,color:"azure",to:"/aulas"},
    {label:"Actividades creadas",desc:"En mis aulas",icon:"tasks",value:assignments.data?.length,loading:assignments.loading,color:"teal",to:"/actividades"},
    {label:"Tareas publicadas",desc:"Disponibles para estudiantes",icon:"book",value:assignments.data?published.length:undefined,loading:assignments.loading,color:"amber",to:"/actividades"},
    {label:"Por revisar",desc:"Aún no publicadas",icon:"activity",value:assignments.data?draftCount:undefined,loading:assignments.loading,color:"purple",to:"/actividades"},
  ];
  const readySteps = [
    {done:hasRooms,label:"Crear mi primera aula",detail:"Organiza el grupo y su año escolar.",to:"/aulas"},
    {done:items.length>0,label:"Preparar una actividad",detail:"Selecciona un grado y un tema de tu planificación.",to:"/actividades/nueva"},
    {done:published.length>0,label:"Publicar para estudiantes",detail:"Revisa la actividad y habilita su entrega.",to:"/actividades"},
  ];
  const completedSteps = readySteps.filter(s => s.done).length;

  return <div className="teacher-dashboard teacher-v2">
    <header className="teacher-dashboard-hero">
      <div className="teacher-dashboard-intro">
        <p className="eyebrow"><Icon name="leaf" /> ESPACIO DOCENTE · KAWSAY AI</p>
        <h2>Bienvenido, <span>Docente</span></h2>
        <p>Transforma cada clase en una oportunidad para aprender, crecer y acompañar a tu comunidad.</p>
        <div className="teacher-dashboard-actions">
          <Link className="button teacher-register-action" to="/estudiantes">
            <Icon name="students"/> Registrar estudiante
          </Link>
          <Link className="button teacher-outline-action" to="/planificacion"><Icon name="book"/> Mi planificación</Link>
        </div>
        <div className="teacher-hero-meta">
          <span><Icon name="classroom"/> {rooms.loading?"Consultando aulas":`${rooms.data?.length??"—"} aulas`}</span>
          <span><Icon name="leaf"/> Aprender · Crecer · Acompañar</span>
        </div>
      </div>
      <span className="teacher-hero-motto">Educación que acompaña a cada comunidad.</span>
    </header>

    <div className="teacher-v2-section-title">
      <div><p className="teacher-v2-eyebrow">TU ESPACIO EDUCATIVO</p><h3>Resumen general</h3></div>
      <button type="button" className="teacher-v2-refresh" onClick={()=>{void rooms.reload();void assignments.reload();}} disabled={rooms.loading||assignments.loading}><Icon name="refresh"/> Actualizar</button>
    </div>
    <ErrorBox message={rooms.error ?? assignments.error}/>
    <div className="teacher-v2-kpis" aria-label="Indicadores reales del docente">
      {statCards.map(card=><Link key={card.label} to={card.to} className={`teacher-v2-kpi teacher-v2-${card.color}`}>
        <span className="teacher-v2-kpi-icon"><Icon name={card.icon}/></span>
        <span className="teacher-v2-kpi-content"><small>{card.label}</small><strong>{card.loading?"…":card.value===undefined?"—":card.value.toLocaleString("es-PE")}</strong><span>{card.desc}</span></span>
        <Icon name="arrow" />
      </Link>)}
    </div>

    <div className="teacher-v2-overview-grid">
      <section className="teacher-v2-panel teacher-v2-classroom" aria-labelledby="teacher-classroom-heading">
        <div className="teacher-v2-panel-head">
          <div><p className="teacher-v2-eyebrow">GESTIÓN ACADÉMICA</p><h3 id="teacher-classroom-heading">Mis aulas</h3></div>
          <Link to="/aulas" className="teacher-v2-text-link">Ver aulas <Icon name="arrow"/></Link>
        </div>
        {rooms.loading ? <p className="teacher-v2-muted">Cargando aulas…</p> :
          rooms.error ? <p className="teacher-v2-muted">No se pudieron consultar tus aulas.</p> :
          !hasRooms ? <div className="teacher-v2-empty-classroom">
            <span className="teacher-v2-empty-icon"><Icon name="classroom"/></span>
            <div><strong>Tu primera aula empieza aquí</strong><p>Para agregar estudiantes y asignar tareas, primero registra el aula o sección que acompañas.</p></div>
            <Link to="/aulas">Crear aula <Icon name="arrow"/></Link>
          </div> :
          <div className="teacher-v2-classroom-body">
            <label htmlFor="teacher-dashboard-room">Aula seleccionada
              <select id="teacher-dashboard-room" value={roomId} onChange={e=>setRoomId(e.target.value)}>
                {rooms.data?.map(room=><option value={room.id} key={room.id}>{room.name} · {room.academic_year}</option>)}
              </select>
            </label>
            <div className="teacher-v2-current-room"><span><Icon name="classroom"/></span><div><strong>{currentRoom?.name}</strong><small>Año escolar {currentRoom?.academic_year}</small></div><Link to="/estudiantes">Gestionar <Icon name="arrow"/></Link></div>
            <p>Los indicadores y las alertas de aprendizaje se muestran debajo para el aula seleccionada.</p>
          </div>}
      </section>
      <section className="teacher-v2-panel teacher-v2-work" aria-labelledby="teacher-work-heading">
        <div className="teacher-v2-panel-head">
          <div><p className="teacher-v2-eyebrow">ORGANIZACIÓN</p><h3 id="teacher-work-heading">Actividades registradas</h3></div>
          <Link to="/actividades" className="teacher-v2-text-link">Ver todas <Icon name="arrow"/></Link>
        </div>
        {assignments.loading ? <p className="teacher-v2-muted">Cargando actividades…</p> :
          assignments.error ? <p className="teacher-v2-muted">Las actividades no están disponibles.</p> :
          visibleAssignments.length===0 ? <div className="teacher-v2-no-work"><Icon name="tasks"/><strong>Sin actividades registradas en esta aula</strong><p>Prepara tu primera actividad según la planificación del grado.</p><Link to="/actividades/nueva">Crear actividad <Icon name="arrow"/></Link></div> :
          <div className="teacher-v2-assignment-list">{visibleAssignments.map(item=><Link key={item.id} to={`/actividades/${item.id}`}>
            <span className="teacher-v2-assignment-icon"><Icon name="tasks"/></span><span className="teacher-v2-assignment-name"><strong>{item.title}</strong><small>{item.status==="PUBLISHED"?"Publicada":"Pendiente de publicación"}</small></span><Icon name="arrow"/>
          </Link>)}</div>}
      </section>
    </div>

    <div className="teacher-v2-bottom-grid">
      <section className="teacher-v2-panel teacher-v2-roadmap" aria-labelledby="teacher-roadmap-title">
        <div className="teacher-v2-panel-head">
          <div><p className="teacher-v2-eyebrow">ACOMPAÑAMIENTO</p><h3 id="teacher-roadmap-title">Ruta de trabajo</h3></div>
          <span className="teacher-v2-step-count">{rooms.loading||assignments.loading?"Cargando":`${completedSteps} de 3`} pasos</span>
        </div>
        <div className="teacher-v2-track" role="progressbar" aria-label="Pasos de configuración" aria-valuenow={completedSteps} aria-valuemin={0} aria-valuemax={3}><span style={{width:`${completedSteps/3*100}%`}}/></div>
        <div className="teacher-v2-steps">
          {readySteps.map((step,i)=><Link to={step.to} key={step.to} className="teacher-v2-step">
            <span className={`teacher-v2-step-mark ${step.done?"is-done":""}`}>{step.done?<Icon name="check"/>:i+1}</span>
            <span><strong>{step.label}</strong><small>{step.detail}</small></span>
            <Icon name="arrow"/>
          </Link>)}
        </div>
      </section>
      <section className="teacher-v2-panel teacher-v2-tools" aria-labelledby="teacher-tools-title">
        <div className="teacher-v2-panel-head"><div><p className="teacher-v2-eyebrow">HERRAMIENTAS</p><h3 id="teacher-tools-title">Accesos rápidos</h3></div></div>
        <div className="teacher-quick-grid" aria-label="Herramientas del docente">
          <Link to="/estudiantes"><span className="teacher-quick-icon t-emerald"><Icon name="students"/></span><strong>Estudiantes</strong><small>Registro y acceso</small><Icon name="arrow"/></Link>
          <Link to="/planificacion"><span className="teacher-quick-icon t-blue"><Icon name="book"/></span><strong>Malla curricular</strong><small>Word, PDF y planes</small><Icon name="arrow"/></Link>
          <Link to="/actividades/nueva"><span className="teacher-quick-icon t-gold"><Icon name="tasks"/></span><strong>Asignar tareas</strong><small>Actividades por grado</small><Icon name="arrow"/></Link>
          <Link to="/alertas"><span className="teacher-quick-icon t-violet"><Icon name="alert"/></span><strong>Alertas y logros</strong><small>Revisión de evidencia</small><Icon name="arrow"/></Link>
        </div>
      </section>
    </div>

    {roomId && <section className="teacher-v2-learning" aria-label="Indicadores del aula seleccionada">
      <div className="teacher-v2-section-title">
        <div><p className="teacher-v2-eyebrow">DATOS DEL AULA · {currentRoom?.name}</p><h3>Seguimiento del aprendizaje</h3></div>
        <Link to="/alertas" className="teacher-v2-text-link">Revisar alertas <Icon name="arrow"/></Link>
      </div>
      <RoomPanel key={roomId} roomId={roomId}/>
    </section>}
    <div className="teacher-v2-footer"><Icon name="book"/><span><strong>Juntos transformamos comunidades.</strong><small>La tecnología acompaña; cada decisión pedagógica pertenece al docente.</small></span><em>KAWSAY AI</em></div>
  </div>;
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
        {!forecast.loading && !forecast.error && (forecast.data?.guidance?.length ?? 0) > 0 && (
          <section className="teacher-ml-guidance" aria-label="Sugerencias pedagógicas basadas en respuestas reales">
            <h4>Recomendaciones basadas en ejercicios realizados</h4>
            <p>Estas sugerencias por reglas funcionan aun sin modelo ML. No cambian el grado ni asignan actividades automáticamente.</p>
            <ul>{forecast.data?.guidance?.filter(g=>g.action!=="INSUFFICIENT_EVIDENCE").slice(0,8).map(g=>
              <li key={g.student.id+g.competency.id}><strong>{g.student.display_name}</strong>
                <span>{g.competency.name} · {g.evidence_count} ejercicios cerrados</span>
                <p>{g.reason}{g.suggested_difficulty!==null ? ` Dificultad orientativa: ${g.suggested_difficulty} de 3.` : ""}</p>
                <small>Recomendación, no asignación: requiere decisión del docente.</small>
              </li>)}</ul>
            {forecast.data?.guidance?.every(g=>g.action==="INSUFFICIENT_EVIDENCE") &&
              <p>Aún no hay suficiente evidencia para recomendar una dificultad. No se ha calculado ningún nivel.</p>}
          </section>)}
        {forecast.loading ? <Loading /> : forecast.error ? <p className="muted">Las alertas por reglas siguen funcionando.</p> : !forecast.data?.available ? <p className="muted">{forecast.data?.reason ?? "No disponible."} Las alertas por reglas siguen funcionando.</p> : forecast.data.items.length === 0
          ? <p className="muted">Aún no hay suficientes ejercicios para estimar.</p> : (
            <>
              {forecast.data.experimental && <p role="alert" className="notice warn">Modelo EXPERIMENTAL no aprobado: solo demostración, no usar para decidir.</p>}
              <ul>{forecast.data.items.map((f) => <li key={f.student.id + f.competency.id}>
                <strong>{f.student.display_name}</strong> · {f.competency.name}: probabilidad estimada de dificultad {Math.round(f.probability * 100)} %{f.above_threshold ? " (revisar)" : ""}
                <small className="muted"> · Modelo {f.model_id} · {f.model_status}</small>
                {!forecast.data?.experimental && f.difficulty_recommendation && <div className="teacher-flow-guidance">
                  <strong>Recomendación por reglas</strong> · {f.evidence_count ?? 0} ejercicios cerrados. {f.difficulty_recommendation.reason}
                  {f.difficulty_recommendation.suggested_difficulty !== null && <> Dificultad orientativa: {f.difficulty_recommendation.suggested_difficulty} de 3.</>}
                  <small> No cambia el grado ni asigna tareas automáticamente. El docente decide.</small>
                </div>}
              </li>)}</ul>
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
