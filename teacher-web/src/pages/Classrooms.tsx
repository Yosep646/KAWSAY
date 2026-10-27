import { useState, type FormEvent } from "react";
import { Card, ErrorBox, Loading } from "../components/ui";
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
  const [err, setErr] = useState<string | null>(null);

  const add = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setErr(null);
      const gid = gradeId || grades.data?.[0]?.id;
      setCreated(await api.post<StudentCredentials>("/students", { display_name: name, grade_id: gid, classroom_id: id }));
      setName(""); await room.reload();
    } catch (x) { setErr(errMsg(x)); }
  };
  const reset = async (sid: string) => {
    try { const r = await api.post<{ pin: string }>(`/students/${sid}/reset-pin`); setCreated({ id: sid, display_name: "Nuevo PIN", grade_id: 0, login_code: "(el mismo código)", pin: r.pin }); } catch (x) { setErr(errMsg(x)); }
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
      <form className="row" onSubmit={(e) => void add(e)}>
        <label>Nombre<input value={name} onChange={(e) => setName(e.target.value)} required maxLength={120} /></label>
        <label>Grado<select value={gradeId} onChange={(e) => setGradeId(Number(e.target.value))}>
          {grades.data?.map((g) => <option key={g.id} value={g.id}>{gradeLabel(g)}</option>)}</select></label>
        <button type="submit">Agregar estudiante</button>
      </form>
      {created && (
        <div className="notice" role="status">
          <strong>Credenciales de {created.display_name}</strong> — se muestran UNA sola vez. Entrégalas al estudiante.
          <div className="creds">Código: <code>{created.login_code}</code> · PIN: <code>{created.pin}</code></div>
          <button className="ghost" onClick={() => setCreated(null)}>Ya las anoté</button>
        </div>
      )}
    </Card>
  );
}
