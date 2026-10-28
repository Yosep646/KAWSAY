import { useState, type FormEvent } from "react";
import { useAuth } from "../app/AuthContext";
import { CurriculumDocuments } from "../components/CurriculumDocuments";
import { Badge, Card, ErrorBox, Loading } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import type { Framework, FrameworkTree, Grade, PlanBrief, PlanVersionTree } from "../types/api";
import { errMsg, gradeLabel } from "../utils/format";

export function Planning() {
  const { user } = useAuth();
  const plans = useAsync(() => api.get<PlanBrief[]>("/planning/plans"), []);
  const frameworks = useAsync(() => api.get<Framework[]>("/curriculum/frameworks"), []);
  const [versionId, setVersionId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [year, setYear] = useState(new Date().getFullYear());
  const [fw, setFw] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    try { setErr(null); await api.post("/planning/plans", { academic_year: year, framework_id: fw || frameworks.data?.[0]?.id, name }); setName(""); await plans.reload(); } catch (x) { setErr(errMsg(x)); }
  };
  return (
    <div>
      <h2>Planificación de la institución</h2>
      <p className="muted">La planificación vigente define QUÉ corresponde trabajar. Cada cambio crea una versión; las tareas históricas conservan la versión con la que se crearon.</p>
      <CurriculumDocuments />
      <ErrorBox message={plans.error ?? err} />
      {user?.role === "TEACHER" && (
        <Card title="Nueva planificación">
          <form className="row" onSubmit={(e) => void create(e)}>
            <label>Nombre<input value={name} onChange={(e) => setName(e.target.value)} required minLength={2} /></label>
            <label>Año<input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} /></label>
            <label>Marco curricular<select value={fw} onChange={(e) => setFw(e.target.value)}>
              {frameworks.data?.map((f) => <option key={f.id} value={f.id}>{f.name} {f.is_demo ? "(DEMO)" : ""}</option>)}</select></label>
            <button type="submit">Crear</button>
          </form>
        </Card>
      )}
      {plans.loading ? <Loading /> : plans.data?.map((p) => (
        <Card key={p.id} title={p.name} actions={user?.role === "TEACHER" && <button className="ghost" onClick={() => void api.post(`/planning/plans/${p.id}/versions`).then(() => plans.reload()).catch((x: unknown) => setErr(errMsg(x)))}>Nueva versión</button>}>
          <ul className="list">{p.versions.map((v) => (
            <li key={v.id}><button className="link" onClick={() => setVersionId(v.id)}>Versión {v.label}</button> <Badge tone={v.status === "ACTIVE" ? "ok" : v.status === "ARCHIVED" ? "muted" : "info"}>{v.status}</Badge></li>))}</ul>
        </Card>))}
      {versionId && <VersionEditor key={versionId} versionId={versionId} frameworkId={plans.data?.find((p) => p.versions.some((v) => v.id === versionId))?.framework_id ?? ""} onChanged={() => void plans.reload()} />}
    </div>
  );
}

