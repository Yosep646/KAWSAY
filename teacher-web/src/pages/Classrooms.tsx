import { useState, type FormEvent } from "react";
import { Card, ErrorBox, Loading } from "../components/ui";
import { Icon } from "../components/Icon";
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

  const create = async (e: FormEvent) => {
    e.preventDefault();
    try { setErr(null); await api.post("/classrooms", { name, academic_year: year }); setName(""); await rooms.reload(); } catch (x) { setErr(errMsg(x)); }
  };
  return (
    <div>
      <h2>Mis aulas</h2>
      <Card title="Nueva aula (puede mezclar grados)">
        <form className="row" onSubmit={(e) => void create(e)}>
          <label>Nombre<input value={name} onChange={(e) => setName(e.target.value)} required maxLength={100} /></label>
          <label>Año<input type="number" value={year} min={2020} max={2100} onChange={(e) => setYear(Number(e.target.value))} /></label>
          <button type="submit">Crear aula</button>
        </form>
        <ErrorBox message={err} />
      </Card>
      <ErrorBox message={rooms.error} />
      {rooms.loading ? <Loading /> : (
        <ul className="list">{rooms.data?.map((r) => (
          <li key={r.id}><button className="link" onClick={() => setSelected(r.id)}>{r.name} · {r.academic_year}</button></li>))}</ul>
      )}
      {selected && <RoomDetail key={selected} id={selected} />}
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
