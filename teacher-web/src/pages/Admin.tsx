import { useState, type FormEvent } from "react";
import { useAuth } from "../app/AuthContext";
import { Card, ErrorBox } from "../components/ui";
import { Icon, type IconName } from "../components/Icon";
import { AdminOverview, type AdminStatistics } from "./AdminOverview";
import { CurriculumDocuments } from "../components/CurriculumDocuments";
import "./admin-sections.css";
import "./admin-institutions.css";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { errMsg } from "../utils/format";

interface School { id: string; name: string; region?: string | null }
interface Audit { id: string; action: string; target_type: string; created_at: string; request_id: string | null }
interface Ev { id: string; type: string; status: string; attempts: number; last_error: string | null }
interface Staff { id: string; email: string | null; display_name: string; role: string; is_active: boolean }

type AdminSection = "overview" | "schools" | "teachers" | "curriculum" | "system" | "students" | "tasks" | "reports" | "users" | "configuration" | "backups";
const pageMeta: Record<Exclude<AdminSection,"overview">,{label:string;title:string;description:string;icon:IconName}> = {
  schools:{label:"GESTIÓN ACADÉMICA",title:"Instituciones educativas",description:"Administra los colegios y sedes de tu comunidad educativa.",icon:"classroom"},
  teachers:{label:"GESTIÓN ACADÉMICA",title:"Equipo docente",description:"Registra docentes y administra sus accesos de forma segura.",icon:"students"},
  students:{label:"SEGUIMIENTO EDUCATIVO",title:"Estudiantes",description:"Consulta indicadores agregados y la distribución por grado.",icon:"graduation"},
  curriculum:{label:"CONTENIDOS Y APRENDIZAJE",title:"Currículo y contenidos",description:"Revisa e importa marcos curriculares validados por una persona.",icon:"book"},
  tasks:{label:"SEGUIMIENTO EDUCATIVO",title:"Asignaciones y tareas",description:"Visualiza las tareas y asignaciones de los grupos educativos.",icon:"tasks"},
  reports:{label:"ANÁLISIS Y REPORTES",title:"Reportes de aprendizaje",description:"Consulta estadísticas reales de la plataforma, sin datos simulados.",icon:"chart"},
  system:{label:"SEGURIDAD Y CONTROL",title:"Auditoría y registros",description:"Consulta las operaciones registradas y los eventos de automatización.",icon:"shield"},
  users:{label:"SEGURIDAD Y CONTROL",title:"Usuarios y roles",description:"Supervisa el acceso del personal y los permisos activos.",icon:"students"},
  configuration:{label:"CONFIGURACIÓN",title:"Configuración del sistema",description:"Consulta los controles de acceso y la configuración disponible.",icon:"settings"},
  backups:{label:"SEGURIDAD DE DATOS",title:"Respaldos y persistencia",description:"Revisa el estado de almacenamiento y sus limitaciones.",icon:"database"},
};

