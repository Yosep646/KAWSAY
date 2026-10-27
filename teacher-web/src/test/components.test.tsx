import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QuestionsEditor } from "../components/QuestionsEditor";
import { FlagCard } from "../components/FlagCard";
import { Login } from "../pages/Login";
import { Students } from "../pages/Students";
import { AuthProvider } from "../app/AuthContext";
import { App } from "../app/App";
import * as svc from "../services/api";
import type { Question, SupportFlag } from "../types/api";

const flag: SupportFlag = {
  id: "f1", status: "OPEN", student: { id: "s1", display_name: "Juan", grade: "1.º PRIMARIA" },
  competency: { id: "c1", name: "Resuelve problemas de cantidad" }, rule_id: "R-SUP-001", rule_version: "1",
  message: "Se recomienda revisar el progreso de Juan en Resuelve problemas de cantidad.", recommendation: "Actividad guiada",
  evidence: { window: 5, difficult: 4, hints_total: 6, wrong_attempts_total: 11, distinct_days: 1, topics: ["Comparar cantidades"],
    results: [{ question_id: "q1", score: 0, correct: false, attempts: 3, hints: 2, at: "2026-05-04T10:00:00Z", topic: "Comparar cantidades" }] },
};

describe("FlagCard", () => {
  it("muestra la evidencia, no solo un nivel de riesgo, y aclara que no es un diagnóstico", () => {
    render(<FlagCard flag={flag} onChanged={() => undefined} />);
    expect(screen.getByText(/4 de los últimos 5 ejercicios presentan dificultad/)).toBeInTheDocument();
    expect(screen.getByText(/6 pistas utilizadas · 11 intentos incorrectos/)).toBeInTheDocument();
    expect(screen.getByText(/Regla R-SUP-001 v1/)).toBeInTheDocument();
    expect(screen.getByText(/Esto no es un diagnóstico/)).toBeInTheDocument();
    expect(screen.queryByText(/riesgo alto/i)).toBeNull();
  });

  it("registra una intervención vinculada a la alerta", async () => {
    const post = vi.spyOn(svc.api, "post").mockResolvedValue({ id: "i1" });
    const changed = vi.fn();
    render(<FlagCard flag={flag} onChanged={changed} />);
    await userEvent.click(screen.getByText("REGISTRAR INTERVENCIÓN"));
    await userEvent.type(screen.getByLabelText("Estrategia"), "Actividad guiada con material concreto");
    await userEvent.click(screen.getByText("Guardar intervención"));
    await waitFor(() => expect(changed).toHaveBeenCalled());
    expect(post).toHaveBeenCalledWith("/interventions", expect.objectContaining({ student_id: "s1", competency_id: "c1", support_flag_id: "f1" }));
  });
});

