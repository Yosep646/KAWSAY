import { useEffect, useState, type FormEvent } from "react";
import { Card, ErrorBox, Loading } from "../components/ui";
import { Icon } from "../components/Icon";
import "./student-enroll.css";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import type {
  Classroom, ClassroomDetail, Grade, Language, StudentBrief, StudentCredentials, StudentDetail,
  StudentLanguages, StudentLanguagesInput,
} from "../types/api";
import { errMsg, gradeLabel } from "../utils/format";

export function Students() {
  const rooms = useAsync(() => api.get<Classroom[]>("/classrooms"), []);
  const languages = useAsync(() => api.get<Language[]>("/languages"), []);
  const [classroomId, setClassroomId] = useState("");

  return (
    <div className="student-management">
      <header className="student-management-hero"><span><Icon name="graduation" /> GESTIÓN DEL AULA</span><h2>Mis estudiantes</h2><p>Registra estudiantes y asigna sus credenciales para entrar a KAWSAY AI, incluso desde su teléfono.</p></header>
      <p className="muted">Gestiona estudiantes y registra el idioma que cada persona declara. KAWSAY nunca lo infiere por su ubicación.</p>
      <Card title="Seleccionar aula">
        <ErrorBox message={rooms.error ?? languages.error} />
        {rooms.loading || languages.loading ? <Loading /> : rooms.data?.length ? (
          <label>Aula
            <select aria-label="Aula" value={classroomId} onChange={(e) => setClassroomId(e.target.value)}>
              <option value="">Selecciona un aula</option>
              {rooms.data.map((room) => <option key={room.id} value={room.id}>{room.name} · {room.academic_year}</option>)}
            </select>
          </label>
        ) : <p>No hay aulas creadas. Crea una en “Mis aulas” antes de registrar estudiantes.</p>}
      </Card>
      {classroomId && languages.data && <ClassroomStudents key={classroomId} classroomId={classroomId} languages={languages.data} />}
    </div>
  );
}