export function Admin({ section = "overview" }: { section?: AdminSection }) {
  const { user } = useAuth();
  const schools = useAsync(() => api.get<School[]>("/schools"), []);
  const audit = useAsync(() => api.get<Audit[]>("/audit-log?limit=20"), []);
  const events = useAsync(() => api.get<Ev[]>("/automation/events?limit=20"), []);
  const staff = useAsync(() => api.get<Staff[]>("/users?limit=100"), []);
  const stats = useAsync(() => api.get<AdminStatistics>("/analytics/admin/overview"), []);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [school, setSchool] = useState("");
  const [schoolRegion, setSchoolRegion] = useState("");
  const [schoolBusy, setSchoolBusy] = useState(false);
  const [schoolQuery, setSchoolQuery] = useState("");
  const [staffQuery, setStaffQuery] = useState("");
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [t, setT] = useState({ email: "", name: "", password: "", school_id: "" });
  const [showTeacherPassword, setShowTeacherPassword] = useState(false);
  const [teacherBusy, setTeacherBusy] = useState(false);

  const run = async (fn: () => Promise<unknown>, ok: string) => { try { setErr(null); await fn(); setMsg(ok); await schools.reload(); } catch (x) { setErr(errMsg(x)); } };
  const addSchool = async (e: FormEvent) => {
    e.preventDefault();
    if (schoolBusy) return;
    setErr(null);setMsg(null);setSchoolBusy(true);
    try {
      await api.post("/schools", { name: school.trim(), region: schoolRegion.trim() || null });
      setSchool("");setSchoolRegion("");
      setMsg("Institución creada correctamente.");
      await Promise.all([schools.reload(), stats.reload()]);
    } catch (error) {setErr(errMsg(error));}
    finally {setSchoolBusy(false);}
  };
  const changeStaffStatus = async (member: Staff) => {
    if (member.id === user?.id) {setErr("No puedes modificar el estado de tu propia cuenta.");return;}
    const action = member.is_active ? "desactivar" : "reactivar";
    if (!window.confirm(`¿Deseas ${action} el acceso de ${member.display_name}? ${member.is_active ? "Las sesiones activas quedarán revocadas." : ""}`)) return;
    setUpdatingId(member.id);setErr(null);setMsg(null);
    try {
      await api.patch(`/users/${member.id}`,{is_active:!member.is_active});
      await staff.reload();
      setMsg(`Acceso de ${member.display_name} actualizado correctamente.`);
    } catch (error) {setErr(errMsg(error));}
    finally {setUpdatingId(null);}
  };
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

  const page = section === "overview" ? null : pageMeta[section];
  const pageCount = section === "schools" ? schools.data?.length : section === "teachers" ? staff.data?.filter(member => member.role === "TEACHER").length : section === "students" ? stats.data?.students : section === "tasks" ? stats.data?.student_assignments : section === "users" ? staff.data?.filter(member => member.role !== "STUDENT").length : undefined;
  const countLabel = section === "schools" ? "instituciones" : section === "teachers" ? "docentes" : section === "students" ? "estudiantes" : section === "tasks" ? "asignaciones" : section === "users" ? "usuarios" : "";
  return (
    <div className={section === "overview" ? "admin-overview-page" : "admin-section-page"} data-admin-section={section}>
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
      <header className="role-hero admin-hero admin-section-hero">
        <div className="admin-hero-copy">
          <p className="eyebrow">KAWSAY AI <span className="admin-hero-separator">/</span> {page?.label}</p>
          <h2>{page?.title}</h2>
          <p>{page?.description}</p>
          <div className="admin-hero-meta"><span><Icon name="leaf"/> Educación que acompaña</span>{pageCount !== undefined && <span><Icon name={page?.icon ?? "dashboard"}/> {pageCount.toLocaleString("es-PE")} {countLabel}</span>}</div>
        </div>
        <div className="admin-hero-emblem" aria-hidden="true">{page && <Icon name={page.icon}/>}</div>
      </header>
      )}
      <ErrorBox message={section === "overview" ? null : schools.error ?? (section === "system" ? audit.error ?? events.error : null)} />
      <ErrorBox message={err} />
      {msg && <p role="status" className="notice">{msg}</p>}
      {section === "schools" && <section className="admin-institutions" aria-label="Gestión de instituciones educativas">
        <div className="admin-institutions-layout">
          <section className="admin-institution-panel admin-institutions-directory" aria-labelledby="admin-institutions-heading">
            <header className="admin-institution-panel-head">
              <span className="admin-institution-symbol"><Icon name="classroom"/></span>
              <div className="admin-institution-head-copy">
                <p className="admin-institution-kicker">DIRECTORIO EDUCATIVO</p>
                <h3 id="admin-institutions-heading">Instituciones registradas</h3>
                <p>Consulta las instituciones asociadas a KAWSAY AI.</p>
              </div>
              <span className="admin-institution-count">{schools.loading ? "…" : schools.data?.length ?? "—"} <small>registradas</small></span>
            </header>
            <label className="admin-institution-search-label" htmlFor="admin-institution-search">Buscar institución</label>
            <div className="admin-institution-search">
              <Icon name="search"/>
              <input id="admin-institution-search" type="search" autoComplete="off"
                value={schoolQuery} onChange={e=>setSchoolQuery(e.target.value)}
                placeholder="Busca por nombre o región…"/>
            </div>
            {schools.loading && <p className="admin-institution-state">Cargando instituciones…</p>}
            {!schools.loading && !schools.data?.length && <div className="admin-institution-empty">
              <Icon name="classroom"/>
              <strong>Aún no hay instituciones registradas</strong>
              <span>Utiliza el formulario para registrar tu primera institución.</span>
            </div>}
            {schools.data?.length ? <div className="admin-institution-list">
              {schools.data.filter(s=>`${s.name} ${s.region || ""}`.toLocaleLowerCase("es").includes(schoolQuery.trim().toLocaleLowerCase("es"))).map(s=>
                <article className="admin-institution-item" key={s.id}>
                  <span className="admin-institution-item-icon"><Icon name="classroom"/></span>
                  <div className="admin-institution-item-info">
                    <strong>{s.name}</strong>
                    <small><Icon name="map-pin"/> {s.region || "Región no especificada"}</small>
                  </div>
                  <span className="admin-institution-item-tag">Registrada</span>
                </article>)}
              {schools.data.filter(s=>`${s.name} ${s.region || ""}`.toLocaleLowerCase("es").includes(schoolQuery.trim().toLocaleLowerCase("es"))).length === 0 &&
                <div className="admin-institution-empty"><Icon name="search"/><strong>No se encontraron instituciones</strong><span>Prueba con otro nombre o región.</span></div>}
            </div> : null}
            <footer className="admin-institution-panel-foot"><Icon name="shield"/> Información consultada desde el sistema, sin datos simulados.</footer>
          </section>
          <section className="admin-institution-panel admin-institutions-create" aria-labelledby="admin-create-school-heading">
            <header className="admin-institution-panel-head">
              <span className="admin-institution-symbol admin-institution-symbol-create"><Icon name="leaf"/></span>
              <div className="admin-institution-head-copy">
                <p className="admin-institution-kicker">NUEVA INSTITUCIÓN</p>
                <h3 id="admin-create-school-heading">Registrar institución</h3>
                <p>Agrega un colegio o sede a la plataforma.</p>
              </div>
            </header>
            <form className="admin-institution-form" onSubmit={(e)=>void addSchool(e)}>
              <label htmlFor="new-school-name">Nombre de la institución <span aria-hidden="true">*</span>
                <input id="new-school-name" autoComplete="organization" value={school}
                  onChange={e=>setSchool(e.target.value)}
                  placeholder="Ej. I. E. Rural San José" minLength={2} maxLength={180} required />
              </label>
              <label htmlFor="new-school-region">Región o departamento <small>(opcional)</small>
                <input id="new-school-region" value={schoolRegion}
                  onChange={e=>setSchoolRegion(e.target.value)}
                  placeholder="Ej. Huánuco" maxLength={120} />
              </label>
              <button type="submit" disabled={schoolBusy || school.trim().length < 2}>
                {schoolBusy ? "Registrando…" : "Crear institución"}<Icon name="arrow"/>
              </button>
            </form>
            <div className="admin-institution-next">
              <Icon name="check"/>
              <p>Después de registrar la institución podrás asociarle docentes, aulas y estudiantes.</p>
            </div>
          </section>
        </div>
      </section>}
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
              <div className="admin-directory-toolbar"><span className="admin-directory-count">{staff.data?.filter((u) => u.role === "TEACHER").length ?? "—"} docentes</span><input type="search" aria-label="Buscar docentes" value={staffQuery} onChange={e=>setStaffQuery(e.target.value)} placeholder="Buscar docente…" /></div>
            </div>
            {staff.loading && <p className="muted">Consultando docentes…</p>}
            {staff.error && <ErrorBox message={staff.error} />}
            {staff.data?.filter((u) => u.role === "TEACHER").length === 0 && <p className="admin-empty">Aún no se han registrado docentes.</p>}
            <div className="admin-directory-grid">
              {staff.data?.filter((u) => u.role === "TEACHER" && `${u.display_name} ${u.email ?? ""}`.toLocaleLowerCase().includes(staffQuery.toLocaleLowerCase().trim())).map((u) => (
                <div className="admin-person" key={u.id}>
                  <span className="admin-person-avatar">{u.display_name.trim().slice(0, 1).toUpperCase()}</span>
                  <div><strong>{u.display_name}</strong><small>{u.email}</small></div>
                  <div className="admin-status-actions"><span className={u.is_active ? "admin-person-status" : "admin-person-status disabled"}>
                    {u.is_active ? "Activo" : "Inactivo"}
                  </span><button type="button" className="ghost" disabled={updatingId===u.id || u.id===user?.id} onClick={()=>void changeStaffStatus(u)}>{updatingId===u.id?"Actualizando…":u.is_active?"Desactivar":"Reactivar"}</button></div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
      {section === "curriculum" && <CurriculumDocuments />}
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
        <div className="admin-sup-rows">{staff.data?.filter(u=>u.role!=="STUDENT").map(u=><div key={u.id}><span>{u.display_name} · {u.role==="ADMIN"?"Administrador":"Docente"} · {u.email}</span><span className="admin-user-rows-end"><strong>{u.is_active?"Activo":"Inactivo"}</strong>{u.id!==user?.id&&<button type="button" className="ghost" disabled={updatingId===u.id} onClick={()=>void changeStaffStatus(u)}>{updatingId===u.id?"Guardando…":u.is_active?"Desactivar":"Reactivar"}</button>}</span></div>)}</div>
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
