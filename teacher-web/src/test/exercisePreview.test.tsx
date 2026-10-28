import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ExercisePreview } from "../components/ExercisePreview";

describe("Vista previa de actividades del docente", () => {
  it("muestra el ejercicio escrito como borrador sin afirmar que está publicado", () => {
    render(<ExercisePreview draft title="Suma de números naturales"
      instructions={"Resuelve las siguientes sumas:\n12 + 5 = ?"} />);
    expect(screen.getByRole("heading",{name:"Suma de números naturales"})).toBeInTheDocument();
    expect(screen.getByText(/12 \+ 5 =/)).toBeInTheDocument();
    expect(screen.getByText(/No está guardado como tarea en el servidor/)).toBeInTheDocument();
    expect(screen.getByText(/Aún no hay preguntas individuales/)).toBeInTheDocument();
  });

  it("deja ver preguntas por grado pero no revela las respuestas correctas", () => {
    const {container} = render(<ExercisePreview title="Matemática" instructions="Resuelve"
      questions={[{type:"MULTIPLE_CHOICE",prompt:"¿Cuánto es 2 + 3?",options:["4","5","6"]}]} />);
    expect(screen.getByText("¿Cuánto es 2 + 3?")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/respuesta correcta/i);
    expect(screen.getByText(/publica el ejercicio/i)).toBeInTheDocument();
  });
});
