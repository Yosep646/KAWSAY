import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { Card, ErrorBox, Loading } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { errMsg } from "../utils/format";
import { OfflinePanel } from "../components/OfflinePanel";

interface Task { student_assignment_id: string; title: string; subject: string | null; instructions: string }
interface Pull { tasks: Task[]; has_more: boolean; cursor: number }
interface Progress { competency: string; percent: number | null }

export function StudentHome() {
  const { user } = useAuth();
  const tasks = useAsync(() => api.get<Pull>("/sync/pull?cursor=0&limit=50"), []);
  const progress = useAsync(() => api.get<Progress[]>("/progress/me"), []);
  const [extra, setExtra] = useState<Task[]>([]);
  const [page, setPage] = useState<Pull | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const loadMore = async () => {
    const current = page ?? tasks.data;
    if (!current || busy) return;
    setBusy(true); setPageError(null);
    try {
      const next = await api.get<Pull>(`/sync/pull?cursor=${current.cursor}&limit=50`);
      if (next.cursor < current.cursor || (next.has_more && next.cursor === current.cursor)) throw new Error("La respuesta del servidor no permite continuar.");
      setExtra(old => [...old, ...next.tasks]); setPage(next);
    } catch (error) { setPageError(errMsg(error)); } finally { setBusy(false); }
  };
  return <div className="student-home">
    <header className="student-welcome"><p className="eyebrow">MI ESPACIO DE APRENDIZAJE</p><h2>¡Hola, {user?.display_name}!</h2><p>Vamos a seguir aprendiendo juntos.</p></header>
    <OfflinePanel />
    <p className="notice">Esta vista necesita conexión para actualizar actividades y progreso oficial. Las actividades del apartado «Aprender sin conexión» se pueden resolver después de descargarlas.</p>
    <div className="student-columns">
      <Card title="Mis actividades">
        <ErrorBox message={tasks.error} />
        {tasks.loading ? <Loading /> : tasks.data && (tasks.data.tasks.length || extra.length ? <ul className="student-task-list">{[...tasks.data.tasks, ...extra].map(t => <li key={t.student_assignment_id}><strong>{t.title}</strong><span>{t.subject ?? "Actividad educativa"}</span><p>{t.instructions}</p><Link to={`/estudiante/actividad/${t.student_assignment_id}`}>Abrir actividad</Link></li>)}</ul> : <p>{(page ?? tasks.data).has_more ? "Busca más actividades en la siguiente página." : "Aún no tienes actividades asignadas."}</p>)}
        <ErrorBox message={pageError} />
        {(page ?? tasks.data)?.has_more && <button className="ghost" disabled={busy} onClick={() => void loadMore()}>{busy ? "Cargando…" : "Ver más actividades"}</button>}
      </Card>
      <Card title="Mi progreso">
        <ErrorBox message={progress.error} />
        {progress.loading ? <Loading /> : progress.data && (progress.data.length ? <ul className="student-task-list">{progress.data.map(p => <li key={p.competency}><strong>{p.competency}</strong><span>{p.percent === null ? "Aún estamos reuniendo información" : `${p.percent} % de progreso`}</span></li>)}</ul> : <p>Tu progreso aparecerá cuando completes actividades.</p>)}
      </Card>
    </div>
  </div>;
}
