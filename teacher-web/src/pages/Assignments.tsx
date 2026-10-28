import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Badge, Card, ErrorBox, Loading } from "../components/ui";
import { QuestionsEditor } from "../components/QuestionsEditor";
import { ExercisePreview } from "../components/ExercisePreview";
import { TeacherPageIntro } from "../components/TeacherPageIntro";
import { Icon } from "../components/Icon";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import type { AdaptResult, AssignmentBrief, AssignmentDetail, Classroom, Grade, PlanBrief, PlanVersionTree, Question, Variant } from "../types/api";
import { STATUS_LABEL, errMsg, gradeLabel } from "../utils/format";

export function AssignmentList() {
  const list = useAsync(() => api.get<AssignmentBrief[]>("/assignments"), []);
  const [localDraft] = useState(restoreExerciseDraft);
  const draftAvailable = Boolean(localDraft?.title.trim() || localDraft?.instructions.trim());
  return (
    <div>
      <h2>Actividades</h2>
      <p><Link to="/actividades/nueva">+ Crear actividad</Link></p>
      {draftAvailable && localDraft && <div className="teacher-local-draft">
        <div><strong>Ejercicio pendiente en este navegador</strong><span>Borrador temporal · no publicado</span></div>
        <p>{localDraft.title.trim() || "Sin título"} — {localDraft.instructions.slice(0,160)}</p>
        <Link to="/actividades/nueva">Continuar escribiendo</Link>
      </div>}
      <ErrorBox message={list.error} />
      {list.loading ? <Loading /> : (list.data?.length ?? 0) === 0 ? <p className="muted">Aún no hay actividades.</p> : (
        <ul className="list">{list.data?.map((a) => <li key={a.id}><Link to={`/actividades/${a.id}`}>{a.title}</Link> <Badge tone={a.status === "PUBLISHED" ? "ok" : "info"}>{a.status}</Badge> <span className="muted">{a.mode}</span></li>)}</ul>)}
    </div>
  );
}

const TEACHER_EXERCISE_DRAFT = "kawsay.teacher.exercise-draft.v1";
type ExerciseDraft = { title:string; instructions:string; mode:"MANUAL"|"AI_ASSISTED" };
function restoreExerciseDraft(): ExerciseDraft | null {
  try {
    if (typeof window === "undefined") return null;
    const raw = window.sessionStorage.getItem(TEACHER_EXERCISE_DRAFT);
    if (!raw) return null;
    const draft: unknown = JSON.parse(raw);
    if (!draft || typeof draft !== "object") return null;
    const data = draft as Partial<ExerciseDraft>;
    if (typeof data.title !== "string" || typeof data.instructions !== "string") return null;
    if (data.mode !== "MANUAL" && data.mode !== "AI_ASSISTED") return null;
    return { title:data.title.slice(0,300), instructions:data.instructions.slice(0,5000), mode:data.mode };
  } catch { return null; }
}

