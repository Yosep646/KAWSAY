import { useState, type FormEvent } from "react";
import { Card, ErrorBox } from "../components/ui";
import { Icon } from "../components/Icon";
import { AdminOverview, type AdminStatistics } from "./AdminOverview";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { errMsg } from "../utils/format";

interface School { id: string; name: string; region?: string | null }
interface Audit { id: string; action: string; target_type: string; created_at: string; request_id: string | null }
interface Ev { id: string; type: string; status: string; attempts: number; last_error: string | null }
interface Staff { id: string; email: string | null; display_name: string; role: string; is_active: boolean }

export function Admin({ section = "overview" }: { section?: "overview" | "schools" | "teachers" | "curriculum" | "system" | "students" | "tasks" | "reports" | "users" | "configuration" | "backups" }) {
  const schools = useAsync(() => api.get<School[]>("/schools"), []);
  const audit = useAsync(() => api.get<Audit[]>("/audit-log?limit=20"), []);
  const events = useAsync(() => api.get<Ev[]>("/automation/events?limit=20"), []);
  const staff = useAsync(() => api.get<Staff[]>("/users?limit=100"), []);
  const stats = useAsync(() => api.get<AdminStatistics>("/analytics/admin/overview"), []);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [school, setSchool] = useState("");
  const [t, setT] = useState({ email: "", name: "", password: "", school_id: "" });
  const [fwJson, setFwJson] = useState("");
  const [showTeacherPassword, setShowTeacherPassword] = useState(false);
  const [teacherBusy, setTeacherBusy] = useState(false);

  const run = async (fn: () => Promise<unknown>, ok: string) => { try { setErr(null); await fn(); setMsg(ok); await schools.reload(); } catch (x) { setErr(errMsg(x)); } };
  const addSchool = (e: FormEvent) => { e.preventDefault(); void run(() => api.post("/schools", { name: school }), "Escuela creada"); };
  const addTeacher = async (e: FormEvent) => {
    e.preventDefault();
    if (teacherBusy) return;
    setTeacherBusy(true);
    setErr(null);
    setMsg(null);
    try {
      await api.post("/users", { role: "TEACHER", email: t.email.trim(), display_name: t.name.trim(),
        password: t.password, school_id: t.school_id || schools.data?.[0]?.id });
      setMsg("Docente registrado correctamente. Ya puede iniciar sesión con el correo y contraseña que asignaste.");
      setT({ email: "", name: "", password: "", school_id: t.school_id });
      setShowTeacherPassword(false);
      await staff.reload();
    } catch (x) {
      setErr(errMsg(x));
    } finally {
      setTeacherBusy(false);
    }
  };
  const importFw = (e: FormEvent) => {
    e.preventDefault();
    let parsed: unknown;
    try { parsed = JSON.parse(fwJson); } catch { setErr("El contenido no es un JSON válido. Corrígelo antes de importar."); return; }
    void run(() => api.post("/curriculum/frameworks", parsed), "Marco curricular importado");
  };

  return (
    <div>
      {section === "overview" ? (
        <AdminOverview
          schools={schools.data}
          staff={staff.data}
          audits={audit.data}
          events={events.data}
          stats={stats.data}
          loading={schools.loading || staff.loading || audit.loading || events.loading || stats.loading}
          errors={[schools.error, staff.error, audit.error, events.error, stats.error].filter((value): value is string => Boolean(value))}
          onRefresh={async () => { await Promise.all([schools.reload(), staff.reload(), audit.reload(), events.reload(), stats.reload()]); }}
        />
      ) : (
      <header className="role-hero admin-hero">
        <div className="admin-hero-copy">
          <p className="eyebrow">KAWSAY AI <span className="admin-hero-separator">/</span> CENTRO DE ADMINISTRACIÓN</p>
          <h2>{section === "schools" ? "Instituciones educativas" : section === "teachers" ? "Tu equipo docente." : section === "curriculum" ? "Currículo educativo" : "Sistema y auditoría"}</h2>
          <p>{section === "teachers" ? "Organiza los accesos del personal docente de manera segura y sencilla." : "Una visión clara para acompañar a las instituciones y sus comunidades."}</p>
        </div>
        <div className="admin-hero-emblem" aria-hidden="true"><Icon name="leaf" /></div>
      </header>
      )}
      <ErrorBox message={section === "overview" ? null : schools.error ?? (section === "system" ? audit.error ?? events.error : null)} />
      <ErrorBox message={err} />
      {msg && <p role="status" className="notice">{msg}</p>}
      {section === "schools" && <Card title="Escuelas"><ul>{schools.data?.length === 0 && <li>Aún no hay instituciones registradas.</li>}{schools.data?.map((s) => <li key={s.id}>{s.name}</li>)}</ul>
        <form className="row" onSubmit={addSchool}><label>Nombre<input value={school} onChange={(e) => setSchool(e.target.value)} required /></label><button>Crear escuela</button></form></Card>}
      {section === "teachers" && (
        <div className="admin-teacher-layout">
          <section className="admin-form-card" aria-labelledby="teacher-form-title">
            <div className="admin-form-heading">
              <div className="admin-form-icon"><Icon name="students" /></div>
              <div>
                <p className="admin-kicker">GESTIÓN DE ACCESOS</p>
                <h3 id="teacher-form-title">Registrar nuevo docente</h3>
                <p>Completa los datos para darle acceso a su espacio educativo.</p>
              </div>
            </div>
            <form className="admin-teacher-form" onSubmit={(e) => void addTeacher(e)} autoComplete="off">
              <div className="admin-form-grid">
                <label htmlFor="teacher-name">Nombre completo
                  <input id="teacher-name" name="teacher_display_name" value={t.name}
                    onChange={(e) => setT({ ...t, name: e.target.value })}
                    placeholder="Ej. María Quispe" autoComplete="off" maxLength={120} required />
                </label>
                <label htmlFor="teacher-email">Correo electrónico
                  <input id="teacher-email" name="teacher_email" type="email" value={t.email}
                    onChange={(e) => setT({ ...t, email: e.target.value })}
                    placeholder="docente@colegio.edu.pe" autoComplete="off" required />
                </label>
                <label className="admin-field-wide" htmlFor="teacher-school">Institución educativa
                  <select id="teacher-school" name="teacher_school" required
                    value={t.school_id || schools.data?.[0]?.id || ""}
                    onChange={(e) => setT({ ...t, school_id: e.target.value })}>
                    <option value="" disabled>Selecciona una institución</option>
                    {schools.data?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </label>
                <div className="admin-password-block admin-field-wide">
                  <label htmlFor="teacher-password">Contraseña inicial <span className="admin-required">Mínimo 12 caracteres</span></label>
                  <div className="admin-password-input">
                    <input id="teacher-password" name="teacher_password"
                      type={showTeacherPassword ? "text" : "password"}
                      autoComplete="new-password" minLength={12} maxLength={128} required
                      placeholder="Crea una contraseña segura"
                      value={t.password} onChange={(e) => setT({ ...t, password: e.target.value })} />
                    <button type="button" className="admin-password-toggle"
                      onClick={() => setShowTeacherPassword(!showTeacherPassword)}
                      aria-label={showTeacherPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                      aria-pressed={showTeacherPassword}
                      aria-controls="teacher-password">
                      <Icon name={showTeacherPassword ? "eye-off" : "eye"} />
                      <span>{showTeacherPassword ? "Ocultar" : "Mostrar"}</span>
                    </button>
                  </div>
                  <div className="admin-password-meta">
                    <span className={t.password.length >= 12 ? "admin-pass-valid" : ""}>
                      <Icon name={t.password.length >= 12 ? "check" : "settings"} />
                      {t.password.length >= 12 ? "Longitud mínima cumplida" : "Usa al menos 12 caracteres"}
                    </span>
                    <span>{t.password.length}/128</span>
                  </div>
                </div>
              </div>
              <div className="admin-form-actions">
                <p><Icon name="check" /> Las contraseñas se guardan cifradas. No se pueden consultar después.</p>
                <button className="admin-submit" type="submit"
                  disabled={teacherBusy || !schools.data?.length}>
                  {teacherBusy ? "Registrando…" : "Crear docente"}
                  <Icon name="arrow" />
                </button>
              </div>
            </form>
          </section>
          <aside className="admin-onboarding">
            <div className="admin-onboarding-icon"><Icon name="leaf" /></div>
            <p className="admin-kicker">COMUNIDAD EDUCATIVA</p>
            <h3>Educación que crece en equipo.</h3>
            <p>Cada docente registrado tendrá acceso a sus propias aulas, estudiantes y actividades.</p>
            <div className="admin-onboarding-step"><span>01</span> Completa los datos</div>
            <div className="admin-onboarding-step"><span>02</span> Asigna su institución</div>
            <div className="admin-onboarding-step"><span>03</span> Comparte el acceso de forma privada</div>
            <div className="admin-onboarding-art" aria-hidden="true"><Icon name="book" /><Icon name="leaf" /></div>
          </aside>
          <section className="admin-teacher-directory" aria-labelledby="registered-teachers-title">
            <div className="admin-directory-heading">
              <div>
                <p className="admin-kicker">DIRECTORIO</p>
                <h3 id="registered-teachers-title">Personal docente registrado</h3>
              </div>
              <span className="admin-directory-count">{staff.data?.filter((u) => u.role === "TEACHER").length ?? "—"} docentes</span>
            </div>
            {staff.loading && <p className="muted">Consultando docentes…</p>}
            {staff.error && <ErrorBox message={staff.error} />}
            {staff.data?.filter((u) => u.role === "TEACHER").length === 0 && <p className="admin-empty">Aún no se han registrado docentes.</p>}
            <div className="admin-directory-grid">
              {staff.data?.filter((u) => u.role === "TEACHER").map((u) => (
                <div className="admin-person" key={u.id}>
                  <span className="admin-person-avatar">{u.display_name.trim().slice(0, 1).toUpperCase()}</span>
                  <div><strong>{u.display_name}</strong><small>{u.email}</small></div>
                  <span className={u.is_active ? "admin-person-status" : "admin-person-status disabled"}>
                    {u.is_active ? "Activo" : "Inactivo"}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
      {section === "curriculum" && <Card title="Importar marco curricular (JSON revisado por una persona)">
        <p className="muted">Debe indicar explícitamente <code>is_demo</code>. No se importa automáticamente ningún PDF como currículo oficial.</p>
        <form className="stack" onSubmit={importFw}><textarea rows={6} value={fwJson} onChange={(e) => setFwJson(e.target.value)} required /><button>Importar</button></form></Card>}
      {section === "system" && <Card title="Auditoría de accesos a datos de estudiantes (últimos 20)"><ul>{audit.data?.map((a) => <li key={a.id}>{new Date(a.created_at).toLocaleString()} · {a.action} · {a.target_type}</li>)}</ul></Card>}
      {section === "system" && <Card title="Eventos de automatización (n8n es opcional)"><ul>{events.data?.map((e) => <li key={e.id}>{e.type} · {e.status} · intentos {e.attempts}{e.last_error ? ` · ${e.last_error}` : ""}</li>)}</ul>
        <button className="ghost" onClick={() => void run(() => api.post("/automation/dispatch"), "Despacho ejecutado").then(() => events.reload())}>Despachar pendientes</button></Card>}

      {section === "students" && <section className="admin-supplement">
        <h2>Estudiantes de la plataforma</h2>
        <p>Visión general de los estudiantes activos, sin revelar datos personales. La gestión individual corresponde a los docentes autorizados.</p>
        <div className="admin-sup-grid">
          <div><Icon name="graduation"/><strong>{stats.data?.students ?? "—"}</strong><span>Estudiantes activos</span></div>
          <div><Icon name="classroom"/><strong>{stats.data?.institutions ?? "—"}</strong><span>Instituciones</span></div>
        </div>
        <h3>Distribución por grado</h3>
        <div className="admin-sup-rows">{stats.data?.grades.length ? stats.data.grades.map(g=><div key={g.level+g.grade}><span>{g.grade}.° {g.level.toLowerCase()}</span><strong>{g.count}</strong></div>) : <p>Aún no hay estudiantes con grados registrados.</p>}</div>
      </section>}
      {section === "tasks" && <section className="admin-supplement">
        <h2>Asignaciones y tareas</h2><p>Resumen global de las tareas. Solo los docentes pueden crear, revisar y publicar actividades educativas.</p>
        <div className="admin-sup-grid"><div><Icon name="tasks"/><strong>{stats.data?.published_assignments ?? "—"}</strong><span>Tareas publicadas</span></div><div><Icon name="check"/><strong>{stats.data?.student_assignments ?? "—"}</strong><span>Asignaciones a estudiantes</span></div></div>
      </section>}
      {section === "reports" && <section className="admin-supplement">
        <h2>Reportes de aprendizaje</h2><p>Indicadores agregados para administrar la plataforma. Estos valores proceden del servidor; no son resultados simulados de IA.</p>
        <div className="admin-sup-grid">{[["Instituciones",stats.data?.institutions],["Docentes",stats.data?.teachers],["Estudiantes",stats.data?.students],["Tareas publicadas",stats.data?.published_assignments]].map(([label,value])=><div key={String(label)}><Icon name="chart"/><strong>{value ?? "—"}</strong><span>{label}</span></div>)}</div>
        <p>Los análisis pedagógicos individuales se mantienen en las cuentas docentes autorizadas.</p>
      </section>}
      {section === "users" && <section className="admin-supplement">
        <h2>Usuarios y roles</h2><p>Directorio de usuarios del personal. Los accesos están protegidos por permisos de administrador y docente.</p>
        <div className="admin-sup-rows">{staff.data?.filter(u=>u.role!=="STUDENT").map(u=><div key={u.id}><span>{u.display_name} · {u.role==="ADMIN"?"Administrador":"Docente"}</span><strong>{u.is_active?"Activo":"Inactivo"}</strong></div>)}</div>
      </section>}
      {section === "configuration" && <section className="admin-supplement">
        <h2>Configuración</h2><p>KAWSAY AI utiliza permisos por roles, autenticación y registro de auditoría. Las opciones de configuración del servidor se administran de forma privada desde Render.</p>
        <div className="admin-sup-rows"><div><span>Autenticación</span><strong>Habilitada</strong></div><div><span>Acceso administrativo</span><strong>Restringido</strong></div></div>
      </section>}
      {section === "backups" && <section className="admin-supplement">
        <h2>Respaldos</h2><p>Atención: esta demostración utiliza SQLite en el sistema de archivos efímero de Render Free. El contenido puede perderse durante reinicios o despliegues.</p>
        <p>Para datos escolares reales se necesita una base de datos persistente, respaldos automatizados y una política de recuperación antes de usar este servicio.</p>
        <div className="admin-sup-rows"><div><span>Persistencia garantizada</span><strong>No disponible en esta demo</strong></div></div>
      </section>}
    </div>
  );
}
