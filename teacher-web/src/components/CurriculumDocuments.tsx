import { useState, type FormEvent } from "react";
import { useAuth } from "../app/AuthContext";
import { Icon } from "./Icon";
import { useAsync } from "../hooks/useAsync";
import { api, documentApi } from "../services/api";
import { errMsg } from "../utils/format";
import "./curriculum-documents.css";

type Level = "PRIMARIA" | "SECUNDARIA";
interface School { id: string; name: string }
interface MineduGrade { number:number; name:string; planning_pdf_url:string; planning_word_url:string }
interface MineduCatalog {
  source_label:string;
  curriculum:{name:string;year:number;url:string};
  national_framework:{name:string;year:number;url:string};
  resource_index_url:string;
  notice:string;
  grades:MineduGrade[];
  math_competencies:string[];
}
export interface CurriculumDocumentReference { filename:string; academic_year:number; education_level:Level; grade_number:number; area:string; }
interface DocumentRecord {
  id: string; school_id: string; education_level: Level; grade_number: number;
  academic_year: number; area: string; filename: string; file_size: number;
  created_at: string; status: "PENDING"|"APPROVED"|"REJECTED";
}
const AREAS = [
  "Matemática", "Comunicación", "Ciencia y Tecnología", "Personal Social",
  "Arte y Cultura", "Educación Física", "Inglés", "Educación Religiosa",
  "Tutoría", "Multigrado / General",
];
const MAX_SIZE = 4 * 1024 * 1024;

