import type { Question } from "../types/api";

const blank = (): Question => ({ type: "MULTIPLE_CHOICE", prompt: "", options: ["", ""], correct_answer: { index: 0 }, hints: [], explanation: null, difficulty: 2 });

export function QuestionsEditor({ questions, onChange, disabled }: { questions: Question[]; onChange: (q: Question[]) => void; disabled?: boolean }) {
  const set = (i: number, q: Question) => onChange(questions.map((x, j) => (j === i ? q : x)));
  return (
    <div className="questions">
      <h4>Preguntas ({questions.length})</h4>
      {questions.map((q, i) => (
        <fieldset key={q.id ?? i} disabled={disabled}>
          <legend>Pregunta {i + 1}</legend>
          <label>Tipo<select value={q.type} onChange={(e) => {
            const type = e.target.value as Question["type"];
            set(i, { ...q, type, options: type === "MULTIPLE_CHOICE" ? ["", ""] : null, correct_answer: type === "MULTIPLE_CHOICE" ? { index: 0 } : type === "NUMERIC" ? { value: 0, tolerance: 0 } : { accepted: [""] } });
          }}><option value="MULTIPLE_CHOICE">Opción múltiple</option><option value="NUMERIC">Numérica</option><option value="SHORT_TEXT">Texto corto</option></select></label>
          <label>Enunciado<textarea value={q.prompt} onChange={(e) => set(i, { ...q, prompt: e.target.value })} /></label>
          {q.type === "MULTIPLE_CHOICE" && (
            <div>{(q.options ?? []).map((o, k) => (
              <label key={k} className="row"><input type="radio" name={`c${i}`} checked={q.correct_answer.index === k} onChange={() => set(i, { ...q, correct_answer: { index: k } })} aria-label={`correcta ${k + 1}`} />
                <input value={o} onChange={(e) => set(i, { ...q, options: (q.options ?? []).map((x, j) => (j === k ? e.target.value : x)) })} aria-label={`opción ${k + 1}`} /></label>))}
              <button type="button" className="ghost" onClick={() => set(i, { ...q, options: [...(q.options ?? []), ""] })}>+ opción</button></div>)}
          {q.type === "NUMERIC" && <label>Respuesta<input type="number" step="any" value={Number(q.correct_answer.value ?? 0)} onChange={(e) => set(i, { ...q, correct_answer: { value: Number(e.target.value), tolerance: Number(q.correct_answer.tolerance ?? 0) } })} /></label>}
          {q.type === "SHORT_TEXT" && <label>Respuestas aceptadas (una por línea)<textarea value={((q.correct_answer.accepted as string[] | undefined) ?? []).join("\n")} onChange={(e) => set(i, { ...q, correct_answer: { accepted: e.target.value.split("\n").filter(Boolean) } })} /></label>}
          <label>Pistas (una por línea; se usan también sin Internet)<textarea value={q.hints.join("\n")} onChange={(e) => set(i, { ...q, hints: e.target.value.split("\n").filter(Boolean) })} /></label>
          <label>Explicación (se muestra al cerrar el ejercicio)<textarea value={q.explanation ?? ""} onChange={(e) => set(i, { ...q, explanation: e.target.value || null })} /></label>
          <button type="button" className="ghost" onClick={() => onChange(questions.filter((_, j) => j !== i))}>Quitar pregunta</button>
        </fieldset>))}
      {!disabled && <button type="button" onClick={() => onChange([...questions, blank()])}>+ Agregar pregunta</button>}
    </div>
  );
}
