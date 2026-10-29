import { useEffect, useState } from "react";
import { offlineTasks, type OfflineTask } from "../services/offlineTasks";
import { offlineCourses, type OfflineCourse } from "../services/offlineCourses";
import { Link } from "react-router-dom";
import { Icon } from "../components/Icon";
import { useAuth } from "../app/AuthContext";
import { Card, ErrorBox, Loading } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { errMsg } from "../utils/format";

interface Task { student_assignment_id: string; title: string; subject: string | null; course_id?: string | null; instructions: string }
interface Pull { tasks: Task[]; has_more: boolean; cursor: number }
interface Progress { competency: string; percent: number | null }

export function StudentHome({ focus = "home" }: { focus?: "home" | "activities" | "progress" | "courses" }) {
  const { user } = useAuth();
  const tasks = useAsync(() => api.get<Pull>("/sync/pull?cursor=0&limit=50"), []);
  const progress = useAsync(() => api.get<Progress[]>("/progress/me"), []);
  const courses = useAsync(() => focus === "courses" ? api.get<OfflineCourse[]>("/sync/courses") : Promise.resolve([]), [focus]);
  const [savedCourses, setSavedCourses] = useState<OfflineCourse[]>([]);
  const [extra, setExtra] = useState<Task[]>([]);
  const [saved, setSaved] = useState<OfflineTask[]>([]);
  const [search, setSearch] = useState("");
  const [syncBusy, setSyncBusy] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [online, setOnline] = useState(typeof navigator !== "undefined" ? navigator.onLine : true);
  useEffect(() => { const update = () => setOnline(navigator.onLine); window.addEventListener("online", update); window.addEventListener("offline", update); return () => { window.removeEventListener("online", update); window.removeEventListener("offline", update); }; }, []);
  const [offlineMessage, setOfflineMessage] = useState<string | null>(null);
  useEffect(() => {
    if (user?.id && focus === "courses") void offlineCourses.list(user.id).then(setSavedCourses).catch(() => setOfflineMessage("No se pudo leer el catálogo de cursos sin conexión."));
  }, [user?.id, focus]);
  useEffect(() => {
    if (user?.id && focus === "courses" && courses.data) void offlineCourses.save(user.id, courses.data).then(() => setSavedCourses(courses.data ?? [])).catch(() => setOfflineMessage("No se pudo guardar el catálogo de cursos en este dispositivo."));
  }, [user?.id, focus, courses.data]);
  useEffect(() => { if (user?.id) void offlineTasks.list(user.id).then(setSaved).catch(() => setOfflineMessage("No se pudo leer la biblioteca local.")); }, [user?.id]);
  useEffect(() => { if (user?.id && tasks.data?.tasks.length) void offlineTasks.save(user.id, tasks.data.tasks).then(() => offlineTasks.list(user.id)).then(setSaved).catch(() => setOfflineMessage("No se pudieron descargar las actividades.")); }, [user?.id, tasks.data]);
  const visibleTasks = Array.from(new Map([...saved, ...(tasks.data?.tasks ?? []), ...extra].map(task => [task.student_assignment_id, task])).values());
  const courseCatalog = courses.data ?? savedCourses;
  const courseIds = new Set(courseCatalog.map(course => course.id));
  const courseIdByName = new Map<string, string>();
  for (const course of courseCatalog) {
    const key = course.name.trim().toLocaleLowerCase("es");
    if (!courseIdByName.has(key)) courseIdByName.set(key, course.id);
  }
  const tasksByCourse = new Map<string, OfflineTask[]>();
  const priorTasks: OfflineTask[] = [];
  for (const task of visibleTasks) {
    const courseId = task.course_id ?? courseIdByName.get((task.subject ?? "").trim().toLocaleLowerCase("es"));
    if (courseId && courseIds.has(courseId)) {
      tasksByCourse.set(courseId, [...(tasksByCourse.get(courseId) ?? []), task]);
    } else {
      priorTasks.push(task);
    }
  }
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
        <h2>{focus === "home" ? `¡Hola, ${user?.display_name}!` : focus === "activities" ? "Mis actividades" : focus === "courses" ? "Mis cursos" : "Mi progreso"}</h2>
        <p>{focus === "home" ? "Cada día puedes descubrir algo nuevo. ¡Sigue aprendiendo a tu ritmo!" : focus === "activities" ? "Revisa los ejercicios que tu docente preparó para ti." : focus === "courses" ? "Accede a las áreas de tu grado y resuelve las actividades del maestro." : "Reconoce tus logros y descubre lo que puedes seguir practicando."}</p>
        <Link to={focus === "courses" ? "/estudiante/actividades" : "/estudiante/cursos"} className="student-hero-link">{focus === "courses" ? "Ver mis actividades" : "Ver mis cursos"} <Icon name="arrow" /></Link>
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
        <Link to="/estudiante/actividades"><span className="student-overview-icon t-violet"><Icon name="book"/></span><div><strong>Explorar</strong><small>Recursos y actividades</small></div><Icon name="arrow"/></Link>
      </div>
      <div className="student-quick-links"><Link to="/estudiante/cursos"><Icon name="book" /> Ver mis cursos <Icon name="arrow"/></Link><Link to="/estudiante/actividades"><Icon name="book" /> Ver mis actividades <Icon name="arrow"/></Link><Link to="/estudiante/progreso"><Icon name="chart" /> Consultar mi progreso <Icon name="arrow"/></Link></div>
    </>}
    <p className="notice" role="note">Puedes responder actividades descargadas sin conexión. Cada respuesta se conserva localmente y se confirma al volver a comunicarse con el servidor. Evita eliminar los datos del navegador antes de sincronizar.</p>
    {offlineMessage && <p role="alert" className="notice warn">{offlineMessage}</p>}
    <div className="student-columns">
      {focus === "courses" && <Card title="Cursos de mi aula">
        <p>Estas áreas provienen de la planificación activa de tu institución y tu grado. Puedes consultar los cursos guardados sin Internet.</p>
        <button type="button" className="ghost" onClick={() => { void courses.reload(); void tasks.reload(); }} disabled={courses.loading || tasks.loading}>Actualizar cursos y actividades</button>
        {courses.error && <p className="notice warn" role="status">No se pudo actualizar el catálogo. Se muestran los cursos guardados en este dispositivo, si existen.</p>}
        {courses.loading && !savedCourses.length ? <Loading /> : <div className="student-courses-grid">
          {courseCatalog.map(course => {
            const assigned = tasksByCourse.get(course.id) ?? [];
            return <section className="student-course-card" key={course.id} aria-label={`Curso ${course.name}`}>
              <div className="student-course-card-head"><Icon name="book"/><div>
                <h3>{course.name}</h3>
                <p>{course.classroom_name} · {course.academic_year}{course.is_demo ? " · Plan de prueba" : ""}</p>
              </div></div>
              <strong>{assigned.length} actividades · {assigned.length ? "Con tareas del docente" : "Aún sin tareas publicadas"}</strong>
              {assigned.length > 0 && <ul className="student-course-activities">{assigned.map(task =>
                <li key={task.student_assignment_id}><Link to={`/estudiante/actividad/${task.student_assignment_id}`}>{task.title} <Icon name="arrow"/></Link></li>
              )}</ul>}
            </section>;
          })}
          {!courseCatalog.length && !priorTasks.length && <p>Aún no tienes cursos en una planificación activa. Cuando tu institución la publique y te conectes, los encontrarás aquí.</p>}
          {priorTasks.length > 0 && <section className="student-course-card" aria-label="Actividades descargadas anteriormente">
            <h3>Actividades descargadas anteriormente</h3>
            <p>Siguen disponibles aunque haya cambiado la planificación de tu escuela.</p>
            <ul className="student-course-activities">{priorTasks.map(task =>
              <li key={task.student_assignment_id}><Link to={`/estudiante/actividad/${task.student_assignment_id}`}>{task.title} <Icon name="arrow"/></Link></li>
            )}</ul>
          </section>}
        </div>}
        {(page ?? tasks.data)?.has_more && <button type="button" className="ghost" disabled={busy} onClick={() => void loadMore()}>{busy ? "Cargando…" : "Ver más actividades"}</button>}
      </Card>}
      {focus !== "progress" && focus !== "courses" && <Card title="Mis actividades">
        <label className="student-search">Buscar actividad<input type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Busca por título o curso" /></label>
        {tasks.error && saved.length > 0 ? <p role="status" className="notice warn">Servidor no disponible. Puedes acceder a tus actividades descargadas.</p> : <ErrorBox message={tasks.error} />}
        {tasks.loading && saved.length === 0 ? <Loading /> : (tasks.data || saved.length > 0) && (visibleTasks.length ? <ul className="student-task-list">{visibleTasks.filter(t => `${t.title} ${t.subject ?? ""}`.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase())).map(t => <li key={t.student_assignment_id}><span className="student-task-glyph"><Icon name="book"/></span><div><strong>{t.title}</strong><span>{t.subject ?? "Actividad educativa"}</span><p>{t.instructions}</p><Link to={`/estudiante/actividad/${t.student_assignment_id}`}>Abrir actividad <Icon name="arrow"/></Link></div></li>)}</ul> : <p>{(page ?? tasks.data)?.has_more ? "Busca más actividades en la siguiente página." : "Aún no tienes actividades asignadas."}</p>)}
        <ErrorBox message={pageError} />
        {(page ?? tasks.data)?.has_more && <button className="ghost" disabled={busy} onClick={() => void loadMore()}>{busy ? "Cargando…" : "Ver más actividades"}</button>}
      </Card>}
      {focus !== "activities" && focus !== "courses" && <Card title="Mi progreso">
        {progress.error ? <p role="status" className="notice warn">No se pudo actualizar tu progreso. Vuelve a consultar cuando tengas conexión con el servidor.</p> : null}
        {progress.loading ? <Loading /> : progress.data && (progress.data.length ? <ul className="student-task-list">{progress.data.map(p => <li key={p.competency} className="student-progress-item"><strong>{p.competency}</strong><span>{p.percent === null ? "Aún estamos reuniendo información" : `${p.percent} % de progreso`}</span>{p.percent !== null && Number.isFinite(p.percent) && <div className="student-progress-track" role="progressbar" aria-label={`Progreso de ${p.competency}`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.max(0,Math.min(100,p.percent))}><span style={{width:`${Math.max(0,Math.min(100,p.percent))}%`}}/></div>}</li>)}</ul> : <p>Tu progreso aparecerá cuando completes actividades.</p>)}
      </Card>}
    </div>
  </div>;
}