/** Document library; Word/PDF attachments, NOT automated curriculum parsing. */
export function CurriculumDocuments({ onPreparePlan }: { onPreparePlan?: (document: CurriculumDocumentReference) => void } = {}) {
  const { user } = useAuth();
  const admin = user?.role === "ADMIN";
  const schools = useAsync(() => api.get<School[]>("/curriculum/documents/schools"), []);
  const official = useAsync(() => api.get<MineduCatalog>("/curriculum/minedu/primaria"), []);
  const [selectedSchool,setSelectedSchool] = useState("");
  const schoolId = selectedSchool || schools.data?.[0]?.id || "";
  const [year,setYear] = useState(new Date().getFullYear());
  const [level,setLevel] = useState<Level>("PRIMARIA");
  const [grade,setGrade] = useState(1);
  const [area,setArea] = useState(AREAS[0] ?? "Matemática");
  const [file,setFile] = useState<File|null>(null);
  const [busy,setBusy] = useState(false);
  const [reviewing,setReviewing] = useState<string|null>(null);
  const [error,setError] = useState<string|null>(null);
  const [notice,setNotice] = useState<string|null>(null);
  const gradeCount = level === "PRIMARIA" ? 6 : 5;
  const search = new URLSearchParams({school_id:schoolId,academic_year:String(year),education_level:level,grade_number:String(grade)});
  const documents = useAsync(
    () => schoolId ? api.get<DocumentRecord[]>(`/curriculum/documents?${search.toString()}`) : Promise.resolve([]),
    [schoolId,year,level,grade],
  );
  const activeAreas = AREAS.filter(a => documents.data?.some(d => d.area === a));
  const grouped = activeAreas.map(a => ({name:a,files:(documents.data||[]).filter(d=>d.area===a)}));
  const mineduGrade = official.data?.grades.find(g => g.number === grade);

  async function upload(event: FormEvent) {
    event.preventDefault();
    setError(null); setNotice(null);
    if (!schoolId || !file) { setError("Selecciona una institución y un archivo."); return; }
    if (!/\.(docx|pdf)$/i.test(file.name)) {setError("Selecciona un archivo .docx o .pdf.");return;}
    if (file.size === 0 || file.size > MAX_SIZE) {setError("El archivo debe ocupar entre 1 byte y 4 MB.");return;}
    setBusy(true);
    try {
      const params = new URLSearchParams({
        school_id:schoolId,academic_year:String(year),education_level:level,
        grade_number:String(grade),area,filename:file.name,
      });
      await documentApi.upload<DocumentRecord>(`/curriculum/documents?${params}`,file);
      setFile(null);
      const field=document.getElementById("kawsay-curriculum-file") as HTMLInputElement|null;
      if (field) field.value = "";
      setNotice("Archivo subido. Queda pendiente de revisión y no modifica automáticamente la planificación.");
      await documents.reload();
    } catch (e) {setError(errMsg(e));}
    finally {setBusy(false);}
  }

  async function download(doc:DocumentRecord) {
    setError(null);
    try {
      const blob=await documentApi.download(`/curriculum/documents/${doc.id}/download`);
      const url=URL.createObjectURL(blob);
      const a=document.createElement("a");
      a.href=url;a.download=doc.filename;a.style.display="none";
      document.body.appendChild(a);a.click();a.remove();
      window.setTimeout(()=>URL.revokeObjectURL(url),1000);
    } catch (e) {setError(errMsg(e));}
  }

  async function review(doc:DocumentRecord,approved:boolean) {
    setError(null);setNotice(null);setReviewing(doc.id);
    try {
      await api.post(`/curriculum/documents/${doc.id}/review?approved=${approved}`,{});
      await documents.reload();
      setNotice(approved?"Documento aprobado tras la revisión humana.":"Documento marcado como rechazado.");
    } catch(e) {setError(errMsg(e));}
    finally {setReviewing(null);}
  }
  return <section className="curriculum-library" aria-labelledby="curriculum-library-title">
    <header className="curriculum-library-head">
      <span className="curriculum-library-icon"><Icon name="book"/></span>
      <div>
        <p className="curriculum-library-kicker">DOCUMENTOS DE LA MALLA CURRICULAR</p>
        <h3 id="curriculum-library-title">Biblioteca por grados y áreas</h3>
        <p>Adjunta los documentos Word o PDF de cada grado. No es necesario escribir JSON.</p>
      </div>
    </header>
    <div className="curriculum-library-controls">
      <label>Institución educativa
        <select value={schoolId} disabled={!admin || schools.loading || !schools.data?.length}
          onChange={e=>{setSelectedSchool(e.target.value);setFile(null);}}>
          {schools.data?.map(s=><option value={s.id} key={s.id}>{s.name}</option>)}
        </select>
      </label>
      <label>Año escolar
        <select value={year} onChange={e=>setYear(Number(e.target.value))}>
          {Array.from({length:6},(_,i)=>new Date().getFullYear()-3+i).map(y=><option key={y} value={y}>{y}</option>)}
        </select>
      </label>
      <label>Nivel educativo
        <select value={level} onChange={e=>{setLevel(e.target.value as Level);setGrade(1);}}>
          <option value="PRIMARIA">Primaria</option>
          <option value="SECUNDARIA">Secundaria</option>
        </select>
      </label>
    </div>
    {schools.error&&<p className="curriculum-feedback error" role="alert">{schools.error}</p>}
    {!schools.loading&&!schools.data?.length&&<p className="curriculum-feedback">No hay institución asignada. {admin?"Registra primero una institución.":"Solicita que el administrador te asigne a una institución."}</p>}
    <div className="curriculum-grade-tabs" role="group" aria-label="Grado educativo">
      {Array.from({length:gradeCount},(_,i)=>i+1).map(n=><button key={n} type="button"
        className={grade===n?"active":""} aria-pressed={grade===n}
        onClick={()=>{setGrade(n);setNotice(null);setError(null);}}>
        <span>{n}.º</span><small>grado</small>
      </button>)}
    </div>
    {level==="PRIMARIA" && <section className="curriculum-minedu" aria-labelledby="curriculum-minedu-heading">
      <div className="curriculum-minedu-heading">
        <span className="curriculum-minedu-symbol"><Icon name="book"/></span>
        <div><p>FUENTES EDUCATIVAS DEL PERÚ</p><h4 id="curriculum-minedu-heading">Referencias oficiales MINEDU · {grade}.º de primaria</h4>
          <small>Material público de consulta. El colegio decide su programación; no se activa automáticamente.</small></div>
      </div>
      {official.loading && <p className="curriculum-minedu-notice">Consultando el catálogo curricular…</p>}
      {official.error && <p className="curriculum-feedback error" role="alert">No se pudo cargar el catálogo MINEDU: {official.error}</p>}
      {official.data && <>
        <div className="curriculum-minedu-links">
          <a href={official.data.curriculum.url} target="_blank" rel="noopener noreferrer"><Icon name="book"/> Programa de Educación Primaria <Icon name="arrow"/></a>
          {mineduGrade && <>
            <a href={mineduGrade.planning_pdf_url} target="_blank" rel="noopener noreferrer"><Icon name="book"/> Planificación {grade}.º · PDF <Icon name="arrow"/></a>
            <a href={mineduGrade.planning_word_url} target="_blank" rel="noopener noreferrer"><Icon name="book"/> Planificación {grade}.º · Word <Icon name="arrow"/></a>
          </>}
          <a href={official.data.resource_index_url} target="_blank" rel="noopener noreferrer">Más recursos MINEDU <Icon name="arrow"/></a>
        </div>
        {area==="Matemática" && <div className="curriculum-minedu-math"><strong>Competencias de Matemática</strong>
          <ul>{official.data.math_competencies.map(item=><li key={item}>{item}</li>)}</ul>
        </div>}
        <p className="curriculum-minedu-notice">{official.data.notice}</p>
      </>}
    </section>}
    <div className="curriculum-library-columns">
      <form className="curriculum-upload" onSubmit={e=>void upload(e)}>
        <h4><Icon name="book"/> Subir material de {grade}.º de {level.toLowerCase()}</h4>
        <p>Selecciona el área curricular y adjunta el documento correspondiente.</p>
        <label>Área o sección curricular
          <select value={area} onChange={e=>setArea(e.target.value)}>
            {AREAS.map(a=><option key={a} value={a}>{a}</option>)}
          </select>
        </label>
        <label className="curriculum-file-zone" htmlFor="kawsay-curriculum-file">
          <Icon name="book"/>
          <strong>{file?.name || "Seleccionar archivo Word o PDF"}</strong>
          <span>{file?(`${(file.size/1024).toFixed(0)} KB`):"Formatos .docx y .pdf · máximo 4 MB"}</span>
          <input id="kawsay-curriculum-file" type="file" accept=".docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={e=>{setFile(e.target.files?.[0]??null);setError(null);}} required/>
        </label>
        <button className="curriculum-upload-submit" type="submit" disabled={!schoolId||!file||busy}>
          <Icon name="check"/>{busy?"Subiendo archivo…":"Guardar documento"}<Icon name="arrow"/>
        </button>
        <p className="curriculum-upload-hint">Los documentos se guardan por institución, grado, año y área. La revisión es humana; no se convierten automáticamente en contenidos oficiales ni ejercicios de IA.</p>
      </form>
      <div className="curriculum-records">
        <div className="curriculum-records-head">
          <h4>Archivos de {grade}.º grado</h4>
          <span>{documents.data?.length ?? 0} documentos</span>
        </div>
        {documents.loading&&<p className="curriculum-no-files">Cargando archivos…</p>}
        {documents.error&&<p className="curriculum-feedback error" role="alert">{documents.error}</p>}
        {!documents.loading&&!documents.data?.length&&<div className="curriculum-no-files"><Icon name="book"/><strong>Sin archivos para este grado</strong><p>Sube un documento por área, como Matemática o Comunicación. Los seis grados se organizan por separado.</p></div>}
        {grouped.map(group=><section className="curriculum-area-group" key={group.name}>
          <h5>{group.name}</h5>
          {group.files.map(doc=><div className="curriculum-document" key={doc.id}>
            <span className="curriculum-document-type">{doc.filename.toLowerCase().endsWith(".pdf")?"PDF":"DOCX"}</span>
            <div className="curriculum-document-info">
              <strong title={doc.filename}>{doc.filename}</strong>
              <small>{Math.ceil(doc.file_size/1024)} KB · {new Date(doc.created_at).toLocaleDateString("es-PE")}</small>
              <span className={`curriculum-status ${doc.status.toLowerCase()}`}>
                {doc.status==="PENDING"?"Pendiente de revisión":doc.status==="APPROVED"?"Documento aprobado":"Documento rechazado"}
              </span>
            </div>
            <div className="curriculum-document-actions">
              <button type="button" onClick={()=>void download(doc)}>Descargar</button>
              {!admin && doc.status === "APPROVED" && onPreparePlan && (
                <button type="button" className="curriculum-continue" onClick={() => onPreparePlan({
                  filename:doc.filename, academic_year:doc.academic_year,
                  education_level:doc.education_level, grade_number:doc.grade_number, area:doc.area,
                })}>Preparar plan</button>
              )}
              {admin&&doc.status==="PENDING"&&<>
                <button type="button" disabled={reviewing===doc.id} onClick={()=>void review(doc,true)}>Aprobar</button>
                <button type="button" className="reject" disabled={reviewing===doc.id} onClick={()=>void review(doc,false)}>Rechazar</button>
              </>}
            </div>
          </div>)}
        </section>)}
      </div>
    </div>
    {!admin && documents.data?.some(doc => doc.status==="APPROVED") && (
      <div className="curriculum-next-step" role="note">
        <Icon name="book" />
        <p><strong>Documentos revisados, pero todavía no activos como planificación.</strong>
          Elige «Preparar plan» para usar el grado, año y área como referencia de un borrador.
          Después debes agregar y validar los contenidos, y el administrador debe activar la versión.
          Este proceso no extrae automáticamente los temas del PDF.</p>
      </div>
    )}
    {error&&<p className="curriculum-feedback error" role="alert">{error}</p>}
    {notice&&<p className="curriculum-feedback success" role="status">{notice}</p>}
  </section>;
}