describe("Login y control de acceso", () => {
  beforeEach(() => { sessionStorage.clear(); localStorage.removeItem("kawsay_last_email"); svc.setTokens(null); vi.restoreAllMocks(); });

  it("ofrece administrador, docente y estudiante con controles accesibles y recuperación honesta", async () => {
    render(<MemoryRouter><AuthProvider><Login /></AuthProvider></MemoryRouter>);
    expect(screen.getByRole("button", {name:"Administrador"})).toHaveAttribute("aria-pressed","true");
    await userEvent.click(screen.getByRole("button", {name:"Docente",exact:true}));
    expect(screen.getByRole("button", {name:"Docente",exact:true})).toHaveAttribute("aria-pressed","true");
    await userEvent.click(screen.getByRole("button", {name:"Estudiante",exact:true}));
    expect(screen.getByRole("button", {name:"Estudiante",exact:true})).toHaveAttribute("aria-pressed","true");
    expect(screen.getByRole("button", {name:"Código y PIN"})).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", {name:"¿Olvidaste tu contraseña?"}));
    expect(screen.getByRole("status")).toHaveTextContent("Solicita a tu docente");
    expect(screen.getByText(/Más educación/)).toBeInTheDocument();
  });

  it("muestra el error del servidor sin exponer detalles", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ code: "unauthorized", message: "Credenciales inválidas" }), { status: 401 }));
    render(<MemoryRouter><AuthProvider><Login /></AuthProvider></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Correo"), "a@b.pe");
    await userEvent.type(screen.getByLabelText("Contraseña"), "mala");
    await userEvent.click(screen.getByText("Ingresar"));
    expect(await screen.findByRole("alert")).toHaveTextContent("Credenciales inválidas");
  });

  it("un estudiante no puede entrar al panel docente", async () => {
    const t = { access_token: "A", refresh_token: "R", expires_in: 900, user: { id: "u", role: "STUDENT", display_name: "Kid" } };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(t), { status: 200 }));
    render(<MemoryRouter><AuthProvider><Login /></AuthProvider></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Correo"), "k@b.pe");
    await userEvent.type(screen.getByLabelText("Contraseña"), "x");
    await userEvent.click(screen.getByText("Ingresar"));
    expect(await screen.findByRole("alert")).toHaveTextContent("solo para docentes");
    expect(svc.hasStoredSession()).toBe(false);
  });

  it("sin sesión redirige a /login", async () => {
    render(<MemoryRouter initialEntries={["/aulas"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", {name: "Bienvenido"})).toBeInTheDocument();
  });

  it("permite acceso de estudiante y muestra sus datos sin exponer rutas docentes", async () => {
    vi.spyOn(crypto, "randomUUID").mockReturnValue("11111111-1111-4111-8111-111111111111");
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("student-login")) return new Response(JSON.stringify({ access_token: "A", refresh_token: "R", expires_in: 900, user: { id: "u", role: "STUDENT", display_name: "Ana" } }), { status: 200 });
      if (url.includes("sync/pull")) return new Response(JSON.stringify({ tasks: [{ student_assignment_id: "a", title: "Mi tarea", subject: "Matemática", instructions: "Resuelve" }], has_more: false }), { status: 200 });
      return new Response(JSON.stringify([{ competency: "Cantidad", percent: 70 }]), { status: 200 });
    });
    localStorage.removeItem("kawsay_web_device_id");
    render(<MemoryRouter initialEntries={["/login"]}><App /></MemoryRouter>);
    await userEvent.click(screen.getByRole("button", {name: "Estudiante", exact: true}));
    await userEvent.click(screen.getByRole("button", {name: "Código y PIN"}));
    await userEvent.type(screen.getByLabelText("Código de estudiante"), "ABCD");
    await userEvent.type(screen.getByLabelText("PIN"), "1234");
    await userEvent.click(screen.getByText("Ingresar"));
    expect(await screen.findByText("Mi tarea")).toBeInTheDocument();
    expect(screen.getByText("70 % de progreso")).toBeInTheDocument();
    expect(screen.queryByText("Mis aulas")).not.toBeInTheDocument();
    expect(screen.getByText(/Puedes responder actividades descargadas sin conexión/)).toBeInTheDocument();
  });

  it("consulta actividades por páginas usando el límite admitido por la API", async () => {
    vi.spyOn(crypto, "randomUUID").mockReturnValue("11111111-1111-4111-8111-111111111111");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("student-login")) return new Response(JSON.stringify({ access_token: "A", refresh_token: "R", expires_in: 900, user: { id: "u", role: "STUDENT", display_name: "Ana" } }));
      if (url.includes("cursor=0&limit=50")) return new Response(JSON.stringify({ tasks: [], cursor: 7, has_more: true }));
      if (url.includes("cursor=7&limit=50")) return new Response(JSON.stringify({ tasks: [{ student_assignment_id: "b", title: "Actividad siguiente", subject: null, instructions: "Lee" }], cursor: 8, has_more: false }));
      return new Response(JSON.stringify([]));
    });
    render(<MemoryRouter initialEntries={["/login"]}><App /></MemoryRouter>);
    await userEvent.click(screen.getByRole("button", {name: "Estudiante", exact: true}));
    await userEvent.click(screen.getByRole("button", {name: "Código y PIN"}));
    await userEvent.type(screen.getByLabelText("Código de estudiante"), "ABCD");
    await userEvent.type(screen.getByLabelText("PIN"), "1234");
    await userEvent.click(screen.getByText("Ingresar"));
    await userEvent.click(await screen.findByText("Ver más actividades"));
    expect(await screen.findByText("Actividad siguiente")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("cursor=7&limit=50"))).toBe(true);
  });
});

