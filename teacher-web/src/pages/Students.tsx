import { useEffect, useState, type FormEvent } from "react";
import { Card, ErrorBox, Loading } from "../components/ui";
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
    <div>
      <h2>Estudiantes</h2>
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
  const [gradeId, setGradeId] = useState(0);
  const [credentials, setCredentials] = useState<StudentCredentials | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [languageRevision, setLanguageRevision] = useState(0);

  const add = async (event: FormEvent) => {
    event.preventDefault();
    const selectedGrade = gradeId || grades.data?.[0]?.id;
    if (!selectedGrade) return setError("No hay grados disponibles para registrar al estudiante.");
    try {
      setError(null);
      const created = await api.post<StudentCredentials>("/students", {
        display_name: name, grade_id: selectedGrade, classroom_id: classroomId,
      });
      setCredentials(created);
      setName("");
      await room.reload();
    } catch (reason) { setError(errMsg(reason)); }
  };

  const resetPin = async (student: StudentBrief) => {
    try {
      setError(null);
      const [pin, detail] = await Promise.all([
        api.post<{ pin: string }>(`/students/${student.id}/reset-pin`),
        api.get<StudentDetail>(`/students/${student.id}`),
      ]);
      setCredentials({ id: student.id, display_name: student.display_name, grade_id: student.grade_id, login_code: detail.login_code ?? "", pin: pin.pin });
    } catch (reason) { setError(errMsg(reason)); }
  };

  return (
    <Card title={room.data?.name ?? "Estudiantes del aula"}>
      <ErrorBox message={room.error ?? grades.error ?? error} />
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
                <button type="button" className="ghost" onClick={() => void resetPin(student)}>Restablecer PIN</button>
              </td>
            </tr>
          ))}</tbody>
        </table></div>
      ) : <p>Esta aula todavía no tiene estudiantes.</p>}

      <form className="row" onSubmit={(event) => void add(event)}>
        <label>Nombre del estudiante<input value={name} onChange={(e) => setName(e.target.value)} required maxLength={120} /></label>
        <label>Grado<select value={gradeId} onChange={(e) => setGradeId(Number(e.target.value))}>
          {grades.data?.map((grade) => <option key={grade.id} value={grade.id}>{gradeLabel(grade)}</option>)}
        </select></label>
        <button type="submit">Agregar estudiante</button>
      </form>

      {credentials && <div className="notice" role="status">
        <strong>Credenciales de {credentials.display_name}</strong> · se muestran una sola vez.
        <div className="creds">Código: <code>{credentials.login_code || "sin cambios"}</code> · PIN: <code>{credentials.pin}</code></div>
        <button type="button" className="ghost" onClick={() => setCredentials(null)}>Ya las anoté</button>
      </div>}

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
