import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAsync } from "../hooks/useAsync";
import { errMsg } from "../utils/format";
import type { PlanBrief, PlanVersionTree } from "../types/api";
import { Icon } from "./Icon";
import "./admin-planning-review.css";

const VERSION_STATUS: Record<string,string> = {
  DRAFT:"Borrador", UNDER_REVIEW:"En revisión", APPROVED:"Aprobada", ACTIVE:"Activa", ARCHIVED:"Archivada",
};

/** Admin-only workflow. Reusing backend review/activate endpoints; never automatically approves school curricula. */
export function AdminPlanningReview() {
  const plans = useAsync(() => api.get<PlanBrief[]>("/planning/plans"), []);
  const [selected,setSelected] = useState("");
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState<string|null>(null);
  const [notice,setNotice] = useState<string|null>(null);
  const available = plans.data?.flatMap(plan=>plan.versions.map(version=>({plan,version}))) ?? [];
  useEffect(() => {
    if (plans.loading || !available.length) return;
    if (available.some(x=>x.version.id===selected)) return;
    const pending = available.find(x=>x.version.status==="UNDER_REVIEW")
      ?? available.find(x=>x.version.status==="APPROVED");
    setSelected((pending??available[available.length-1]!).version.id);
  },[plans.loading,plans.data,selected]); // update selection only when list changes
  const detail = useAsync<PlanVersionTree|null>(
    () => selected ? api.get<PlanVersionTree>(`/planning/versions/${selected}`) : Promise.resolve(null),[selected]);
  const chosen = available.find(x=>x.version.id===selected);

  const perform = async (action:"approve"|"reject"|"activate") => {
    if (busy || !selected || !chosen) return;
    setBusy(true);setError(null);setNotice(null);
    try {
      await api.post(`/planning/versions/${selected}/${action}`,{});
      await Promise.all([plans.reload(),detail.reload()]);
      setNotice(action==="approve"?"Planificación aprobada. Falta activarla.":
        action==="activate"?"Planificación activa. El docente ya puede utilizar sus temas en actividades.":"Planificación devuelta al docente para corregir.");
    } catch (e) {setError(errMsg(e));} finally {setBusy(false);}
  };

  return <section className="admin-planning-review" aria-labelledby="admin-planning-review-heading">
    <header className="admin-planning-review-head">
      <span className="admin-planning-review-icon"><Icon name="check"/></span>
      <div><p>VALIDACIÓN CURRICULAR</p><h3 id="admin-planning-review-heading">Revisar y activar planificaciones</h3>
        <small>La aprobación de un PDF no activa un plan. Revisa los periodos, unidades y temas enviados por los docentes.</small></div>
      <button className="admin-planning-refresh" type="button" onClick={()=>void plans.reload()} disabled={busy||plans.loading}>
        <Icon name="refresh"/> Actualizar
      </button>
    </header>
    {error && <p role="alert" className="admin-planning-error">{error}</p>}
    {plans.error && <p role="alert" className="admin-planning-error">{plans.error}</p>}
    {notice && <p role="status" className="admin-planning-notice">{notice}</p>}
    {plans.loading ? <p className="admin-planning-empty">Consultando las planificaciones de las instituciones…</p> :
      !available.length ? <div className="admin-planning-empty">
        <Icon name="book"/><strong>No hay planificaciones estructuradas.</strong>
        <span>Los docentes deben crear un plan y enviarlo a revisión. Los archivos Word o PDF de la biblioteca son referencias independientes.</span>
      </div> : <div className="admin-planning-grid">
        <div className="admin-planning-versions" aria-label="Versiones curriculares">
          {available.map(({plan,version})=><button key={version.id} type="button" className="admin-planning-version" aria-pressed={version.id===selected} onClick={()=>{setSelected(version.id);setNotice(null);setError(null);}}>
            <span><strong>{plan.name}</strong><small>Versión {version.label}</small></span>
            <em data-status={version.status}>{VERSION_STATUS[version.status]??version.status}</em>
          </button>)}
        </div>
        <div className="admin-planning-detail">
          <div className="admin-planning-detail-top"><h4>{chosen?.plan.name}</h4><span>{chosen ? VERSION_STATUS[chosen.version.status]??chosen.version.status : ""}</span></div>
          {detail.loading ? <p>Cargando contenidos…</p> : detail.error ? <p role="alert">{detail.error}</p> :
            !detail.data?.periods.length ? <p>No se registraron periodos ni unidades en esta versión.</p> :
              <div className="admin-planning-periods">
                {detail.data.periods.map(period=><div key={period.id}>
                  <h5>{period.name}</h5>
                  {!period.units.length ? <small>Sin unidades</small> : period.units.map(unit=><div key={unit.id} className="admin-planning-unit">
                    <strong>{unit.title}</strong><small>{unit.topics.length} {unit.topics.length===1?"tema":"temas"} · Grado ID {unit.grade_id}</small>
                    {unit.topics.length>0 && <ul>{unit.topics.map(topic=><li key={topic.id}><strong>{topic.title}</strong><span>{topic.learning_objective}</span></li>)}</ul>}
                  </div>)}
                </div>)}
              </div>}
          {chosen?.version.status==="UNDER_REVIEW" && <>
            <p className="admin-planning-caution">Comprueba que las competencias, los grados y los objetivos correspondan al currículo aprobado por tu institución antes de autorizar la versión.</p>
            <div className="admin-planning-actions"><button type="button" disabled={busy||detail.loading||!detail.data} onClick={()=>void perform("approve")}>Aprobar planificación</button>
              <button type="button" className="admin-planning-secondary" disabled={busy} onClick={()=>void perform("reject")}>Devolver para corregir</button></div>
          </>}
          {chosen?.version.status==="APPROVED" && <div className="admin-planning-actions">
            <button type="button" disabled={busy||detail.loading||!detail.data} onClick={()=>void perform("activate")}>Activar versión curricular</button>
          </div>}
          {chosen?.version.status==="ACTIVE" && <p className="admin-planning-notice">Esta versión está activa. Las actividades podrán utilizar sus temas en el año escolar correspondiente.</p>}
          {chosen?.version.status==="DRAFT" && <p className="admin-planning-caution">El docente todavía está editando este borrador y debe enviarlo a revisión.</p>}
        </div>
      </div>}
  </section>;
}