function VersionEditor({ versionId, frameworkId, onChanged }: { versionId: string; frameworkId: string; onChanged: () => void }) {
  const { user } = useAuth();
  const tree = useAsync(() => api.get<PlanVersionTree>(`/planning/versions/${versionId}`), [versionId]);
  const fw = useAsync(() => api.get<FrameworkTree>(`/curriculum/frameworks/${frameworkId}`), [frameworkId]);
  const grades = useAsync(() => api.get<Grade[]>("/curriculum/grades"), []);
  const [err, setErr] = useState<string | null>(null);
  const [periodName, setPeriodName] = useState("");
  const [u, setU] = useState({ period: "", grade: 0, subject: "", title: "" });
  const [t, setT] = useState({ unit: "", comp: "", title: "", objective: "" });
  const draft = tree.data?.status === "DRAFT";
  const run = async (fn: () => Promise<unknown>) => { try { setErr(null); await fn(); await tree.reload(); onChanged(); } catch (x) { setErr(errMsg(x)); } };
  const allUnits = tree.data?.periods.flatMap((p) => p.units) ?? [];
  const subj = fw.data?.subjects.find((s) => s.id === (allUnits.find((x) => x.id === t.unit)?.subject_id ?? ""));

  return (
    <Card title={tree.data ? `Versión ${tree.data.label} — ${tree.data.status}` : "Versión"}>
      <ErrorBox message={tree.error ?? err} />
      {tree.loading ? <Loading /> : tree.data?.periods.map((p) => (
        <div key={p.id}><h4>{p.name}</h4><ul>{p.units.map((un) => (
          <li key={un.id}><strong>{un.title}</strong> ({gradeLabel(grades.data?.find((g) => g.id === un.grade_id) ?? { level: "PRIMARIA", number: un.grade_id })})
            <ul>{un.topics.map((tp) => <li key={tp.id}>{tp.title} — <em>{tp.learning_objective}</em></li>)}</ul></li>))}</ul></div>))}
      {user?.role === "TEACHER" && draft && fw.data && (
        <div className="stack">
          <form className="row" onSubmit={(e) => { e.preventDefault(); void run(() => api.post(`/planning/versions/${versionId}/periods`, { name: periodName, sequence: (tree.data?.periods.length ?? 0) + 1 })).then(() => setPeriodName("")); }}>
            <label>Periodo<input value={periodName} onChange={(e) => setPeriodName(e.target.value)} placeholder="I Bimestre" required /></label><button>Agregar periodo</button></form>
          <form className="row" onSubmit={(e) => { e.preventDefault(); void run(() => api.post(`/planning/versions/${versionId}/units`, { period_id: u.period || tree.data?.periods[0]?.id, grade_id: u.grade || grades.data?.[0]?.id, subject_id: u.subject || fw.data?.subjects[0]?.id, title: u.title })); }}>
            <label>Periodo<select value={u.period} onChange={(e) => setU({ ...u, period: e.target.value })}>{tree.data?.periods.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
            <label>Grado<select value={u.grade} onChange={(e) => setU({ ...u, grade: Number(e.target.value) })}>{grades.data?.map((g) => <option key={g.id} value={g.id}>{gradeLabel(g)}</option>)}</select></label>
            <label>Área<select value={u.subject} onChange={(e) => setU({ ...u, subject: e.target.value })}>{fw.data.subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></label>
            <label>Unidad<input value={u.title} onChange={(e) => setU({ ...u, title: e.target.value })} required minLength={2} /></label><button>Agregar unidad</button></form>
          <form className="row" onSubmit={(e) => { e.preventDefault(); void run(() => api.post(`/planning/versions/${versionId}/topics`, { unit_id: t.unit || allUnits[0]?.id, competency_id: t.comp || subj?.competencies[0]?.id, title: t.title, learning_objective: t.objective })); }}>
            <label>Unidad<select value={t.unit} onChange={(e) => setT({ ...t, unit: e.target.value })}>{allUnits.map((x) => <option key={x.id} value={x.id}>{x.title}</option>)}</select></label>
            <label>Competencia<select value={t.comp} onChange={(e) => setT({ ...t, comp: e.target.value })}>{(subj ?? fw.data.subjects.find((s) => s.id === allUnits[0]?.subject_id))?.competencies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
            <label>Tema<input value={t.title} onChange={(e) => setT({ ...t, title: e.target.value })} required minLength={2} /></label>
            <label>Objetivo<input value={t.objective} onChange={(e) => setT({ ...t, objective: e.target.value })} required minLength={5} /></label><button>Agregar tema</button></form>
          <button onClick={() => void run(() => api.post(`/planning/versions/${versionId}/submit`))}>Enviar a revisión</button>
        </div>
      )}
      {user?.role === "ADMIN" && tree.data?.status === "UNDER_REVIEW" && (
        <div className="row"><button onClick={() => void run(() => api.post(`/planning/versions/${versionId}/approve`))}>Aprobar</button>
          <button className="ghost" onClick={() => void run(() => api.post(`/planning/versions/${versionId}/reject`))}>Devolver a borrador</button></div>)}
      {user?.role === "ADMIN" && tree.data?.status === "APPROVED" && <button onClick={() => void run(() => api.post(`/planning/versions/${versionId}/activate`))}>Activar versión</button>}
    </Card>
  );
}
