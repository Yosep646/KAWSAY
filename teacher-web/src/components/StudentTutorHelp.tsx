import { useState } from "react";
import { api } from "../services/api";
import { errMsg } from "../utils/format";
import { Icon } from "./Icon";

export interface TutorQuestion {
  id: string;
  prompt: string;
  hints?: string[] | null;
}

interface TutorReply {
  step: number;
  source: "AI" | "RULES";
  message: string;
  answer_revealed: boolean;
  closed: boolean;
}

/** Usa solamente datos aprobados y ya descargados; no simula un modelo ML. */
export function offlineTutorHint(question: TutorQuestion, step: number): string {
  const hints = question.hints ?? [];
  const choice = hints[Math.min(Math.max(step - 1, 0), hints.length - 1)];
  if (choice?.trim()) return choice.trim();
  const guidance = [
    "Lee la pregunta con calma. ¿Qué te pide resolver?",
    "Identifica los datos importantes y piensa qué procedimiento puedes utilizar.",
    "Intenta resolver una parte más pequeña antes de elegir una respuesta.",
  ];
  return guidance[Math.min(Math.max(step - 1, 0), 2)]!;
}

export function StudentTutorHelp({
  assignmentId, question, onHintUsed,
}: { assignmentId: string; question: TutorQuestion; onHintUsed: (count: number) => void }) {
  const [step, setStep] = useState(0);
  const [reply, setReply] = useState<{ text: string; source: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask() {
    if (busy || step >= 3) return;
    const next = step + 1;
    setBusy(true); setError(null);
    try {
      // Nunca envía respuesta del alumno, nombres, DNI o datos personales a la IA.
      const response = await api.post<TutorReply>("/tutor/turn", {
        student_assignment_id: assignmentId, question_id: question.id, step: next,
      });
      if (!response.message || typeof response.message !== "string") throw new Error("Pista no disponible.");
      setReply({ text: response.message, source: response.source === "AI" ? "IA asistida, con revisión de seguridad" : "Pista pedagógica" });
    } catch (reason) {
      setReply({ text: offlineTutorHint(question, next), source: "Pista descargada (funciona sin internet)" });
      // Una desconexión no bloquea el aprendizaje; el fallback está claramente identificado.
      if (navigator.onLine) setError(`Se utilizó una pista local: ${errMsg(reason)}`);
    } finally {
      setStep(next);
      onHintUsed(next);
      setBusy(false);
    }
  }

  return <section className="student-tutor-box" aria-label="Tutor KAWSAY">
    <h4><Icon name="spark"/> Tutor KAWSAY</h4>
    <p>Te acompaño con pistas, sin darte la respuesta. Puedes seguir aprendiendo sin internet.</p>
    <button type="button" onClick={() => void ask()} disabled={busy || step >= 3}>
      {busy ? "Buscando una pista…" : step >= 3 ? "Ya utilizaste las tres pistas" : "Pedir una pista"}
    </button>
    {reply && <div role="status" className="student-tutor-answer">
      <p>{reply.text}</p><span className="student-tutor-source">{reply.source} · Paso {step} de 3</span>
    </div>}
    {error && <p role="status" className="student-tutor-source">{error}</p>}
  </section>;
}