function ClassroomStudents({ classroomId, languages }: { classroomId: string; languages: Language[] }) {
  const room = useAsync(() => api.get<ClassroomDetail>(`/classrooms/${classroomId}`), [classroomId]);
  const grades = useAsync(() => api.get<Grade[]>("/curriculum/grades"), []);
  const [selected, setSelected] = useState<StudentBrief | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loginMode, setLoginMode] = useState<"email" | "pin">("email");
  const [busy, setBusy] = useState(false);
  const [resetTarget, setResetTarget] = useState<StudentBrief | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [resetBusy, setResetBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [gradeId, setGradeId] = useState(0);
  const [credentials, setCredentials] = useState<StudentCredentials | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [languageRevision, setLanguageRevision] = useState(0);

  const add = async (event: FormEvent) => {
    event.preventDefault();
    if (busy) return;
    const selectedGrade = gradeId || grades.data?.[0]?.id;
    if (!selectedGrade) return setError("No hay grados disponibles para registrar al estudiante.");
    if (loginMode === "email" && password.length < 12) return setError("La contraseña debe tener al menos 12 caracteres.");
    try {
      setBusy(true); setError(null); setNotice(null); setCredentials(null);
      const created = await api.post<StudentCredentials>("/students", {
        display_name: name.trim(), grade_id: selectedGrade, classroom_id: classroomId,
        ...(loginMode === "email" ? {email: email.trim().toLowerCase(), password} : {}),
      });
      setCredentials(created);
      setNotice(loginMode === "email"
        ? "Cuenta estudiantil creada. Entrega el correo y contraseña de manera privada al estudiante o su familia."
        : "Cuenta estudiantil creada con código y PIN para acceso tradicional.");
      setName(""); setEmail(""); setPassword(""); setShowPassword(false);
      await room.reload();
    } catch (reason) { setError(errMsg(reason)); } finally { setBusy(false); }
  };

  const resetAccess = async (student: StudentBrief) => {
    try {
      setError(null); setNotice(null); setCredentials(null); setResetTarget(null);
      const detail = await api.get<StudentDetail>(`/students/${student.id}`);
      if (detail.email) {
        setResetTarget(student); setNewPassword("");
      } else {
        const pin = await api.post<{ pin: string }>(`/students/${student.id}/reset-pin`);
        setCredentials({ id: student.id, display_name: student.display_name, grade_id: student.grade_id,
          login_code: detail.login_code, pin: pin.pin });
        setNotice("El PIN anterior ya no funciona. Entrega estas nuevas credenciales en privado.");
      }
    } catch (reason) { setError(errMsg(reason)); }
  };

  const savePassword = async (event: FormEvent) => {
    event.preventDefault();
    if (!resetTarget || newPassword.length < 12 || resetBusy) return;
    try {
      setResetBusy(true); setError(null);
      await api.post(`/students/${resetTarget.id}/reset-password`, {password: newPassword});
      setNotice("Contraseña actualizada. Las sesiones anteriores quedaron revocadas. Comparte la nueva contraseña por un canal privado.");
      setResetTarget(null); setNewPassword(""); setShowResetPassword(false);
    } catch (reason) { setError(errMsg(reason)); } finally { setResetBusy(false); }
  };

  return (
    <Card title={room.data?.name ?? "Estudiantes del aula"}>
      <ErrorBox message={room.error ?? grades.error ?? error} />
      {notice && <p className="notice" role="status">{notice}</p>}
      {room.loading ? <Loading /> : room.data?.students.length ? (
        <div className="table-wrap"><table>
          <thead><tr><th>Estudiante</th><th>Grado</th><th>Idioma preferido</th><th>Acciones</th></tr></thead>
          <tbody>{room.data.students.map((student) => (
            <tr key={student.id}>
              <td className="student-name">{student.display_name}</td>
              <td>{gradeLabel({ level: student.grade_level, number: student.grade_number })}</td>
              <td><LanguageSummary key={`${student.id}-${languageRevision}`} studentId={student.id} /></td>
              <td className="row">
                <button type="button" className="ghost" onClick={() => setSelected(student)}>Configurar idioma</button>
                <button type="button" className="ghost" onClick={() => void resetAccess(student)}>Restablecer acceso</button>
              </td>
            </tr>
          ))}</tbody>
        </table></div>
      ) : <p>Esta aula todavía no tiene estudiantes.</p>}

      <section className="student-enroll" aria-labelledby="student-enroll-title">
        <div className="student-enroll-heading"><span className="student-enroll-badge"><Icon name="students" /></span>
          <div><p className="student-enroll-kicker">ACCESO EDUCATIVO</p><h3 id="student-enroll-title">Registrar nuevo estudiante</h3>
          <p>El docente asigna el correo y la contraseña para ingresar al espacio de aprendizaje.</p></div>
        </div>
        <div className="student-enroll-method" role="group" aria-label="Método de inicio de sesión">
          <button type="button" className={loginMode === "email" ? "active" : ""} aria-pressed={loginMode === "email"} onClick={() => {setLoginMode("email"); setCredentials(null); setError(null);}}>Correo y contraseña</button>
          <button type="button" className={loginMode === "pin" ? "active" : ""} aria-pressed={loginMode === "pin"} onClick={() => {setLoginMode("pin"); setCredentials(null); setError(null);}}>Código y PIN</button>
        </div>
        <form className="student-enroll-form" onSubmit={(event) => void add(event)} autoComplete="off">
          <label htmlFor="new-student-name">Nombre completo<input id="new-student-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Ej. María Quispe" required maxLength={120} autoComplete="off" /></label>
          <label htmlFor="new-student-grade">Grado<select id="new-student-grade" value={gradeId || grades.data?.[0]?.id || ""} onChange={(e) => setGradeId(Number(e.target.value))} required>
            {grades.data?.map((grade) => <option key={grade.id} value={grade.id}>{gradeLabel(grade)}</option>)}
          </select></label>
          {loginMode === "email" && <>
            <label htmlFor="new-student-email">Correo electrónico del estudiante<input id="new-student-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="estudiante@colegio.edu.pe" autoComplete="off" required /></label>
            <div className="student-enroll-password">
              <label htmlFor="new-student-password">Contraseña inicial (mínimo 12 caracteres)</label>
              <div className="student-enroll-password-control"><input id="new-student-password" type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} minLength={12} maxLength={128} placeholder="Establece una contraseña segura" autoComplete="new-password" required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"} aria-pressed={showPassword}><Icon name={showPassword ? "eye-off" : "eye"} />{showPassword ? "Ocultar" : "Mostrar"}</button>
              </div>
              <p className="student-enroll-hint">{password.length >= 12 ? "✓ Longitud mínima cumplida" : `${password.length}/12 caracteres mínimos`}. No reutilices contraseñas personales.</p>
            </div>
          </>}
          <div className="student-enroll-footer"><p><Icon name="shield" /> Solo el docente asignado puede crear cuentas en esta aula. La contraseña se guarda con hash.</p>
            <button type="submit" disabled={busy || !grades.data?.length}>{busy ? "Registrando…" : "Crear estudiante"} <Icon name="arrow" /></button></div>
        </form>
      </section>

      {credentials && <div className="student-access-created" role="status">
        <strong><Icon name="check" /> Estudiante registrado: {credentials.display_name}</strong>
        {credentials.email ? <p>Acceso mediante el correo <code>{credentials.email}</code> y la contraseña que acabas de establecer. Por seguridad, el servidor no vuelve a mostrarla.</p>
          : <p>Credenciales de un solo uso: <span>Código <code>{credentials.login_code}</code> · PIN <code>{credentials.pin}</code></span></p>}
        <button type="button" className="ghost" onClick={() => setCredentials(null)}>Entendido</button>
      </div>}
      {resetTarget && <form className="student-enroll-reset" onSubmit={(event) => void savePassword(event)}>
        <h3>Cambiar contraseña de {resetTarget.display_name}</h3>
        <p>La nueva contraseña desactivará todas las sesiones anteriores del estudiante.</p>
        <label htmlFor="reset-student-password">Nueva contraseña</label>
        <div className="student-enroll-password-control"><input id="reset-student-password" type={showResetPassword ? "text" : "password"} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} minLength={12} maxLength={128} autoComplete="new-password" required />
          <button type="button" onClick={() => setShowResetPassword(!showResetPassword)} aria-label={showResetPassword ? "Ocultar contraseña" : "Mostrar contraseña"}><Icon name={showResetPassword ? "eye-off" : "eye"} />{showResetPassword ? "Ocultar" : "Mostrar"}</button>
        </div>
        <div className="row"><button type="submit" disabled={resetBusy || newPassword.length < 12}>{resetBusy ? "Guardando…" : "Cambiar contraseña"}</button><button type="button" className="ghost" onClick={() => setResetTarget(null)}>Cancelar</button></div>
      </form>}}

      {selected && <LanguageEditor key={selected.id} student={selected} languages={languages} onClose={() => setSelected(null)} onSaved={() => setLanguageRevision((value) => value + 1)} />}
    </Card>
  );
}

