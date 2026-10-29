import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StudentHome } from "../pages/StudentHome";
import { api } from "../services/api";
import { offlineCourses } from "../services/offlineCourses";
import { offlineTasks } from "../services/offlineTasks";

vi.mock("../app/AuthContext", () => ({
  useAuth: () => ({ user: { id: "student1", role: "STUDENT", display_name: "Estudiante" } }),
}));
vi.mock("../services/offlineCourses", () => ({
  offlineCourses: { list: vi.fn(), save: vi.fn() },
}));
vi.mock("../services/offlineTasks", () => ({
  offlineTasks: { list: vi.fn(), save: vi.fn() },
}));

const catalog = [
  { id:"room1:math", subject_id:"math", name:"Matemática", classroom_id:"room1",
    classroom_name:"Aula Multigrado", academic_year:2026, grade_id:4, is_demo:false },
  { id:"room1:comm", subject_id:"comm", name:"Comunicación", classroom_id:"room1",
    classroom_name:"Aula Multigrado", academic_year:2026, grade_id:4, is_demo:false },
];
const task = {
  student_assignment_id:"sa-math", title:"Sumas del cuarto grado", subject:"Matemática",
  course_id:"room1:math", instructions:"Resuelve las preguntas",
};

beforeEach(() => {
  vi.mocked(offlineCourses.list).mockResolvedValue([]);
  vi.mocked(offlineCourses.save).mockResolvedValue();
  vi.mocked(offlineTasks.list).mockResolvedValue([]);
  vi.mocked(offlineTasks.save).mockResolvedValue();
});
afterEach(() => vi.restoreAllMocks());

describe("Cursos del estudiante en la web", () => {
  it("muestra cursos activos del grado antes de recibir tareas, sin inventar actividades", async () => {
    vi.spyOn(api, "get").mockImplementation(async (path: string) => {
      if (path === "/sync/courses") return catalog;
      if (path.startsWith("/sync/pull")) return { tasks: [], cursor: 0, has_more: false };
      if (path === "/progress/me") return [];
      throw new Error("Ruta inesperada");
    });
    render(<MemoryRouter><StudentHome focus="courses"/></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Matemática" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Comunicación" })).toBeInTheDocument();
    expect(screen.getAllByText(/Aún sin tareas publicadas/)).toHaveLength(2);
    await waitFor(() => expect(offlineCourses.save).toHaveBeenCalledWith("student1", catalog));
  });

  it("permite consultar cursos y tareas guardadas aunque el servidor esté desconectado", async () => {
    vi.mocked(offlineCourses.list).mockResolvedValue(catalog);
    vi.mocked(offlineTasks.list).mockResolvedValue([task]);
    vi.spyOn(api, "get").mockRejectedValue(new Error("Sin conexión"));
    render(<MemoryRouter><StudentHome focus="courses"/></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Matemática" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Comunicación" })).toBeInTheDocument();
    const link = await screen.findByRole("link", { name: /Sumas del cuarto grado/ });
    expect(link).toHaveAttribute("href", "/estudiante/actividad/sa-math");
    expect(screen.getByText(/Se muestran los cursos guardados/)).toBeInTheDocument();
  });
});
