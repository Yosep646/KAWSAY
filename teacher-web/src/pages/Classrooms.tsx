import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Card, ErrorBox, Loading } from "../components/ui";
import { Icon } from "../components/Icon";
import { TeacherPageIntro } from "../components/TeacherPageIntro";
import "./student-enroll.css";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import type { Classroom, ClassroomDetail, Grade, StudentCredentials } from "../types/api";
import { errMsg, gradeLabel } from "../utils/format";

export function Classrooms() {
  const rooms = useAsync(() => api.get<Classroom[]>("/classrooms"), []);
  const [selected, setSelected] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [year, setYear] = useState(new Date().getFullYear());
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    try { setBusy(true);setErr(null); const created = await api.post<Classroom>("/classrooms", { name:name.trim(), academic_year: year }); setName(""); await rooms.reload(); if (created?.id) setSelected(created.id); } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  };
  return (
    <div className="teacher-workflow teacher-classrooms-page">
      <TeacherPageIntro kicker="GESTIÓN DE AULAS · KAWSAY AI" title="Mis aulas" description="Organiza tus secciones, incluso cuando enseñas varios grados en una misma aula." icon="classroom">
        <Link to="/estudiantes"><Icon name="students"/> Gestionar estudiantes</Link>
        <Link className="secondary" to="/planificacion"><Icon name="book"/> Ver planificación</Link>
      </TeacherPageIntro>
      <div className="teacher-flow-kpis">
        <div className="teacher-flow-stat"><span><Icon name="classroom"/></span><div><strong>{rooms.loading?"…":rooms.data?.length??"—"}</strong><small>Aulas registradas</small></div></div>
        <div className="teacher-flow-stat"><span><Icon name="graduation"/></span><div><strong>{rooms.data?.length ? new Set(rooms.data.map(r => r.academic_year)).size : rooms.loading ? "…" : 0}</strong><small>Años escolares con aulas</small></div></div>
        <div className="teacher-flow-stat"><span><Icon name="leaf"/></span><div><strong>Multigrado</strong><small>Cada estudiante conserva su grado oficial</small></div></div>
      </div>
      <ErrorBox message={rooms.error ?? err}/>
      <div className="teacher-flow-grid">
        <section className="teacher-flow-card">
          <div className="teacher-flow-card-heading"><span><Icon name="classroom"/></span><div><h3>Mis secciones</h3><p>Selecciona un aula para consultar su lista de estudiantes.</p></div></div>
          {rooms.loading ? <Loading/> : rooms.data?.length ? (
            <div className="teacher-room-list">{rooms.data.map(r => <button key={r.id} type="button" className="teacher-room-item" aria-pressed={selected===r.id} onClick={() => setSelected(r.id)}>
              <span><Icon name="classroom"/></span><div><strong>{r.name}</strong><small>Año escolar {r.academic_year}</small></div><Icon name="arrow"/>
            </button>)}</div>
          ) : <div className="teacher-flow-empty"><Icon name="classroom"/><h3>Aún no tienes aulas</h3><p>Registra tu primera aula. Después podrás agregar estudiantes y preparar actividades por grado.</p></div>}
        </section>
        <section className="teacher-flow-card">
          <div className="teacher-flow-card-heading"><span><Icon name="book"/></span><div><h3>Registrar nueva aula</h3><p>Los estudiantes pueden pertenecer a distintos grados.</p></div></div>
          <form className="teacher-flow-form" onSubmit={e=>void create(e)}>
            <label>Nombre de la sección<input value={name} onChange={e=>setName(e.target.value)} placeholder="Ej. Aula multigrado A" minLength={2} maxLength={100} required/></label>
            <label>Año escolar<input type="number" value={year} min={2020} max={2100} onChange={e=>setYear(Number(e.target.value))} required/></label>
            <button type="submit" disabled={busy||name.trim().length<2}>{busy?"Creando aula…":"Crear aula"} <Icon name="arrow"/></button>
          </form>
          <div className="teacher-flow-guidance" style={{marginTop:16}}>Después de crear el aula, registra a los estudiantes y activa una planificación estructurada. <Link to="/planificacion">Revisar planificación</Link></div>
        </section>
      </div>
      {selected && <section className="teacher-flow-card" aria-label="Detalle del aula seleccionada"><RoomDetail key={selected} id={selected}/></section>}
    </div>
  );
}

