import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StudentTutorHelp, offlineTutorHint } from "../components/StudentTutorHelp";
import { ExistingEnrollment } from "../components/ExistingEnrollment";
import { StudentLanguageSettings } from "../pages/StudentLanguageSettings";
import { api } from "../services/api";

afterEach(() => vi.restoreAllMocks());

describe("Tutor educativo", () => {
  const question = { id: "q1", prompt: "¿Cómo se resuelve?", hints: ["Piensa en la suma", "Cuenta los objetos"] };

  it("muestra pistas aprobadas descargadas cuando falla la red, sin inventar IA", async () => {
    const hintUsed = vi.fn();
    vi.spyOn(api, "post").mockRejectedValue(new Error("Sin conexión"));
    render(<StudentTutorHelp assignmentId="a1" question={question} onHintUsed={hintUsed} />);
    await userEvent.click(screen.getByRole("button", { name: "Pedir una pista" }));
    expect(await screen.findByText("Piensa en la suma")).toBeInTheDocument();
    expect(screen.getByText(/Pista descargada/)).toBeInTheDocument();
    expect(hintUsed).toHaveBeenCalledWith(1);
    expect(offlineTutorHint(question, 2)).toBe("Cuenta los objetos");
  });

  it("usa respuesta real del tutor remoto e indica su procedencia", async () => {
    const post = vi.spyOn(api, "post").mockResolvedValue({
      step: 1, source: "AI", message: "Identifica primero los datos.", answer_revealed: false, closed: false,
    });
    render(<StudentTutorHelp assignmentId="a1" question={question} onHintUsed={() => {}} />);
    await userEvent.click(screen.getByRole("button", { name: "Pedir una pista" }));
    expect(await screen.findByText("Identifica primero los datos.")).toBeInTheDocument();
    expect(screen.getByText(/IA asistida/)).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith("/tutor/turn", {
      student_assignment_id: "a1", question_id: "q1", step: 1,
    });
  });
});

describe("Idioma del estudiante", () => {
  it("guarda preferencia con su propia cuenta y deja claras las traducciones verificadas", async () => {
    vi.spyOn(api, "get").mockImplementation(async (path: string) => {
      if (path === "/languages") return [{ code: "es", name: "Español", variants: [] },
                                         { code: "qu", name: "Quechua", variants: [] },
                                         { code: "ay", name: "Aimara", variants: [] }];
      if (path === "/students/me/languages") return {
        mother_language: null, mother_variant_id: null, preferred_language: null,
      };
      throw new Error("Unexpected endpoint");
    });
    const put = vi.spyOn(api, "put").mockResolvedValue({
      mother_language: "qu", mother_variant_id: null, preferred_language: "ay",
    });
    render(<MemoryRouter><StudentLanguageSettings /></MemoryRouter>);
    const mother = await screen.findByLabelText("Mi lengua materna");
    await userEvent.selectOptions(mother, "qu");
    await userEvent.selectOptions(screen.getByLabelText("Idioma en que prefiero aprender"), "ay");
    await userEvent.click(screen.getByRole("button", { name: "Guardar mi idioma" }));
    await waitFor(() => expect(put).toHaveBeenCalledWith("/students/me/languages", {
      mother_language_code: "qu", mother_variant_id: null, preferred_language_code: "ay",
    }));
    expect(await screen.findByText(/Idioma guardado en tu cuenta/)).toBeInTheDocument();
  });
});

describe("Matrícula existente", () => {
  it("matricula en un aula de otro año sin volver a crear cuenta estudiantil", async () => {
    vi.spyOn(api, "get").mockResolvedValue([{
      id: "student-1", display_name: "Estudiante de prueba", grade_number: 4,
      previous_classroom: "Aula 2026", previous_academic_year: 2026,
    }]);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const post = vi.spyOn(api, "post").mockResolvedValue({ status: "ENROLLED" });
    const reload = vi.fn().mockResolvedValue(undefined);
    render(<ExistingEnrollment classroomId="room-2027" onEnrolled={reload} />);
    await userEvent.selectOptions(await screen.findByLabelText("Estudiante de año anterior"), "student-1");
    await userEvent.click(screen.getByRole("button", { name: "Confirmar matrícula" }));
    await waitFor(() => expect(post).toHaveBeenCalledWith("/classrooms/room-2027/enrollments", {
      student_id: "student-1",
    }));
    expect(reload).toHaveBeenCalled();
  });
});
