import { useState, type FormEvent } from "react";
import { api } from "../services/api";
import { useAsync } from "../hooks/useAsync";
import { ErrorBox, Loading } from "./ui";
import { errMsg } from "../utils/format";

interface Candidate {
  id: string;
  display_name: string;
  grade_number: number;
  previous_classroom: string;
  previous_academic_year: number;
}

export function ExistingEnrollment({
  classroomId, onEnrolled,
}: { classroomId: string; onEnrolled: () => Promise<unknown> }) {
  const students = useAsync(() => api.get<Candidate[]>(`/classrooms/${classroomId}/eligible-students`), [classroomId]);
  const [studentId, setStudentId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function enroll(event: FormEvent) {
    event.preventDefault();
    if (!studentId || busy) return;
    if (!window.confirm("Se conservará el grado y el historial del estudiante. ¿Confirmas la nueva matrícula?")) return;
    try {
      setBusy(true);
      setMessage(null); setError(null);
      await api.post(`/classrooms/${classroomId}/enrollments`, { student_id: studentId });
      setStudentId("");
      await Promise.all([students.reload(), onEnrolled()]);
      setMessage("Matrícula confirmada. El estudiante conserva su cuenta y recibe las tareas ya publicadas para su grado.");
    } catch (reason) { setError(errMsg(reason)); }
    finally { setBusy(false); }
  }

  return <section className="student-enroll" aria-labelledby="existing-enrollment-title">
    <div className="student-enroll-heading">
      <div><h3 id="existing-enrollment-title">Matricular estudiante existente</h3>
        <p>Reutiliza la cuenta de un alumno que ya estudió contigo en un año anterior de la misma institución.</p></div>
    </div>
    <ErrorBox message={students.error ?? error}/>
    {message && <p role="status" className="notice">{message}</p>}
    {students.loading ? <Loading /> : !students.data?.length
      ? <p>No hay estudiantes de años anteriores disponibles. Usa «Registrar nuevo estudiante» si es su primer ingreso.</p>
      : <form className="student-enroll-form" onSubmit={(e) => void enroll(e)}>
          <label htmlFor="existing-student">Estudiante de año anterior
            <select id="existing-student" value={studentId} onChange={e => setStudentId(e.target.value)} required>
              <option value="">Selecciona un estudiante</option>
              {students.data.map(item => <option key={item.id} value={item.id}>
                {item.display_name} · {item.grade_number}.º · {item.previous_classroom} ({item.previous_academic_year})
              </option>)}
            </select>
          </label>
          <div className="student-enroll-footer"><p>Evita cuentas duplicadas. Una nueva matrícula no modifica el grado oficial.</p>
            <button type="submit" disabled={!studentId || busy}>{busy ? "Matriculando…" : "Confirmar matrícula"}</button>
          </div>
        </form>}
  </section>;
}
