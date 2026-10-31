import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StudentTutor } from "../pages/StudentTutor";
import { api } from "../services/api";
import { offlineTasks } from "../services/offlineTasks";

vi.mock("../app/AuthContext", () => ({
  useAuth: () => ({ user: { id: "alumno-1", display_name: "Alumno", role: "STUDENT" } }),
}));
vi.mock("../services/offlineTasks", () => ({
  offlineTasks: { list: vi.fn(), save: vi.fn() },
}));

beforeEach(() => vi.mocked(offlineTasks.list).mockResolvedValue([]));
afterEach(() => vi.restoreAllMocks());

describe("Tutor IA KAWSAY visible sin respuestas inventadas", () => {
  it("muestra tareas reales asignadas, estado del modelo y acceso a pista", async () => {
    vi.spyOn(api, "get").mockImplementation(async (path: string) => {
      if (path === "/tutor/status") return {
        ai_configured: true, provider: "ollama", model_health_verified: false, message: "Configurado",
      };
      if (path.startsWith("/sync/pull")) return {
        cursor: 1, has_more: false, tasks: [{student_assignment_id: "act-1", title: "Problemas de fracciones",
          subject: "Matemática", questions: [{id:"q1", prompt:"¿Cuál es mayor?"}]}],
      };
      throw new Error("Ruta no esperada");
    });
    render(<MemoryRouter><StudentTutor /></MemoryRouter>);
    expect(await screen.findByRole("heading", {name:"Tutor IA KAWSAY"})).toBeInTheDocument();
    expect(await screen.findByText(/IA configurada: ollama/)).toBeInTheDocument();
    expect(screen.getByText(/La disponibilidad se comprueba al pedir una pista/)).toBeInTheDocument();
    const access = screen.getByRole("link", {name:/Abrir tutor/});
    expect(access).toHaveAttribute("href", "/estudiante/actividad/act-1");
    expect(screen.getByText("Problemas de fracciones")).toBeInTheDocument();
  });

  it("sin Internet mantiene actividad descargada y no inventa LLM", async () => {
    vi.mocked(offlineTasks.list).mockResolvedValue([
      {student_assignment_id:"cache-1",title:"Lectura del bosque",subject:"Comunicación"},
    ]);
    vi.spyOn(api, "get").mockRejectedValue(new Error("offline"));
    render(<MemoryRouter><StudentTutor/></MemoryRouter>);
    const access = await screen.findByRole("link", {name:/Abrir tutor/});
    expect(access).toHaveAttribute("href", "/estudiante/actividad/cache-1");
    await waitFor(() => expect(screen.getByText(/Sin conexión con el servidor/)).toBeInTheDocument());
    expect(screen.getByText(/El estado del modelo no se pudo verificar/)).toBeInTheDocument();
  });

  it("sin un modelo configurado no lo anuncia como IA generativa", async () => {
    vi.spyOn(api, "get").mockImplementation(async (path: string) => path === "/tutor/status"
      ? {ai_configured:false,provider:"none",model_health_verified:false,message:"Reglas"}
      : {tasks:[],has_more:false,cursor:0});
    render(<MemoryRouter><StudentTutor/></MemoryRouter>);
    expect(await screen.findByText(/Aún no se ha configurado un modelo generativo/)).toBeInTheDocument();
  });
});