describe("QuestionsEditor", () => {
  it("permite agregar preguntas, marcar la correcta y escribir pistas", async () => {
    let qs: Question[] = [];
    const { rerender } = render(<QuestionsEditor questions={qs} onChange={(q) => { qs = q; }} />);
    await userEvent.click(screen.getByText("+ Agregar pregunta"));
    expect(qs).toHaveLength(1);
    rerender(<QuestionsEditor questions={qs} onChange={(q) => { qs = q; }} />);
    await userEvent.click(screen.getByLabelText("correcta 2"));
    expect(qs[0]?.correct_answer).toEqual({ index: 1 });
  });

  it("no permite editar cuando la variante está publicada", () => {
    const q: Question = { type: "MULTIPLE_CHOICE", prompt: "¿?", options: ["a", "b"], correct_answer: { index: 0 }, hints: [], explanation: null, difficulty: 2 };
    render(<QuestionsEditor questions={[q]} onChange={() => undefined} disabled />);
    expect(screen.queryByText("+ Agregar pregunta")).toBeNull();
    expect(screen.getByLabelText("opción 1").closest("fieldset")).toBeDisabled();
  });
});

describe("Gestión de estudiantes e idiomas", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("carga la preferencia declarada y guarda el idioma completo sin inferirlo", async () => {
    vi.spyOn(svc.api, "get").mockImplementation(async (path: string) => {
      if (path === "/classrooms") return [{ id: "r1", school_id: "e1", name: "Aula multigrado", academic_year: 2026 }];
      if (path === "/languages") return [
        { code: "es", name: "Español", variants: [] },
        { code: "qu", name: "Quechua", variants: [{ id: "v1", code: "q1", name: "Variante verificada", note: null }] },
        { code: "ay", name: "Aimara", variants: [] },
      ];
      if (path === "/classrooms/r1") return {
        id: "r1", school_id: "e1", name: "Aula multigrado", academic_year: 2026, grades_present: ["1.º PRIMARIA"],
        students: [{ id: "s1", display_name: "Rosa", grade_id: 1, grade_level: "PRIMARIA", grade_number: 1 }],
      };
      if (path === "/curriculum/grades") return [{ id: 1, level: "PRIMARIA", number: 1 }];
      if (path === "/students/s1/languages") return { mother_language: null, mother_variant_id: null, preferred_language: null };
      throw new Error(`GET inesperado: ${path}`);
    });
    const put = vi.spyOn(svc.api, "put").mockResolvedValue({ mother_language: "qu", mother_variant_id: "v1", preferred_language: "ay" });

    render(<MemoryRouter><Students /></MemoryRouter>);
    await userEvent.selectOptions(await screen.findByLabelText("Aula"), "r1");
    await userEvent.click(await screen.findByText("Configurar idioma"));
    await userEvent.selectOptions(await screen.findByLabelText("Lengua materna"), "qu");
    await userEvent.selectOptions(await screen.findByLabelText("Variante declarada"), "v1");
    await userEvent.selectOptions(screen.getByLabelText("Idioma preferido para aprender"), "ay");
    await userEvent.click(screen.getByText("Guardar idioma"));

    await waitFor(() => expect(put).toHaveBeenCalledWith("/students/s1/languages", {
      mother_language_code: "qu", mother_variant_id: "v1", preferred_language_code: "ay",
    }));
    expect(screen.getByText(/traducción humana verificada/)).toBeInTheDocument();
  });
});
