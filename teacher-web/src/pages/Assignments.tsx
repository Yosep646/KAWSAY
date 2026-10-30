import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Badge, Card, ErrorBox, Loading } from "../components/ui";
import { QuestionsEditor } from "../components/QuestionsEditor";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import type { AdaptResult, AssignmentBrief, AssignmentDetail, Classroom, Grade, PlanVersionTree, Question, Variant } from "../types/api";
import { STATUS_LABEL, errMsg, gradeLabel } from "../utils/format";

export function AssignmentList() {
  const list = useAsync(() => api.get<AssignmentBrief[]>("/assignments"), []);
  return (
    <div>
      <h2>Actividades</h2>
      <p><Link to="/actividades/nueva">+ Crear actividad</Link></p>
      <ErrorBox message={list.error} />
      {list.loading ? <Loading /> : (list.data?.length ?? 0) === 0 ? <p className="muted">Aún no hay actividades.</p> : (
        <ul className="list">{list.data?.map((a) => <li key={a.id}><Link to={`/actividades/${a.id}`}>{a.title}</Link> <Badge tone={a.status === "PUBLISHED" ? "ok" : "info"}>{a.status}</Badge> <span className="muted">{a.mode}</span></li>)}</ul>)}
    </div>
  );
}

export function CreateAssignment() {
  const nav = useNavigate();
  const rooms = useAsync(() => api.get<Classroom[]>("/classrooms"), []);
  const grades = useAsync(() => api.get<Grade[]>("/curriculum/grades"), []);
  const [roomId, setRoomId] = useState("");
  const rid = roomId || rooms.data?.[0]?.id || "";
  const active = useAsync(() => (rid ? api.get<PlanVersionTree[]>(`/planning/active?classroom_id=${rid}`) : Promise.resolve([])), [rid]);
  const [picked, setPicked] = useState<Record<number, string>>({});
  const [title, setTitle] = useState("");
  const [instructions, setInstructions] = useState("");
  const [mode, setMode] = useState<"MANUAL" | "AI_ASSISTED">("AI_ASSISTED");
  const [err, setErr] = useState<string | null>(null);

  const units = active.data?.flatMap((v) => v.periods.flatMap((p) => p.units)) ?? [];
  const gradeIds = [...new Set(units.map((u) => u.grade_id))].sort((a, b) => a - b);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const grade_topics = Object.entries(picked).filter(([, t]) => t).map(([g, t]) => ({ grade_id: Number(g), topic_id: t }));
    try {
      setErr(null);
      const a = await api.post<AssignmentDetail>("/assignments", { classroom_id: rid, title, instructions, mode, grade_topics });
      nav(`/actividades/${a.id}`);
    } catch (x) { setErr(errMsg(x)); }
  };
  return (
    <div>
      <h2>Crear actividad</h2>
      <ErrorBox message={rooms.error} />
      <form className="stack" onSubmit={(e) => void submit(e)}>
        <label>Aula<select value={rid} onChange={(e) => { setRoomId(e.target.value); setPicked({}); }}>{rooms.data?.map((r) => <option key={r.id} value={r.id}>{r.name} ({r.academic_year})</option>)}</select></label>
        {active.loading ? <Loading /> : units.length === 0
          ? <p className="notice">Esta aula no tiene una planificación vigente (versión ACTIVA) con unidades. Pide a la administración que active la planificación.</p>
          : <fieldset><legend>Grados y tema de la planificación vigente</legend>
            {gradeIds.map((gid) => {
              const g = grades.data?.find((x) => x.id === gid);
              const topics = units.filter((u) => u.grade_id === gid).flatMap((u) => u.topics.map((t) => ({ ...t, unit: u.title })));
              return (
                <label key={gid} className="row"><input type="checkbox" checked={gid in picked} onChange={(e) => setPicked((p) => { const n = { ...p }; if (e.target.checked) n[gid] = topics[0]?.id ?? ""; else delete n[gid]; return n; })} />
                  <span>{g ? gradeLabel(g) : gid}</span>
                  <select disabled={!(gid in picked)} value={picked[gid] ?? ""} onChange={(e) => setPicked((p) => ({ ...p, [gid]: e.target.value }))}>
                    {topics.map((t) => <option key={t.id} value={t.id}>{t.unit} — {t.title}</option>)}</select></label>);
            })}</fieldset>}
        <label>Título<input value={title} onChange={(e) => setTitle(e.target.value)} required minLength={2} /></label>
        <label>Actividad base<textarea value={instructions} onChange={(e) => setInstructions(e.target.value)} required minLength={5} /></label>
        <fieldset><legend>Modo</legend>
          <label><input type="radio" checked={mode === "AI_ASSISTED"} onChange={() => setMode("AI_ASSISTED")} /> Asistido por KAWSAY AI (tú revisas y apruebas)</label>
          <label><input type="radio" checked={mode === "MANUAL"} onChange={() => setMode("MANUAL")} /> Manual</label></fieldset>
        <ErrorBox message={err} />
        <button type="submit" disabled={Object.keys(picked).length === 0}>Crear variantes por grado</button>
      </form>
    </div>
  );
}