function LanguageSummary({ studentId }: { studentId: string }) {
  const preference = useAsync(() => api.get<StudentLanguages>(`/students/${studentId}/languages`), [studentId]);
  if (preference.loading) return <span className="muted">Cargando…</span>;
  if (preference.error) return <span className="error">No disponible</span>;
  return <span>{preference.data?.preferred_language?.toUpperCase() ?? "Sin especificar"}</span>;
}

function LanguageEditor({ student, languages, onClose, onSaved }: { student: StudentBrief; languages: Language[]; onClose: () => void; onSaved: () => void }) {
  const preference = useAsync(() => api.get<StudentLanguages>(`/students/${student.id}/languages`), [student.id]);
  const [mother, setMother] = useState("");
  const [variantId, setVariantId] = useState("");
  const [preferred, setPreferred] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!preference.data) return;
    setMother(preference.data.mother_language ?? "");
    setVariantId(preference.data.mother_variant_id ?? "");
    setPreferred(preference.data.preferred_language ?? "");
  }, [preference.data]);

  const variants = languages.find((language) => language.code === mother)?.variants ?? [];
  const save = async (event: FormEvent) => {
    event.preventDefault();
    const body: StudentLanguagesInput = {
      mother_language_code: mother || null,
      mother_variant_id: variantId || null,
      preferred_language_code: preferred || null,
    };
    try {
      setSaving(true); setError(null); setMessage(null);
      await api.put<StudentLanguages>(`/students/${student.id}/languages`, body);
      setMessage("Preferencias guardadas. El contenido traducido solo se mostrará cuando haya una traducción humana verificada.");
      await preference.reload();
      onSaved();
    } catch (reason) { setError(errMsg(reason)); } finally { setSaving(false); }
  };

  return <section className="language-form">
    <div className="card-h"><h3>Idioma de {student.display_name}</h3><button type="button" className="ghost" onClick={onClose}>Cerrar</button></div>
    <p className="muted">Registra únicamente lo declarado por el estudiante o su familia. “Sin especificar” no presupone español.</p>
    <ErrorBox message={preference.error ?? error} />
    {preference.loading ? <Loading /> : <form className="stack" onSubmit={(event) => void save(event)}>
      <div className="row">
        <label>Lengua materna<select aria-label="Lengua materna" value={mother} onChange={(e) => { setMother(e.target.value); setVariantId(""); }}>
          <option value="">Sin especificar</option>
          {languages.map((language) => <option key={language.code} value={language.code}>{language.name}</option>)}
        </select></label>
        {variants.length > 0 && <label>Variante declarada<select aria-label="Variante declarada" value={variantId} onChange={(e) => setVariantId(e.target.value)}>
          <option value="">Sin especificar</option>
          {variants.map((variant) => <option key={variant.id} value={variant.id}>{variant.name}</option>)}
        </select></label>}
        <label>Idioma preferido para aprender<select aria-label="Idioma preferido para aprender" value={preferred} onChange={(e) => setPreferred(e.target.value)}>
          <option value="">Sin especificar</option>
          {languages.map((language) => <option key={language.code} value={language.code}>{language.name}</option>)}
        </select></label>
      </div>
      <button type="submit" disabled={saving}>{saving ? "Guardando…" : "Guardar idioma"}</button>
      {message && <p className="notice" role="status">{message}</p>}
    </form>}
  </section>;
}
