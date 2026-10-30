import { useState, type FormEvent } from "react";
import { Card, ErrorBox } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { errMsg } from "../utils/format";

interface School { id: string; name: string }
interface Audit { id: string; action: string; target_type: string; created_at: string; request_id: string | null }
interface Ev { id: string; type: string; status: string; attempts: number; last_error: string | null }

export function Admin() {
  const schools = useAsync(() => api.get<School[]>("/schools"), []);
  const audit = useAsync(() => api.get<Audit[]>("/audit-log?limit=20"), []);
  const events = useAsync(() => api.get<Ev[]>("/automation/events?limit=20"), []);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [school, setSchool] = useState("");
  const [t, setT] = useState({ email: "", name: "", password: "", school_id: "" });
  const [fwJson, setFwJson] = useState("");

  const run = async (fn: () => Promise<unknown>, ok: string) => { try { setErr(null); await fn(); setMsg(ok); await schools.reload(); } catch (x) { setErr(errMsg(x)); } };
  const addSchool = (e: FormEvent) => { e.preventDefault(); void run(() => api.post("/schools", { name: school }), "Escuela creada"); };
  const addTeacher = (e: FormEvent) => { e.preventDefault(); void run(() => api.post("/users", { role: "TEACHER", email: t.email, display_name: t.name, password: t.password, school_id: t.school_id || schools.data?.[0]?.id }), "Docente creado"); };
  const importFw = (e: FormEvent) => { e.preventDefault(); void run(() => api.post("/curriculum/frameworks", JSON.parse(fwJson) as unknown), "Marco curricular importado"); };

  return (
    <div>
      <h2>Administración</h2>
      <ErrorBox message={err} />
      {msg && <p role="status" className="notice">{msg}</p>}
      <Card title="Escuelas"><ul>{schools.data?.map((s) => <li key={s.id}>{s.name}</li>)}</ul>
        <form className="row" onSubmit={addSchool}><label>Nombre<input value={school} onChange={(e) => setSchool(e.target.value)} required /></label><button>Crear escuela</button></form></Card>
      <Card title="Nuevo docente">
        <form className="row" onSubmit={addTeacher}>
          <label>Correo<input type="email" value={t.email} onChange={(e) => setT({ ...t, email: e.target.value })} required /></label>
          <label>Nombre<input value={t.name} onChange={(e) => setT({ ...t, name: e.target.value })} required /></label>
          <label>Contraseña (≥12)<input type="password" minLength={12} value={t.password} onChange={(e) => setT({ ...t, password: e.target.value })} required /></label>
          <label>Escuela<select value={t.school_id} onChange={(e) => setT({ ...t, school_id: e.target.value })}>{schools.data?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></label>
          <button>Crear docente</button></form></Card>
      <Card title="Importar marco curricular (JSON revisado por una persona)">
        <p className="muted">Debe indicar explícitamente <code>is_demo</code>. No se importa automáticamente ningún PDF como currículo oficial.</p>
        <form className="stack" onSubmit={importFw}><textarea rows={6} value={fwJson} onChange={(e) => setFwJson(e.target.value)} required /><button>Importar</button></form></Card>
      <Card title="Auditoría de accesos a datos de estudiantes (últimos 20)"><ul>{audit.data?.map((a) => <li key={a.id}>{new Date(a.created_at).toLocaleString()} · {a.action} · {a.target_type}</li>)}</ul></Card>
      <Card title="Eventos de automatización (n8n es opcional)"><ul>{events.data?.map((e) => <li key={e.id}>{e.type} · {e.status} · intentos {e.attempts}{e.last_error ? ` · ${e.last_error}` : ""}</li>)}</ul>
        <button className="ghost" onClick={() => void run(() => api.post("/automation/dispatch"), "Despacho ejecutado").then(() => events.reload())}>Despachar pendientes</button></Card>
    </div>
  );
}