function RoomDetail({ id }: { id: string }) {
  const room = useAsync(() => api.get<ClassroomDetail>(`/classrooms/${id}`), [id]);
  const grades = useAsync(() => api.get<Grade[]>("/curriculum/grades"), []);
  const [name, setName] = useState("");
  const [gradeId, setGradeId] = useState<number>(0);
  const [created, setCreated] = useState<StudentCredentials | null>(null);
  const [studentEmail, setStudentEmail] = useState("");
  const [studentPassword, setStudentPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loginMode, setLoginMode] = useState<"email"|"pin">("email");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const add = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    try {
      setBusy(true); setErr(null);
      const gid = gradeId || grades.data?.[0]?.id;
      if (!gid) { setErr("Selecciona un grado válido."); return; }
      const created = await api.post<StudentCredentials>("/students", {
        display_name: name.trim(), grade_id: gid, classroom_id: id,
        ...(loginMode==="email" ? {email:studentEmail.trim().toLowerCase(),password:studentPassword} : {})
      });
      setCreated(created); setName(""); setStudentEmail(""); setStudentPassword(""); setShowPassword(false);
      await room.reload();
    } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  };
  const reset = async (sid: string) => {
    try { setErr(null); const detail = await api.get<{id:string;display_name:string;grade_id:number;login_code:string|null;email:string|null}>(`/students/${sid}`);
      if (detail.email) {setErr("Este estudiante usa correo y contraseña. Ve a «Estudiantes» para cambiar su contraseña."); return;}
      const r = await api.post<{ pin: string }>(`/students/${sid}/reset-pin`);
      setCreated({ id: sid, display_name: detail.display_name, grade_id: detail.grade_id, login_code: detail.login_code, pin: r.pin });
    } catch (x) { setErr(errMsg(x)); }
  };
  return (
    <Card title={room.data ? `${room.data.name} — grados: ${room.data.grades_present.join(", ") || "sin estudiantes"}` : "Aula"}>
      <ErrorBox message={room.error ?? err} />
      {room.loading ? <Loading /> : (
        <table><thead><tr><th>Estudiante</th><th>Grado</th><th /></tr></thead>
          <tbody>{room.data?.students.map((s) => (
            <tr key={s.id}><td>{s.display_name}</td><td>{gradeLabel({ level: s.grade_level, number: s.grade_number })}</td>
              <td><button className="ghost" onClick={() => void reset(s.id)}>Restablecer PIN</button></td></tr>))}
          </tbody></table>
      )}
      <section className="student-enroll">
        <div className="student-enroll-heading"><span className="student-enroll-badge"><Icon name="students" /></span><div><p className="student-enroll-kicker">REGISTRO DEL AULA</p><h3>Agregar estudiante</h3><p>Configura las credenciales de acceso de un estudiante de esta aula.</p></div></div>
        <div className="student-enroll-method" role="group" aria-label="Método de acceso">
          <button type="button" aria-pressed={loginMode==="email"} className={loginMode==="email"?"active":""} onClick={()=>setLoginMode("email")}>Correo y contraseña</button>
          <button type="button" aria-pressed={loginMode==="pin"} className={loginMode==="pin"?"active":""} onClick={()=>setLoginMode("pin")}>Código y PIN</button>
        </div>
        <form className="student-enroll-form" onSubmit={(e) => void add(e)} autoComplete="off">
          <label>Nombre completo<input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nombre del estudiante" required maxLength={120} autoComplete="off"/></label>
          <label>Grado<select value={gradeId || grades.data?.[0]?.id || ""} onChange={(e) => setGradeId(Number(e.target.value))} required>
            {grades.data?.map((g) => <option key={g.id} value={g.id}>{gradeLabel(g)}</option>)}</select></label>
          {loginMode==="email" && <>
            <label>Correo electrónico<input type="email" value={studentEmail} onChange={e=>setStudentEmail(e.target.value)} required placeholder="alumno@colegio.edu.pe" autoComplete="off" /></label>
            <div className="student-enroll-password"><label htmlFor="classroom-student-password">Contraseña inicial (12 caracteres mínimo)</label>
              <div className="student-enroll-password-control"><input id="classroom-student-password" type={showPassword?"text":"password"} value={studentPassword} onChange={e=>setStudentPassword(e.target.value)} minLength={12} maxLength={128} required autoComplete="new-password" />
                <button type="button" onClick={()=>setShowPassword(!showPassword)} aria-label={showPassword?"Ocultar contraseña":"Mostrar contraseña"}><Icon name={showPassword?"eye-off":"eye"}/>{showPassword?"Ocultar":"Mostrar"}</button>
              </div>
            </div>
          </>}
          <div className="student-enroll-footer"><p><Icon name="shield"/> Entrega las credenciales solo al estudiante o su familia.</p><button type="submit" disabled={busy||!grades.data?.length}>{busy?"Guardando…":"Agregar estudiante"}<Icon name="arrow"/></button></div>
        </form>
      </section>
      {created && (
        <div className="notice" role="status">
          <strong>Credenciales de {created.display_name}</strong> — se muestran UNA sola vez. Entrégalas al estudiante.
          <div className="creds">{created.email ? <>Correo: <code>{created.email}</code> · Contraseña: la que asignaste en el formulario (el servidor no la devuelve).</> : <>Código: <code>{created.login_code}</code> · PIN: <code>{created.pin}</code></>}</div>
          <button className="ghost" onClick={() => setCreated(null)}>Ya las anoté</button>
        </div>
      )}
    </Card>
  );
}
