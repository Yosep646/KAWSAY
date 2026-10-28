import type { Question } from "../types/api";
import "./exercise-preview.css";

/**
 * Read-only rendering of what a learner can read.
 * Never includes correct_answer, hints, or hidden assessment metadata.
 * Preview is not a publication.
 */
export function ExercisePreview({
  title, instructions, questions = [], draft = false,
}: { title:string; instructions:string; questions?: Pick<Question,"type"|"prompt"|"options">[]; draft?:boolean }) {
  const meaningful = title.trim() || instructions.trim() || questions.length>0;
  return <section className="exercise-preview" aria-label="Vista previa de ejercicios">
    <div className="exercise-preview-head">
      <h3>Vista previa de ejercicios</h3>
      <span>{draft ? "Borrador local · solo docente" : "Vista de lectura · solo docente"}</span>
    </div>
    {!meaningful ? <p className="exercise-preview-empty">Escribe el título y la actividad base para verlos aquí.</p> :
      <div className="exercise-preview-sheet">
        <h4>{title.trim() || "Actividad sin título"}</h4>
        {instructions.trim() && <p className="exercise-preview-instructions">{instructions}</p>}
        {questions.length ? <ol className="exercise-preview-questions">
          {questions.map((question,i)=><li key={i}>
            <p>{question.prompt.trim() || "Pregunta sin enunciado"}</p>
            {question.type === "MULTIPLE_CHOICE" && Boolean(question.options?.length) &&
              <ul>{question.options?.map((option,j)=><li key={j}>{option.trim() || "Opción pendiente"}</li>)}</ul>}
            {question.type === "NUMERIC" && <span className="exercise-preview-placeholder">Respuesta numérica</span>}
            {question.type === "SHORT_TEXT" && <span className="exercise-preview-placeholder">Respuesta escrita</span>}
          </li>)}
        </ol> : <p className="exercise-preview-empty">Aún no hay preguntas individuales. Se agregan en la revisión de las variantes por grado.</p>}
      </div>}
    <p className="exercise-preview-footnote">{draft
      ? "Esto es una vista previa de lo escrito en este dispositivo. No está guardado como tarea en el servidor ni es visible para estudiantes."
      : "La vista previa no publica el ejercicio. Los estudiantes lo verán únicamente cuando apruebes y publiques las variantes para su grado."}</p>
  </section>;
}