export function CreateAssignment() {
  const nav = useNavigate();
  const rooms = useAsync(() => api.get<Classroom[]>("/classrooms"), []);
  const grades = useAsync(() => api.get<Grade[]>("/curriculum/grades"), []);
  const plans = useAsync(() => api.get<PlanBrief[]>("/planning/plans"), []);
  const [roomId,setRoomId] = useState("");
  const rid = roomId || rooms.data?.[0]?.id || "";
  const active = useAsync(() => rid ? api.get<PlanVersionTree[]>(`/planning/active?classroom_id=${rid}`) : Promise.resolve([]), [rid]);
  const [picked,setPicked] = useState<Record<number,string>>({});
  const [savedDraft] = useState(restoreExerciseDraft);
  const [title,setTitle] = useState(savedDraft?.title ?? "");
  const [instructions,setInstructions] = useState(savedDraft?.instructions ?? "");
  const [mode,setMode] = useState<"MANUAL"|"AI_ASSISTED">(savedDraft?.mode ?? "AI_ASSISTED");
  useEffect(() => {
    try {
      window.sessionStorage.setItem(TEACHER_EXERCISE_DRAFT, JSON.stringify({ title, instructions, mode }));
    } catch { /* Session storage may be unavailable; the form still works. */ }
  }, [title,instructions,mode]);
  const [err,setErr] = useState<string|null>(null);
  const [busy,setBusy] = useState(false);
  const units = active.data?.flatMap(v => v.periods.flatMap(p=>p.units)) ?? [];
  const selectableUnits = units.filter(u => u.topics.length > 0);
  const gradeIds = [...new Set(selectableUnits.map(u=>u.grade_id))].sort((a,b)=>a-b);
  const selectedCount = Object.values(picked).filter(Boolean).length;
  const ready = Boolean(rid && !active.loading && !active.error && selectableUnits.length && selectedCount && title.trim().length>=2 && instructions.trim().length>=5);
  const planVersions = plans.data?.flatMap(p=>p.versions) ?? [];
  const hasSubmittedPlan = planVersions.some(v=>v.status==="UNDER_REVIEW");
  const hasApprovedPlan = planVersions.some(v=>v.status==="APPROVED");
  const hasDraftPlan = planVersions.some(v=>v.status==="DRAFT");
  const missingReason = !rid
    ? "Debes crear o seleccionar un aula."
    : active.loading
      ? "Consultando la planificación vigente de tu aula…"
      : active.error
        ? "No se pudo consultar la planificación; revisa el error de conexión."
        : gradeIds.length===0
          ? "Primero necesitas una planificación estructurada activa, con temas del grado de tu aula."
          : !selectedCount
            ? "Selecciona al menos un grado y un tema."
            : title.trim().length<2 || instructions.trim().length<5
              ? "Completa el título y la actividad base."
              : "";

  const submit = async (event:FormEvent) => {
    event.preventDefault();
    if(busy)return;
    const grade_topics = Object.entries(picked).filter(([,topic])=>topic).map(([g,topic])=>({grade_id:Number(g),topic_id:topic}));
    if(!rid || !grade_topics.length) {setErr("Selecciona un aula, los grados y los temas de una planificación activa.");return;}
    try {
      setBusy(true);setErr(null);
      const record = await api.post<AssignmentDetail>("/assignments", {
        classroom_id:rid,title:title.trim(),instructions:instructions.trim(),mode,grade_topics,
      });
      try { window.sessionStorage.removeItem(TEACHER_EXERCISE_DRAFT); } catch { /* Optional draft storage. */ }
      nav(`/actividades/${record.id}`);
    } catch(x) {setErr(errMsg(x));} finally {setBusy(false);}
  };

  return <div className="teacher-workflow teacher-activities-page">
    <TeacherPageIntro kicker="DISEÑO PEDAGÓGICO · KAWSAY AI" title="Crear actividad" icon="tasks"
      description="Prepara una actividad alineada al currículo de tu institución, con versiones diferenciadas para cada grado.">
      <Link to="/planificacion"><Icon name="book"/> Ver planificación</Link>
      <Link className="secondary" to="/aulas"><Icon name="classroom"/> Mis aulas</Link>
    </TeacherPageIntro>
    <div className="teacher-flow-kpis">
      <div className="teacher-flow-stat"><span><Icon name="classroom"/></span><div><strong>{rooms.loading?"…":rooms.data?.length??0}</strong><small>Aulas disponibles</small></div></div>
      <div className="teacher-flow-stat"><span><Icon name="book"/></span><div><strong>{active.loading?"…":gradeIds.length}</strong><small>Grados con temas activos</small></div></div>
      <div className="teacher-flow-stat"><span><Icon name="check"/></span><div><strong>{selectedCount}</strong><small>Grados seleccionados</small></div></div>
    </div>
    <ErrorBox message={rooms.error ?? active.error ?? grades.error ?? plans.error ?? err}/>
    <div className="teacher-flow-grid">
      <section className="teacher-flow-card">
        <div className="teacher-flow-card-heading"><span><Icon name="tasks"/></span><div><h3>Preparar actividad por grados</h3><p>Completa los datos, elige el contenido y guarda un borrador para revisión.</p></div></div>
        {rooms.loading ? <Loading/> : !rooms.data?.length ?
          <div className="teacher-flow-empty"><Icon name="classroom"/><h3>Primero registra tu aula</h3><p>No se puede asignar una actividad sin indicar a qué aula pertenece.</p><Link to="/aulas"><Icon name="arrow"/> Crear aula</Link></div> :
          <form className="teacher-flow-form" onSubmit={e=>void submit(e)}>
            <label className="wide">Aula o sección
              <select value={rid} onChange={e=>{setRoomId(e.target.value);setPicked({});}} required>
                {rooms.data.map(r=><option key={r.id} value={r.id}>{r.name} · {r.academic_year}</option>)}
              </select>
            </label>
            {active.loading ? <div className="wide"><Loading/></div> : gradeIds.length===0 ?
              <div className="teacher-flow-empty wide" role="status">
                <Icon name="book"/><h3>{active.data?.length ? "El plan activo no tiene temas para seleccionar" : "Falta activar una planificación curricular"}</h3>
                <p>Tu título y tus instrucciones se conservarán como borrador en esta pestaña mientras completas los requisitos.</p>
                {plans.loading ? <p>Consultando los planes de la institución…</p> :
                  <p>{hasSubmittedPlan ? "Hay una versión enviada a revisión: el administrador debe aprobarla y activarla." :
                    hasApprovedPlan ? "Hay una versión aprobada pendiente de activación por el administrador." :
                    hasDraftPlan ? "Hay un borrador: agrega periodo, unidad y tema, y envíalo a revisión." :
                    "Primero crea un plan estructurado con competencias, periodo, unidad y tema; luego solicita su activación."}</p>}
                <Link to="/planificacion#crear-plan-estructurado"><Icon name="arrow"/> Continuar con planificación</Link>
              </div> :
              <fieldset className="teacher-flow-grade-list wide"><legend>Grados y temas disponibles</legend>
                {gradeIds.map(gid=>{
                  const g=grades.data?.find(x=>x.id===gid);
                  const options=units.filter(u=>u.grade_id===gid).flatMap(u=>u.topics.map(t=>({...t,unit:u.title})));
                  if(!options.length)return null;
                  return <label className="teacher-flow-grade" key={gid}>
                    <input type="checkbox" checked={gid in picked} onChange={e=>setPicked(p=>{const n={...p};if(e.target.checked)n[gid]=options[0]?.id??"";else delete n[gid];return n;})}/>
                    <span>{g?gradeLabel(g):`Grado ${gid}`}</span>
                    <select disabled={!(gid in picked)} aria-label={`Tema para ${g?gradeLabel(g):gid}`} value={picked[gid]??""} onChange={e=>setPicked(p=>({...p,[gid]:e.target.value}))}>
                      {options.map(t=><option value={t.id} key={t.id}>{t.unit} · {t.title}</option>)}
                    </select>
                  </label>;
                })}
              </fieldset>}
            <label className="wide">Título de la actividad
              <input value={title} onChange={e=>setTitle(e.target.value)} maxLength={300} minLength={2} required placeholder="Ej. Sumas y restas con situaciones de mi comunidad"/>
            </label>
            <label className="wide">Actividad base
              <textarea rows={4} maxLength={5000} value={instructions} onChange={e=>setInstructions(e.target.value)} minLength={5} required placeholder="Describe el aprendizaje que deseas trabajar, las consignas y los materiales de apoyo."/>
            </label>
            <div className="wide"><ExercisePreview title={title} instructions={instructions} draft/></div>
            <fieldset className="teacher-flow-assignment-mode wide"><legend>Cómo preparar las variantes</legend>
              <label><input type="radio" name="activity-mode" checked={mode==="AI_ASSISTED"} onChange={()=>setMode("AI_ASSISTED")}/>
                <span><strong>Asistido por KAWSAY AI</strong><small>Generación opcional; el docente revisa y aprueba cada grado. Requiere proveedor de IA habilitado.</small></span>
              </label>
              <label><input type="radio" name="activity-mode" checked={mode==="MANUAL"} onChange={()=>setMode("MANUAL")}/>
                <span><strong>Creación manual</strong><small>Redacta las preguntas y adapta el contenido de cada grado directamente.</small></span>
              </label>
            </fieldset>
            {!ready && <p className="teacher-activity-missing wide" role="status"><Icon name="book"/> {missingReason}</p>}
            {(title.trim() || instructions.trim()) && <p className="teacher-activity-autosave wide">El ejercicio escrito se conserva temporalmente en esta pestaña. No se ha enviado a los estudiantes.</p>}
            <button type="submit" disabled={!ready||busy}>{busy?"Guardando…":"Crear variantes para revisión"} <Icon name="arrow"/></button>
          </form>}
      </section>
      <aside className="teacher-flow-next">
        <div className="teacher-flow-card-heading"><span><Icon name="leaf"/></span><div><h3>Cómo funciona KAWSAY</h3><p>Secuencia pedagógica segura por grado.</p></div></div>
        <ol className="teacher-flow-steps">
          <li><span>1</span><div><strong>Currículo activo</strong><p>Cada tema corresponde a una unidad revisada por tu institución.</p></div></li>
          <li><span>2</span><div><strong>Versiones por grado</strong><p>Una misma actividad puede adaptarse a 1.º, 2.º, 3.º y otros grados.</p></div></li>
          <li><span>3</span><div><strong>Revisión humana</strong><p>Revisa, corrige y aprueba antes de publicar ejercicios.</p></div></li>
          <li><span>4</span><div><strong>Seguimiento</strong><p>Las respuestas generan indicadores y recomendaciones de refuerzo; todavía no cambian automáticamente de grado.</p></div></li>
        </ol>
        <div className="teacher-flow-guidance">El grado oficial no cambia aunque se recomienden ejercicios de refuerzo. La reducción automática entre grados sigue pendiente de implementar y validar.</div>
      </aside>
    </div>
  </div>;
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
      <ExercisePreview title={title} instructions={instructions} questions={questions}/>
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
