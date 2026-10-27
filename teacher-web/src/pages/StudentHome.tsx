import { useEffect, useState } from "react";
import { offlineTasks, type OfflineTask } from "../services/offlineTasks";
import { Link } from "react-router-dom";
import { Icon } from "../components/Icon";
import { useAuth } from "../app/AuthContext";
import { Card, ErrorBox, Loading } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { errMsg } from "../utils/format";

interface Task { student_assignment_id: string; title: string; subject: string | null; instructions: string }
interface Pull { tasks: Task[]; has_more: boolean; cursor: number }
interface Progress { competency: string; percent: number | null }

export function StudentHome({ focus = "home" }: { focus?: "home" | "activities" | "progress" }) {
  const { user } = useAuth();
  const tasks = useAsync(() => api.get<Pull>("/sync/pull?cursor=0&limit=50"), []);
  const progress = useAsync(() => api.get<Progress[]>("/progress/me"), []);
  const [extra, setExtra] = useState<Task[]>([]);
  const [saved, setSaved] = useState<OfflineTask[]>([]);
  const [search, setSearch] = useState("");
  const [syncBusy, setSyncBusy] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [online, setOnline] = useState(typeof navigator !== "undefined" ? navigator.onLine : true);
  useEffect(() => { const update = () => setOnline(navigator.onLine); window.addEventListener("online", update); window.addEventListener("offline", update); return () => { window.removeEventListener("online", update); window.removeEventListener("offline", update); }; }, []);
  const [offlineMessage, setOfflineMessage] = useState<string | null>(null);
  useEffect(() => { if (user?.id) void offlineTasks.list(user.id).then(setSaved).catch(() => setOfflineMessage("No se pudo leer la biblioteca local.")); }, [user?.id]);
  useEffect(() => { if (user?.id && tasks.data?.tasks.length) void offlineTasks.save(user.id, tasks.data.tasks).then(() => offlineTasks.list(user.id)).then(setSaved).catch(() => setOfflineMessage("No se pudieron descargar las actividades.")); }, [user?.id, tasks.data]);
  const visibleTasks = Array.from(new Map([...saved, ...(tasks.data?.tasks ?? []), ...extra].map(task => [task.student_assignment_id, task])).values());
  const validScores = progress.data?.filter(p => typeof p.percent === "number" && Number.isFinite(p.percent)) ?? [];
  const averageProgress = validScores.length
    ? Math.round(validScores.reduce((total, p) => total + (p.percent ?? 0), 0) / validScores.length) : null;
  const saveForOffline = async () => {
    if (!user?.id || !tasks.data) return;
    setSyncBusy(true); setSyncMessage(null);
    try {
      await offlineTasks.save(user.id, visibleTasks);
      const updated = await offlineTasks.list(user.id);
      setSaved(updated);
      setSyncMessage(`${updated.length} actividades disponibles en este dispositivo. Para responder sin Internet, abre una actividad mientras tengas conexión para descargar sus preguntas.`);
    } catch (error) { setOfflineMessage(errMsg(error)); } finally { setSyncBusy(false); }
  };
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
      if (user?.id) await offlineTasks.save(user.id, next.tasks);
      if (user?.id) setSaved(await offlineTasks.list(user.id));
    } catch (error) { setPageError(errMsg(error)); } finally { setBusy(false); }
  };
  return <div className="student-home">
    <header className="student-welcome">
      <div className="student-hero-content"><p className="eyebrow"><Icon name="spark" /> MI ESPACIO DE APRENDIZAJE</p>
        <h2>{focus === "home" ? `¡Hola, ${user?.display_name}!` : focus === "activities" ? "Mis actividades" : "Mi progreso"}</h2>
        <p>{focus === "home" ? "Cada día puedes descubrir algo nuevo. ¡Sigue aprendiendo a tu ritmo!" : focus === "activities" ? "Revisa los ejercicios que tu docente preparó para ti." : "Reconoce tus logros y descubre lo que puedes seguir practicando."}</p>
        <Link to="/estudiante/actividades" className="student-hero-link">Ver mis actividades <Icon name="arrow" /></Link>
      </div>
      <div className="student-hero-decoration" aria-hidden="true"><span className="student-sun"/><span className="student-mountain m1"/><span className="student-mountain m2"/><span className="student-student-icon"><Icon name="graduation"/></span></div>
    </header>
    <div className="student-status-line">
      <div role="status" className={`connection-status ${online ? "connected" : "disconnected"}`}><span aria-hidden="true">●</span> {online ? "Conexión de red disponible" : "Sin Internet: consulta actividades descargadas"}</div>
      {online && tasks.data && <button type="button" className="student-offline-save" disabled={syncBusy} onClick={() => void saveForOffline()}><Icon name="database"/>{syncBusy ? "Guardando…" : "Guardar actividades para offline"}</button>}
    </div>
    {syncMessage && <p role="status" className="notice">{syncMessage}</p>}
    {focus === "home" && <>
      <div className="student-overview-stats" aria-label="Resumen real de tu aprendizaje">
        <Link to="/estudiante/actividades"><span className="student-overview-icon t-pink"><Icon name="tasks"/></span><div><strong>{visibleTasks.length}</strong><small>Actividades asignadas</small></div><Icon name="arrow"/></Link>
        <Link to="/estudiante/actividades"><span className="student-overview-icon t-blue"><Icon name="database"/></span><div><strong>{saved.length}</strong><small>Disponibles en este dispositivo</small></div><Icon name="arrow"/></Link>
        <Link to="/estudiante/progreso"><span className="student-overview-icon t-emerald"><Icon name="activity"/></span><div><strong>{averageProgress === null ? "—" : `${averageProgress} %`}</strong><small>Progreso medio con evidencia</small></div><Icon name="arrow"/></Link>
      </div>
      <div className="student-quick-links"><Link to="/estudiante/actividades"><Icon name="book" /> Ver mis actividades <Icon name="arrow"/></Link><Link to="/estudiante/progreso"><Icon name="chart" /> Consultar mi progreso <Icon name="arrow"/></Link></div>
    </>}
    <p className="notice" role="note">Puedes responder actividades descargadas sin conexión. Cada respuesta se conserva localmente y se confirma al volver a comunicarse con el servidor. Evita eliminar los datos del navegador antes de sincronizar.</p>
    {offlineMessage && <p role="alert" className="notice warn">{offlineMessage}</p>}
    <div className="student-columns">
      {focus !== "progress" && <Card title="Mis actividades">
        <label className="student-search">Buscar actividad<input type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Busca por título o curso" /></label>
        {tasks.error && saved.length > 0 ? <p role="status" className="notice warn">Servidor no disponible. Puedes acceder a tus actividades descargadas.</p> : <ErrorBox message={tasks.error} />}
        {tasks.loading && saved.length === 0 ? <Loading /> : (tasks.data || saved.length > 0) && (visibleTasks.length ? <ul className="student-task-list">{visibleTasks.filter(t => `${t.title} ${t.subject ?? ""}`.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase())).map(t => <li key={t.student_assignment_id}><span className="student-task-glyph"><Icon name="book"/></span><div><strong>{t.title}</strong><span>{t.subject ?? "Actividad educativa"}</span><p>{t.instructions}</p><Link to={`/estudiante/actividad/${t.student_assignment_id}`}>Abrir actividad <Icon name="arrow"/></Link></div></li>)}</ul> : <p>{(page ?? tasks.data)?.has_more ? "Busca más actividades en la siguiente página." : "Aún no tienes actividades asignadas."}</p>)}
        <ErrorBox message={pageError} />
        {(page ?? tasks.data)?.has_more && <button className="ghost" disabled={busy} onClick={() => void loadMore()}>{busy ? "Cargando…" : "Ver más actividades"}</button>}
      </Card>}
      {focus !== "activities" && <Card title="Mi progreso">
        {progress.error ? <p role="status" className="notice warn">No se pudo actualizar tu progreso. Vuelve a consultar cuando tengas conexión con el servidor.</p> : null}
        {progress.loading ? <Loading /> : progress.data && (progress.data.length ? <ul className="student-task-list">{progress.data.map(p => <li key={p.competency} className="student-progress-item"><strong>{p.competency}</strong><span>{p.percent === null ? "Aún estamos reuniendo información" : `${p.percent} % de progreso`}</span>{p.percent !== null && Number.isFinite(p.percent) && <div className="student-progress-track" role="progressbar" aria-label={`Progreso de ${p.competency}`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.max(0,Math.min(100,p.percent))}><span style={{width:`${Math.max(0,Math.min(100,p.percent))}%`}}/></div>}</li>)}</ul> : <p>Tu progreso aparecerá cuando completes actividades.</p>)}
      </Card>}
    </div>
  </div>;
}
