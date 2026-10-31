import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { Icon } from "../components/Icon";
import { Card, ErrorBox, Loading } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { offlineTasks, type OfflineTask } from "../services/offlineTasks";
import "./student-preferences.css";

type Pull = { tasks: OfflineTask[]; has_more: boolean; cursor: number };

/** Acceso visible al Tutor IA: solo actúa sobre tareas asignadas al estudiante.
 * Sin conexión se usan las preguntas y pistas descargadas; nunca inventamos contenido.
 */
export function StudentTutor() {
  const { user } = useAuth();
  const recent = useAsync(() => api.get<Pull>("/sync/pull?cursor=0&limit=50"), []);
  const [downloaded, setDownloaded] = useState<OfflineTask[]>([]);
  const [localError, setLocalError] = useState<string | null>(null);
  useEffect(() => {
    if (!user?.id) return;
    let cancelled = false;
    void offlineTasks.list(user.id).then(tasks => {
      if (!cancelled) setDownloaded(tasks);
    }).catch(() => { if (!cancelled) setLocalError("No se pudo abrir tu biblioteca de ejercicios guardados."); });
    return () => { cancelled = true; };
  }, [user?.id]);
  const tasks = Array.from(new Map([
    ...downloaded, ...(recent.data?.tasks ?? []),
  ].map(task => [task.student_assignment_id, task])).values());
  return <div className="student-tutor-landing">
    <header className="student-preference-hero">
      <p><Icon name="spark"/> KAWSAY AI / ACOMPAÑAMIENTO EDUCATIVO</p>
      <h2>Tutor IA KAWSAY</h2>
      <span>Aprende con pistas paso a paso, según las actividades de tu maestro.</span>
    </header>
    <Card title="¿En qué ejercicio necesitas ayuda?">
      <p>Elige una actividad y pulsa «Pedir una pista». El tutor no responde el ejercicio por ti. Sin Internet utiliza las pistas descargadas y reglas educativas.</p>
      <ErrorBox message={localError}/>
      {recent.error && <p role="status">Sin conexión con el servidor. Se muestran tus actividades guardadas, si las hay.</p>}
      {recent.loading && !tasks.length ? <Loading/> : !tasks.length
        ? <p>Todavía no tienes actividades descargadas. Tu docente debe publicar una actividad y debes conectarte al menos una vez para recibirla.</p>
        : <div className="student-tutor-activity-list">
            {tasks.map(task => <div className="student-tutor-activity" key={task.student_assignment_id}>
              <div><strong>{task.title}</strong><p>{task.subject || "Actividad de mi grado"}</p></div>
              <Link to={`/estudiante/actividad/${task.student_assignment_id}`}>Abrir tutor <Icon name="arrow"/></Link>
            </div>)}
          </div>}
      {recent.data?.has_more && <p className="muted">Hay más actividades disponibles en <Link to="/estudiante/actividades">Mis actividades</Link>.</p>}
    </Card>
  </div>;
}