export function AssignmentReview() {
  const { id = "" } = useParams();
  const a = useAsync(() => api.get<AssignmentDetail>(`/assignments/${id}`), [id]);
  const grades = useAsync(() => api.get<Grade[]>("/curriculum/grades"), []);
  const [err, setErr] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [constraints, setConstraints] = useState("");
  const run = async (fn: () => Promise<unknown>) => { try { setErr(null); await fn(); await a.reload(); } catch (x) { setErr(errMsg(x)); } };

  const adapt = () => run(async () => {
    const r = await api.post<AdaptResult>(`/assignments/${id}/adapt`, { constraints: constraints || null });
    setInfo(r.results.map((x) => `${x.grade_id}: ${x.status}${x.reasons.length ? ` (${x.reasons.join("; ")})` : ""}`).join(" · "));
  });
  const publish = () => run(async () => { const r = await api.post<{ students_assigned: number; students_without_variant: string[] }>(`/assignments/${id}/publish`); setInfo(`Publicada. Estudiantes asignados: ${r.students_assigned}. Sin variante para su grado: ${r.students_without_variant.length}.`); });

  if (a.loading) return <Loading />;
  if (!a.data) return <ErrorBox message={a.error} />;
  const published = a.data.status === "PUBLISHED";
  return (
    <div>
      <h2>{a.data.title} <Badge tone={published ? "ok" : "info"}>{a.data.status}</Badge></h2>
      <p className="muted">Flujo: KAWSAY propone → tú revisas → editas → apruebas → publicas. Nada llega a los estudiantes sin tu aprobación.</p>
      <ErrorBox message={err ?? a.error} />
      {info && <p role="status" className="notice">{info}</p>}
      {!published && a.data.mode === "AI_ASSISTED" && (
        <Card title="Adaptación con KAWSAY AI">
          <label>Restricciones (opcional)<input value={constraints} onChange={(e) => setConstraints(e.target.value)} maxLength={1000} placeholder="p. ej., usar ejemplos de chacra" /></label>
          <button onClick={() => void adapt()}>ADAPTAR CON KAWSAY AI</button>
          <p className="muted">Si la IA no está disponible, puedes escribir las variantes manualmente; el resto del sistema sigue funcionando.</p>
        </Card>)}
      {a.data.variants.map((v) => <VariantEditor key={v.id} assignmentId={id} v={v} grade={grades.data?.find((g) => g.id === v.grade_id)} locked={published} onChanged={() => void a.reload()} />)}
      {!published && <button onClick={() => void publish()} disabled={a.data.variants.some((v) => v.status !== "APPROVED")}>PUBLICAR (todas las variantes aprobadas)</button>}
    </div>
  );
}

function VariantEditor({ assignmentId, v, grade, locked, onChanged }: { assignmentId: string; v: Variant; grade?: Grade; locked: boolean; onChanged: () => void }) {
  const [title, setTitle] = useState(v.title);
  const [instructions, setInstructions] = useState(v.instructions);
  const [questions, setQuestions] = useState<Question[]>(v.questions);
  const [ack, setAck] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const base = `/assignments/${assignmentId}/variants/${v.id}`;
  const run = async (fn: () => Promise<unknown>) => { try { setErr(null); await fn(); onChanged(); } catch (x) { setErr(errMsg(x)); } };
  const save = () => run(async () => {
    await api.patch(base, { title, instructions });
    if (questions.length) await api.put(`${base}/questions`, { questions: questions.map(({ id: _id, ...q }) => q) });
  });
  return (
    <Card title={`${grade ? gradeLabel(grade) : `Grado ${v.grade_id}`} — ${STATUS_LABEL[v.status]}`}>
      <p className="muted">Objetivo (según la planificación): {v.learning_objective}</p>
      {v.source !== "TEACHER" && <p>Origen: <Badge tone="warn">{v.source === "AI" ? "Generado por IA" : "IA editado por docente"}</Badge> <span className="muted">{v.generated_by}</span></p>}
      {v.validation_status === "NEEDS_REVIEW" && <div className="notice warn" role="alert"><strong>El validador curricular detectó posibles desvíos:</strong><ul>{(v.validation_notes ?? []).map((n) => <li key={n}>{n}</li>)}</ul></div>}
      <ErrorBox message={err} />
      <label>Título<input value={title} onChange={(e) => setTitle(e.target.value)} disabled={locked} /></label>
      <label>Instrucciones<textarea value={instructions} onChange={(e) => setInstructions(e.target.value)} disabled={locked} /></label>
      <QuestionsEditor questions={questions} onChange={setQuestions} disabled={locked} />
      {!locked && (
        <div className="row">
          <button onClick={() => void save()}>Guardar cambios</button>
          {(v.status === "DRAFT" || v.status === "AI_GENERATED") && <button className="ghost" onClick={() => void run(() => api.post(`${base}/review`))}>Marcar en revisión</button>}
          {v.validation_status === "NEEDS_REVIEW" && <label className="inline"><input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} /> Revisé las advertencias</label>}
          {(v.status === "DRAFT" && v.source === "TEACHER") || v.status === "TEACHER_REVIEW" ? <button onClick={() => void run(() => api.post(`${base}/approve${ack ? "?acknowledge_warnings=true" : ""}`))}>Aprobar variante</button> : null}
        </div>)}
    </Card>
  );
}
