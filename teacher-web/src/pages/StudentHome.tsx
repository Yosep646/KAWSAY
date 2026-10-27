import { useEffect, useState } from "react";
import { offlineTasks, type OfflineTask } from "../services/offlineTasks";
import { Link } from "react-router-dom";
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
  const [online, setOnline] = useState(typeof navigator !== "undefined" ? navigator.onLine : true);
  useEffect(() => { const update = () => setOnline(navigator.onLine); window.addEventListener("online", update); window.addEventListener("offline", update); return () => { window.removeEventListener("online", update); window.removeEventListener("offline", update); }; }, []);
  const [offlineMessage, setOfflineMessage] = useState<string | null>(null);
  useEffect(() => { if (user?.id) void offlineTasks.list(user.id).then(setSaved).catch(() => setOfflineMessage("No se pudo leer la biblioteca local.")); }, [user?.id]);
  useEffect(() => { if (user?.id && tasks.data?.tasks.length) void offlineTasks.save(user.id, tasks.data.tasks).then(() => offlineTasks.list(user.id)).then(setSaved).catch(() => setOfflineMessage("No se pudieron descargar las actividades.")); }, [user?.id, tasks.data]);
  const visibleTasks = Array.from(new Map([...saved, ...(tasks.data?.tasks ?? []), ...extra].map(task => [task.student_assignment_id, task])).values());
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
    <header className="student-welcome"><p className="eyebrow">MI ESPACIO DE APRENDIZAJE</p><h2>{focus === "home" ? `¡Hola, ${user?.display_name}!` : focus === "activities" ? "Mis actividades" : "Mi progreso"}</h2><p>{focus === "home" ? "Vamos a seguir aprendiendo juntos." : focus === "activities" ? "Revisa las actividades asignadas por tus docentes." : "Descubre cómo vas avanzando en tus competencias."}</p></header>
    <div role="status" className={`connection-status ${online ? "connected" : "disconnected"}`}><span aria-hidden="true">●</span> {online ? "Conexión de red disponible" : "Sin Internet: consulta actividades descargadas"}</div>
    {focus === "home" && <div className="student-quick-links"><Link to="/estudiante/actividades">📚 Ver mis actividades</Link><Link to="/estudiante/progreso">🌱 Consultar mi progreso</Link></div>}
    <p className="notice" role="note">Puedes responder actividades descargadas sin conexión. Cada respuesta se conserva localmente y se confirma al volver a comunicarse con el servidor. Evita eliminar los datos del navegador antes de sincronizar.</p>
    {offlineMessage && <p role="alert" className="notice warn">{offlineMessage}</p>}
    <div className="student-columns">
      {focus !== "progress" && <Card title="Mis actividades">
        <label className="student-search">Buscar actividad<input type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Busca por título o curso" /></label>
        {tasks.error && saved.length > 0 ? <p role="status" className="notice warn">Servidor no disponible. Puedes acceder a tus actividades descargadas.</p> : <ErrorBox message={tasks.error} />}
        {tasks.loading && saved.length === 0 ? <Loading /> : (tasks.data || saved.length > 0) && (visibleTasks.length ? <ul className="student-task-list">{visibleTasks.filter(t => `${t.title} ${t.subject ?? ""}`.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase())).map(t => <li key={t.student_assignment_id}><strong>{t.title}</strong><span>{t.subject ?? "Actividad educativa"}</span><p>{t.instructions}</p><Link to={`/estudiante/actividad/${t.student_assignment_id}`}>Abrir actividad</Link></li>)}</ul> : <p>{(page ?? tasks.data)?.has_more ? "Busca más actividades en la siguiente página." : "Aún no tienes actividades asignadas."}</p>)}
        <ErrorBox message={pageError} />
        {(page ?? tasks.data)?.has_more && <button className="ghost" disabled={busy} onClick={() => void loadMore()}>{busy ? "Cargando…" : "Ver más actividades"}</button>}
      </Card>}
      {focus !== "activities" && <Card title="Mi progreso">
        {progress.error ? <p role="status" className="notice warn">No se pudo actualizar tu progreso. Vuelve a consultar cuando tengas conexión con el servidor.</p> : null}
        {progress.loading ? <Loading /> : progress.data && (progress.data.length ? <ul className="student-task-list">{progress.data.map(p => <li key={p.competency}><strong>{p.competency}</strong><span>{p.percent === null ? "Aún estamos reuniendo información" : `${p.percent} % de progreso`}</span></li>)}</ul> : <p>Tu progreso aparecerá cuando completes actividades.</p>)}
      </Card>}
    </div>
  </div>;
}
